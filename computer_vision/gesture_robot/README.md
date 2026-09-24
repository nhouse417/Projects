# Gesture-controlled robot

A hand gesture seen by a XIAO Vision AI Camera drives a simulated robot in ROS 2. Rock, paper, and scissors each trigger a distinct robot action. The camera-to-ROS link starts as a Python serial bridge (v1) and is later replaced by micro-ROS over Wi-Fi (v2), without changing anything downstream of the topic. Development runs natively on an M4 Mac.

## Status

| Phase | Work | Status |
|---|---|---|
| 1 | Firmware v1: Arduino sketch reads gestures, debounces, prints JSON over USB | Done |
| 2 | `gesture_msgs` contract and the Python serial bridge | Done |
| 3 | C++ behavior node drives turtlesim, with a safety watchdog | Done |
| 4 | Hand mimic in RViz2, then hand and TurtleBot3 in Gazebo | Next |
| 5 | Firmware v2: ESP-IDF, a custom AT client, micro-ROS over Wi-Fi | Planned |
| 6 | Swap the transport, rerun the same tests, benchmark v1 against v2 | Planned |

## Goals

- Rock, paper, and scissors each trigger a distinct, repeatable robot action in simulation.
- A dropped gesture, unplugged camera, or lost Wi-Fi link always stops the robot within about 2 seconds.
- The camera-to-ROS link can be swapped from the Python bridge to micro-ROS with no change to the behavior node, the simulation, or the topic.
- The project produces measurable v1 vs v2 results.

Out of scope: training a custom model, real robot hardware, and continuous hand tracking. The bounding-box center is carried in the message so tracking can be added later.

## Architecture

Both versions share the camera, the debounce code, the topic, and everything on the ROS side after the topic. Only the path from the ESP32-C3 into ROS 2 changes.

```mermaid
flowchart LR
    subgraph cam["XIAO Vision AI Camera"]
        OV["OV5647"] --> VAI["Grove Vision AI V2<br/>gesture model"] --> ESP["XIAO ESP32-C3<br/>debouncer"]
    end
    subgraph mac["Mac, ROS 2 Jazzy"]
        BR["gesture_bridge<br/>Python, v1"]
        AG["micro-ROS agent<br/>v2"]
        BEH["gesture_behavior<br/>mapping, 2 s watchdog"]
        SIM["turtlesim, RViz2, Gazebo"]
    end
    ESP -->|"v1: USB serial, JSON lines"| BR
    ESP -.->|"v2: Wi-Fi UDP 8888, XRCE-DDS"| AG
    BR -->|"/gesture/event"| BEH
    AG -->|"/gesture/event"| BEH
    BEH -->|"velocity or joint commands"| SIM
```

| Part | v1 | v2 |
|---|---|---|
| Device framework | Arduino | ESP-IDF with FreeRTOS tasks |
| Vision AI V2 client | Seeed Arduino SSCMA library | Custom AT client over UART |
| Debounce logic | Same C++ files in `firmware/common/` | Same C++ files in `firmware/common/` |
| Device to host | USB serial, JSON lines | Wi-Fi UDP to the micro-ROS agent |
| Publisher of `/gesture/event` | `gesture_bridge` on the Mac | The ESP32-C3 itself |
| Timestamp source | Mac receive time | Device time, synced with the agent |

## Interface contract

The one thing both versions must agree on. A change to it goes into firmware v1, firmware v2, and the bridge in the same commit.

| | |
|---|---|
| Topic | `/gesture/event` |
| Type | `gesture_msgs/msg/Gesture` |
| QoS | Reliable, keep last 10, volatile |
| When published | Immediately when the confirmed gesture changes, plus a heartbeat with the current state every 1 s |
| `frame_id` | `gesture_camera` |

```
uint8 PAPER=0
uint8 ROCK=1
uint8 SCISSORS=2
uint8 NONE=255

std_msgs/Header header
uint8 gesture        # one of the constants above
float32 confidence   # 0.0 to 1.0
float32 bbox_cx      # normalized box center, 0.0 to 1.0
float32 bbox_cy
```

The heartbeat is what makes silence meaningful. The behavior node's watchdog stops the robot after 2 s, or two missed heartbeats, without a message. It also lets a node that starts late learn the current gesture within a second.

## Hardware and software

