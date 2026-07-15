<!--
  SPDX-FileCopyrightText: 2024-2026 LimX Dynamics Technology Co., Ltd.
  SPDX-License-Identifier: Apache-2.0
-->

[English](README.md) | [中文](README_zh-CN.md)

# tron2-mujoco-sim

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
  are pinned by commit and must be initialized separately:
  - `robot-description/` — URDF / MJCF meshes and models.
  - `robot-joystick/` — gamepad helper binary.
  - `limxsdk-lowlevel/` — LimX low-level SDK (with prebuilt wheels).

**Not included — by design:**

- The submodules themselves. After cloning, run
  `git submodule update --init --recursive` (or clone with
  `--recurse-submodules`). See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
  §2 for the per-submodule license and re-distribution status
  (currently `⚠ TO CONFIRM`).
- ONNX control policies (`.onnx`, `.pt`, `.pth`, `.ckpt`). The
  simulator does not load them directly; the deploy stack in the
  sibling repository **`tron2-rl-deploy-python`** does — see
  [§3 Model file locations](#3-model-file-locations).
- SDK binaries (`.so`, `.dll`) or wheels (`.whl`) directly in this
  tree. SDK wheels live under the `limxsdk-lowlevel` submodule.
- Factory calibration values, firmware, motion / bag data.

The internal example IP referenced in
[§2 Running the controller](#2-running-the-controller) (`10.192.1.2`)
is an **internal example, pending owner sign-off** for public
release; replace it with your own robot's address before use.

## 1. Running the simulator

### Step 1: Open a terminal

### Step 2: Clone the repository

```bash
git clone --recurse-submodules https://github.com/limx-tron2/tron2-mujoco-sim.git
```

If you already cloned without submodules:

```bash
cd tron2-mujoco-sim
git submodule update --init --recursive
```

### Step 3: Install Python dependencies

```bash
pip install -U pip
pip install mujoco numpy scipy pyyaml onnxruntime pygame
```

### Step 4: Install the LimX SDK (required)

Install the SDK wheel that matches your machine architecture
(example):

```bash
# x86_64
pip install limxsdk-lowlevel/python3/amd64/limxsdk-*-py3-none-any.whl

# aarch64
pip install limxsdk-lowlevel/python3/aarch64/limxsdk-*-py3-none-any.whl
```

### Step 5: Choose the robot type

Currently supported:

- `SF_TRON2A`
- `WF_TRON2A`

Example:

```bash
export ROBOT_TYPE=SF_TRON2A
```

### Step 6: Launch the MuJoCo simulator

```bash
cd tron2-mujoco-sim
python3 simulator.py
```

Optional — specify the SDK communication IP (default `127.0.0.1`):

```bash
python3 simulator.py 127.0.0.1
```

---

## 2. Running the controller

### Step 1: Open a new terminal

### Step 2: Launch the ONNX controller entry point

```bash
cd tron2-rl-deploy-python
export ROBOT_TYPE=SF_TRON2A
python3 main.py
```

Optional — specify the robot IP (same convention as tron1):

```bash
# NOTE: 10.192.1.2 is an INTERNAL EXAMPLE, pending owner sign-off for
# public release. Replace with your own robot's address before use;
# see CHANGELOG.md → "Pending owner sign-off".
python3 main.py 10.192.1.2
```

### Step 3: Gamepad control

- `L1 + Y`: switch to WALK
- `L1 + X`: switch back to IDLE
- `R1`: clear velocity commands
- Open a Bash terminal.

- Run `robot-joystick`:

  ```
  ./robot-joystick/robot-joystick
  ```
---

## 3. Model file locations

Place the ONNX models under the directory matching each robot type:

- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/policy.onnx`
- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/encoder.onnx`
- `tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/params.yaml`

For example:

- `tron2-rl-deploy-python/controller/model/SF_TRON2A/...`
- `tron2-rl-deploy-python/controller/model/WF_TRON2A/...`

---

## 4. Screenshots / GIFs

### Simulation

![SF Simulation](doc/sfmj-ezgif.com-video-to-gif-converter.gif)
![WF Simulation](doc/wfmj-ezgif.com-video-to-gif-converter.gif)

### Real-world deployment

For real-robot deployment, suspend the robot before launching the
controller.

![Deploy](doc/deploy.jpg)

![SF Real-world](doc/sf.GIF)
![WF Real-world](doc/wf.GIF)


## 5. FAQ

- `ROBOT_TYPE not set`: run `export ROBOT_TYPE=...` first.
- `Model not found`: check that all model files under
  `controller/model/<ROBOT_TYPE>/` are present.
- `No module named limxsdk`: the SDK wheel is not installed into
  the active Python environment.
- `RobotState has not been received yet`: usually means the
  simulator is not running, or the simulator and the controller
  disagree on `ROBOT_TYPE`.

## Verification

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

## Cite & support

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
