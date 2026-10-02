#!/usr/bin/env bash
# Re-apply the macOS/RoboStack patch to the micro-ROS ESP-IDF component after a
# fresh `git submodule update --init` (phase 5, firmware v2). A submodule tracks
# a commit, not working-tree edits, so this one-line patch to libmicroros.mk
# does not travel with the pinned commit and has to be reapplied on a clean
# checkout.
#
# Why: the component builds its host-side micro-ROS library with colcon, and on
# this Mac that needs two fixes (same gotchas noted in the README):
#   - g++ instead of gcc for the C++ build (gcc doesn't link libc++), and
#   - the ESP-IDF venv's python3 forced via -DPython3_EXECUTABLE, because macOS
#     cmake otherwise grabs Homebrew's framework python, which lacks catkin_pkg.
# Idempotent; safe to run repeatedly.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MK="$ROOT/firmware/v2_espidf/components/micro_ros_espidf_component/libmicroros.mk"

if [ ! -f "$MK" ]; then
  echo "error: $MK not found. Set up the submodule first:" >&2
  echo "       git submodule update --init firmware/v2_espidf/components/micro_ros_espidf_component" >&2
  exit 1
fi

if grep -q 'Python3_EXECUTABLE' "$MK"; then
  echo "libmicroros.mk already patched"
  exit 0
fi

# Literal string replacement (no regex): the replacements contain make's $$ and
# shell $(...), which a regex engine would mangle.
python3 - "$MK" <<'PY'
import sys

path = sys.argv[1]
text = open(path).read()
flags = "-DPython3_EXECUTABLE=$$(which python3) -DPYTHON_EXECUTABLE=$$(which python3)"
subs = [
    ("-DCMAKE_CXX_COMPILER=gcc;",
     "-DCMAKE_CXX_COMPILER=g++ " + flags + ";"),
    ("-DUCLIENT_C_STANDARD=$(C_STANDARD);",
     "-DUCLIENT_C_STANDARD=$(C_STANDARD) " + flags + ";"),
]
for old, new in subs:
    if old not in text:
        sys.exit(f"error: expected text not found in libmicroros.mk:\n  {old}")
    text = text.replace(old, new)
open(path, "w").write(text)
PY

echo "patched libmicroros.mk (g++, Python3_EXECUTABLE)"
