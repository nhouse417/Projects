#!/usr/bin/env bash
# Build the micro-ROS agent from source into ros2_ws (phase 5, migration step M2).
# No prebuilt ros-jazzy-micro-ros-agent exists for osx-arm64 in RoboStack, so the
# agent is cloned and built here. The two repos are gitignored (external tooling),
# so this script recreates them. Run inside `pixi shell` from the repo root.
set -euo pipefail

WS="$(cd "$(dirname "$0")/.." && pwd)/ros2_ws"
cd "$WS/src"

clone() {  # clone <dir> <url>
  if [ -d "$1" ]; then
    echo "$1 already present"
  else
    git clone -b jazzy "$2" "$1"
  fi
}

clone micro_ros_msgs   https://github.com/micro-ROS/micro_ros_msgs.git
clone micro-ROS-Agent  https://github.com/micro-ROS/micro-ROS-Agent.git

# RoboStack's fmt (12.x) is too new for the pinned Micro-XRCE-DDS-Agent: its
# spdlog logging of endpoint types fails to compile under fmt 10+. Disable that
# logger profile in the agent's own CMake cache args (the outer colcon
# --cmake-args does not reach the inner ExternalProject). The agent still works.
SUPERBUILD=micro-ROS-Agent/micro_ros_agent/cmake/SuperBuild.cmake
if ! grep -q 'UAGENT_LOGGER_PROFILE' "$SUPERBUILD"; then
  # Insert the flag right after the system-logger line inside the xrceagent args.
  perl -0pi -e 's/(-DUAGENT_USE_SYSTEM_LOGGER:BOOL=\$\{UAGENT_USE_SYSTEM_LOGGER\}\n)/$1                -DUAGENT_LOGGER_PROFILE:BOOL=OFF\n/' "$SUPERBUILD"
  echo "patched $SUPERBUILD (UAGENT_LOGGER_PROFILE=OFF)"
fi

cd "$WS"
# -Wl,-dead_strip_dylibs: the agent links Python typesupport libraries
# (rosidl_generator_py) it never uses; on macOS they load at startup and abort
# with a flat-namespace _PyExc_RuntimeError (no libpython in a C++ binary).
# Stripping unused dylibs from the load commands fixes it — same fix as the
# C++ behavior node.
colcon build --packages-up-to micro_ros_agent \
  --cmake-args -DCMAKE_EXE_LINKER_FLAGS="-Wl,-dead_strip_dylibs"

echo
echo "Done. Test it with:"
echo "  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 -v6"
echo "The bringup launch starts it automatically with transport:=microros."
