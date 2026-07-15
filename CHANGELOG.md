# Changelog

All notable changes to `tron2-mujoco-sim` will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Open-source scaffolding: `NOTICE`, `THIRD_PARTY_NOTICES.md`,
  `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- `.gitignore` covering Python build artefacts (`__pycache__/`,
  `*.pyc`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`,
  `*.egg-info/`), editor / OS junk, and an explicit deny-list for
  run-time artefacts that must not be committed here (`*.onnx`,
  `*.pt`, `*.pth`, `*.ckpt`, `*.so`, `*.dll`, `*.dylib`, `*.lib`,
  `*.whl`, `*.bag`, `*.mcap`).
- GitHub CI workflow: Python byte-compile (`python -m py_compile`),
  `ruff` / `pyflakes` lint, submodule status non-empty check,
  optional MuJoCo import smoke test, EXIF sanity scan on doc images,
  private-IP scan with allowlist, and a deny-list check that fails
  on any committed `__pycache__/`, `*.pyc`, `*.onnx`, `*.pt`,
  `*.so`, `*.dll`, `*.whl`, or `*.bag`.
- Issue templates and PR template under `.github/`; the PR template
  includes an explicit **submodule-pin-update** checkbox.
- `.github/CODEOWNERS` with maintainers / legal / SDK / sim /
  robotics team routing.
- `README.md`: SPDX header, "License & attribution" block, "Scope /
  not included" (with submodule init note and pointer to the
  external `tron2-rl-deploy-python` ONNX repository), "Verification"
  section, and "Cite & support" block with `contact@limxdynamics.com`.

### Changed
- `README.md`: repository clone URL corrected from
  `https://github.com/limxdynamics/tron2-mujoco-sim.git` to
  `https://github.com/limx-tron2/tron2-mujoco-sim.git` so the
  documented URL matches the target `limx-tron2` organization for
  the public release.

### Pending owner sign-off (blocks first public tag)
- **Submodule clearance — `robot-description`.** Confirm the pinned
  commit (`8a11c12…`, ⚠ TO CONFIRM exact SHA), the license
  (expected Apache-2.0 per the sibling repo `NOTICE`), and
  re-distribution terms. See `THIRD_PARTY_NOTICES.md` §2.
- **Submodule clearance — `robot-joystick`.** Confirm the pinned
  commit (`30f69a9…`, ⚠ TO CONFIRM exact SHA), the license, and
  whether the submodule ships pre-built binaries subject to
  additional terms.
- **Submodule clearance — `limxsdk-lowlevel`.** Confirm the pinned
  commit (`17a4b25…`, ⚠ TO CONFIRM exact SHA), the SDK license,
  and re-distribution terms for the wheels under
  `python3/{amd64,aarch64}/limxsdk-*.whl`.
- **Private IP in `README.md`.** The example `10.192.1.2`
  (documented as an internal example, pending owner sign-off) must
  be confirmed as publishable or replaced with a placeholder such
  as `<robot-ip>` before the first public tag. This release
  intentionally does **not** rewrite that string; the annotation
  in `README.md` records the decision as pending.
- **Committed `__pycache__/` cleanup.** The current tree contains a
  checked-in `__pycache__/` directory. This release only adds it to
  `.gitignore` (which prevents future re-introduction); the actual
  `git rm -r --cached __pycache__/` cleanup is scheduled as a
  separate PR so it lands as a single, reviewable removal commit.
- **Documentation media.** EXIF strip and content review of
  `doc/deploy.jpg`, `doc/sf.GIF`, `doc/wf.GIF`, and the two
  `doc/*mj-*.gif` simulation captures — including publication
  clearance from every identifiable person visible in the
  real-world deploy photo.
- **Linked external repository.** Confirm that
  `tron2-rl-deploy-python` will be published under the
  `limx-tron2` organization and that referencing its model paths
  in `README.md` is safe.

## [0.1.0] — TBD

First public release. Contents:

- `simulator.py`: MuJoCo simulator bridging LimX SDK `RobotCmd`
  (`q`, `dq`, `tau`, `Kp`, `Kd`) to `mujoco.MjData` for the TRON2A
  `SF_TRON2A` and `WF_TRON2A` variants.
- Three git submodules (`robot-description`, `robot-joystick`,
  `limxsdk-lowlevel`) — pinned by commit, not vendored.
- Documentation under `doc/` and `README.md`.

[Unreleased]: https://github.com/limx-tron2/tron2-mujoco-sim/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/limx-tron2/tron2-mujoco-sim/releases/tag/v0.1.0
