# Camera–LiDAR Fusion on KITTI (Project A) — Project Brief

Brief for Claude Code. Work through it milestone by milestone.

---

## Context

- **Goal:** a portfolio project for robotics **perception engineer** roles (with overlap into perception validation roles).
- **What employers look for:** C++, camera geometry (intrinsics/extrinsics/projection), sensor fusion, tf2, and measured results on real data.
- **My background:** former SDET (strong on Python, testing, CI); finished deeplearning.ai ML/DL courses; built a ROS 2 project (gesture-controlled robot sim, `../gesture_robot`) with RViz2. Strengthening C++.
- **Dataset:** KITTI **tracking** dataset. It has synchronized left color images, Velodyne LiDAR, calibration, and labels with 3D locations.

## Environment constraints (important)

- **macOS.** Gazebo doesn't run well. **No Gazebo anywhere in this project.**
- **ROS 2 Jazzy via RoboStack + pixi**, same distro as `../gesture_robot/pixi.toml`.
- **RViz2 works** and is the visualization tool.
- `pixi.toml` lists `osx-arm64` and `linux-64`, so the same lockfile runs in **GitHub Actions** (`prefix-dev/setup-pixi`). CI is the Linux machine.
- C++ deps come from conda-forge through pixi: OpenCV, Eigen, ONNX Runtime C++. Verify exact package names before adding.
- Data is large. Use **3–5 training sequences** only. Keep raw data and bags out of git (`.gitignore`); download steps are in the README.

### Resolved environment facts (verified 2026-10-28)

- `ros-jazzy-vision-msgs` 4.1.1 and `ros-jazzy-vision-msgs-rviz-plugins` exist on RoboStack for both platforms, so there's no custom message package.
- OpenCV is **4.13** (`opencv` pinned `<5`). `ros-jazzy-cv-bridge` needs 4.x, even though conda-forge has 5.0.
- Eigen is **5.0.1**. ONNX Runtime is `onnxruntime-cpp` 1.31.
- `pytest` is pinned `<9`. The `launch_testing` plugin that ships with ROS uses a hook argument that pytest 9 removed, so `pytest` won't start under 9.
- This project lives in the `nhouse417/Projects` monorepo under `computer_vision/camera_lidar_fusion/`. GitHub Actions workflows must sit at the **monorepo root** (`.github/workflows/`) with `working-directory: computer_vision/camera_lidar_fusion` and a `paths:` filter.

## Working style

- Work one milestone at a time. Confirm it runs before moving on.
- The core algorithms (projection math, robust depth, back-projection) are interview material. **Explain them and review my code rather than writing them silently.** Scaffolding, build files, launch files, and tooling can be generated directly.
- Every milestone ends with: builds cleanly, tests pass, RViz2 shows the expected result, and a short note goes in the README.
- One milestone per branch/PR into `main`.

---

## Repo layout

```
camera_lidar_fusion/
├── pixi.toml
├── README.md
├── CLAUDE.md                 # this file
├── tools/
│   └── kitti_to_bag.py       # KITTI tracking -> rosbag2 (uses `rosbags` lib)   [done]
├── tests/                    # pytest for tools/ and eval/
├── src/
│   ├── kitti_bringup/        # launch files, RViz2 config, static TF
│   ├── detector_cpp/         # 2D detection node (ONNX Runtime C++)
│   └── fusion_cpp/           # LiDAR->image projection, depth per box, 3D detections
├── eval/
│   └── eval_localization.py  # Project A metrics
├── models/                   # exported ONNX (gitignored)
└── data/, bags/              # KITTI download and converted bags (gitignored)
```

---

## Step 0: KITTI → rosbag2 (done)

`tools/kitti_to_bag.py` uses the pure-Python `rosbags` library (no ROS needed to write bags). Output is MCAP, one bag per sequence.

Per frame (10 Hz), with **identical timestamps** across topics (frame k → `start_time + k·0.1 s`):

| Topic | Type | Source | frame_id |
|---|---|---|---|
| `/kitti/camera/image_raw` | `sensor_msgs/Image` (bgr8) | `image_02` (left color) | `camera_02` |
| `/kitti/camera/camera_info` | `sensor_msgs/CameraInfo` | `P2` from calib | `camera_02` |
| `/kitti/velodyne/points` | `sensor_msgs/PointCloud2` | `velodyne/*.bin` (x, y, z, intensity) | `velodyne` |
| `/kitti/gt/objects` | `vision_msgs/Detection3DArray` | `label_02`, DontCare dropped | `camera_rect` |
| `/tf_static` | `tf2_msgs/TFMessage` (transient local) | `Tr_velo_cam`, `R_rect`, `P2` | |

