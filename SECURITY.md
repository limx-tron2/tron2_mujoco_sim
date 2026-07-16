# Security Policy

## Scope

`tron2-mujoco-sim` is a Python MuJoCo-based simulator for the TRON2A
humanoid platform. Its central file, `simulator.py`, bridges the LimX
low-level SDK to a MuJoCo simulation: it accepts `RobotCmd` messages
(`q`, `dq`, `tau`, `Kp`, `Kd`) over the SDK transport and applies the
resulting joint torques inside `mujoco.MjData`.

### Sim-vs-real boundary — read before deploying

The **wire format** and **command semantics** used by this simulator
are identical to those used to drive the real TRON2A robot. That means:

- Any process that can reach the SDK endpoint (default `127.0.0.1`,
  overridable on the command line) can push `q` / `dq` / `tau` /
  `Kp` / `Kd` targets. On a real robot, those same targets move
  physical actuators.
- A controller that misbehaves against the simulator will misbehave
  against the physical robot the moment the endpoint IP is changed.
  The IP switch is the entire safety boundary between sim and real.
- Bugs in `simulator.py` that cause it to accept malformed or
  out-of-range commands mask the same bugs in a downstream controller
  and can lead to unsafe real-robot behavior.

For those reasons this repository intentionally does **not** ship:
control policies, calibration values, or a mode that silently forwards
to a real robot. See `THIRD_PARTY_NOTICES.md` for the exclusion list.

Control-path vulnerabilities in the deployment stack itself belong to
`tron2-rl-deploy-python` / `tron2-rl-deploy-ros`, not here.

## Private-IP handling

`<robot-ip>` in this repository's Markdown / YAML command examples is
a **placeholder token**, not a real address. Substitute your own
robot or simulator IP before running. Nothing in this repository
(including `simulator.py`, CI, or configuration) hard-codes a private
IP; the SDK endpoint defaults to `127.0.0.1` and is overridable on
the command line.

The internal-only sibling repository `tron2-rl-deploy-ros` retains a
documentation-example literal `10.192.1.2` in its source / launch
files (e.g. `Tron2HW.cpp`, `tron2_hw_node.cpp`, `tron2_hw.launch`),
kept per owner decision and declared in that repository's
`SECURITY.md`. That literal is documented there and is not mirrored
into this repository.

## Supported versions

Only the tip of the `main` branch and the most recent tagged release
receive security fixes. Older tags are provided as-is.

| Version   | Supported |
|-----------|-----------|
| `main`    | ✅        |
| Latest tag| ✅        |
| Older tags| ❌        |

## Reporting a vulnerability

**Do not** open a public issue for security reports.

Email: **contact@limxdynamics.com**
Subject prefix: `[tron2-mujoco-sim]`

Please include:

- Affected file(s) and commit / tag (and, if relevant, submodule
  pin recorded by `git submodule status --recursive`).
- A minimal reproducer or proof of concept.
- Impact assessment (e.g., "simulator accepts NaN torque without
  clamping", "SDK endpoint binds to 0.0.0.0 by default", "malformed
  RobotCmd crashes the sim").
- Whether the issue could affect a real robot if the endpoint IP were
  changed to a physical unit.
- Your preferred disclosure timeline and contact.

We aim to acknowledge reports within **3 business days** and provide a
remediation plan or an initial mitigation within **14 calendar days**.
We support coordinated disclosure; please do not publish details until
a fix or advisory is available.

## Out of scope

- Bugs in third-party parsers or runtimes (MuJoCo, onnxruntime, NumPy,
  SciPy, pygame) — report those upstream.
- Bugs inside the git submodules (`robot-description`, `robot-joystick`,
  `limxsdk-lowlevel`) — report those to the respective repositories.
- Physical safety of the robot itself — report to the deployment
  repositories or to LimX product support.
- Requests to publish calibration data, control policies, or firmware —
  this repository intentionally excludes those.

## Safe harbor

Good-faith security research that follows this policy will not be
pursued legally by LimX Dynamics. Please respect user privacy, avoid
service disruption, and do not access data beyond what is necessary to
demonstrate the issue. Never point a proof-of-concept at a real
robot's control endpoint — use the local `127.0.0.1` simulator target.
