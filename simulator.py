# Copyright information
#
# © [2025] LimX Dynamics Technology Co., Ltd. All rights reserved.
#
# DACH_TRON2A-only MuJoCo simulator.
#   - Loads robot.xml (arms + head) or robot_grasper.xml (arms + head + 2F gripper).
#   - Motor (arms + head) commands/state and IMU go over the limxsdk-lowlevel SDK
#     (sim-side API: subscribeRobotCmdForSim / publishRobotStateForSim / publishImuDataForSim).
#   - The 2F gripper also goes over limxsdk, sim-side: subscribeGripperCmdForSim /
#     publishGripperStateForSim (GripperCmd opening/speed/force, GripperState q, 0~100 per side
#     [L,R]). Requires limxsdk >= 4.0.2 (sim-side gripper API). limxsdk gripper clients
#     (publishGripperCmd/subscribeGripperState) interoperate on /limx/2F-gripper/* unchanged.

import os
import sys
import time
import mujoco
import mujoco.viewer as viewer
import yaml

import limxsdk.datatypes as datatypes
import limxsdk.robot.Robot as Robot
import limxsdk.robot.RobotType as RobotType


class SimulatorMujoco:
    def __init__(self, asset_path, joint_sensor_names):
        self.joint_sensor_names = joint_sensor_names
        self.joint_num = len(joint_sensor_names)

        # Load the MuJoCo model and data from the specified XML asset path
        self.mujoco_model = mujoco.MjModel.from_xml_path(asset_path)
        self.mujoco_data = mujoco.MjData(self.mujoco_model)

        # The model may carry extra actuators beyond the controlled joints (robot_grasper.xml
        # adds grasper base + drive actuators). Require at least joint_num actuators; per-joint
        # indices are resolved by name in joint_map below.
        if self.mujoco_model.nu < self.joint_num:
            raise ValueError(
                f"Model has only {self.mujoco_model.nu} actuators but {self.joint_num} joint_sensor_names."
            )

        # Store original control ranges for restoration (manual mode narrows them to joint limits)
        self.original_ctrlrange = self.mujoco_model.actuator_ctrlrange.copy()

        # Launch the MuJoCo viewer in passive mode
        self.viewer = viewer.launch_passive(self.mujoco_model, self.mujoco_data,
                                            key_callback=self.key_callback,
                                            show_left_ui=True, show_right_ui=True)
        self.viewer.cam.distance = 10
        self.viewer.cam.elevation = -20

        self.dt = self.mujoco_model.opt.timestep
        self.fps = 1 / self.dt

        self.paused = False        # paused = manual control, running = auto control
        self.manual_mode = False   # manual control mode flag (synced with paused)

        # Robot command (input) — replaced wholesale by the limxsdk callback (see _on_robot_cmd).
        self.robot_cmd = datatypes.RobotCmd()
        self.robot_cmd.mode = [0.0] * self.joint_num
        self.robot_cmd.q = [0.0] * self.joint_num
        self.robot_cmd.dq = [0.0] * self.joint_num
        self.robot_cmd.tau = [0.0] * self.joint_num
        self.robot_cmd.Kp = [0.0] * self.joint_num
        self.robot_cmd.Kd = [0.0] * self.joint_num

        # Robot state (output) — published every tick over limxsdk.
        self.robot_state = datatypes.RobotState()
        self.robot_state.tau = [0.0] * self.joint_num
        self.robot_state.q = [0.0] * self.joint_num
        self.robot_state.dq = [0.0] * self.joint_num

        # IMU data — extracted from the base_imu_* sensors, published over limxsdk.
        self.imu_data = datatypes.ImuData()

        # Resolve each controlled joint's qpos/qvel/actuator index BY NAME. robot_grasper.xml has
        # a floating base and interleaves the grasper linkage between the arms (the right arm's
        # qpos does not immediately follow the left), so positional offsets are wrong; name
        # resolution is correct for any joint/actuator ordering.
        self.joint_map = []
        for name in self.joint_sensor_names:
            jid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_JOINT, name)
            if jid < 0:
                raise ValueError(f"joint '{name}' not found in model")
            aid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, name + "_ctrl")
            if aid < 0:
                # fallback: match by the joint an actuator drives (actuators here are named e.g.
                # "proximal_pitch_L"/"head_yaw", not "<joint>_ctrl")
                for a in range(self.mujoco_model.nu):
                    if self.mujoco_model.actuator_trnid[a, 0] == jid:
                        aid = a
                        break
            self.joint_map.append({
                'qpos': int(self.mujoco_model.jnt_qposadr[jid]),
                'qvel': int(self.mujoco_model.jnt_dofadr[jid]),
                'act':  int(aid),
            })

        # LIMX two-finger gripper control (auto-enabled when the grasper drive actuators exist,
        # i.e. robot_grasper.xml). Sets self.gripper_topic_cmd/state used by _init_comm.
        self.gripper_control_enabled = False
        if (mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, "grasper_L_drive_Joint_ctrl") >= 0
                and mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, "grasper_R_drive_Joint_ctrl") >= 0):
            self._init_gripper_control()

        # Set up communication (limxsdk sim-side: motor/IMU + gripper).
        self._init_comm()

    # ---------------- communication (limxsdk sim-side: motor/IMU + gripper) ----------------

    def _init_comm(self):
        """Motor(arms+head)+IMU and the 2F gripper all over the limxsdk sim-side API.

        Requires limxsdk >= 4.0.2 (sim-side gripper methods subscribeGripperCmdForSim /
        publishGripperStateForSim). limxsdk gripper clients (publishGripperCmd /
        subscribeGripperState) interoperate on /limx/2F-gripper/* unchanged.
        """
        # limxsdk sim-side node (motor cmd IN, robot state + IMU OUT; gripper cmd IN / state OUT).
        self.sdk = Robot(RobotType.Tron2, is_sim=True)
        sdk_ok = self.sdk.init(os.getenv("ROBOT_IP", "127.0.0.1"))
        self.sdk.subscribeRobotCmdForSim(self._on_robot_cmd)
        print(f"✅ limxsdk 初始化{'成功' if sdk_ok else '（init 返回 False，仍将发布仿真状态）'}"
              f" (Tron2, is_sim=True)")
        print("   📡 电机指令入: /motor/cmd  (subscribeRobotCmdForSim, RobotCmd)")
        print("   📤 电机状态出: /motor/state (publishRobotStateForSim, RobotState)")
        print("   📤 IMU 出:     /ImuData     (publishImuDataForSim, ImuData)")

        # Gripper over the limxsdk sim-side API (only when the grasper model is loaded).
        if self.gripper_control_enabled:
            self.sdk.subscribeGripperCmdForSim(self._on_gripper_cmd)
            print("   🤏 夹爪: /limx/2F-gripper/cmd (subscribeGripperCmdForSim, GripperCmd) → "
                  "/limx/2F-gripper/state (publishGripperStateForSim, GripperState)")

    def _on_robot_cmd(self, cmd):
        """limxsdk sim-side robot-command callback (runs on an SDK dispatch thread).

        `cmd` is a datatypes.RobotCmd (q/dq/tau/Kp/Kd/mode, one entry per motor). Store the whole
        object atomically; the control loop snapshots self.robot_cmd once per tick.
        """
        self.robot_cmd = cmd

    def _publish_robot_state(self):
        """Publish joint state (q/dq/tau, per joint) over limxsdk."""
        try:
            st = datatypes.RobotState()
            st.stamp = time.time_ns()
            st.q = [float(v) for v in self.robot_state.q]
            st.dq = [float(v) for v in self.robot_state.dq]
            st.tau = [float(v) for v in self.robot_state.tau]
            st.motor_names = list(self.joint_sensor_names)
            self.sdk.publishRobotStateForSim(st)
        except Exception:
            pass

    def _publish_imu_data(self):
        """Publish IMU (acc/gyro/quat) over limxsdk. self.imu_data.quat holds MuJoCo order
        [w,x,y,z]; limxsdk expects [x,y,z,w]."""
        try:
            imu = datatypes.ImuData()
            imu.stamp = time.time_ns()
            imu.acc = [float(v) for v in self.imu_data.acc]
            imu.gyro = [float(v) for v in self.imu_data.gyro]
            w, x, y, z = self.imu_data.quat
            imu.quat = [float(x), float(y), float(z), float(w)]
            self.sdk.publishImuDataForSim(imu)
        except Exception:
            pass

    # Callback for keypress events in the MuJoCo viewer
    def key_callback(self, keycode):
        # Space (32): toggle pause/resume (pause = manual control, resume = auto control)
        if keycode == 32:
            self.paused = not self.paused
            self.manual_mode = self.paused
            if self.paused:
                print("⏸️  PAUSED - Manual control enabled")
                self._init_manual_mode()
            else:
                print("▶️  RESUMED - Auto control active")
                self._clear_manual_mode()

    def _ctrl_indices(self, i):
        """(qpos_idx, qvel_idx, act_idx) for controlled joint i, resolved by name via joint_map."""
        m = self.joint_map[i]
        return m['qpos'], m['qvel'], m['act']

    # ---------------- LIMX two-finger gripper control (DACH grasper) ----------------

    def _load_gripper_config(self):
        """Load gripper tunables from yaml, falling back to built-in defaults (in the
        revolute drive-joint domain) if the file is missing or fields are absent."""
        defaults = {
            'topics': {'cmd': '/limx/2F-gripper/cmd', 'state': '/limx/2F-gripper/state'},
            'joint_range': {'q_low': -0.09522, 'q_high': 0.77302},  # drive joint (rad)
            'full_travel_time_s': 1.0,
            'tau_min_n': 0.3,
            'tau_full_n': 2.0,      # <= drive actuator ctrlrange (±2)
            'gains': {'kp': 2.0, 'kd': 0.05},
        }
        path = os.environ.get(
            'GRIPPER_CONFIG',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gripper_config.yaml'))
        cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in defaults.items()}
        try:
            with open(path) as f:
                loaded = (yaml.safe_load(f) or {}).get('gripper', {}) or {}
            for k, v in loaded.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k] = {**cfg[k], **v}
                else:
                    cfg[k] = v
            print(f"✅ 夹爪配置已加载: {path}")
        except FileNotFoundError:
            print(f"⚠️  未找到夹爪配置 {path}，使用内置默认值")
        except Exception as e:
            print(f"⚠️  夹爪配置解析失败({e})，使用内置默认值")
        return cfg

    @staticmethod
    def _polyval(coef, x):
        """Evaluate a MuJoCo equality polycoef: c0 + c1*x + c2*x^2 + c3*x^3 + c4*x^4."""
        y = 0.0
        for c in reversed(coef):
            y = y * x + c
        return y

    def _eq_polycoef(self, jid):
        """Return the <equality><joint> polycoef mapping the drive joint to follower
        joint `jid` (identity fallback), used for kinematic posing in manual mode."""
        try:
            for e in range(self.mujoco_model.neq):
                if (self.mujoco_model.eq_type[e] == mujoco.mjtEq.mjEQ_JOINT
                        and self.mujoco_model.eq_obj1id[e] == jid):
                    return [float(x) for x in self.mujoco_model.eq_data[e][:5]]
        except Exception:
            pass
        return [0.0, 1.0, 0.0, 0.0, 0.0]

    def _init_gripper_control(self):
        """Resolve gripper joint/actuator indices and derive control constants.

        The grasper is a single-DOF linkage: one revolute drive joint per side
        (grasper_{L,R}_drive_Joint) actuated by grasper_{L,R}_drive_Joint_ctrl; the
        jaw fingers follow via <equality> polycoef couplings (read for manual posing)."""
        cfg = self._load_gripper_config()
        self.gripper_cfg = cfg
        self.gripper_topic_cmd = cfg['topics']['cmd']
        self.gripper_topic_state = cfg['topics']['state']
        self.grip_q_low = float(cfg['joint_range']['q_low'])
        self.grip_q_high = float(cfg['joint_range']['q_high'])
        self.grip_q_span = self.grip_q_high - self.grip_q_low
        ttime = float(cfg['full_travel_time_s'])
        self.grip_v_full = self.grip_q_span / ttime if ttime > 1e-9 else 0.0
        self.grip_tau_min = float(cfg['tau_min_n'])
        self.grip_tau_full = float(cfg['tau_full_n'])
        self.grip_kp = float(cfg['gains']['kp'])
        self.grip_kd = float(cfg['gains']['kd'])

        # side -> (revolute drive joint, its actuator, [visual jaw follower joints])
        spec = {
            'left':  ('grasper_L_drive_Joint', 'grasper_L_drive_Joint_ctrl',
                      ['grasper_L_jaw_left_Joint', 'grasper_L_jaw_right_Joint']),
            'right': ('grasper_R_drive_Joint', 'grasper_R_drive_Joint_ctrl',
                      ['grasper_R_jaw_left_Joint', 'grasper_R_jaw_right_Joint']),
        }
        self.gripper_idx = {}
        for side, (jd, an, followers) in spec.items():
            jid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_JOINT, jd)
            aid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, an)
            if jid < 0 or aid < 0:
                print(f"⚠️  夹爪驱动关节/执行器缺失 ({side})，夹爪控制未启用")
                return
            follower_idx = []
            for fname in followers:
                fj = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_JOINT, fname)
                if fj >= 0:
                    follower_idx.append((int(self.mujoco_model.jnt_qposadr[fj]),
                                         int(self.mujoco_model.jnt_dofadr[fj]),
                                         self._eq_polycoef(fj)))
            self.gripper_idx[side] = {
                'qpos': int(self.mujoco_model.jnt_qposadr[jid]),
                'qvel': int(self.mujoco_model.jnt_dofadr[jid]),
                'act':  int(aid),
                'followers': follower_idx,
            }

        self.grasper_cmd = {}
        for side in ('left', 'right'):
            cur = float(self.mujoco_data.qpos[self.gripper_idx[side]['qpos']])
            self.grasper_cmd[side] = {'q_cmd': 0.0, 'v_cmd': 0.0, 'tau_cmd': 0.0,
                                      'q_tgt': cur, 'active': False}
        self.gripper_control_enabled = True
        print(f"✅ 夹爪控制已启用 (topics: {self.gripper_topic_cmd} / {self.gripper_topic_state})")

    def _on_gripper_cmd(self, cmd):
        """limxsdk sim-side 2F-gripper command callback (runs on an SDK dispatch thread).
        cmd.opening/speed/force are 0~100 per side ([0]=left,[1]=right). Only the command inputs
        (q/v/tau) are mutated here; the slew state (q_tgt) is owned by the main loop."""
        try:
            op = getattr(cmd, 'opening', None)
            sp = getattr(cmd, 'speed', None)
            fo = getattr(cmd, 'force', None)
            n = len(op) if op is not None else 0
            for i, side in enumerate(('left', 'right')):
                if i >= n:
                    break
                c = self.grasper_cmd[side]
                c['q_cmd'] = min(100.0, max(0.0, float(op[i])))
                c['v_cmd'] = min(100.0, max(0.0, float(sp[i]))) if sp is not None and len(sp) > i else 0.0
                c['tau_cmd'] = min(100.0, max(0.0, float(fo[i]))) if fo is not None and len(fo) > i else 0.0
                c['active'] = True
        except Exception:
            pass

    def _apply_gripper_control(self):
        """Per-step gripper update: velocity-limited setpoint slew + force-limited
        position law on the revolute drive joint (automatic), or kinematic set of the
        drive joint + jaw followers via equality polycoef (manual)."""
        if not self.gripper_control_enabled:
            return
        dt = self.dt
        for side, idx in self.gripper_idx.items():
            c = self.grasper_cmd[side]
            q_goal = self.grip_q_low + (c['q_cmd'] / 100.0) * self.grip_q_span
            v_max = (c['v_cmd'] / 100.0) * self.grip_v_full
            step = v_max * dt
            qt = c['q_tgt']
            if qt < q_goal:
                qt = min(qt + step, q_goal)
            elif qt > q_goal:
                qt = max(qt - step, q_goal)
            c['q_tgt'] = qt

            if self.manual_mode:
                # Kinematic: set drive joint + evaluate jaw followers via equality polycoef
                self.mujoco_data.qpos[idx['qpos']] = qt
                self.mujoco_data.qvel[idx['qvel']] = 0.0
                for fqpos, fqvel, poly in idx['followers']:
                    self.mujoco_data.qpos[fqpos] = self._polyval(poly, qt)
                    self.mujoco_data.qvel[fqvel] = 0.0
            else:
                qpos = self.mujoco_data.qpos[idx['qpos']]
                qvel = self.mujoco_data.qvel[idx['qvel']]
                tau_lim = self.grip_tau_min + (c['tau_cmd'] / 100.0) * (self.grip_tau_full - self.grip_tau_min)
                trq = self.grip_kp * (qt - qpos) - self.grip_kd * qvel
                trq = max(-tau_lim, min(tau_lim, trq))
                self.mujoco_data.ctrl[idx['act']] = trq

    def _publish_gripper_state(self):
        """Publish actual gripper opening over limxsdk (publishGripperStateForSim).
        GripperState.q = opening 0~100 ([0]=left,[1]=right) derived from the drive-joint angle."""
        if not self.gripper_control_enabled:
            return
        try:
            q_pct = []
            for side in ('left', 'right'):
                qpos = float(self.mujoco_data.qpos[self.gripper_idx[side]['qpos']])
                pct = (qpos - self.grip_q_low) / self.grip_q_span * 100.0 if self.grip_q_span > 1e-9 else 0.0
                q_pct.append(min(100.0, max(0.0, pct)))
            gs = datatypes.GripperState()
            gs.stamp = time.time_ns()
            gs.q = q_pct
            gs.v = [0.0, 0.0]
            gs.vd = [0.0, 0.0]
            gs.tau = [0.0, 0.0]
            self.sdk.publishGripperStateForSim(gs)
        except Exception:
            pass

    # ---------------- manual mode ----------------

    def _init_manual_mode(self):
        """Set control sliders to current joint positions for a smooth transition to manual."""
        self._set_manual_control_ranges()
        for i in range(self.joint_num):
            qpos_idx, qvel_idx, act = self._ctrl_indices(i)
            self.mujoco_data.ctrl[act] = self.mujoco_data.qpos[qpos_idx]

    def _trigger_ui_rebuild(self):
        """Inject a tiny ctrlrange offset to force the viewer to rebuild the Control panel."""
        self.ui_offset_toggle = 1e-9
        for i in range(min(self.mujoco_model.nu, self.joint_num)):
            joint_id = self.mujoco_model.actuator(i).trnid[0]
            if joint_id >= 0:
                jnt_min = self.mujoco_model.jnt_range[joint_id][0]
                jnt_max = self.mujoco_model.jnt_range[joint_id][1]
                self.mujoco_model.actuator_ctrlrange[i][0] = jnt_min + self.ui_offset_toggle
                self.mujoco_model.actuator_ctrlrange[i][1] = jnt_max + self.ui_offset_toggle

    def _clear_manual_mode(self):
        """Restore control ranges and clear commands for automatic mode."""
        self.mujoco_model.actuator_ctrlrange[:] = self.original_ctrlrange
        for i in range(self.joint_num):
            _, _, act = self._ctrl_indices(i)
            self.mujoco_data.ctrl[act] = 0.0

    def _set_manual_control_ranges(self):
        """Set actuator control ranges to match joint limits (nicer manual sliders)."""
        for i in range(min(self.mujoco_model.nu, self.joint_num)):
            joint_id = self.mujoco_model.actuator(i).trnid[0]
            if joint_id >= 0:
                self.mujoco_model.actuator_ctrlrange[i] = self.mujoco_model.jnt_range[joint_id]

    # ---------------- main tick / loop ----------------

    def _simulation_tick(self):
        """One control/physics tick: poll gripper cmd, apply control (kinematic or torque),
        update robot state, publish state + gripper + IMU."""
        # Motor and gripper commands both arrive async via limxsdk sim-side callbacks.

        # Step 1: control
        if self.manual_mode:
            # Manual: ctrl sliders are target positions (kinematic control)
            needs_ui_rebuild = False
            for i in range(self.joint_num):
                qpos_idx, qvel_idx, act = self._ctrl_indices(i)
                target_pos = self.mujoco_data.ctrl[act]
                joint_id = self.mujoco_model.actuator(act).trnid[0]
                if joint_id >= 0:
                    jnt_min = self.mujoco_model.jnt_range[joint_id][0]
                    jnt_max = self.mujoco_model.jnt_range[joint_id][1]
                    # slider dragged onto a torque range (-200~200) -> rebuild the UI
                    if target_pos > jnt_max + 0.05 or target_pos < jnt_min - 0.05:
                        needs_ui_rebuild = True
                    target_pos = max(jnt_min, min(target_pos, jnt_max))
                    self.mujoco_data.ctrl[act] = target_pos
                self.mujoco_data.qpos[qpos_idx] = target_pos
                self.mujoco_data.qvel[qvel_idx] = 0.0

            if self.gripper_control_enabled:
                self._apply_gripper_control()
            if needs_ui_rebuild:
                self._trigger_ui_rebuild()
            mujoco.mj_forward(self.mujoco_model, self.mujoco_data)

        elif not self.paused:
            # Auto: ctrl values are motor torques (dynamic control)
            c = self.robot_cmd   # snapshot (replaced atomically by the SDK callback thread)
            for i in range(self.joint_num):
                qpos_idx, qvel_idx, act = self._ctrl_indices(i)
                if (i < len(c.Kp) and i < len(c.q) and i < len(c.dq) and i < len(c.tau)):
                    self.mujoco_data.ctrl[act] = (
                        c.Kp[i] * (c.q[i] - self.mujoco_data.qpos[qpos_idx]) +
                        c.Kd[i] * (c.dq[i] - self.mujoco_data.qvel[qvel_idx]) +
                        c.tau[i]
                    )
                else:
                    self.mujoco_data.ctrl[act] = 0.0

            if self.gripper_control_enabled:
                self._apply_gripper_control()
            mujoco.mj_step(self.mujoco_model, self.mujoco_data)

        # Step 2: update robot state (always, for state tracking)
        for i in range(self.joint_num):
            qpos_idx, qvel_idx, act = self._ctrl_indices(i)
            self.robot_state.q[i] = self.mujoco_data.qpos[qpos_idx]
            self.robot_state.dq[i] = self.mujoco_data.qvel[qvel_idx]
            self.robot_state.tau[i] = 0.0 if self.manual_mode else self.mujoco_data.ctrl[act]

        # Step 3: publish (only when not paused)
        if not self.paused:
            self._publish_robot_state()
            if self.gripper_control_enabled:
                self._publish_gripper_state()

            # Extract IMU from the base_imu_* sensors (MuJoCo quat order [w,x,y,z]).
            imu_quat_id = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_SENSOR, "base_imu_quat")
            self.imu_data.quat[0] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_quat_id] + 0]
            self.imu_data.quat[1] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_quat_id] + 1]
            self.imu_data.quat[2] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_quat_id] + 2]
            self.imu_data.quat[3] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_quat_id] + 3]

            imu_gyro_id = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_SENSOR, "base_imu_gyro")
            self.imu_data.gyro[0] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_gyro_id] + 0]
            self.imu_data.gyro[1] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_gyro_id] + 1]
            self.imu_data.gyro[2] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_gyro_id] + 2]

            imu_acc_id = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_SENSOR, "base_imu_acc")
            self.imu_data.acc[0] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_acc_id] + 0]
            self.imu_data.acc[1] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_acc_id] + 1]
            self.imu_data.acc[2] = self.mujoco_data.sensordata[self.mujoco_model.sensor_adr[imu_acc_id] + 2]

            self._publish_imu_data()

    def run(self):
        """Main loop: decouple physics stepping from rendering.

        Physics advances to track wall-clock time via a fixed-dt accumulator, while viewer.sync()
        runs on a steady ~60 Hz cadence.
        """
        render_period = 1.0 / 60.0
        max_catchup = 0.05
        self._last_render = time.time()
        sim_clock = time.time()
        print(f"✅ 仿真循环开始 (FPS: {self.fps:.1f}, dt: {self.dt:.4f}s, 渲染: {1.0/render_period:.0f}Hz)")

        while self.viewer.is_running():
            now = time.time()

            if self.paused or self.manual_mode:
                self._simulation_tick()
                sim_clock = now
                self._render_if_due(render_period)
                time.sleep(0.002)
                continue

            if now - sim_clock > max_catchup:
                sim_clock = now - max_catchup
            while sim_clock < now:
                self._simulation_tick()
                sim_clock += self.dt

            self._render_if_due(render_period)

            sleep_until = min(sim_clock, self._last_render + render_period)
            sleep_for = sleep_until - time.time()
            if sleep_for > 0:
                time.sleep(sleep_for)

        # Skip limxsdk's native teardown (it can segfault on interpreter shutdown); work is done.
        os._exit(0)

    def _render_if_due(self, render_period):
        """Sync the viewer on a fixed wall-clock cadence, decoupled from the physics rate."""
        now = time.time()
        if now - self._last_render >= render_period:
            self.viewer.sync()
            self._last_render += render_period
            if now - self._last_render >= render_period:
                self._last_render = now


