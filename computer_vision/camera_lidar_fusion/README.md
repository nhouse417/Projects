# Camera–LiDAR Fusion on KITTI

A C++ ROS 2 (Jazzy) pipeline that detects objects in the KITTI left color camera, uses the Velodyne LiDAR to estimate each object's 3D position, and evaluates the result against KITTI ground truth. Runs on macOS and Linux with RoboStack + pixi. RViz2 is the visualizer; there's no Gazebo.

**Status:** environment and KITTI → rosbag2 converter are done and verified on real KITTI data. Next: 2D detector (ONNX Runtime), LiDAR→image projection check, depth per detection → 3D positions, evaluation, and tests + CI.

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

Only training sequences have labels, and five of them are used. They were picked to cover both evaluated classes (counts are labeled objects summed over frames):

| Sequence | Frames | Car | Pedestrian | Notes |
|---|---|---|---|---|
| 0000 | 154 | 243 | 22 | short urban street, cyclist ahead |
| 0001 | 447 | 2,681 | 112 | no LiDAR scan for frames 177–180 |
| 0005 | 297 | 1,275 | 0 | |
| 0011 | 373 | 3,405 | 201 | |
| 0016 | 209 | 836 | 2,027 | pedestrian-heavy |
| **Total** | **1,480** | **8,440** | **2,362** | |

To compare other sequences, count the classes in their label files:

```bash
awk '{print $3}' data/kitti_tracking/training/label_02/0016.txt | sort | uniq -c
```

The archives are large, so extract only the sequences you need:

```bash
mkdir -p data/kitti_tracking && cd data/kitti_tracking
unzip ~/Downloads/data_tracking_calib.zip
unzip ~/Downloads/data_tracking_label_2.zip
for s in 0000 0001 0005 0011 0016; do
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

### Keeping the data on an external drive

The velodyne zip alone is ~35 GB, so the zips, extracted sequences and bags can all live on a USB drive.

- **Format:** exFAT or APFS. FAT32 can't hold files over 4 GB. On exFAT, macOS writes hidden `._*` files next to real ones; the converter ignores them.
- **Slow downloads:** KITTI's server limits each connection, so a browser download can take many hours. A multi-connection download is worth trying:
  ```bash
  pixi exec -s aria2 aria2c -x 16 -s 16 --file-allocation=none "<download link>"
  ```
- **Check a zip is complete** before extracting (it reads only the index at the end of the file):
  ```bash
  unzip -l "/Volumes/<drive>/data_tracking_velodyne.zip" | tail -1
  ```
- **Point the tools at the drive.** Run `pixi` from this folder, and quote paths that contain spaces:
  ```bash
  pixi run kitti-to-bag 0000 0001 0005 0011 0016 --kitti-root "/Volumes/<drive>/kitti_tracking" --out-dir "/Volumes/<drive>/bags"
  pixi run play "/Volumes/<drive>/bags/kitti_0000"
  ```

## KITTI → rosbag2

```bash
pixi run kitti-to-bag 0000 0001 0005 0011 0016   # writes bags/kitti_<seq>/ (MCAP)
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
- **Step 0 on real data:** all five sequences (1,480 frames) convert with every topic's count matching the image count, except that sequence 0001 has no scan for frames 177–180 (443 clouds for 447 images). In RViz2, sequence 0000 shows the image, the cloud in the `velodyne` frame, and GT boxes sitting on the parked cars and the cyclist ahead. A numeric check on three sequences:

  | Check | 0000 Car | 0011 Car | 0016 Car | 0016 Pedestrian |
  |---|---|---|---|---|
  | GT boxes containing LiDAR points | 242 / 243 | 3,255 / 3,405 | 836 / 836 | 2,027 / 2,027 |
  | In-box points with `rotation_y` sign flipped | 71% of correct | 55% of correct | n/a | n/a |
  | In-box points that land in the image and inside the labeled 2D box (±3 px) | 100% | 100% | 100% | ~95% |

  - **Cars:** in-box points that miss the 2D box all project outside the image. They belong to cars cut off at the image edge, whose labeled 2D box stops at the border. A3 will only see the in-image part of those cars.
  - **Orientation:** the sign-flip check only works on 0000 and 0011. Every car in 0016 is parked at about ±90°, where a flipped sign gives the same box, and pedestrian boxes are nearly square (1.02 × 0.79 m on average).
  - **Pedestrians:** about 5% of in-image points land outside the labeled 2D box, by a median of 10 px (90th percentile 26 px). KITTI gives each pedestrian track one fixed-size 3D box and labels the left/right image boundaries separately, so the 3D box is looser than the 2D one. That makes background bleed a bigger risk for pedestrians in A3.
  - **Near-surface bias:** inside each box, LiDAR returns cluster on the side facing the sensor. A4 measures this offset against KITTI's box positions.
