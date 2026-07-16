# Third-Party Notices

`tron2-mujoco-sim` (TRON2 MuJoCo simulator) is distributed under the
Apache License 2.0 (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE)).

This file lists third-party components, git submodules, runtime
dependencies, and documentation media so downstream users can comply
with all applicable licenses and re-distribution terms.

> **Status:** items marked `⚠ TO CONFIRM` are pending sign-off from
> the SDK / hardware / product / legal owners. Do not cut a public
> release while any `⚠ TO CONFIRM` entry remains.

---

## 1. First-party sources (LimX Dynamics)

| Path | Kind | License | Notes |
|------|------|---------|-------|
| `simulator.py` | Python source | Apache-2.0 | MuJoCo simulator bridging LimX SDK `RobotCmd` (q / dq / tau / Kp / Kd) to `mujoco.MjData`. Real-robot control interface — see [`SECURITY.md`](SECURITY.md) for the sim-vs-real boundary. |
| `README.md`, `LICENSE`, `NOTICE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, this file | Documentation | Apache-2.0 | Hand-maintained. |

---

## 2. Git submodules (not vendored — pinned by commit)

This repository declares three submodules in `.gitmodules`. Their
content is **not** copied into this tree; users initialize them with
`git submodule update --init --recursive`. Each pin below is the
commit recorded at the time this scaffolding was written; verify with
`git submodule status --recursive` before any public tag.

| Submodule | Path | Upstream URL | Pinned commit (full SHA) | Public reachability (2026-07-16) | License | Re-distribution allowed |
|-----------|------|--------------|--------------------------|-----------------------------------|---------|-------------------------|
| `robot-description` | `robot-description/` | `https://github.com/limx-tron2/robot-description.git` (branch `develop`) | `8a11c12c7851a104dc4cafff1780276f624d2bc6` | ⚠ **PIN NOT ADVERTISED on public upstream** — `git ls-remote` on `github.com/limx-tron2/robot-description` returns only `refs/heads/main` and `refs/heads/feature/grasper`; there is no `develop` branch and the pinned commit is not in the advertised refs. Anonymous `git clone --recurse-submodules` from a public consumer will fail here. Owner must either (a) push the `develop` branch or the pinned commit to the public repository, or (b) point `.gitmodules` at a different upstream (e.g. internal GitLab). | Apache-2.0 (per sibling repo `NOTICE`) ⚠ TO CONFIRM once submodule review lands | ⚠ TO CONFIRM |
| `robot-joystick` | `robot-joystick/` | `https://github.com/limxdynamics/robot-joystick.git` (branch `main`) | `30f69a9b3cba545a23ecf3f28f4e5ae6c78479cd` | ✅ pin is the current `refs/heads/main` HEAD on the public upstream (`git ls-remote`) — anonymous clone succeeds. | ⚠ TO CONFIRM (binary vs. source; likely ships a `robot-joystick` executable) | ⚠ TO CONFIRM |
| `limxsdk-lowlevel` | `limxsdk-lowlevel/` | `https://github.com/limxdynamics/limxsdk-lowlevel.git` | `17a4b25d40d3a71435d2144ac668e72784cc4179` | ✅ pin corresponds to upstream tag **`2.2.0`** on the public repository — anonymous clone succeeds. | ⚠ TO CONFIRM (SDK wheels under `python3/{amd64,aarch64}/limxsdk-*.whl` — redistribution terms unknown) | ⚠ TO CONFIRM |

Reproduce the reachability probe:

```bash
git ls-remote https://github.com/limx-tron2/robot-description.git | head
git ls-remote https://github.com/limxdynamics/robot-joystick.git | head
git ls-remote https://github.com/limxdynamics/limxsdk-lowlevel.git | grep 17a4b25d
```

**Owner action required (per submodule):**

- Confirm the upstream repository is public and intended to remain so.
- **`robot-description`: resolve the pin-not-reachable issue above
  before public tag** — this blocks anonymous `--recurse-submodules`.
- Record the license identifier (SPDX) and re-distribution terms.
- Record whether the submodule ships pre-built binaries (`.whl`,
  `.so`, or a stand-alone executable) that are subject to additional
  terms.
- If a submodule is not cleared for public use, remove the entry from
  `.gitmodules` before publishing this repository.

Do not silently update submodule pins — pin bumps require the same
sign-off flow (see [`CONTRIBUTING.md`](CONTRIBUTING.md) and the
"submodule pin update" checkbox in the PR template).

