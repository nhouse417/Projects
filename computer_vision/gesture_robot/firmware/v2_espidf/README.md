# Firmware v2 (ESP-IDF + micro-ROS)

The ESP32-C3 publishes `/gesture/event` itself over Wi-Fi via micro-ROS
(Micro-XRCE-DDS to the agent on the Mac), replacing the v1 USB serial bridge.
Nothing downstream of the topic changes. Built with ESP-IDF 5.4 and the
`micro_ros_espidf_component` (jazzy), which lives under `components/` as a git
submodule.

Migration runs in steps, each with a visible check (design doc section 7):

| Step | What it adds | Check |
|---|---|---|
| **M3** | custom message built into micro-ROS; hard-coded `Gesture` at 1 Hz | `ros2 topic echo /gesture/event` shows v1's fields |
| M4 | the AT client (UART1, raw then parsed boxes) | parsed boxes match v1 for the same hand |
| M5 | shared debouncer, 1 s heartbeat, time sync, reconnection | `ros2 topic hz` ≈ 1 Hz at rest, extra msgs on change |

**Current: M3.** `main/app_main.cpp` publishes a fixed `Gesture` (ROCK, 0.87,
box 0.512/0.430) once per second. No camera or debouncer yet — this step only
proves the custom message is built into micro-ROS and arrives downstream.

## One-time setup

After checking out this branch, fetch the component submodule and prepare it.
Run from the repo root (`computer_vision/gesture_robot`):

```bash
# 1. Fetch the micro-ROS component (jazzy).
git submodule update --init firmware/v2_espidf/components/micro_ros_espidf_component

# 2. Reapply the macOS build patch. A submodule tracks a commit, not working-tree
#    edits, so the one-line libmicroros.mk patch has to be reapplied on a clean
#    checkout. Idempotent.
scripts/patch_microros_component.sh

# 3. Copy gesture_msgs into the component so it is built into micro-ROS.
#    Re-run after any change to the .msg (then: idf.py clean-microros && idf.py build).
scripts/sync_msgs.sh
```

## Build and flash

Build from a terminal **outside `pixi shell`** so no ROS 2 (Jazzy) environment is
active — the component builds its own ROS 2 libraries from source, and a sourced
Jazzy env confuses that build.

```bash
get_idf                 # ESP-IDF 5.4 export, forcing pyenv Python 3.12 (see below)
cd firmware/v2_espidf
idf.py set-target esp32c3        # first build only
idf.py menuconfig                # micro-ROS Settings: Mac's IP + port 8888; Wi-Fi SSID/password
idf.py build
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

Wi-Fi credentials and the agent IP land in the gitignored `sdkconfig`;
`sdkconfig.defaults` holds only the credential-free settings (target, 4 MB flash,
single-app-large partition, Wi-Fi UDP transport, agent port 8888).

The monitor prints `publishing gesture=1` once per second once Wi-Fi associates
and the agent is reachable.

## Verify (M3 gate)

Start the agent on the Mac (inside `pixi shell`), either through the bringup
launch file or standalone:

```bash
# via the stack (also brings up the behavior node + robot):
ros2 launch gesture_bringup bringup.launch.py transport:=microros robot:=turtlesim
# or just the agent, for a bare topic check:
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 -v6
```

Then, in another `pixi shell`:

```bash
ros2 topic echo /gesture/event
```

Expected at ~1 Hz:

```yaml
header:
  stamp: {sec: 0, nanosec: 0}     # device time sync lands in M5
  frame_id: gesture_camera
gesture: 1                         # ROCK
confidence: 0.87
bbox_cx: 0.512
bbox_cy: 0.430
```

Same fields the v1 bridge publishes — this is the M3 done-when.

## ESP-IDF on this Mac (notes)

- **Python 3.9–3.12, not 3.14** — ESP-IDF 5.4's installer doesn't support
  Homebrew's 3.14. The `get_idf` alias points `export.sh` at a pyenv 3.12.
- The `patch_microros_component.sh` fixes above (`g++` instead of `gcc`, and
  `-DPython3_EXECUTABLE=$(which python3)`) let the component's host-side library
  build succeed on macOS. See the comments in that script.
- Build hygiene: never run `idf.py` from inside `pixi shell`.
