import threading
import time

import rclpy
import serial
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from gesture_msgs.msg import Gesture

from gesture_bridge.parser import parse_gesture_line

GESTURE_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
)


class SerialBridge(Node):
    def __init__(self, **kwargs):
        super().__init__('gesture_bridge', **kwargs)
        # Find yours with: ls /dev/cu.usbmodem*
        self.port = self.declare_parameter('port', '/dev/cu.usbmodem101').value
        self.baud = self.declare_parameter('baud', 115200).value
        self.frame_id = self.declare_parameter('frame_id', 'gesture_camera').value
        self.pub = self.create_publisher(Gesture, '/gesture/event', GESTURE_QOS)
        self.bad_lines = 0
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        while rclpy.ok():
            try:
                with serial.Serial(self.port, self.baud, timeout=1.0) as ser:
                    self.get_logger().info(f'Connected to {self.port}')
                    while rclpy.ok():
                        raw = ser.readline()
                        if raw.endswith(b'\n'):
                            self._handle(raw)
            except serial.SerialException as exc:
                self.get_logger().warn(f'Serial error: {exc}. Retrying in 2 s.')
                time.sleep(2.0)

    def _handle(self, raw):
        parsed = parse_gesture_line(raw)
        if parsed is None:
            self.bad_lines += 1
            self.get_logger().debug(f'Dropped line {raw!r} ({self.bad_lines} total)')
            return
        msg = Gesture()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.gesture = parsed['gesture']
        msg.confidence = parsed['confidence']
        msg.bbox_cx = parsed['bbox_cx']
        msg.bbox_cy = parsed['bbox_cy']
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = SerialBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
