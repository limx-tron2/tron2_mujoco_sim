#!/usr/bin/env python3
import os
import sys
import time
from functools import partial

import mujoco
import mujoco.viewer as viewer
try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

import limxsdk.robot.Rate as Rate
import limxsdk.robot.Robot as Robot
import limxsdk.robot.RobotType as RobotType
import limxsdk.datatypes as datatypes


def load_variant_config(root_dir: str, robot_type: str):
    xml_path = os.path.join(root_dir, "robot-description", "tron2", robot_type, "xml", "robot.xml")

    if robot_type == "SF_TRON2A":
        joint_names = [
            "proximal_pitch_L",
            "proximal_roll_L",
            "proximal_yaw_L",
            "knee_L",
            "ankle_pitch_L",
            "proximal_pitch_R",
            "proximal_roll_R",
            "proximal_yaw_R",
            "knee_R",
            "ankle_pitch_R",
        ]
        sensor_joint_names = list(joint_names)
    elif robot_type == "WF_TRON2A":
        joint_names = [
            "proximal_pitch_L",
            "proximal_roll_L",
            "proximal_yaw_L",
            "knee_L",
            "wheel_L",
            "proximal_pitch_R",
            "proximal_roll_R",
            "proximal_yaw_R",
            "knee_R",
            "wheel_R",
        ]
        sensor_joint_names = [
            "proximal_pitch_L",
            "proximal_roll_L",
            "proximal_yaw_L",
            "knee_L",
            "wheel_L",
            "proximal_pitch_R",
            "proximal_roll_R",
            "proximal_yaw_R",
            "knee_R",
            "wheel_R",
        ]
    else:
        raise ValueError(
            f"Unsupported ROBOT_TYPE: {robot_type}. Supported types: SF_TRON2A, WF_TRON2A"
        )

    return joint_names, sensor_joint_names, xml_path


