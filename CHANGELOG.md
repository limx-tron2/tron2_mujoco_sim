# Changelog

This file records user-visible changes to the public project.

## Unreleased

- Provide a DACH_TRON2A-only MuJoCo simulator for the 16 arm and head joints.
- Support models with and without the two-finger grippers.
- Route simulated motor, IMU, and gripper communication through
  `limxsdk-lowlevel` simulation-side APIs.
- Track the approved `limxsdk-lowlevel` and optional `robot-joystick` baselines
  as Git submodules, while keeping `robot-description` as an external checkout.
