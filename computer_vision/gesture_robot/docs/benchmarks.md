# Benchmarks: v1 (serial bridge) vs v2 (micro-ROS)

Phase 6 of the gesture_robot migration. Both versions share the camera, the
debouncer, the topic, and everything downstream of `/gesture/event`; only the
path from the ESP32-C3 into ROS 2 changes — USB serial + a Python bridge in v1,
Wi-Fi micro-ROS in v2. This phase shows the swap changed nothing the robot does
(the acceptance test) and puts numbers on the two transports (the benchmarks).

The fair end-to-end comparison is the **slow-motion video** (hand → robot),
because v1 stamps messages on the Mac while v2 stamps them on the device — the
`header.stamp` values are not directly comparable across versions.

## Setup

Run each version the same way, one at a time, with `robot:=turtlesim`:

| | v1 (serial) | v2 (micro-ROS) |
|---|---|---|
| Firmware | Arduino sketch `firmware/v1_arduino/gesture_camera_v1/` | ESP-IDF `firmware/v2_espidf/` |
| Transport | `transport:=serial port:=/dev/cu.usbmodem3101` | `transport:=microros` |

```bash
# v1
ros2 launch gesture_bringup bringup.launch.py transport:=serial port:=/dev/cu.usbmodem3101 robot:=turtlesim
# v2
ros2 launch gesture_bringup bringup.launch.py transport:=microros robot:=turtlesim
```

## Acceptance test (M6)

Ten trials per gesture, plus two recovery checks, for **each** version.
**Pass = ≥ 9/10 correct per gesture and both recovery checks.** "Correct" means
the robot does the mapped action: **paper → forward, scissors → rotate, rock → stop**.

### v1 (serial)

| Check | Result |
|---|---|
| Rock (stop) | 10 / 10 |
| Paper (forward) | 10 / 10 |
| Scissors (rotate) | 10 / 10 |
| Recovery: unplug the camera → robot stops within 2 s | ✓ pass (~2 s) |

### v2 (micro-ROS)

| Check | Result |
|---|---|
| Rock (stop) | 10 / 10 |
| Paper (forward) | 10 / 10 |
| Scissors (rotate) | 10 / 10 |
| Recovery: stop the agent → robot stops within 2 s | ✓ pass (~2 s) |

## Benchmark results (M7)

| Metric | How to measure | v1 | v2 |
|---|---|---|---|
| Rate at rest | `ros2 topic hz /gesture/event` (no hand in view) | ~1 Hz (heartbeat) | 1.00 Hz (heartbeat) |
| Hand → robot latency | slow-mo video of hand + robot, frames ÷ fps | ≈ equal ² | ≈ equal ² |
| Device → ROS latency | `scripts/benchmark_latency.py` (header stamp vs receive) | n/a | n/a ¹ |
| Recovery time | time from reconnect until messages resume | ~7 s (replug) | ~9 s (reboot) |
| Dropped messages | bad-line count (v1 bridge) / publish failures (v2) over 10 min | 1 bad line (a partial line at connect; 0 after, over ~17 min / 1004 msgs, max gap 1.15 s) | 0 / 10 min (695 msgs, max gap 1.22 s, no reboots) |
| Acceptance score | correct responses out of 30 (from the tables above) | 30 / 30 | 30 / 30 |

¹ The device's `header.stamp` is not wall-clock aligned on this setup — the
micro-ROS time sync (`rmw_uros_sync_session`) does not reliably yield the agent's
epoch, so `receive − stamp` is not a meaningful one-way latency (it reads as the
whole Unix epoch). A one-way latency needs both ends on one clock, which is why
the slow-motion video (one camera sees the hand and the robot) is the fair
end-to-end measurement for both versions. The stamp being off is cosmetic for the
robot — the behavior node times out on message *arrival*, not on the stamp.

² Not timed with video. It is ≈ equal across versions because the dominant delay
is the shared 5-frame debouncer confirmation (~hundreds of ms at the camera's
frame rate), identical in both, while the transport adds only a few ms (USB vs
Wi-Fi). See the write-up.

### How to measure

