#!/usr/bin/env bash
# Run a command with the colcon workspace (install/) sourced on top of the pixi
# environment. pixi's task shell can't `source`, so tasks go through bash:
#
#   pixi run ws ros2 launch kitti_bringup kitti.launch.py bag:=bags/kitti_0000
#   pixi run ws ros2 run detector_cpp detector_node

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$root/install/setup.bash" ]]; then
  echo "ws_run.sh: $root/install/setup.bash not found; run 'pixi run build' first" >&2
  exit 1
fi
if [[ $# -eq 0 ]]; then
  echo "usage: pixi run ws <command> [args...]" >&2
  exit 2
fi

source "$root/install/setup.bash"
exec "$@"
