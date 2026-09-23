"""Wire-format parsing for the v1 serial link, with no ROS dependency.

Kept separate from the node so the parsing contract can be unit-tested with
plain Python. The node (serial_bridge.py) turns a parsed dict into a
gesture_msgs/Gesture and publishes it.
"""
import json

# Must match the constants in gesture_msgs/msg/Gesture.msg:
# PAPER=0, ROCK=1, SCISSORS=2, NONE=255. This build's generated message class
# does not range-check uint8 on assignment or raise on it; an out-of-range
# gesture silently wraps at serialization (300 -> 44), so the bridge rejects
# out-of-range values here instead of relying on the message class.
VALID_GESTURES = frozenset((0, 1, 2, 255))


def parse_gesture_line(raw):
    """Parse one JSON line from the camera.

    Returns a dict with keys gesture, confidence, bbox_cx, bbox_cy on success,
    or None if the line is malformed, missing a field, or carries an
    out-of-range gesture. `raw` may be bytes or str; extra fields (like the
    device timestamp `t`) are ignored.
    """
    try:
        data = json.loads(raw)
        gesture = int(data['g'])
        if gesture not in VALID_GESTURES:
            return None
        return {
            'gesture': gesture,
            'confidence': float(data['c']),
            'bbox_cx': float(data['x']),
            'bbox_cy': float(data['y']),
        }
    except (ValueError, KeyError, TypeError):
        return None
