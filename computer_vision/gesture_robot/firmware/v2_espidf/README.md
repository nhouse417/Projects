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
| **M4** | the AT client (UART1, raw then parsed boxes) | parsed boxes match v1 for the same hand |
| M5 | shared debouncer, 1 s heartbeat, time sync, reconnection | `ros2 topic hz` ≈ 1 Hz at rest, extra msgs on change |

**Current: M4.** `main/app_main.cpp` runs only `vision_task` (`main/at_client.cpp`):
it drives the Grove Vision AI V2 over UART1 at 921600 baud (XIAO **D6→TX**,
**D7→RX**), sends `AT+INVOKE=-1,0,1`, frames each reply on `\r`/`\n`, parses the
`[x,y,w,h,score,target]` boxes with cJSON, and logs the best one to the USB
console. **No Wi-Fi or micro-ROS in this step** — M3's publisher and this camera
path are joined by the shared debouncer and an event queue in M5, so M4 is
verified on the serial monitor, not a ROS topic.

M3 (the hard-coded `Gesture` publisher) is in git history at the `Phase 5 (M3)`
commit; this step replaces `app_main` with the camera path.

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
idf.py menuconfig                # Wi-Fi/agent settings — not needed for M4 (see below)
idf.py build
idf.py -p /dev/cu.usbmodem3101 flash monitor
```

`idf.py menuconfig` sets the Wi-Fi SSID/password and the Mac's IP (under
*micro-ROS Settings*), which land in the gitignored `sdkconfig`;
`sdkconfig.defaults` holds only the credential-free settings (target, 4 MB flash,
single-app-large partition, Wi-Fi UDP transport, agent port 8888).
**M4 uses neither Wi-Fi nor the agent**, so you can skip `menuconfig` entirely
for this step — it reads the camera over UART and logs to USB only.

## Verify (M4 gate)

UART1 is routed to **D6/D7**, the XIAO header pins already wired to the Vision AI
V2 on this board — the same link v1 drove over UART0, so there's nothing to wire.
Just watch the monitor (no agent, no `ros2`):

```bash
idf.py -p /dev/cu.usbmodem3101 monitor
```

Hold a gesture in front of the camera; each inference frame logs the best box:

```
box x=120 y=118 w=96 h=104 score=82 target=1  (cx=0.500 cy=0.492 s=0.82)
```

The left block is the raw box in the 240×240 frame (same numbers v1 prints with
`LOG_RAW_BOXES 1`); the parenthesised block is the normalized center and 0–1
score the debouncer will consume in M5. **M4 passes** when `target`/`score` and
the box track v1 for the same hand in the same lighting — paper `target 0`, rock
`1`, scissors `2`. Set `LOG_RAW_REPLIES 1` at the top of `at_client.cpp` to dump
the raw JSON replies instead, to eyeball the wire format first.

### M3 gate (for reference)

M3 published a hard-coded `Gesture` over Wi-Fi; with the agent running,
`ros2 topic echo /gesture/event` showed `gesture 1`, `confidence 0.87`,
`bbox 0.512/0.430`, `frame_id gesture_camera` at ~1 Hz. That path returns, driven
by the camera, in M5.

## ESP-IDF on this Mac (notes)

- **Python 3.9–3.12, not 3.14** — ESP-IDF 5.4's installer doesn't support
  Homebrew's 3.14. The `get_idf` alias points `export.sh` at a pyenv 3.12.
- The `patch_microros_component.sh` fixes above (`g++` instead of `gcc`, and
  `-DPython3_EXECUTABLE=$(which python3)`) let the component's host-side library
  build succeed on macOS. See the comments in that script.
- Build hygiene: never run `idf.py` from inside `pixi shell`.