class SimulatorMujoco:
    JOY_BTNS = {"R1": (5, 7)}

    def __init__(self, asset_path, joint_names, sensor_joint_names, robot):
        self.robot = robot
        self.joint_names = joint_names
        self.sensor_joint_names = sensor_joint_names
        self.joint_num = len(joint_names)

        self.mujoco_model = mujoco.MjModel.from_xml_path(asset_path)
        self.mujoco_data = mujoco.MjData(self.mujoco_model)

        self.viewer = viewer.launch_passive(
            self.mujoco_model,
            self.mujoco_data,
            key_callback=self.key_callback,
            show_left_ui=True,
            show_right_ui=True,
        )
        self.viewer.cam.distance = 10
        self.viewer.cam.elevation = -20

        self.dt = self.mujoco_model.opt.timestep
        self.fps = 1.0 / self.dt
        self.qpos_offset = 7
        self.qvel_offset = 6

        (
            self.sensor_pos_adr,
            self.sensor_vel_adr,
            self.sensor_frc_adr,
        ) = self._resolve_joint_sensor_addrs()

        self.actuator_ids = []
        for name in self.joint_names:
            aid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            if aid == -1:
                aid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{name}_ctrl")
            if aid == -1:
                raise RuntimeError(f"Actuator for '{name}' not found in model.")
            self.actuator_ids.append(aid)

        self.imu_quat_adr = self._sensor_adr("base_imu_quat")
        self.imu_gyro_adr = self._sensor_adr("base_imu_gyro")
        self.imu_acc_adr = self._sensor_adr("base_imu_acc")

        self.robot_cmd = datatypes.RobotCmd()
        self.robot_cmd.mode = [0 for _ in range(self.joint_num)]
        self.robot_cmd.q = [0.0 for _ in range(self.joint_num)]
        self.robot_cmd.dq = [0.0 for _ in range(self.joint_num)]
        self.robot_cmd.tau = [0.0 for _ in range(self.joint_num)]
        self.robot_cmd.Kp = [0.0 for _ in range(self.joint_num)]
        self.robot_cmd.Kd = [0.0 for _ in range(self.joint_num)]

        self.robot_state = datatypes.RobotState()
        self.robot_state.tau = [0.0 for _ in range(self.joint_num)]
        self.robot_state.q = [0.0 for _ in range(self.joint_num)]
        self.robot_state.dq = [0.0 for _ in range(self.joint_num)]

        self.imu_data = datatypes.ImuData()

        self.robot_cmd_callback = partial(self.robot_cmd_cb)
        self.robot.subscribeRobotCmdForSim(self.robot_cmd_callback)
        self.robot.subscribeSensorJoy(self.sensor_joy_cb)
        self._last_r1 = 0
        self._reset_requested = False
        self._pygame_enabled = False
        self._pygame_joystick = None
        self._pygame_last_r1 = 0
        self._setup_pygame_joystick()

    def _sensor_adr(self, name: str) -> int:
        sid = mujoco.mj_name2id(self.mujoco_model, mujoco.mjtObj.mjOBJ_SENSOR, name)
        if sid == -1:
            raise RuntimeError(f"Sensor not found: {name}")
        return self.mujoco_model.sensor_adr[sid]

    def _resolve_joint_sensor_addrs(self):
        pos_adr = [self._sensor_adr(f"{n}_pos") for n in self.sensor_joint_names]
        vel_adr = [self._sensor_adr(f"{n}_vel") for n in self.sensor_joint_names]
        frc_adr = [self._sensor_adr(f"{n}_frc") for n in self.sensor_joint_names]
        return pos_adr, vel_adr, frc_adr

    def robot_cmd_cb(self, robot_cmd: datatypes.RobotCmd):
        self.robot_cmd = robot_cmd

    def sensor_joy_cb(self, joy_msg: datatypes.SensorJoy):
        btns = joy_msg.buttons
        r1 = 0
        for btn_idx in self.JOY_BTNS["R1"]:
            if len(btns) > btn_idx and btns[btn_idx]:
                r1 = 1
                break
        if r1 and not self._last_r1:
            self._reset_requested = True
        self._last_r1 = int(r1)

    def _reset_sim(self):
        mujoco.mj_resetData(self.mujoco_model, self.mujoco_data)
        mujoco.mj_forward(self.mujoco_model, self.mujoco_data)

    def _setup_pygame_joystick(self):
        self._pygame_enabled = False
        if not PYGAME_AVAILABLE:
            return
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() <= 0:
                return
            self._pygame_joystick = pygame.joystick.Joystick(0)
            self._pygame_joystick.init()
            self._pygame_enabled = True
            print(f"simulator pygame joystick ready: {self._pygame_joystick.get_name()}")
        except Exception as exc:  # noqa: BLE001
            self._pygame_enabled = False
            self._pygame_joystick = None
            print(f"simulator pygame joystick init failed: {exc}")

    def _poll_pygame_reset(self):
        if not self._pygame_enabled or self._pygame_joystick is None:
            return
        pygame.event.pump()
        joy = self._pygame_joystick
        num_btns = joy.get_numbuttons()
        r1 = 0
        for btn_idx in self.JOY_BTNS["R1"]:
            if num_btns > btn_idx and joy.get_button(btn_idx):
                r1 = 1
                break
        if r1 and not self._pygame_last_r1:
            self._reset_requested = True
        self._pygame_last_r1 = int(r1)

    def key_callback(self, keycode):
        if keycode in (82, 114):
            self._reset_requested = True

    def _read_state(self):
        sensordata = self.mujoco_data.sensordata
        for i in range(self.joint_num):
            self.robot_state.q[i] = float(sensordata[self.sensor_pos_adr[i]])
            self.robot_state.dq[i] = float(sensordata[self.sensor_vel_adr[i]])
            self.robot_state.tau[i] = float(sensordata[self.sensor_frc_adr[i]])

    def _write_ctrl(self):
        for cmd_idx in range(self.joint_num):
            curr_q = self.robot_state.q[cmd_idx]
            curr_dq = self.robot_state.dq[cmd_idx]
            tau = (
                self.robot_cmd.Kp[cmd_idx] * (self.robot_cmd.q[cmd_idx] - curr_q)
                + self.robot_cmd.Kd[cmd_idx] * (self.robot_cmd.dq[cmd_idx] - curr_dq)
                + self.robot_cmd.tau[cmd_idx]
            )
            self.mujoco_data.ctrl[self.actuator_ids[cmd_idx]] = float(tau)

    def _publish_imu(self):
        sd = self.mujoco_data.sensordata
        self.imu_data.quat[0] = float(sd[self.imu_quat_adr + 0])
        self.imu_data.quat[1] = float(sd[self.imu_quat_adr + 1])
        self.imu_data.quat[2] = float(sd[self.imu_quat_adr + 2])
        self.imu_data.quat[3] = float(sd[self.imu_quat_adr + 3])
        self.imu_data.gyro[0] = float(sd[self.imu_gyro_adr + 0])
        self.imu_data.gyro[1] = float(sd[self.imu_gyro_adr + 1])
        self.imu_data.gyro[2] = float(sd[self.imu_gyro_adr + 2])
        self.imu_data.acc[0] = float(sd[self.imu_acc_adr + 0])
        self.imu_data.acc[1] = float(sd[self.imu_acc_adr + 1])
        self.imu_data.acc[2] = float(sd[self.imu_acc_adr + 2])
        self.imu_data.stamp = time.time_ns()
        self.robot.publishImuDataForSim(self.imu_data)

    def run(self):
        frame_count = 0
        self.rate = Rate(self.fps)
        while self.viewer.is_running():
            self._poll_pygame_reset()
            if self._reset_requested:
                self._reset_requested = False
                self._reset_sim()
            mujoco.mj_step(self.mujoco_model, self.mujoco_data)
            self._read_state()
            self._write_ctrl()

            self.robot_state.stamp = time.time_ns()
            self.robot.publishRobotStateForSim(self.robot_state)
            self._publish_imu()

            if frame_count % 20 == 0:
                self.viewer.sync()
            frame_count += 1
            self.rate.sleep()


if __name__ == "__main__":
    robot_type = os.getenv("ROBOT_TYPE")
    if not robot_type:
        print("Error: Please set ROBOT_TYPE, for example: export ROBOT_TYPE=SF_TRON2A")
        sys.exit(1)

    robot = Robot(RobotType.Tron2, True)
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    if not robot.init(robot_ip):
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    joint_names, sensor_joint_names, model_path = load_variant_config(script_dir, robot_type)
    if not os.path.exists(model_path):
        print(f"Error: model file not found: {model_path}")
        sys.exit(1)

    print(f"*** Model File Loaded: robot-description/tron2/{robot_type}/xml/robot.xml ***")
    simulator = SimulatorMujoco(model_path, joint_names, sensor_joint_names, robot)
    simulator.run()
