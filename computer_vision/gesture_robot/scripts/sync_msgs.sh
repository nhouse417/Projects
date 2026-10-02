#!/usr/bin/env bash
# Copy the gesture_msgs package into the micro-ROS component's extra_packages/,
# so it is built into libmicroros and its generated C headers appear under the
# component's include/ for the v2 firmware to use (phase 5, firmware v2).
#
# The custom message has to live inside the component rather than come from the
# registry, and extra_packages/ is gitignored, so this regenerates it. Run it
# once after setting up the submodule, and again after any change to the .msg.
# The component's make-based build does not always notice source changes, so
# after a change force a rebuild of just the micro-ROS library:
#   idf.py clean-microros && idf.py build
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/ros2_ws/src/gesture_msgs"
COMPONENT="$ROOT/firmware/v2_espidf/components/micro_ros_espidf_component"
DST="$COMPONENT/extra_packages/gesture_msgs"

if [ ! -d "$SRC" ]; then
  echo "error: $SRC not found" >&2
  exit 1
fi
if [ ! -d "$COMPONENT/extra_packages" ]; then
  echo "error: micro-ROS component not found. Set up the submodule first:" >&2
  echo "       git submodule update --init firmware/v2_espidf/components/micro_ros_espidf_component" >&2
  exit 1
fi

# Replace wholesale so a removed source file never lingers in the copy.
rm -rf "$DST"
mkdir -p "$DST"
cp -R "$SRC/package.xml" "$SRC/CMakeLists.txt" "$SRC/msg" "$DST/"

echo "synced gesture_msgs -> $DST"