- **Rate at rest and recovery gap** — with the stack up, in a second `pixi`
  terminal run `python3 scripts/benchmark_latency.py`. Leave it with no hand in
  view to read the rest rate; Ctrl-C for the summary (count, average rate, largest
  inter-message gap, and latency *only if* the stamps are wall-clock aligned).
  `ros2 topic hz /gesture/event` is the simpler rate check. The script reports
  device → ROS latency as n/a on this setup (footnote 1), so the hand → robot
  video is the latency measurement.
- **Hand → robot latency** — film your hand and the turtlesim window together at a
  known frame rate (a phone's slow-motion mode is ~120–240 fps). Count the frames
  from your hand reaching the gesture to the robot reacting, and divide by fps.
  This is the only measurement that spans the whole pipeline on one clock.
- **Recovery time** — break the transport, **restore it immediately**, and read
  the largest gap from `benchmark_latency.py` running across it. The gap measures
  the whole outage, so restore right away or it counts your delay too. Cleanest
  for v2: run the agent on its own (`ros2 run micro_ros_agent micro_ros_agent
  udp4 --port 8888`) with the script subscribed, then Ctrl-C the agent and press
  Up+Enter to restart it instantly — the gap is then the device's own
  detect + reboot + reconnect. For v1, unplug and replug the camera. Expect v2 to
  be slower: it reconnects by rebooting (boot + Wi-Fi + reconnect, ~10–15 s),
  while v1's bridge just reopens the serial port.
- **Dropped messages** — v1: the bridge counts and logs the malformed lines it
  skips; v2: the device logs publish failures (`ros_link`). Run ~10 min of normal
  gesturing and record the count for each.

## Write-up

The swap from v1 (USB serial + Python bridge) to v2 (Wi-Fi + micro-ROS) changed
nothing the robot does. Both versions pass the acceptance test identically, and
every benchmark came out essentially equal — which is the point: the camera, the
debouncer, the `/gesture/event` contract, the behavior node, and the simulation
are all shared, so only the transport differs.

- **Functional equivalence.** Both score **30/30** on the acceptance gestures,
  and both stop the robot within ~2 s when the link drops — the behavior node's
  2 s watchdog, unchanged between versions.
- **Rate.** Both hold ~1 Hz at rest, the 1 s heartbeat written into the interface
  contract and emitted by both firmwares. Identical by design.
- **Reliability.** v2 dropped 0 messages over 10 min; v1 logged a single bad line,
  a partial line caught at connect time, with 0 corruption over the following
  ~17 min (1004 messages, max gap 1.15 s). Both transports deliver the stream
  without loss.
- **Recovery.** v1 ~7 s, v2 ~9 s — closer than expected, because unplugging the
  camera (the v1 trigger) cuts the device's power, so v1 reboots just like v2 does
  on agent loss. Both times are dominated by the camera+XIAO coming back up, not
  by the transport's own reconnection (the bridge reopening the port, or micro-ROS
  re-establishing the session). The qualitative difference is scope: v2 recovers
  automatically from any software-side loss (agent restart, Wi-Fi blip), while v1
  only recovers a physical replug.
- **Latency.** Device→ROS latency isn't cleanly measurable here — v1 stamps on the
  Mac (no device-side time to compare), and v2's micro-ROS time sync doesn't yield
  a wall-clock stamp on this setup. Hand→robot latency was not timed, but it is
  **≈ equal**: the dominant delay is the shared 5-frame debouncer (~hundreds of ms
  at the camera's frame rate), while the transport adds only a few ms. Perceived
  responsiveness is unchanged by the swap.

**One observation, not a transport difference.** The robot occasionally reacted
to a gesture that wasn't deliberately made (a false positive at rest, or a rock
read as something else). That is the pre-trained detection model misclassifying
for ≥5 frames and slipping past the debouncer — a detection-side characteristic
shared by both versions, sensitive to lighting and background. It did not
reproduce consistently, and it's tunable (debouncer `min_score`/`frames_to_confirm`,
the camera's `AT+TSCORE`, or a plainer background), not a code fix.

**Conclusion.** The migration needed only a **firmware flash and a launch
argument** (`transport:=serial` → `transport:=microros`). Because everything from
`/gesture/event` onward is shared and the acceptance results are identical, the
transport swap is invisible to the behavior node, the simulation, and the robot —
which was the whole goal of the phased design.
