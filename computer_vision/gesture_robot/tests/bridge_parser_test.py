#!/usr/bin/env python3
"""Host unit tests for the gesture_bridge line parser.

Runs with plain Python, no ROS environment: it imports only
gesture_bridge.parser, which depends on nothing but the standard library.
This covers the wire-format contract (parsing, field extraction, and dropping
bad or out-of-range lines) that the design doc's phase 2 asks to test. The
serial read loop and ROS publishing are exercised separately with a
pseudo-terminal harness that does need the ROS environment.

    python3 tests/bridge_parser_test.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ros2_ws', 'src', 'gesture_bridge'))

from gesture_bridge.parser import VALID_GESTURES, parse_gesture_line  # noqa: E402

checks = 0
failures = 0


def check(cond, msg):
    global checks, failures
    checks += 1
    if not cond:
        failures += 1
        print(f'    FAIL: {msg}')


def expect_drop(raw, note):
    check(parse_gesture_line(raw) is None, f'{note!r} should be dropped')


def expect_parse(raw, gesture, confidence, cx, cy, note):
    got = parse_gesture_line(raw)
    check(got is not None, f'{note!r} should parse')
    if got is None:
        return
    check(got['gesture'] == gesture, f'{note}: gesture {got["gesture"]} != {gesture}')
    check(abs(got['confidence'] - confidence) < 1e-6,
          f'{note}: confidence {got["confidence"]} != {confidence}')
    check(abs(got['bbox_cx'] - cx) < 1e-6, f'{note}: cx {got["bbox_cx"]} != {cx}')
    check(abs(got['bbox_cy'] - cy) < 1e-6, f'{note}: cy {got["bbox_cy"]} != {cy}')


def test_valid_gestures_set():
    check(VALID_GESTURES == frozenset((0, 1, 2, 255)),
          f'VALID_GESTURES is {sorted(VALID_GESTURES)}')


def test_each_gesture_parses():
    expect_parse(b'{"g":0,"c":0.80,"x":0.5,"y":0.48,"t":1}', 0, 0.80, 0.5, 0.48, 'paper')
    expect_parse(b'{"g":1,"c":0.78,"x":0.546,"y":0.554,"t":2}', 1, 0.78, 0.546, 0.554, 'rock')
    expect_parse(b'{"g":2,"c":0.63,"x":0.367,"y":0.571,"t":3}', 2, 0.63, 0.367, 0.571, 'scissors')
    expect_parse(b'{"g":255,"c":0.0,"x":0.0,"y":0.0,"t":4}', 255, 0.0, 0.0, 0.0, 'none')


def test_accepts_str_and_bytes():
    expect_parse('{"g":1,"c":0.9,"x":0.1,"y":0.2}', 1, 0.9, 0.1, 0.2, 'str input')
    expect_parse(b'{"g":1,"c":0.9,"x":0.1,"y":0.2}', 1, 0.9, 0.1, 0.2, 'bytes input')


def test_extra_fields_ignored():
    expect_parse(b'{"g":0,"c":0.7,"x":0.1,"y":0.2,"t":9999,"extra":"z"}',
                 0, 0.7, 0.1, 0.2, 'extra fields')


def test_garbage_dropped():
    expect_drop(b'not json at all\n', 'garbage')
    expect_drop(b'', 'empty')
    expect_drop(b'\n', 'newline only')
    expect_drop(b'{"g":1,"c":0.5', 'truncated json')


def test_missing_fields_dropped():
    expect_drop(b'{"g":1,"c":0.5}', 'missing x,y')
    expect_drop(b'{"c":0.5,"x":0.1,"y":0.2}', 'missing g')
    expect_drop(b'{"g":1,"x":0.1,"y":0.2}', 'missing c')


def test_bad_types_dropped():
    expect_drop(b'{"g":1,"c":"high","x":0.1,"y":0.2}', 'confidence not a number')
    expect_drop(b'{"g":"rock","c":0.5,"x":0.1,"y":0.2}', 'gesture not a number')
    expect_drop(b'{"g":null,"c":0.5,"x":0.1,"y":0.2}', 'gesture null')
    expect_drop(b'[1,2,3]', 'json array, not object')


def test_out_of_range_dropped():
    # The bug the pty test caught: 300 would wrap to 44 at serialization.
    expect_drop(b'{"g":300,"c":0.5,"x":0.1,"y":0.2}', 'gesture 300')
    expect_drop(b'{"g":3,"c":0.5,"x":0.1,"y":0.2}', 'gesture 3 (unknown class)')
    expect_drop(b'{"g":-1,"c":0.5,"x":0.1,"y":0.2}', 'gesture -1')
    expect_drop(b'{"g":256,"c":0.5,"x":0.1,"y":0.2}', 'gesture 256')
    expect_drop(b'{"g":254,"c":0.5,"x":0.1,"y":0.2}', 'gesture 254 (near none)')


def test_boundary_values_parse():
    expect_parse(b'{"g":2,"c":0.0,"x":0.0,"y":0.0}', 2, 0.0, 0.0, 0.0, 'zeros')
    expect_parse(b'{"g":0,"c":1.0,"x":1.0,"y":1.0}', 0, 1.0, 1.0, 1.0, 'ones')
    # A float-looking gesture that is exactly an integer value still parses.
    expect_parse(b'{"g":1.0,"c":0.5,"x":0.1,"y":0.2}', 1, 0.5, 0.1, 0.2, 'g as 1.0')


TESTS = [
    ('valid gestures set', test_valid_gestures_set),
    ('each gesture parses', test_each_gesture_parses),
    ('accepts str and bytes', test_accepts_str_and_bytes),
    ('extra fields ignored', test_extra_fields_ignored),
    ('garbage dropped', test_garbage_dropped),
    ('missing fields dropped', test_missing_fields_dropped),
    ('bad types dropped', test_bad_types_dropped),
    ('out of range dropped', test_out_of_range_dropped),
    ('boundary values parse', test_boundary_values_parse),
]


def main():
    failed = 0
    for name, fn in TESTS:
        before = failures
        fn()
        ok = failures == before
        if not ok:
            failed += 1
        print(f'{"PASS" if ok else "FAIL"}  {name}')
    print(f'\n{len(TESTS) - failed} of {len(TESTS)} tests passed, {checks} checks')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
