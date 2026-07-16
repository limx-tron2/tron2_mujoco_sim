# tron2-mujoco-sim — DACH_TRON2A (limxsdk)

DACH_TRON2A 专用 MuJoCo 仿真器。**仅** 支持 DACH 构型（双臂 7+7 + 头部 2，共 16 个受控关节），
可选带/不带 2 指夹爪。电机（双臂+头）、IMU **和夹爪** 全部通过
**[limxsdk-lowlevel](https://github.com/limxdynamics/limxsdk-lowlevel)** SDK 通信。

> ⚠️ **需要 limxsdk 4.0.2 或兼容版本**（含仿真侧夹爪接口 `subscribeGripperCmdForSim` /
> `publishGripperStateForSim`）。旧版无仿真侧夹爪方法，带夹爪的模型无法通过 SDK 收发夹爪指令。

> ⚠️ 本项目仅用于仿真与研发验证。将控制代码用于真实机器人前，必须完成独立的安全评审、
> 限位/急停验证和现场风险评估。维护者不对未经验证的真机运行负责。

## 1. 安装与准备

```bash
git clone --recurse-submodules https://github.com/limx-tron2/tron2-mujoco-sim-dach.git
cd tron2-mujoco-sim-dach

# Python 3.10（已验证）
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mujoco==3.10.0 "PyYAML>=5.4.1,<7"

# limxsdk-lowlevel 和 robot-joystick 通过 submodule 自动检出到同名目录。
# 如果克隆时漏掉 --recurse-submodules，可执行：
git submodule update --init --recursive

# 机器人描述是独立外部依赖，直接克隆到本项目所需路径
git clone https://github.com/limx-tron2/robot-description.git robot-description
git -C robot-description checkout --detach 6ef32a33b9405e84a6551bc19d380f6747ea9611

# 模型应位于：robot-description/tron2/DACH_TRON2A/xml/
```

> 当前公开基线固定为 `robot-description` commit
> `6ef32a33b9405e84a6551bc19d380f6747ea9611`；该版本的
> `robot_grasper.xml` 包含 `grasper_L_drive_Joint_ctrl` / `grasper_R_drive_Joint_ctrl`。
> 更新依赖基线前应在 CI 和完整联调中重新验证，不要仅依赖上游默认分支。

运动控制开发库（x86_64 为例；aarch64 换对应目录）：

```bash
python -m pip install limxsdk-lowlevel/python3/amd64/limxsdk-4.0.2-py3-none-any.whl
```

> 已验证公开版 **limxsdk 4.0.2**（仓库 commit
> `7df1617be2154365b3e34e3dfacd76fa1b144744`）：仿真侧的电机/IMU/夹爪都调用 SDK 的 `*ForSim` 接口，
> 其中夹爪依赖 `subscribeGripperCmdForSim` / `publishGripperStateForSim`（旧版没有）。
> 可用 `python3 -c "import limxsdk.datatypes as d; print(hasattr(d,'GripperCmd'))"` 快速自检（应为 `True`）。

## 2. 运行

```bash
python3 simulator.py                 # 默认 robot_grasper.xml（含 2 指夹爪）
python3 simulator.py --no-grasper    # robot.xml（仅双臂+头，无夹爪）
```

模型选择优先级：命令行 `--grasper` / `--no-grasper` > 环境变量 `DACH_GRASPER`（`0/false` 关闭夹爪）> 默认带夹爪。
用 `robot.xml` 时检测不到 `grasper_*_drive_Joint_ctrl`，夹爪功能自动关闭。

可选环境变量 `ROBOT_IP`（默认 `127.0.0.1`）传给 limxsdk `robot.init()`。

## 3. 工作模式 / 键盘

- **空格 (Space)**：暂停/恢复。
  - 暂停 = 手动模式（"⏸️ PAUSED"）：右侧 Control 面板拖动滑块直接设关节位置（运动学，不发状态）。
  - 恢复 = 自动模式（"▶️ RESUMED"）：按外部 `RobotCmd` 做 PD+前馈力矩，物理步进并发布状态。

## 4. 通信架构

### 4.1 电机（双臂+头，16 关节）+ IMU —— limxsdk 仿真侧接口

仿真作为“机器人/仿真”一侧，用 limxsdk 的 `*ForSim` 接口收指令、发状态：

| 部件 | 方向 | 仿真侧调用 (limxsdk) | 话题 | 消息 |
|---|---|---|---|---|
| 电机指令 | 入 | `subscribeRobotCmdForSim(cb)` | `/motor/cmd` | `RobotCmd`(q/dq/tau/Kp/Kd) |
| 电机状态 | 出 | `publishRobotStateForSim(st)` | `/motor/state` | `RobotState`(q/dq/tau, `motor_names`=16) |
| IMU | 出 | `publishImuDataForSim(imu)` | `/ImuData` | `ImuData`(acc/gyro/quat) |

初始化：`Robot(RobotType.Tron2, is_sim=True)` + `robot.init(ROBOT_IP)`。
控制律（自动模式）：`ctrl = Kp·(q−q_meas) + Kd·(dq−dq_meas) + tau`，按关节名解析索引（`joint_map`）。

控制器（客户端）侧对应用 `publishRobotCmd` / `subscribeRobotState` / `subscribeImuData`，示例：

```bash
# 先运行仿真，再另开终端跑客户端示例
python3 limxsdk-lowlevel/python3/examples/api/example_tron2.py 127.0.0.1
```

> 注意：客户端 `publishRobotCmd` 必须设置 `cmd.motor_names`（长度需等于 motorNumber=16），否则 SDK 会拒绝。
> IMU 四元数：MuJoCo 传感器为 `[w,x,y,z]`，发布时转成 limxsdk 的 `[x,y,z,w]`。

### 4.2 夹爪（2 指）—— limxsdk 仿真侧接口

仿真用 limxsdk 的 `*ForSim` 夹爪接口收指令、发状态（需要 limxsdk 4.0.2 或兼容版本）：

| 部件 | 方向 | 仿真侧调用 (limxsdk) | 话题 | 消息 | 字段（[0]=左,[1]=右，0~100） |
|---|---|---|---|---|---|
| 夹爪指令 | 入 | `subscribeGripperCmdForSim(cb)` | `/limx/2F-gripper/cmd` | `GripperCmd` | `opening`=开口度, `speed`=速度, `force`=夹持力 |
| 夹爪状态 | 出 | `publishGripperStateForSim(gs)` | `/limx/2F-gripper/state` | `GripperState` | `q`=实际开口度 |

夹爪为单自由度连杆：每侧一个 revolute `grasper_{L,R}_drive_Joint`（执行器 `..._drive_Joint_ctrl`，弧度域，±2 N·m），
夹指经 MJCF `<equality>` 多项式跟随。仿真内部把 0~100 映射到 drive 关节行程，做限速+限力矩位置环，标定见 `gripper_config.yaml`
（可用 `GRIPPER_CONFIG` 覆盖）。

> 命令映射：`GripperCmd.opening/speed/force` 对应内部开口度/速度/夹持力（均 0~100，[0]=左,[1]=右）。

控制器（客户端）侧对应用 `publishGripperCmd` / `subscribeGripperState`。测试脚本（limxsdk 客户端）：

```bash
python3 test_gripper_control.py                      # 双爪三角波循环
python3 test_gripper_control.py --scenario phases    # 开/合/半开/左右异步等分阶段
```

官方夹爪示例：`python3 limxsdk-lowlevel/python3/examples/api/example_tron2_gripper.py 127.0.0.1`

## 5. 备注

- 退出（关闭仿真窗口）时调用 `os._exit(0)`，跳过 limxsdk 底层原生库在解释器退出阶段的清理（否则会有一次无害的 teardown segfault）。
- 电机/IMU/夹爪的仿真侧命令回调都在 SDK 派发线程异步触发；控制循环每 tick 快照一次命令再用。
- `robot-description/` 是独立的外部仓库，不在本仓库版本控制内。
- [`limxsdk-lowlevel/`](https://github.com/limxdynamics/limxsdk-lowlevel) 是公开 Git submodule；
  本仓库只记录已验证 commit，不复制或重新许可其内容。
- [`robot-joystick/`](https://github.com/limxdynamics/robot-joystick) 是可选的公开 Git submodule；
  当前批准基线为 `30f69a9b3cba545a23ecf3f28f4e5ae6c78479cd`。本仓库只记录该 commit，
  不复制或以本项目 Apache-2.0 重新许可其内容及二进制。

## 6. 发布前自检

```bash
python3 -m py_compile simulator.py test_gripper_control.py

# 无界面模型检查由 GitHub Actions 自动执行；本机也可直接加载两套模型
python3 -c "import mujoco; mujoco.MjModel.from_xml_path('robot-description/tron2/DACH_TRON2A/xml/robot.xml')"
python3 -c "import mujoco; mujoco.MjModel.from_xml_path('robot-description/tron2/DACH_TRON2A/xml/robot_grasper.xml')"
```

完整联调需要先启动 `python3 simulator.py` 并保持 `RESUMED`，再在第二个终端运行
`python3 test_gripper_control.py --scenario phases`，确认客户端持续收到夹爪 state。

## 7. 许可证与贡献

本项目采用 Apache License 2.0，详见 `LICENSE` 和 `NOTICE`。外部依赖保持各自的许可证。
安全问题请按 `SECURITY.md` 私下报告；贡献流程见 `CONTRIBUTING.md`。

本项目按尽力而为方式维护，不提供支持 SLA，也不覆盖未经独立安全评审的真机部署。
支持范围和问题报告要求见 `SUPPORT.md`，用户可见变更记录见 `CHANGELOG.md`。
