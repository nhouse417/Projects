# Firmware v2 (ESP-IDF + micro-ROS)

The ESP32-C3 publishes `/gesture/event` itself over Wi-Fi via micro-ROS
(Micro-XRCE-DDS to the agent on the Mac), replacing the v1 USB serial bridge.
Nothing downstream of the topic changes. Built with ESP-IDF 5.4 and the
`micro_ros_espidf_component` (jazzy), which lives under `components/` as a git
submodule.

Migration runs in steps, each with a visible check (design doc section 7):

| Step | What it adds | Check |
|---|---|---|
| M3 | custom message built into micro-ROS; hard-coded `Gesture` at 1 Hz | `ros2 topic echo /gesture/event` shows v1's fields |
| M4 | the AT client (UART1, raw then parsed boxes) | parsed boxes match v1 for the same hand |
| **M5** | shared debouncer, 1 s heartbeat, time sync, reconnection | `ros2 topic hz` ≈ 1 Hz at rest, extra msgs on change |

**Current: M5 — the complete v2 firmware.** Two FreeRTOS tasks, so a slow Wi-Fi
moment never makes the device miss frames:

- **`vision_task`** (`main/at_client.cpp`) reads the camera over UART1, parses
  each frame, runs the **shared debouncer** (`firmware/common/gesture_debouncer.*`,
  the same code v1 uses — symlinked into `main/`), and queues a `gesture::Event`
  on each confirmed change (5 frames ≥ 0.60 to confirm, 500 ms none-timeout).
- **`ros_task`** (`main/ros_link.cpp`) waits for the agent (pinging with
  `rmw_uros_ping_agent_options`), creates the node/publisher, syncs device time to
  the agent (`rmw_uros_sync_session`, so `header.stamp` is real), then publishes
  queued changes immediately plus a **1 Hz heartbeat** with the current state from
  an rclc timer.

**Reconnection.** The link is monitored by publish success: with reliable QoS and
a 1-deep stream, a vanished or restarted agent stops ACKing and `rcl_publish`
fails within ~1-2 s; a few in a row and the device **reboots** (`esp_restart`) to
reconnect. Tearing a micro-ROS session down in place once its agent is gone is
unreliable on this component, whereas a fresh boot reconnects cleanly — the same
path a power-cycle takes. The behavior node's 2 s watchdog has already stopped the
robot by the time the reboot happens, and boot + Wi-Fi + reconnect takes a few
seconds. (The design doc describes a graceful ping-based state machine; this is
the pragmatic substitute that actually survives agent loss here.)

This is the full v1-equivalent behavior, now published by the device itself.

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
idf.py menuconfig                # Wi-Fi SSID/password + Mac's IP (micro-ROS Settings)
idf.py build
idf.py -p /dev/cu.usbmodem3101 flash monitor
```

`idf.py menuconfig` sets the Wi-Fi SSID/password and the Mac's IP (under
*micro-ROS Settings*), which land in the gitignored `sdkconfig`;
`sdkconfig.defaults` holds only the credential-free settings (target, 4 MB flash,
single-app-large partition, Wi-Fi UDP transport, agent port 8888). M5 needs these
set — the Mac's IP must be its current LAN address, reachable from the ESP32.

## Verify (M5 gate)

Start the agent on the Mac (inside `pixi shell`, workspace sourced), then watch
the topic. The device connects on its own once the agent is up (and reconnects if
it isn't — no need to reset the board):

```bash
# terminal A (pixi): the whole stack, driving a robot from the camera
ros2 launch gesture_bringup bringup.launch.py transport:=microros robot:=turtlesim
# terminal B (pixi): rate + contents
ros2 topic hz /gesture/event
ros2 topic echo /gesture/event
```

**M5 passes** when:

- `ros2 topic hz` shows **~1 Hz at rest** (the heartbeat), with **extra messages
  on each gesture change**;
- `header.stamp` is real wall-clock time now (not 0), from the agent time sync;
- the robot responds to rock/paper/scissors exactly as it did under
  `transport:=serial` (v1), and stops within ~2 s when the camera is covered or
  unplugged (the behavior node's watchdog);
- **reconnection:** Ctrl-C the launch and relaunch it — within a few seconds the
  device reboots and reconnects on its own, and the topic resumes (the monitor
  prints `agent lost; rebooting to reconnect`, then after the reboot `agent
  connected`). A power-cycle of the board recovers the same way.

The monitor also prints `gesture -> N (conf ...)` on each confirmed change.
`LOG_RAW_REPLIES 1` at the top of `at_client.cpp` dumps raw camera JSON instead,
for debugging the UART side.

## ESP-IDF on this Mac (notes)

- **Python 3.9–3.12, not 3.14** — ESP-IDF 5.4's installer doesn't support
  Homebrew's 3.14. The `get_idf` alias points `export.sh` at a pyenv 3.12.
- The `patch_microros_component.sh` fixes above (`g++` instead of `gcc`, and
  `-DPython3_EXECUTABLE=$(which python3)`) let the component's host-side library
  build succeed on macOS. See the comments in that script.
- Build hygiene: never run `idf.py` from inside `pixi shell`.
