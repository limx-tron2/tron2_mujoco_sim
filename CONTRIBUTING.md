# Contributing

1. Check existing issues before starting substantial work. Open an issue first
   for changes to robot, model, SDK, network, or safety behavior.
2. Follow the installation steps in `README.md`.
3. Record the exact `limxsdk-lowlevel` and `robot-description` revisions used
   for validation.
4. Run `python3 -m py_compile simulator.py test_gripper_control.py`.
5. Test both `python3 simulator.py` and `python3 simulator.py --no-grasper`.
6. For gripper changes, run the phased client scenario and confirm state is
   received continuously.
7. Keep pull requests focused and document user-visible behavior.

Contributions are licensed under Apache-2.0. Do not submit confidential
information or assets that you do not have permission to redistribute. Do not
vendor `limxsdk-lowlevel`, `robot-description`, binaries, models, datasets, or
media without an explicit provenance and redistribution review.

Use the pull request template and report security vulnerabilities according to
`SECURITY.md`, never in a public issue.
