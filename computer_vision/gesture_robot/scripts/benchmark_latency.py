#!/usr/bin/env python3
"""Measure /gesture/event timing for the v1-vs-v2 benchmark (phase 6).

Run inside `pixi shell` with the workspace sourced, while the stack is up:

    ros2 launch gesture_bringup bringup.launch.py transport:=microros robot:=turtlesim
    python3 scripts/benchmark_latency.py        # Ctrl-C to print the summary

Reports message count and average rate, the device->ROS latency (v2 only, from
header.stamp vs receive time on the synced clock), and the largest inter-message
gap (a hint for recovery time). v1 stamps on the PC, so its latency reads ~0 and
is n/a there; use the slow-motion video method for the fair end-to-end
hand->robot comparison.
"""
import statistics

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from gesture_msgs.msg import Gesture


class Bench(Node):
    def __init__(self):
        super().__init__('gesture_benchmark')
        # Match the contract: reliable, keep last 10.
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.create_subscription(Gesture, '/gesture/event', self._on_msg, qos)
        self.count = 0
        self.latencies_ms = []
        self.unsynced = 0
        self.first_recv_ns = None
        self.last_recv_ns = None
        self.max_gap_s = 0.0

    def _on_msg(self, msg):
        now_ns = self.get_clock().now().nanoseconds  # system/ROS clock
        self.count += 1
        if self.first_recv_ns is None:
            self.first_recv_ns = now_ns
        if self.last_recv_ns is not None:
            gap = (now_ns - self.last_recv_ns) / 1e9
            self.max_gap_s = max(self.max_gap_s, gap)
        self.last_recv_ns = now_ns

        stamp = msg.header.stamp
        stamp_ns = stamp.sec * 1_000_000_000 + stamp.nanosec
        # A real one-way latency needs the stamp on the same wall clock as the
        # receiver. A valid wall-clock stamp is within a day of now; anything
        # further off means the device clock isn't synced to the agent's wall
        # clock (micro-ROS time sync not applied), so the delta is meaningless.
        if 0 < stamp_ns and abs(now_ns - stamp_ns) < 86_400 * 1_000_000_000:
            self.latencies_ms.append((now_ns - stamp_ns) / 1e6)
        else:
            self.unsynced += 1

    def summary(self):
        print('\n=== /gesture/event benchmark ===')
        print(f'messages: {self.count}')
        if self.count > 1 and self.first_recv_ns is not None:
            elapsed = (self.last_recv_ns - self.first_recv_ns) / 1e9
            if elapsed > 0:
                print(f'elapsed: {elapsed:.1f} s    average rate: '
                      f'{self.count / elapsed:.2f} Hz')
            print(f'largest inter-message gap: {self.max_gap_s:.2f} s')
        if self.latencies_ms:
            xs = sorted(self.latencies_ms)
            n = len(xs)
            pct = lambda q: xs[min(n - 1, int(q * n))]
            print(f'device->ROS latency (n={n}): mean {statistics.mean(xs):.1f} ms, '
                  f'p50 {pct(0.5):.1f} ms, p95 {pct(0.95):.1f} ms, max {xs[-1]:.1f} ms')
        elif self.unsynced:
            print(f'device->ROS latency: n/a -- stamps are not wall-clock aligned '
                  f'({self.unsynced} messages). The device clock is not synced to the '
                  f'agent (v1 stamps on the PC; v2 time sync not applied here). Use the '
                  f'slow-motion video for the end-to-end hand->robot latency.')
        else:
            print('device->ROS latency: n/a (no messages carried a stamp)')


def main():
    rclpy.init()
    node = Bench()
    print('listening on /gesture/event ... Ctrl-C for the summary')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.summary()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