# DACH_TRON2A joint order (matches XML actuator order): left arm(7) + right arm(7) + head(2).
DACH_JOINT_SENSOR_NAMES = [
    "proximal_pitch_L_Joint", "proximal_roll_L_Joint", "proximal_yaw_L_Joint", "elbow_L_Joint",
    "wrist_yaw_L_Joint", "wrist_pitch_L_Joint", "wrist_roll_L_Joint",
    "proximal_pitch_R_Joint", "proximal_roll_R_Joint", "proximal_yaw_R_Joint", "elbow_R_Joint",
    "wrist_yaw_R_Joint", "wrist_pitch_R_Joint", "wrist_roll_R_Joint",
    "head_pitch_Joint", "head_yaw_Joint",
]


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(
        description="DACH_TRON2A MuJoCo 仿真器 (motor/IMU + 夹爪 全走 limxsdk 仿真侧接口)")
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--grasper", dest="use_grasper", action="store_true", default=None,
                     help="加载带夹爪的 robot_grasper.xml（默认）")
    grp.add_argument("--no-grasper", dest="use_grasper", action="store_false",
                     help="加载不带夹爪的 robot.xml（仅双臂+头）")
    cli_args, _ = parser.parse_known_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Model selection: robot_grasper.xml (default) or robot.xml (--no-grasper / DACH_GRASPER=0).
    use_grasper = cli_args.use_grasper
    if use_grasper is None:
        use_grasper = os.getenv("DACH_GRASPER", "1").lower() not in ("0", "false", "no", "off")
    dach_xml = "robot_grasper.xml" if use_grasper else "robot.xml"
    model_path = f'{script_dir}/robot-description/tron2/DACH_TRON2A/xml/{dach_xml}'
    print(f"🤖 DACH_TRON2A | Model: {model_path} （{'含夹爪' if use_grasper else '无夹爪'}）")

    if not os.path.exists(model_path):
        print(f"Error: The file {model_path} does not exist.")
        sys.exit(1)

    simulator = SimulatorMujoco(model_path, DACH_JOINT_SENSOR_NAMES)
    simulator.run()
