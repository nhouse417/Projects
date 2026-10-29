# Camera–LiDAR Fusion on KITTI

A C++ ROS 2 (Jazzy) pipeline that detects objects in the KITTI left color camera, uses the Velodyne LiDAR to estimate each object's 3D position, and evaluates the result against KITTI ground truth. Runs on macOS and Linux with RoboStack + pixi. RViz2 is the visualizer; there's no Gazebo.

**Status:** environment and KITTI → rosbag2 converter are done. Milestones A1–A5 are next (see [CLAUDE.md](CLAUDE.md)).

## Setup

```bash
pixi install          # ROS 2 Jazzy, OpenCV, Eigen, ONNX Runtime, rosbags
pixi run test-tools   # converter tests
```

## Data: KITTI tracking

Download from the [KITTI tracking benchmark](https://www.cvlibs.net/datasets/kitti/eval_tracking.php). You need a free account. Get these four archives:

| Archive | Size |
|---|---|
| left color images (`data_tracking_image_2.zip`) | ~15 GB |
| Velodyne point clouds (`data_tracking_velodyne.zip`) | ~35 GB |
| camera calibration (`data_tracking_calib.zip`) | tiny |
| training labels (`data_tracking_label_2.zip`) | tiny |

Only 3–5 training sequences are used. The archives are large, so extract only the sequences you need:

```bash
mkdir -p data/kitti_tracking && cd data/kitti_tracking
unzip ~/Downloads/data_tracking_calib.zip
unzip ~/Downloads/data_tracking_label_2.zip
for s in 0000 0001 0005 0011; do
  unzip ~/Downloads/data_tracking_image_2.zip "training/image_02/$s/*"
  unzip ~/Downloads/data_tracking_velodyne.zip "training/velodyne/$s/*"
done
```

Expected layout:

```
data/kitti_tracking/training/
├── image_02/0000/000000.png …
├── velodyne/0000/000000.bin …
├── calib/0000.txt
└── label_02/0000.txt
```

`data/` and `bags/` are gitignored.

## KITTI → rosbag2

```bash
pixi run kitti-to-bag 0000 0001 0005 0011   # writes bags/kitti_<seq>/ (MCAP)
pixi run kitti-to-bag 0000 --max-frames 50  # quick subset
```

Each frame k is stamped `1600000000 s + k·0.1 s`, and every topic in a frame has the same stamp.

| Topic | Type | frame_id |
|---|---|---|
| `/kitti/camera/image_raw` | `sensor_msgs/Image` (bgr8) | `camera_02` |
| `/kitti/camera/camera_info` | `sensor_msgs/CameraInfo` | `camera_02` |
| `/kitti/velodyne/points` | `sensor_msgs/PointCloud2` (x, y, z, intensity) | `velodyne` |
| `/kitti/gt/objects` | `vision_msgs/Detection3DArray` | `camera_rect` |
| `/tf_static` | `velodyne → camera_rect → camera_02` | |

`camera_rect` is KITTI's rectified camera-0 frame (`R0_rect · Tr_velo_cam`), where the labels live. `camera_02` adds P2's ~6 cm offset, so `camera_info.p` is `[K | 0]`. Projecting through TF to `camera_02` and then K gives the same pixel as KITTI's `P2 · R0_rect · Tr_velo_cam`. A unit test checks this.

### View it

```bash
pixi run rviz                       # terminal 1
pixi run play bags/kitti_0000       # terminal 2
```

RViz2 shows the camera image, the point cloud colored by intensity, the TF frames, and the GT boxes.

## Notes

- **Step 0 (converter):** tested on a synthetic sequence with real KITTI calibration. Tests cover parsing, timestamps, image/cloud round-trip, GT box placement, `/tf_static` latching, and agreement with the KITTI projection chain. `ros2 bag play` runs at 10 Hz, and `tf2_echo velodyne camera_02` shows the camera 0.27 m ahead of and 7 cm below the LiDAR.
