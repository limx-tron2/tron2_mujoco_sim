---
name: Bug report
about: MuJoCo simulator / SDK bridge / joystick / doc defect
title: "[bug] <short summary>"
labels: bug
assignees: ''
---

## Affected component

<!-- e.g. simulator.py, README.md, .github/workflows/ci.yml -->

- File(s):
- Robot type: `SF_TRON2A` / `WF_TRON2A` / other
- Commit / tag:
- Submodule pins (`git submodule status --recursive`):

## Environment

- OS + arch (e.g. Ubuntu 22.04 x86_64 / aarch64):
- Python version:
- MuJoCo version:
- LimX SDK wheel: `limxsdk-*-py3-none-any.whl` filename
- Are you running against a real robot?  **No — sim only** / Yes

  > If Yes, review `SECURITY.md`; do not attach PoCs that could
  > move a physical robot.

## Expected behavior

## Actual behavior

<!-- log lines, screenshots, numeric mismatches -->

## Minimal reproduction

```bash
# commands that reproduce it locally, ideally starting from a fresh clone
git clone --recurse-submodules https://github.com/limx-tron2/tron2-mujoco-sim.git
cd tron2-mujoco-sim
export ROBOT_TYPE=SF_TRON2A
python3 simulator.py 127.0.0.1
```

## Additional context

<!-- upstream MuJoCo quirks, controller version, joystick model, etc. -->

## Checklist

- [ ] I have searched existing issues.
- [ ] I have included the exact commit / tag and submodule status.
- [ ] I am **not** reporting a security issue (those go to
      `contact@limxdynamics.com` per `SECURITY.md`).
- [ ] I did not attach any control policies, calibration values,
      rosbags, or media that discloses individuals or sites.