---

## 3. Runtime dependencies (not vendored)

The simulator imports the following at runtime. None of them are
vendored or bundled in this repository; users install them
independently (see [`README.md`](README.md) for install commands).

| Dependency | Purpose | License | Where obtained |
|------------|---------|---------|----------------|
| MuJoCo (`mujoco` Python package, ≥ 2.3) | Physics simulation, model loading | Apache-2.0 | https://mujoco.org — `pip install mujoco` |
| NumPy | Array math in the SDK bridge | BSD-3-Clause | `pip install numpy` |
| SciPy | Rotation / spatial utilities | BSD-3-Clause | `pip install scipy` |
| PyYAML | Config parsing (`params.yaml`) | MIT | `pip install pyyaml` |
| onnxruntime | Consumed by the linked `tron2-rl-deploy-python` controller (not by `simulator.py` directly) | MIT | `pip install onnxruntime` |
| pygame | Joystick input on the deploy side | LGPL-2.1 | `pip install pygame` |
| LimX SDK (`limxsdk`) | RobotCmd / RobotState bridge | ⚠ TO CONFIRM (shipped as a wheel under submodule `limxsdk-lowlevel/`) | This repo does **not** ship the wheel; installed by the user from the submodule. |

None of the above are bundled here; users must obtain and license them
independently.

---

## 4. Linked (not vendored) external controller

`README.md` documents that the ONNX policy is loaded by an external
sibling repository, **`tron2-rl-deploy-python`**:

```
tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/policy.onnx
tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/encoder.onnx
tron2-rl-deploy-python/controllers/model/<ROBOT_TYPE>/params.yaml
```

- No `.onnx`, `.pt`, `.pth`, or `.ckpt` file is committed to
  `tron2-mujoco-sim`; the deny-list in
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml) enforces this.
- The deployment repository has its own license, `THIRD_PARTY_NOTICES`,
  and model provenance. This repository only **references** it and
  does not re-distribute its contents. ⚠ TO CONFIRM that the linked
  repo will be public under the `limx-tron2` org.

---

## 5. Documentation media

| Path | Kind | Provenance | License |
|------|------|------------|---------|
| `doc/sfmj-ezgif.com-video-to-gif-converter.gif` | Simulation screen capture (SF) | ⚠ TO CONFIRM | ⚠ TO CONFIRM |
| `doc/wfmj-ezgif.com-video-to-gif-converter.gif` | Simulation screen capture (WF) | ⚠ TO CONFIRM | ⚠ TO CONFIRM |
| `doc/deploy.jpg` | Real-world deploy photo | ⚠ TO CONFIRM (may show individuals / office / hoist rig) | ⚠ TO CONFIRM |
| `doc/sf.GIF` | Real-world capture (SF) | ⚠ TO CONFIRM | ⚠ TO CONFIRM |
| `doc/wf.GIF` | Real-world capture (WF) | ⚠ TO CONFIRM | ⚠ TO CONFIRM |

Before release, run:
```bash
exiftool doc/* | grep -iE '(gps|serial|make|model|software|author|artist|copyright)'
```
and strip anything that discloses office locations, camera serials, or
individual contributors' names, unless intentionally kept:
```bash
exiftool -all= doc/*.jpg doc/*.GIF doc/*.gif
```

The real-world deploy photo/GIFs may show people or non-public
hardware — obtain publication clearance from every identifiable person
before release, or replace with a sanitized capture.

---

## 6. What this repository does **not** include

- No control policies (`.onnx`, `.pt`, `.pth`, `.ckpt`) — see
  `tron2-rl-deploy-python`.
- No SDK binaries (`.so`, `.dll`, `.dylib`, `.lib`) directly in this
  tree. SDK wheels live under the `limxsdk-lowlevel` submodule and are
  installed by the user, not bundled.
- No factory calibration values or per-serial calibration files.
- No motion / bag / trajectory data (`.bag`, `.mcap`).
- No firmware.
- No customer- or site-specific configuration.

---

## 7. Update procedure

Whenever a submodule pin, a runtime dependency, or a documentation
image is added or changed:

1. Update the corresponding row in this file.
2. Re-run the EXIF strip (§5) on any new / touched media.
3. If the change touches an `⚠ TO CONFIRM` row, block the merge on
   written sign-off from the responsible owner.
4. Bump `CHANGELOG.md` under `## [Unreleased]`.
