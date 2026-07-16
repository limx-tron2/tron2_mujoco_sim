# Contributing to `tron2-mujoco-sim`

Thanks for helping improve the TRON2 MuJoCo simulator. This repository
holds `simulator.py` (a LimX-SDK ↔ MuJoCo bridge) plus documentation.
The runtime model / meshes and SDK binaries live in the three git
submodules — this repo pins them by commit but does not vendor their
contents.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Submodule workflow](#submodule-workflow)
- [Coding style](#coding-style)
- [Verification before opening a PR](#verification-before-opening-a-pr)
- [Commit messages](#commit-messages)
- [Pull request checklist](#pull-request-checklist)
- [Updating a submodule pin](#updating-a-submodule-pin)
- [Sign-off (DCO)](#sign-off-dco)
- [Code of conduct](#code-of-conduct)

## Ways to contribute

- Bug reports for the MuJoCo bridge (torque handling, sensor mapping,
  SDK message translation).
- Improvements to the joystick / IP configuration surface.
- Documentation, verification snippets, sim integration examples.
- Additional simulator smoke tests.

We do **not** accept:

- Control policies, model weights, or trained artifacts (`.onnx`,
  `.pt`, `.pth`, `.ckpt`) — those live in the deployment repository.
- SDK wheels or vendor binaries checked into this tree — the SDK is
  consumed through the `limxsdk-lowlevel` submodule.
- Calibration values, firmware, rosbags / MCAP captures.
- Media disclosing individuals, office locations, or non-public
  products.

## Development setup

Prerequisites:

- Python ≥ 3.8 (matching the SDK wheels shipped in
  `limxsdk-lowlevel/python3/{amd64,aarch64}/`).
- MuJoCo ≥ 2.3 (`pip install mujoco`).
- NumPy, SciPy, PyYAML, onnxruntime, pygame (see
  [`README.md`](README.md)).
- A LimX SDK wheel from the `limxsdk-lowlevel` submodule.

```bash
# clone with submodules
git clone --recurse-submodules https://github.com/limx-tron2/tron2-mujoco-sim.git
cd tron2-mujoco-sim

# python deps
pip install -U pip
pip install mujoco numpy scipy pyyaml onnxruntime pygame

# SDK wheel (pick the arch that matches your host)
pip install limxsdk-lowlevel/python3/amd64/limxsdk-*-py3-none-any.whl
# or:
pip install limxsdk-lowlevel/python3/aarch64/limxsdk-*-py3-none-any.whl
```

If you did not clone with `--recurse-submodules`, run:

```bash
git submodule update --init --recursive
```

## Submodule workflow

This repository has three submodules:

| Submodule | Purpose |
|-----------|---------|
| `robot-description` | URDF / MuJoCo XML / meshes loaded by `simulator.py`. |
| `robot-joystick` | Joystick binary used by the deploy stack. |
| `limxsdk-lowlevel` | LimX SDK sources and pre-built wheels. |

- **Never** commit inside a submodule from this repository; open a PR
  in the submodule's own repo, land it there, then update the pin
  here in a separate PR (see [Updating a submodule
  pin](#updating-a-submodule-pin)).
- `git submodule status --recursive` must produce a non-empty listing
  before any smoke test — CI enforces this.
- Do not add new submodules without a `THIRD_PARTY_NOTICES.md` entry
  and legal sign-off. New submodules are treated as new third-party
  dependencies.

## Coding style

- Format with `ruff format` (or `black` if you prefer — keep the same
  line length as existing code).
- Lint with `ruff check`. CI fails on lint errors.
- All new `.py` files must byte-compile:

  ```bash
  python -m py_compile simulator.py
  ```

- Do not introduce hard-coded machine IPs, hostnames, or credentials.
  The `<robot-ip>` token used in `README.md` command examples is a
  **placeholder** — users substitute their own robot / simulator IP
  when running. Do not replace it with a real address, and do not
  propagate hard-coded IPs into other files.

## Verification before opening a PR

Run all of the following and paste the summary into the PR description:

```bash
# 1. Byte-compile every Python file
find . -name '*.py' -not -path './*/.git/*' -not -path './limxsdk-lowlevel/*' \
       -not -path './robot-description/*' -not -path './robot-joystick/*' \
    -print0 | xargs -0 -n1 python -m py_compile

# 2. Ruff lint
pip install ruff
ruff check simulator.py

# 3. Submodules initialized
git submodule status --recursive

# 4. MuJoCo can import
python -c "import mujoco, sys; print(mujoco.__version__)"

# 5. Simulator dry-run (loads model, no controller connected)
#    Ctrl-C after the window appears; success = no traceback.
ROBOT_TYPE=SF_TRON2A timeout 5 python3 simulator.py 127.0.0.1 || true

# 6. No forbidden artifacts staged
git ls-files | grep -iE '\.(onnx|pt|pth|ckpt|so|dll|dylib|lib|whl|bag|mcap|pyc)$' || echo OK
```

CI runs equivalent steps; local pre-checks save review round-trips.

## Commit messages

Follow Conventional Commits:

```
type(scope): short imperative summary

Longer explanation if needed.

Signed-off-by: Your Name <you@example.com>
```

`type` ∈ `feat | fix | docs | refactor | chore | ci | test | submodule`.
`scope` is usually `sim`, `sdk-bridge`, `joystick`, or `meta`.

## Pull request checklist

- [ ] Python files byte-compile and pass `ruff check`.
- [ ] `git submodule status --recursive` reported all submodules
      initialized during testing.
- [ ] No new hard-coded IPs, hostnames, credentials, or private paths.
- [ ] No `.onnx`, `.pt`, `.so`, `.whl`, `.bag`, `.mcap`, or
      `__pycache__/` staged.
- [ ] `THIRD_PARTY_NOTICES.md` updated if a runtime dep or submodule
      pin changed.
- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`.
- [ ] DCO sign-off on every commit.

## Updating a submodule pin

1. Land the change upstream in the submodule's own repository.
2. In this repo:

   ```bash
   cd robot-description   # or robot-joystick / limxsdk-lowlevel
   git fetch
   git checkout <new-sha>
   cd ..
   git add robot-description
   ```
3. Update the row in `THIRD_PARTY_NOTICES.md` §2 with the new SHA and
   re-verify the license / re-distribution status.
4. Tick the "submodule pin update" box in the PR template and describe
   the rationale.
5. Bump `CHANGELOG.md` under `## [Unreleased]` — pin bumps are
   user-visible.

## Sign-off (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/).
Every commit must be signed off:

```bash
git commit -s -m "your message"
```

Signing off certifies that you have the right to submit the change
under the repository's license.

## Code of conduct

Be respectful and constructive. Reports to `contact@limxdynamics.com`.