**TF tree:** `velodyne → camera_rect → camera_02`
- `camera_rect` is the rectified camera-0 frame. KITTI labels live here: `X_rect = R0_rect · Tr_velo_cam · X_velo`.
- `camera_02` is the left color camera's optical frame. `P2 = K [I | t]`, so `X_cam2 = X_rect + t` with `t = K⁻¹ · P2[:,3]` (about 6 cm along x).
- **Convention:** `camera_info.p` is `[K | 0]`, not P2 verbatim, because the image's `frame_id` is already `camera_02`. Use either TF to `camera_02` and then K, or TF to `camera_rect` and then the full P2. Both give the same pixel. Doing TF to `camera_02` and then P2 counts the 6 cm twice. A test in `tests/test_kitti_to_bag.py` checks that both paths agree.
- GT box: KITTI `location` is the **bottom** center. The converter publishes the geometric center (`y − h/2`, since camera y points down), size `(l, h, w)`, and orientation = rotation of `rotation_y` about camera y. `id` = track id, `class_id` = KITTI type.
- Missing scans (some sequences, for example 0001, skip velodyne frames) are skipped with a warning, so exact-time sync just drops those frames.

**Done when:** `ros2 bag play` plus RViz2 shows the image, the point cloud in the correct frame, and GT boxes for one sequence. *(Verified on a synthetic fixture: unit tests, `ros2 bag info`, 10 Hz playback, `tf2_echo`, RViz2 loads cleanly. Still needs a visual check on real KITTI data.)*

---

## Project A — Camera–LiDAR fusion: 2D detections → 3D positions (C++)

### Goal
A C++ ROS 2 pipeline that detects objects in the camera image, uses LiDAR to estimate each object's 3D position, and publishes `vision_msgs/Detection3DArray`, shown in RViz2.

### Key math
Project a LiDAR point into the left color image:

```
x_img = P2 · R0_rect · Tr_velo_to_cam · X_velo     (homogeneous coords; divide by z)
```

Keep only points with positive depth in the camera frame and inside image bounds.

### Milestones

**A1 — Detector node (C++)**
- Export a pretrained YOLO to ONNX (Ultralytics, COCO classes). Map `car`→Car and `person`→Pedestrian. Skip Cyclist at first.
- C++ node: subscribe to the image, run ONNX Runtime, apply NMS, publish `Detection2DArray` and an annotated image.
- Log per-frame inference latency.
- **Done when:** RViz2 shows boxes on the image stream at a stable rate.

**A2 — Projection sanity check**
- Node subscribes to the cloud and camera_info, projects points into the image, and publishes an overlay colored by depth.
- **Done when:** points visually line up with cars and poles. This is the key debug step. Get it right before moving on.

**A3 — Depth per detection → 3D detections**
- Sync image detections and the cloud with `message_filters` (exact time works for KITTI).
- For each 2D box, take the projected points inside a **shrunk box** (about 80%) to avoid background bleed. Estimate depth robustly (median or lower percentile), and handle boxes with too few points.
- Back-project the box center at that depth into 3D. Publish `Detection3DArray`, plus `MarkerArray` for RViz2.
- **Done when:** 3D markers sit on top of the GT boxes in RViz2 for most cars.

**A4 — Evaluation (`eval/eval_localization.py`)**
- Match predictions to GT by 2D IoU ≥ 0.5 per frame.
- Report position error and range error **by distance bin** (0–10, 10–20, 20–40, 40+ m) and by KITTI occlusion level.
- Report the miss rate for boxes with too few LiDAR points.
- Report latency per node (mean / p95).
- **Known bias to document:** KITTI's GT location is the bottom-center of the 3D box, while LiDAR hits the object's near surface. Quantify the offset; don't hide it.

**A5 — Tests + CI**
- Unit tests (gtest) for the projection function, using a known point and a known calibration.
- Unit tests for robust depth on synthetic point sets, including the empty/few-points case.
- CI: `pixi run` build + test on ubuntu-latest.

### Definition of done
README with a results table, an RViz2 GIF, an architecture diagram, and a "limitations and next steps" section.

---

## Interview talking points to capture as you go

- Why the shrunk box and median depth beat the mean (outliers, background bleed).
- How the calibration chain works and what breaks if `R0_rect` is skipped.
- The `camera_rect` vs `camera_02` frame split and why `camera_info.p` is `[K | 0]` here.
- One real bug you found through the RViz2 overlay or the evaluation scripts.

## Resume bullet template (fill in real numbers)

- Built a C++ ROS 2 camera–LiDAR fusion pipeline on KITTI (ONNX Runtime, tf2, message_filters) that localizes detected objects in 3D with [X] m median range error within 20 m at [Y] ms per frame.
