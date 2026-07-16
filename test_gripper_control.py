#!/usr/bin/env python3
"""
LIMX 二指夹爪 limxsdk 客户端测试脚本：命令下发 + 状态读取

使用 limxsdk 夹爪客户端接口（需要 limxsdk >= 4.0.2）：
  发布:  Robot.publishGripperCmd(GripperCmd)   -> /limx/2F-gripper/cmd
  订阅:  Robot.subscribeGripperState(cb)        -> /limx/2F-gripper/state

GripperCmd 字段（[0]=左, [1]=右, 均为 0~100）:
  opening 开口度 (0=闭合, 100=最大张开)
  speed   速度
  force   夹持力
GripperState 字段:
  q       实际开口度 0~100 ([0]=左, [1]=右)

用法:
  python3 test_gripper_control.py                     # 双爪三角波循环开合
  python3 test_gripper_control.py --scenario phases    # 分阶段场景
  python3 test_gripper_control.py --speed 50 --force 60 --period 8
先启动 simulator.py (ROBOT_TYPE=DACH_TRON2A, 带夹爪)，再运行本脚本。按 Ctrl+C 退出。

© [2025] LimX Dynamics Technology Co., Ltd. All rights reserved.
"""

import os
import sys
import time
import argparse

import limxsdk.robot.Robot as Robot
import limxsdk.robot.RobotType as RobotType
import limxsdk.datatypes as datatypes


def triangle(t, period):
    """0..100..0 三角波, 周期 period 秒。"""
    x = (t % period) / period
    return (1.0 - abs(2.0 * x - 1.0)) * 100.0


def scenario_value(scenario, t, period):
    """返回 (opening_lr, label)，opening_lr = [left, right] 0~100。"""
    if scenario == "phases":
        phase = int(t / period) % 5
        table = [
            ([0, 0],     "both CLOSE"),
            ([100, 100], "both OPEN (right auto-clamped)"),
            ([100, 0],   "L open / R close (asymmetric)"),
            ([50, 50],   "both HALF"),
            ([0, 100],   "L close / R open (asymmetric)"),
        ]
        op, label = table[phase]
        return op, f"phase{phase}: {label}"
    q = triangle(t, period)
    return [q, q], "triangle"


def main():
    ap = argparse.ArgumentParser(description="LIMX 二指夹爪 limxsdk 客户端测试")
    ap.add_argument("--ip", default="127.0.0.1", help="robot/sim IP (limxsdk init)")
    ap.add_argument("--scenario", choices=["triangle", "phases"], default="triangle",
                    help="triangle=双爪三角波循环; phases=分阶段场景")
    ap.add_argument("--period", type=float, default=6.0, help="三角波周期 或 每阶段时长 (秒)")
    ap.add_argument("--speed", type=float, default=60.0, help="速度 0~100")
    ap.add_argument("--force", type=float, default=50.0, help="夹持力 0~100")
    ap.add_argument("--rate", type=float, default=20.0, help="发布频率 Hz")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(line_buffering=True)  # 实时刷新输出
    except Exception:
        pass

    print("🔬 LIMX 二指夹爪 limxsdk 客户端测试")
    print("=" * 60)
    print("   📤 发布: publishGripperCmd -> /limx/2F-gripper/cmd (GripperCmd)")
    print("   📡 订阅: subscribeGripperState <- /limx/2F-gripper/state (GripperState)")
    print(f"   场景={args.scenario} 周期={args.period}s speed={args.speed} force={args.force} rate={args.rate}Hz")
    print("   先确保 simulator.py 已运行 (ROBOT_TYPE=DACH_TRON2A, 带夹爪)")
    print("   按 Ctrl+C 退出")
    print("=" * 60)

    robot = Robot(RobotType.Tron2)
    robot.init(args.ip)

    last_state = {'q': None}

    def on_state(state):
        try:
            last_state['q'] = list(state.q)
        except Exception:
            pass

    robot.subscribeGripperState(on_state)

    cmd = datatypes.GripperCmd()
    start = time.time()
    count = 0
    pub_period = 1.0 / args.rate
    print_every = max(1, int(args.rate / 2))  # ~0.5s 打印一次

    try:
        while True:
            t = time.time() - start
            opening, label = scenario_value(args.scenario, t, args.period)
            cmd.opening = [float(opening[0]), float(opening[1])]
            cmd.speed = [float(args.speed), float(args.speed)]
            cmd.force = [float(args.force), float(args.force)]
            cmd.stamp = time.time_ns()
            robot.publishGripperCmd(cmd)

            count += 1
            if count % print_every == 0:
                st = last_state['q']
                if not st:
                    print(f"⏰ {t:5.1f}s | cmd L/R=({opening[0]:5.1f},{opening[1]:5.1f}) "
                          f"| {label} | ⚠️  尚未收到 state (simulator 是否在运行?)")
                else:
                    sl = st[0]
                    sr = st[1] if len(st) > 1 else float("nan")
                    el, er = sl - opening[0], sr - opening[1]
                    print(f"⏰ {t:5.1f}s | cmd L/R=({opening[0]:5.1f},{opening[1]:5.1f}) "
                          f"| state L/R=({sl:5.1f},{sr:5.1f}) "
                          f"| err L/R=({el:+5.1f},{er:+5.1f}) | {label}")
            time.sleep(pub_period)
    except KeyboardInterrupt:
        print("\n🛑 退出，发送闭合指令...")
        try:
            cmd.opening = [0.0, 0.0]
            cmd.stamp = time.time_ns()
            robot.publishGripperCmd(cmd)
        except Exception:
            pass
    print("✅ 测试结束")
    os._exit(0)


if __name__ == "__main__":
    main()