- **Camera:** XIAO Vision AI Camera, which is a Grove Vision AI V2 (Himax WiseEye2), a XIAO ESP32-C3, and an OV5647 sensor
- **Model:** SenseCraft AI Gesture Detection (rock, paper, scissors), deployed from the SenseCraft web tool
- **Dev machine:** M4 Mac running ROS 2 Jazzy natively through [RoboStack](https://robostack.github.io/) and pixi
- **Simulation:** turtlesim and RViz2 through phase 4, then Gazebo Harmonic
- **Firmware v1:** Arduino IDE with the Arduino-ESP32 core and the Seeed Arduino SSCMA library
- **Firmware v2:** ESP-IDF 5.4 or newer with `micro_ros_espidf_component` (jazzy branch)

## Repository layout

```
gesture_robot/
├── pixi.toml, pixi.lock        # ROS 2 Jazzy environment for the Mac
├── firmware/
│   ├── common/                 # gesture_debouncer.h/.cpp, shared by v1 and v2
│   └── v1_arduino/
│       └── gesture_camera_v1/  # Arduino sketch; debouncer files are symlinks into common/
├── ros2_ws/src/
│   ├── gesture_msgs/           # the Gesture.msg interface contract
│   ├── gesture_bridge/         # v1: reads JSON over USB, publishes /gesture/event
│   ├── gesture_behavior/       # C++ node: gestures -> velocity, with a watchdog
│   └── gesture_bringup/        # one launch file for the whole stack
└── tests/
    ├── debouncer_test.cpp      # host unit tests for the debouncer (C++)
    └── bridge_parser_test.py   # host unit tests for the bridge parser (Python)
```

## Firmware v1

### Debouncer

Detection models flicker between classes on transitional frames, so the device only reports a gesture after seeing it for several frames in a row.

- A gesture is confirmed after **5 consecutive frames** of the same class at **0.60 confidence or higher**.
- A single missed frame doesn't break a streak. A gap longer than 500 ms clears it, so frames on either side of a dropout never count as consecutive.
- After **500 ms** with no usable detection, it reports `NONE` once.
- Model classes map 0 to paper, 1 to rock, 2 to scissors, and anything else to none. `map_class()` is the only place that knows this order.
- It's plain C++ with no Arduino or ESP-IDF calls, so both firmware versions compile the same files and it runs in host unit tests. Timestamps use unsigned arithmetic, so `millis()` wrapping after 49.7 days is handled.

### Serial output

One JSON line per gesture change, plus a heartbeat every second:

```json
{"g":1,"c":0.87,"x":0.512,"y":0.430,"t":48213}
```

`g` is the gesture constant from the message definition, `c` the confidence, `x` and `y` the normalized box center, and `t` the device's `millis()` for debugging. Heartbeats repeat the values from the last change.

### What the hardware showed

None of these were documented reliably, so each was measured on the device:

- **Box `x` and `y` are the center, in a 240×240 frame.** The model's input is 192×192, but the camera rescales boxes to the preview frame before sending them.
- **Scores arrive as 0 to 100**, and the class order is paper 0, rock 1, scissors 2.
- **The camera has its own confidence threshold.** It's device state (`AT+TSCORE`), set from the SenseCraft web tool and kept in flash across power cycles. It's set to 50 so that the debouncer's 0.60 is the threshold that decides.
- **The SSCMA library's `invoke()` arguments are easy to get backwards.** The library builds `AT+INVOKE=<times>,<!filter>,<filter>`, so `AI.invoke(1, false, false)` asks the camera to reply only when the result changes and to include the image. `AI.invoke(1, true, false)` sends `AT+INVOKE=1,0,1`: every frame, results only.

### Flashing

1. In the Arduino IDE, install the **esp32** board package by Espressif Systems and the **Seeed Arduino SSCMA** library. Accept its ArduinoJson dependency.
2. Open `firmware/v1_arduino/gesture_camera_v1/gesture_camera_v1.ino`. The two debouncer files in that folder are symlinks into `firmware/common/`, so don't copy the sketch elsewhere or use Save As.
3. Select board **XIAO_ESP32C3**, keep **USB CDC On Boot** enabled, and pick the `/dev/cu.usbmodem…` port.
4. Upload. If it can't sync, hold BOOT, tap RESET, release BOOT, and try again.
5. Open the Serial Monitor at 115200 baud. Set `LOG_RAW_BOXES` to 1 to also print every raw box.

## Behavior node

`gesture_behavior` (C++, rclcpp) subscribes to `/gesture/event` and drives the robot:

- **Change detection.** It holds the active gesture. A heartbeat carrying the same gesture only refreshes the watchdog; it does not re-trigger anything.
- **Velocity output.** A 10 Hz timer publishes the active gesture's velocity as `geometry_msgs/Twist` on `cmd_vel_topic`. `NONE` publishes zero. Turtlesim needs a continuous stream, so this publishes every tick, not only on change.
- **Watchdog.** A 5 Hz timer drops the active gesture to `NONE` (stop) when no message has arrived for `watchdog_timeout_s` (2 s, two missed heartbeats). This is what stops the robot when the camera is unplugged.
- **Mapping.** The topic and the per-gesture velocities load from a per-robot YAML (`config/turtlesim.yaml`), so remapping needs no rebuild.

`TwistStamped` output (for some TurtleBot3 setups) and the hand `JointTrajectory` output come in phase 4, where they can be tested against the sims that need them.

### Running the stack

```bash
pixi shell
cd ros2_ws && colcon build && source install/setup.zsh
ros2 launch gesture_bringup bringup.launch.py transport:=serial port:=/dev/cu.usbmodemXXXX robot:=turtlesim
```

Rock stops the turtle, paper drives it forward, scissors rotates it, and unplugging the camera stops it within 2 s.

### macOS build note

On RoboStack (conda) macOS, a C++ node that uses a message package can abort at startup with `symbol not found in flat namespace '_PyExc_RuntimeError'`. The message package's CMake targets transitively pull in their `rosidl_generator_py` libraries, which load at startup but need libpython, which a standalone C++ binary doesn't link. `gesture_behavior/CMakeLists.txt` links only the `__rosidl_typesupport_cpp` targets and adds `-Wl,-dead_strip_dylibs`, which drops the unused Python libraries from the load commands. The real typesupport is loaded by the middleware at runtime, so this is safe, and it matches how the prebuilt RoboStack binaries are linked.

## Running the tests

Both test files are self-contained runners with no framework to install, and neither needs the ROS environment. From the repo root:

```bash
# Debouncer (C++)
mkdir -p build && g++ -std=c++17 -Wall -Wextra -Werror -Ifirmware/common tests/debouncer_test.cpp firmware/common/gesture_debouncer.cpp -o build/debouncer_test && build/debouncer_test

# Bridge line parser (Python)
python3 tests/bridge_parser_test.py
```

The 24 debouncer tests cover flicker, low scores, the score threshold, a single missed frame, gaps that break a streak, the 500 ms timeout, switching gestures, unknown classes, and `millis()` wraparound.

The bridge parser tests cover the wire-format contract: each gesture parsing, extra fields ignored, and dropping garbage, missing fields, bad types, and out-of-range gestures. That last case matters because this ROS build does not range-check `uint8`, so an out-of-range gesture would otherwise wrap (300 -> 44) at serialization. The parser (`gesture_bridge/parser.py`) is deliberately ROS-free so it can be tested this way; the full serial-read and publish path is checked with a pseudo-terminal harness that does need the ROS environment.

## Mac setup

The ROS 2 environment is pinned in `pixi.toml` and `pixi.lock`:

```bash
curl -fsSL https://pixi.sh/install.sh | sh
pixi install
pixi shell
```

Run all ROS 2 commands and `colcon build` inside `pixi shell`. Build ESP-IDF projects from a terminal outside it, so the ROS environment doesn't interfere.

## Failure handling

| Failure | Detected by | Result |
|---|---|---|
| Gesture flicker | Class changes between frames | The debouncer needs 5 matching frames |
| Hand leaves the frame | No usable box for 500 ms | The device reports `NONE` and the robot stops |
| Camera unplugged (v1) | Serial error in the bridge | The bridge retries every 2 s; the watchdog stops the robot |
| Wi-Fi or agent lost (v2) | Agent ping fails | The device waits for the agent; the watchdog stops the robot |
| Vision AI V2 stops sending | No inference result for 2 s | The device restarts inference |
| Corrupt serial data | JSON parse error | The line is dropped and counted |
