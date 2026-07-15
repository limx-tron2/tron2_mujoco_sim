<!--
Thanks for contributing to tron2-mujoco-sim!
Please fill in the sections below. Delete any that are not applicable.
-->

## Summary

<!-- One paragraph: what and why. -->

## Type of change

- [ ] `fix`      — corrects a defect in `simulator.py`, CI, or docs
- [ ] `feat`     — new capability (new robot type, new SDK message, etc.)
- [ ] `docs`     — README, THIRD_PARTY_NOTICES, CONTRIBUTING, SECURITY
- [ ] `ci`       — GitHub Actions or verification tooling
- [ ] `chore`    — repo maintenance (deps, formatting, cleanup)
- [ ] `submodule`— submodule pin update (see checkbox below)

## Affected surfaces

- [ ] `simulator.py` (SDK ↔ MuJoCo bridge)
- [ ] Documentation / media (`README.md`, `doc/`)
- [ ] CI / templates (`.github/`)
- [ ] Meta / repo-wide

## Submodule pin update

- [ ] This PR **updates a submodule pin**. If ticked, complete:
  - Submodule: `robot-description` / `robot-joystick` / `limxsdk-lowlevel`
  - Old SHA → new SHA:
  - Reason for the bump:
  - Upstream PR / release notes:
  - `THIRD_PARTY_NOTICES.md` §2 row updated: yes / no
  - License / re-distribution status re-verified: yes / no
  - Owner sign-off recorded (issue link or reviewer):

## Verification

Paste the output (or a summary) of the local verification steps from
`CONTRIBUTING.md#verification-before-opening-a-pr`:

```text
py_compile:              ...
ruff check:              ...
git submodule status:    ...
mujoco import:           ...
simulator.py dry-run:    ...
forbidden-artifacts scan: ...
```

## Provenance & sensitivity

- [ ] No control policies (`.onnx`, `.pt`, `.pth`, `.ckpt`) are added.
- [ ] No SDK binaries (`.so`, `.dll`, `.dylib`, `.lib`) or wheels
      (`.whl`) are added directly to this tree.
- [ ] No calibration values, firmware, rosbags (`.bag`, `.mcap`), or
      customer data are added.
- [ ] No new hard-coded IPs, hostnames, or credentials are introduced.
      The existing `10.192.1.2` example remains untouched pending
      owner sign-off (see `CHANGELOG.md`).
- [ ] Any new / modified media under `doc/` has been EXIF-stripped and
      cleared for people / office / non-public product visibility.
- [ ] `THIRD_PARTY_NOTICES.md` is up to date.

## Sim-vs-real boundary

- [ ] This PR does **not** introduce a code path that silently
      forwards simulator commands to a physical robot, and does not
      widen the default SDK bind address beyond `127.0.0.1`.
      (If it does, describe the safety controls added.)

## Checklist

- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`.
- [ ] All commits are DCO-signed (`git commit -s`).
- [ ] CI is expected to pass.

## Related issues

<!-- Fixes #123 / Refs #456 -->
