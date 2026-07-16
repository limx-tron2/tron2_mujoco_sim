<!--
  SPDX-FileCopyrightText: 2024-2026 LimX Dynamics Technology Co., Ltd.
  SPDX-License-Identifier: Apache-2.0
-->

[English](README.md) | [中文](README_zh-CN.md)

> **发布渠道。** 本仓库的主发布点为 GitHub：
> <https://github.com/limx-tron2/tron2-mujoco-sim>。
> LimX 内部 GitLab 为镜像；Issue、PR 与安全报告请提交到 GitHub。

# tron2-mujoco-sim 使用说明

面向 TRON2A 人形平台的 MuJoCo 仿真器。`simulator.py` 将 LimX 底层
SDK（`RobotCmd` / `RobotState`，字段 `q` / `dq` / `tau` / `Kp` /
`Kd`）与 `mujoco.MjData` 打通，让驱动真实机器人的同一套控制器接口
可以直接在仿真环境中运行。

## 许可与归属

本项目采用 **Apache License, Version 2.0**（2004 年 1 月）授权。
完整许可文本见 [`LICENSE`](LICENSE)。SPDX 标识符：`Apache-2.0`。

- [`NOTICE`](NOTICE) — 必需的归属声明。
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — 各子模块与
  依赖的来源信息，以及文档媒体资源的审阅记录。
- [`SECURITY.md`](SECURITY.md) — 漏洞上报流程，以及仿真 vs 实机
  的边界说明。
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Python 与子模块工作流、
  DCO 签署要求、子模块 commit 升级流程。
- [`CHANGELOG.md`](CHANGELOG.md) — 发布记录，含所有待负责人签字
  确认的条目。

## 适用范围与除外

**本仓库包含：**

- `simulator.py` — MuJoCo 仿真器与 LimX SDK 桥接。
- 文档（`README.md`、`doc/*.jpg`、`doc/*.gif`、`doc/*.GIF`）。
- 子模块**声明**（通过 `.gitmodules`）— 共三个子模块按 commit 固定,
  需单独初始化：
  - `robot-description/` — URDF / MJCF 网格与模型。
  - `robot-joystick/` — 手柄辅助程序。
  - `limxsdk-lowlevel/` — LimX 底层 SDK（含预编译 wheel）。

**本仓库不包含（有意为之）：**

- 子模块本身。clone 后请执行
  `git submodule update --init --recursive`（或 clone 时加
  `--recurse-submodules`）。子模块的许可与再分发状态见
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) §2
  （当前为 `⚠ TO CONFIRM`）。
