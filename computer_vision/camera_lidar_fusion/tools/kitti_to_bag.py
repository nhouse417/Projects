#!/usr/bin/env python3
"""Convert KITTI tracking sequences to rosbag2 (MCAP).

Writes one bag per sequence with the pure-Python `rosbags` library, so no
ROS install is needed to write. Every topic in a frame shares one timestamp:
frame k is stamped start_time + k * 0.1 s (KITTI tracking is 10 Hz and ships
no per-frame timestamps).

Topics
  /kitti/camera/image_raw     sensor_msgs/Image             image_02, bgr8
  /kitti/camera/camera_info   sensor_msgs/CameraInfo        from P2
  /kitti/velodyne/points      sensor_msgs/PointCloud2       x, y, z, intensity
  /kitti/gt/objects           vision_msgs/Detection3DArray  label_02, no DontCare
  /tf_static                  tf2_msgs/TFMessage            calib, transient local

TF tree (all static)
  velodyne -> camera_rect -> camera_02

  camera_rect  rectified camera-0 frame. KITTI labels live here, and
               X_rect = R0_rect * Tr_velo_cam * X_velo.
  camera_02    optical frame of the left color camera. P2 = K [I | t], so
               X_cam2 = X_rect + t with t = K^-1 * P2[:, 3] (about 6 cm).

The image and camera_info use frame camera_02, so camera_info.p is [K | 0],
not P2 verbatim. Projecting a velodyne point is then: TF to camera_02, then
K. That equals P2 * R0_rect * Tr_velo_cam * X_velo. Applying P2 after a TF
to camera_02 would count the 6 cm offset twice.

Expected layout under --kitti-root (as unzipped from the KITTI site):
  <split>/image_02/<seq>/<frame>.png
  <split>/velodyne/<seq>/<frame>.bin
  <split>/calib/<seq>.txt
  <split>/label_02/<seq>.txt          (training split only)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from rosbags.interfaces import (
    Qos,
    QosDurability,
    QosHistory,
    QosLiveliness,
    QosReliability,
    QosTime,
)
from rosbags.rosbag2 import StoragePlugin, Writer
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

FRAME_PERIOD_NS = 100_000_000  # 10 Hz
DEFAULT_START_TIME_S = 1_600_000_000  # arbitrary, nonzero (t=0 means "latest" in tf2)

VELO_FRAME = "velodyne"
RECT_FRAME = "camera_rect"
CAM_FRAME = "camera_02"

TOPIC_IMAGE = "/kitti/camera/image_raw"
TOPIC_INFO = "/kitti/camera/camera_info"
TOPIC_POINTS = "/kitti/velodyne/points"
TOPIC_GT = "/kitti/gt/objects"
TOPIC_TF_STATIC = "/tf_static"

_ZERO = QosTime(0, 0)
QOS_DEFAULT = Qos(
    QosHistory.KEEP_LAST, 10, QosReliability.RELIABLE, QosDurability.VOLATILE,
    _ZERO, _ZERO, QosLiveliness.AUTOMATIC, _ZERO, False,
)
# Matches tf2_ros::StaticTransformBroadcaster, so `ros2 bag play` latches it.
QOS_TF_STATIC = Qos(
    QosHistory.KEEP_LAST, 1, QosReliability.RELIABLE, QosDurability.TRANSIENT_LOCAL,
    _ZERO, _ZERO, QosLiveliness.AUTOMATIC, _ZERO, False,
)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

@dataclass
class Calib:
    P2: np.ndarray           # 3x4, projects camera_rect points into image_02
    R0_rect: np.ndarray      # 3x3
    Tr_velo_cam: np.ndarray  # 3x4, velodyne -> unrectified camera 0


def parse_calib(path: Path) -> Calib:
    """Parse a KITTI tracking calib file.

    Tracking files spell keys `P2:`, `R_rect` and `Tr_velo_cam` (no colon on
    the last two); the object/raw files use `R0_rect:` and `Tr_velo_to_cam:`.
    Accept both.
    """
    values: dict[str, np.ndarray] = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        values[parts[0].rstrip(":")] = np.array([float(v) for v in parts[1:]])

    def pick(*keys: str) -> np.ndarray:
        for k in keys:
            if k in values:
                return values[k]
        raise KeyError(f"{path}: none of {keys} found")

    return Calib(
        P2=pick("P2").reshape(3, 4),
        R0_rect=pick("R_rect", "R0_rect").reshape(3, 3),
        Tr_velo_cam=pick("Tr_velo_cam", "Tr_velo_to_cam").reshape(3, 4),
    )


@dataclass
class Label:
    frame: int
    track_id: int
    type: str
    truncated: float
    occluded: int
    alpha: float
    bbox: tuple[float, float, float, float]  # left, top, right, bottom (px)
    h: float
    w: float
    l: float
    location: tuple[float, float, float]     # bottom center, camera_rect (m)
    rotation_y: float


def parse_labels(path: Path) -> dict[int, list[Label]]:
    """Parse a label_02 file into {frame: [Label]}, dropping DontCare."""
    by_frame: dict[int, list[Label]] = {}
    for line in path.read_text().splitlines():
        f = line.split()
        if len(f) < 17 or f[2] == "DontCare":
            continue
        lab = Label(
            frame=int(f[0]), track_id=int(f[1]), type=f[2],
            truncated=float(f[3]), occluded=int(f[4]), alpha=float(f[5]),
            bbox=(float(f[6]), float(f[7]), float(f[8]), float(f[9])),
            h=float(f[10]), w=float(f[11]), l=float(f[12]),
            location=(float(f[13]), float(f[14]), float(f[15])),
            rotation_y=float(f[16]),
        )
        by_frame.setdefault(lab.frame, []).append(lab)
    return by_frame


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

def to_homogeneous(m: np.ndarray) -> np.ndarray:
    """Pad a 3x3 or 3x4 matrix to 4x4."""
    out = np.eye(4)
    out[: m.shape[0], : m.shape[1]] = m
    return out


def T_rect_velo(calib: Calib) -> np.ndarray:
    """4x4 mapping velodyne points into camera_rect: R0_rect * Tr_velo_cam."""
    return to_homogeneous(calib.R0_rect) @ to_homogeneous(calib.Tr_velo_cam)


def cam2_offset(calib: Calib) -> np.ndarray:
    """t with P2 = K [I | t], i.e. X_cam2 = X_rect + t."""
    K = calib.P2[:, :3]
    return np.linalg.solve(K, calib.P2[:, 3])


def nearest_rotation(R: np.ndarray) -> np.ndarray:
    """Project onto SO(3). KITTI's calibrated rotations are not exactly
    orthonormal, and a quaternion can only hold a true rotation."""
    U, _, Vt = np.linalg.svd(R)
    out = U @ Vt
    if np.linalg.det(out) < 0:
        U[:, -1] *= -1
        out = U @ Vt
    return out


def quat_from_matrix(R: np.ndarray) -> tuple[float, float, float, float]:
    """Rotation matrix -> (x, y, z, w), Shepperd's method."""
    tr = np.trace(R)
    if tr > 0:
        s = 2.0 * np.sqrt(tr + 1.0)
        w, x = 0.25 * s, (R[2, 1] - R[1, 2]) / s
        y, z = (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        w, x = (R[2, 1] - R[1, 2]) / s, 0.25 * s
        y, z = (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        w, x = (R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s
        y, z = 0.25 * s, (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        w, x = (R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s
        y, z = (R[1, 2] + R[2, 1]) / s, 0.25 * s
    q = np.array([x, y, z, w])
    q /= np.linalg.norm(q)
    return tuple(float(v) for v in q)


def label_box_center(lab: Label) -> np.ndarray:
    """KITTI location is the box's bottom center; camera y points down, so
    the geometric center is h/2 above it."""
    x, y, z = lab.location
    return np.array([x, y - lab.h / 2.0, z])


# --------------------------------------------------------------------------
# Message builders
# --------------------------------------------------------------------------

class Builder:
    """Builds rosbags message objects from a typestore."""

    def __init__(self, typestore):
        self.ts = typestore
        self.t = typestore.types

    def header(self, stamp_ns: int, frame_id: str):
        sec, nsec = divmod(stamp_ns, 1_000_000_000)
        return self.t["std_msgs/msg/Header"](
            stamp=self.t["builtin_interfaces/msg/Time"](sec=sec, nanosec=nsec),
            frame_id=frame_id,
        )

    def vec3(self, v):
        return self.t["geometry_msgs/msg/Vector3"](x=float(v[0]), y=float(v[1]), z=float(v[2]))

    def quat(self, q):
        x, y, z, w = q
        return self.t["geometry_msgs/msg/Quaternion"](x=x, y=y, z=z, w=w)

    def transform(self, stamp_ns: int, parent: str, child: str, T_parent_child: np.ndarray):
        """TransformStamped holds the child's pose in the parent frame, i.e.
        the matrix that maps child-frame points into the parent frame."""
        return self.t["geometry_msgs/msg/TransformStamped"](
            header=self.header(stamp_ns, parent),
            child_frame_id=child,
            transform=self.t["geometry_msgs/msg/Transform"](
                translation=self.vec3(T_parent_child[:3, 3]),
                rotation=self.quat(quat_from_matrix(nearest_rotation(T_parent_child[:3, :3]))),
            ),
        )

    def tf_static(self, stamp_ns: int, calib: Calib):
        # velodyne -> camera_rect: invert the velo->rect point mapping.
        T_velo_rect = np.linalg.inv(T_rect_velo(calib))
        # camera_rect -> camera_02: camera_02's origin sits at -t in camera_rect.
        T_rect_cam2 = np.eye(4)
        T_rect_cam2[:3, 3] = -cam2_offset(calib)
        return self.t["tf2_msgs/msg/TFMessage"](transforms=[
            self.transform(stamp_ns, VELO_FRAME, RECT_FRAME, T_velo_rect),
            self.transform(stamp_ns, RECT_FRAME, CAM_FRAME, T_rect_cam2),
        ])

    def image(self, stamp_ns: int, bgr: np.ndarray):
        h, w = bgr.shape[:2]
        return self.t["sensor_msgs/msg/Image"](
            header=self.header(stamp_ns, CAM_FRAME),
            height=h, width=w, encoding="bgr8", is_bigendian=0, step=w * 3,
            data=np.ascontiguousarray(bgr).reshape(-1),
        )

    def camera_info(self, stamp_ns: int, calib: Calib, width: int, height: int):
        K = calib.P2[:, :3]
        P = np.hstack([K, np.zeros((3, 1))])
        return self.t["sensor_msgs/msg/CameraInfo"](
            header=self.header(stamp_ns, CAM_FRAME),
            height=height, width=width,
            distortion_model="plumb_bob",
            d=np.zeros(5),               # images are already rectified
            k=K.reshape(-1).astype(np.float64),
            r=np.eye(3).reshape(-1),
            p=P.reshape(-1).astype(np.float64),
            binning_x=0, binning_y=0,
            roi=self.t["sensor_msgs/msg/RegionOfInterest"](
                x_offset=0, y_offset=0, height=0, width=0, do_rectify=False),
        )

    def point_cloud(self, stamp_ns: int, scan: np.ndarray):
        """scan: (N, 4) float32 x, y, z, intensity — the .bin layout as-is."""
        PF = self.t["sensor_msgs/msg/PointField"]
        fields = [PF(name=n, offset=4 * i, datatype=PF.FLOAT32, count=1)
                  for i, n in enumerate(("x", "y", "z", "intensity"))]
        n = scan.shape[0]
        return self.t["sensor_msgs/msg/PointCloud2"](
            header=self.header(stamp_ns, VELO_FRAME),
            height=1, width=n, fields=fields, is_bigendian=False,
            point_step=16, row_step=16 * n,
            data=np.ascontiguousarray(scan, dtype="<f4").view(np.uint8).reshape(-1),
            is_dense=True,
        )

    def detections(self, stamp_ns: int, labels: list[Label]):
        t = self.t
        header = self.header(stamp_ns, RECT_FRAME)
        dets = []
        for lab in labels:
            # Rotation about camera y. In the object frame the box extends
            # l along x, h along y, w along z (KITTI devkit convention).
            half = lab.rotation_y / 2.0
            cx, cy, cz = label_box_center(lab)
            pose = t["geometry_msgs/msg/Pose"](
                position=t["geometry_msgs/msg/Point"](x=float(cx), y=float(cy), z=float(cz)),
                orientation=self.quat((0.0, float(np.sin(half)), 0.0, float(np.cos(half)))),
            )
            hyp = t["vision_msgs/msg/ObjectHypothesisWithPose"](
                hypothesis=t["vision_msgs/msg/ObjectHypothesis"](class_id=lab.type, score=1.0),
                pose=t["geometry_msgs/msg/PoseWithCovariance"](pose=pose, covariance=np.zeros(36)),
            )
            dets.append(t["vision_msgs/msg/Detection3D"](
                header=header,
                results=[hyp],
                bbox=t["vision_msgs/msg/BoundingBox3D"](
                    center=pose, size=self.vec3((lab.l, lab.h, lab.w))),
                id=str(lab.track_id),
            ))
        return t["vision_msgs/msg/Detection3DArray"](header=header, detections=dets)


# --------------------------------------------------------------------------
# Conversion
# --------------------------------------------------------------------------

def find_vision_msgs_dir() -> Path:
    """vision_msgs isn't in rosbags' built-in typestore; load the .msg files
    that the pixi env installs, so the bag's schema matches what ROS sees."""
    for env in ("CONDA_PREFIX", "AMENT_PREFIX_PATH"):
        for prefix in os.environ.get(env, "").split(os.pathsep):
            d = Path(prefix) / "share" / "vision_msgs" / "msg"
            if d.is_dir():
                return d
    raise FileNotFoundError("vision_msgs .msg files not found; run inside `pixi run`/`pixi shell`")


def make_typestore():
    ts = get_typestore(Stores.ROS2_JAZZY)
    msg_dir = find_vision_msgs_dir()
    types = {}
    for f in sorted(msg_dir.glob("*.msg")):
        types.update(get_types_from_msg(f.read_text(), f"vision_msgs/msg/{f.stem}"))
    ts.register(types)
    return ts


def frame_ids(split_dir: Path, seq: str) -> list[int]:
    return sorted(int(p.stem) for p in (split_dir / "image_02" / seq).glob("*.png"))


def convert_sequence(kitti_root: Path, split: str, seq: str, out_path: Path,
                     max_frames: int | None = None,
                     start_time_s: int = DEFAULT_START_TIME_S) -> dict[str, int]:
    """Write one sequence to `out_path`. Returns message counts per topic."""
    split_dir = kitti_root / split
    calib = parse_calib(split_dir / "calib" / f"{seq}.txt")
    label_file = split_dir / "label_02" / f"{seq}.txt"
    labels = parse_labels(label_file) if label_file.exists() else None
    frames = frame_ids(split_dir, seq)
    if not frames:
        raise FileNotFoundError(f"no images in {split_dir / 'image_02' / seq}")
    if max_frames is not None:
        frames = frames[:max_frames]

    ts = make_typestore()
    b = Builder(ts)
    t0 = start_time_s * 1_000_000_000
    counts = {TOPIC_IMAGE: 0, TOPIC_INFO: 0, TOPIC_POINTS: 0, TOPIC_GT: 0, TOPIC_TF_STATIC: 0}
    missing_scans: list[int] = []

    with Writer(out_path, version=9, storage_plugin=StoragePlugin.MCAP) as w:
        def conn(topic, msgtype, qos=QOS_DEFAULT):
            return w.add_connection(topic, msgtype, typestore=ts, offered_qos_profiles=[qos])

        c_tf = conn(TOPIC_TF_STATIC, "tf2_msgs/msg/TFMessage", QOS_TF_STATIC)
        c_img = conn(TOPIC_IMAGE, "sensor_msgs/msg/Image")
        c_info = conn(TOPIC_INFO, "sensor_msgs/msg/CameraInfo")
        c_pts = conn(TOPIC_POINTS, "sensor_msgs/msg/PointCloud2")
        c_gt = conn(TOPIC_GT, "vision_msgs/msg/Detection3DArray") if labels is not None else None

        def write(c, stamp, msg, topic):
            w.write(c, stamp, ts.serialize_cdr(msg, c.msgtype))
            counts[topic] += 1

        write(c_tf, t0, b.tf_static(t0, calib), TOPIC_TF_STATIC)

        for k in frames:
            stamp = t0 + k * FRAME_PERIOD_NS
            img_path = split_dir / "image_02" / seq / f"{k:06d}.png"
            bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
            if bgr is None:
                raise OSError(f"could not read {img_path}")
            write(c_img, stamp, b.image(stamp, bgr), TOPIC_IMAGE)
            write(c_info, stamp, b.camera_info(stamp, calib, bgr.shape[1], bgr.shape[0]), TOPIC_INFO)

            # Some tracking sequences (e.g. 0001) have frames with no scan.
            bin_path = split_dir / "velodyne" / seq / f"{k:06d}.bin"
            if bin_path.exists():
                scan = np.fromfile(bin_path, dtype="<f4").reshape(-1, 4)
                write(c_pts, stamp, b.point_cloud(stamp, scan), TOPIC_POINTS)
            else:
                missing_scans.append(k)

            if c_gt is not None:
                write(c_gt, stamp, b.detections(stamp, labels.get(k, [])), TOPIC_GT)

    if missing_scans:
        print(f"[{seq}] warning: no velodyne scan for frames {missing_scans}", file=sys.stderr)
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sequences", nargs="+", help="sequence ids, e.g. 0000 0001")
    ap.add_argument("--kitti-root", type=Path, default=Path("data/kitti_tracking"))
    ap.add_argument("--split", default="training", choices=["training", "testing"])
    ap.add_argument("--out-dir", type=Path, default=Path("bags"))
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start-time", type=int, default=DEFAULT_START_TIME_S,
                    help="stamp of frame 0, in seconds since epoch")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for seq in args.sequences:
        seq = f"{int(seq):04d}"
        out = args.out_dir / f"kitti_{seq}"
        if out.exists():
            if not args.overwrite:
                print(f"{out} exists; pass --overwrite to replace it", file=sys.stderr)
                return 1
            shutil.rmtree(out)
        counts = convert_sequence(args.kitti_root, args.split, seq, out,
                                  args.max_frames, args.start_time)
        print(f"[{seq}] wrote {out}: " + ", ".join(f"{t}={n}" for t, n in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
