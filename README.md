<!--
  SPDX-FileCopyrightText: 2024-2026 LimX Dynamics Technology Co., Ltd.
  SPDX-License-Identifier: Apache-2.0
-->

# tron2-mujoco-sim 使用说明

MuJoCo-based simulator for the TRON2A humanoid platform. `simulator.py`
bridges the LimX low-level SDK (`RobotCmd` / `RobotState` with
`q` / `dq` / `tau` / `Kp` / `Kd`) to `mujoco.MjData`, so the same
controller wire-format that drives a real robot can be exercised
against a simulated one.

## License & attribution

This project is licensed under the **Apache License, Version 2.0**
(January 2004). See the [`LICENSE`](LICENSE) file for the full text.
SPDX identifier: `Apache-2.0`.

- [`NOTICE`](NOTICE) — required attribution notice.
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — per-submodule
  and per-dependency provenance, plus documentation-media review.
- [`SECURITY.md`](SECURITY.md) — how to report a vulnerability, and
  the sim-vs-real boundary note.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Python + submodule workflow,
  DCO sign-off, submodule-pin-update procedure.
- [`CHANGELOG.md`](CHANGELOG.md) — release notes, including all
  items currently blocked on owner sign-off.

## Scope / not included

**Included** in this repository:

- `simulator.py` — MuJoCo simulator and LimX SDK bridge.
- Documentation (`README.md`, `doc/*.jpg`, `doc/*.gif`, `doc/*.GIF`).
- Submodule **declarations** (via `.gitmodules`) — three submodules
  are pinned by commit and must be initialized separately.

**Not included — by design:**

- The submodules themselves. After cloning, run
  `git submodule update --init --recursive` (or clone with
  `--recurse-submodules`). See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
  §2 for the per-submodule license and re-distribution status
  (currently `⚠ TO CONFIRM`).
- ONNX control policies (`.onnx`, `.pt`, `.pth`, `.ckpt`). The
  simulator does not load them directly; the deploy stack in the
  sibling repository **`tron2-rl-deploy-python`** does — see
  [§3 model file locations](#3-模型文件位置).
- SDK binaries (`.so`, `.dll`) or wheels (`.whl`) directly in this
  tree. SDK wheels live under the `limxsdk-lowlevel` submodule.
- Factory calibration values, firmware, motion / bag data.

The internal example IP referenced in [§2 running the controller](#2-运行控制器)
(`10.192.1.2`) is an **internal example, pending owner sign-off** for
public release; replace it with your own robot's address before use.

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
# NOTE: 10.192.1.2 is an INTERNAL EXAMPLE, pending owner sign-off for
# public release. Replace with your own robot's address before use;
# see CHANGELOG.md → "Pending owner sign-off".
python3 main.py 10.192.1.2
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

## 6. Verification

The commands below are the same ones CI runs (see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)); running them
locally before opening a PR saves review round-trips.

```bash
# 1. Byte-compile the simulator entry point
python -m py_compile simulator.py

# 2. Submodules are declared and (locally) initialized
git submodule status --recursive

# 3. Lint (matches CI)
pip install ruff
ruff check --exclude robot-description --exclude robot-joystick \
           --exclude limxsdk-lowlevel --exclude __pycache__ .

# 4. MuJoCo import dry-run (skipped in environments without MuJoCo)
pip install "mujoco>=2.3"
python -c "import mujoco; print('mujoco', mujoco.__version__)"

# 5. Nothing forbidden staged
git ls-files | grep -iE '(^|/)__pycache__(/|$)|\.(pyc|onnx|pt|pth|ckpt|so|dll|whl|bag|mcap)$' && echo BAD || echo OK
```

For a full simulator dry-run (loads the MuJoCo model, no controller
connected — Ctrl-C when the viewer appears):

```bash
export ROBOT_TYPE=SF_TRON2A
python3 simulator.py 127.0.0.1
```

## 7. Cite & support

If you use this simulator in academic or public work, please cite the
repository:

```
@misc{limx_tron2_mujoco_sim_2026,
  title  = {TRON2 MuJoCo simulator},
  author = {LimX Dynamics},
  year   = {2026},
  howpublished = {\url{https://github.com/limx-tron2/tron2-mujoco-sim}}
}
```

- **Bug reports / feature requests:**
  [GitHub Issues](https://github.com/limx-tron2/tron2-mujoco-sim/issues).
- **Questions / integration help:**
  [GitHub Discussions](https://github.com/limx-tron2/tron2-mujoco-sim/discussions).
- **Security reports:** email `contact@limxdynamics.com`; see
  [`SECURITY.md`](SECURITY.md) for the sim-vs-real boundary note.
- **Company / commercial contact:** <https://www.limxdynamics.com>.

## 8. License

[Apache 2.0](LICENSE) — see also [`NOTICE`](NOTICE) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