- ONNX 控制策略（`.onnx`、`.pt`、`.pth`、`.ckpt`）。仿真器本身
  不直接加载它们；加载工作由姊妹仓库
  **`tron2-rl-deploy-python`** 中的部署栈完成 —
  见 [§3 模型文件位置](#3-模型文件位置)。
- SDK 的二进制（`.so`、`.dll`）或 wheel（`.whl`）不会直接进入
  本仓库；SDK wheel 位于 `limxsdk-lowlevel` 子模块中。
- 工厂标定数据、固件、运动 / bag 数据。

[§2 运行控制器](#2-运行控制器)中出现的 `<robot-ip>` 是**占位符**，
运行前请替换为您自己机器人或仿真器的实际 IP。本仓库源码不包含任何
硬编码的私网地址。仅内部使用的姊妹仓库 `tron2-rl-deploy-ros` 在其
源码 / launch 文件中保留了一处作为文档示例的字面量 `10.192.1.2`，
已在该仓库的 `SECURITY.md` 中声明；本仓库有意不含此类字面量。

## 1. 运行仿真

### Step 1: 打开终端

### Step 2: 克隆仓库

```bash
git clone --recurse-submodules https://github.com/limx-tron2/tron2-mujoco-sim.git
```

If you already cloned without submodules:

```bash
cd tron2-mujoco-sim
git submodule update --init --recursive
```

### Step 3: 安装 Python 依赖

```bash
pip install -U pip
pip install mujoco numpy scipy pyyaml onnxruntime pygame
```

### Step 4: 安装 LimX SDK（必须）

根据机器架构安装 SDK wheel（示例）：

```bash
# x86_64
pip install limxsdk-lowlevel/python3/amd64/limxsdk-*-py3-none-any.whl

# aarch64
pip install limxsdk-lowlevel/python3/aarch64/limxsdk-*-py3-none-any.whl
```

### Step 5: 设置机器人型号

当前支持：

- `SF_TRON2A`
- `WF_TRON2A`

示例：

```bash
export ROBOT_TYPE=SF_TRON2A
```

### Step 6: 启动 MuJoCo 仿真器

```bash
cd tron2-mujoco-sim
python3 simulator.py
```

可选：指定 SDK 通信 IP（默认 `127.0.0.1`）：

```bash
python3 simulator.py 127.0.0.1
```

---

## 2. 运行控制器

### Step 1: 打开新终端

### Step 2: 启动 ONNX 控制入口

```bash
cd tron2-rl-deploy-python
export ROBOT_TYPE=SF_TRON2A
python3 main.py
```

可选：指定机器人 IP（和 tron1 用法一致）：

```bash
# 说明：<robot-ip> 是占位符，运行前请替换为您自己机器人 /
# 仿真器的实际 IP。本仓库源码未硬编码任何私网地址。
# （仅内部使用的姊妹仓库 tron2-rl-deploy-ros 在其源码 /
# launch 文件中保留了作为文档示例的字面量 10.192.1.2，
# 已在该仓库的 SECURITY.md 中声明。）
python3 main.py <robot-ip>
```

### Step 3: 手柄控制说明

- `L1 + Y`：切换到 WALK
- `L1 + X`：切回 IDLE
- `R1`：清空速度指令
- 打开一个 Bash 终端。

- 运行 robot-joystick：

  ```
  ./robot-joystick/robot-joystick
  ```
---

## 3. 模型文件位置


请将 ONNX 模型按机型放在：

- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/policy.onnx`
- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/encoder.onnx`
- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/params.yaml`

例如：

- `tron2-rl-deploy-python/controller/model/SF_TRON2A/...`
- `tron2-rl-deploy-python/controller/model/WF_TRON2A/...`

---

## 4. 效果展示

### 仿真部署 (Simulation)

![SF Simulation](doc/sfmj-ezgif.com-video-to-gif-converter.gif)
![WF Simulation](doc/wfmj-ezgif.com-video-to-gif-converter.gif)

### 实机部署 (Real-world)

实机部署时请悬挂启动控制器

![Deploy](doc/deploy.jpg)

![SF Real-world](doc/sf.GIF)
![WF Real-world](doc/wf.GIF)


## 5. 常见问题

- `ROBOT_TYPE not set`：先执行 `export ROBOT_TYPE=...`
- `Model not found`：检查 `controller/model/<ROBOT_TYPE>/` 下模型文件是否齐全
- `No module named limxsdk`：SDK wheel 未安装到当前 Python 环境
- `RobotState has not been received yet`：通常是仿真器没启动，或仿真与控制器的 `ROBOT_TYPE` 不一致

## 验证

下列命令与 CI 保持一致（见
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)）；在提交
PR 前本地跑一遍，可以省去大量来回。

```bash
# 1. 字节码编译仿真器入口
python -m py_compile simulator.py

# 2. 子模块已声明并（本地）已初始化
git submodule status --recursive

# 3. 代码风格检查（与 CI 一致）
pip install ruff
ruff check --exclude robot-description --exclude robot-joystick \
           --exclude limxsdk-lowlevel --exclude __pycache__ .

# 4. MuJoCo 导入检查（无 MuJoCo 环境可跳过）
pip install "mujoco>=2.3"
python -c "import mujoco; print('mujoco', mujoco.__version__)"

# 5. 无禁止入库的文件被暂存
git ls-files | grep -iE '(^|/)__pycache__(/|$)|\.(pyc|onnx|pt|pth|ckpt|so|dll|whl|bag|mcap)$' && echo BAD || echo OK
```

完整仿真 dry-run（加载 MuJoCo 模型，不接控制器 —
可视化窗口出现后按 Ctrl-C 结束）：

```bash
export ROBOT_TYPE=SF_TRON2A
python3 simulator.py 127.0.0.1
```

## 引用与支持

如果你在学术或公开工作中使用了本仿真器，请引用本仓库：

```
@misc{limx_tron2_mujoco_sim_2026,
  title  = {TRON2 MuJoCo simulator},
  author = {LimX Dynamics},
  year   = {2026},
  howpublished = {\url{https://github.com/limx-tron2/tron2-mujoco-sim}}
}
```

- **Bug 反馈 / 功能建议：**
  [GitHub Issues](https://github.com/limx-tron2/tron2-mujoco-sim/issues)。
- **使用问题 / 集成帮助：**
  [GitHub Discussions](https://github.com/limx-tron2/tron2-mujoco-sim/discussions)。
- **安全问题上报：** 邮箱 `contact@limxdynamics.com`；仿真 vs 实机
  的边界说明见 [`SECURITY.md`](SECURITY.md)。
- **公司 / 商务联系：** <https://www.limxdynamics.com>。
