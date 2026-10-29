"""Tests for tools/kitti_to_bag.py on a tiny synthetic KITTI sequence."""

import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from rosbags.interfaces import QosDurability
from rosbags.rosbag2 import Reader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kitti_to_bag as k2b  # noqa: E402

# Calibration in KITTI tracking format (values from a 2011_09_26 drive).
CALIB = """\
P0: 7.215377e+02 0.000000e+00 6.095593e+02 0.000000e+00 0.000000e+00 7.215377e+02 1.728540e+02 0.000000e+00 0.000000e+00 0.000000e+00 1.000000e+00 0.000000e+00
P1: 7.215377e+02 0.000000e+00 6.095593e+02 -3.875744e+02 0.000000e+00 7.215377e+02 1.728540e+02 0.000000e+00 0.000000e+00 0.000000e+00 1.000000e+00 0.000000e+00
P2: 7.215377e+02 0.000000e+00 6.095593e+02 4.485728e+01 0.000000e+00 7.215377e+02 1.728540e+02 2.163791e-01 0.000000e+00 0.000000e+00 1.000000e+00 2.745884e-03
P3: 7.215377e+02 0.000000e+00 6.095593e+02 -3.395242e+02 0.000000e+00 7.215377e+02 1.728540e+02 2.199936e+00 0.000000e+00 0.000000e+00 1.000000e+00 2.729905e-03
R_rect 9.999239e-01 9.837760e-03 -7.445048e-03 -9.869795e-03 9.999421e-01 -4.278459e-03 7.402527e-03 4.351614e-03 9.999631e-01
Tr_velo_cam 7.533745e-03 -9.999714e-01 -6.166020e-04 -4.069766e-03 1.480249e-02 7.280733e-04 -9.998902e-01 -7.631618e-02 9.998621e-01 7.523790e-03 1.480755e-02 -2.717806e-01
Tr_imu_velo 9.999976e-01 7.553071e-04 -2.035826e-03 -8.086759e-01 -7.854027e-04 9.998898e-01 -1.482298e-02 3.195559e-01 2.024406e-03 1.482454e-02 9.998881e-01 -7.997231e-01
"""

LABELS = """\
0 0 Car 0 0 -1.79 296.7 161.7 455.2 292.0 2.00 1.82 4.43 -4.55 1.80 13.75 -2.11
0 1 Pedestrian 0 1 0.10 700.0 150.0 740.0 260.0 1.75 0.60 0.80 2.00 1.70 15.00 0.25
0 -1 DontCare -1 -1 -10 100.0 150.0 200.0 200.0 -1 -1 -1 -1000 -1000 -1000 -10
2 0 Car 0 0 -1.80 300.0 160.0 460.0 290.0 2.00 1.82 4.43 -4.50 1.80 13.50 -2.10
"""

SEQ = "0003"
N_FRAMES = 3
MISSING_SCAN = 1
IMG_W, IMG_H = 64, 32


@pytest.fixture
def kitti_root(tmp_path):
    split = tmp_path / "kitti" / "training"
    for d in ("image_02", "velodyne"):
        (split / d / SEQ).mkdir(parents=True)
    (split / "calib").mkdir()
    (split / "label_02").mkdir()
    (split / "calib" / f"{SEQ}.txt").write_text(CALIB)
    (split / "label_02" / f"{SEQ}.txt").write_text(LABELS)

    rng = np.random.default_rng(0)
    for k in range(N_FRAMES):
        img = rng.integers(0, 256, (IMG_H, IMG_W, 3), dtype=np.uint8)
        cv2.imwrite(str(split / "image_02" / SEQ / f"{k:06d}.png"), img)
        if k != MISSING_SCAN:
            scan = rng.normal(0, 10, (100 + k, 4)).astype("<f4")
            scan.tofile(split / "velodyne" / SEQ / f"{k:06d}.bin")
    return tmp_path / "kitti"


@pytest.fixture
def bag(kitti_root, tmp_path):
    out = tmp_path / "bag"
    k2b.convert_sequence(kitti_root, "training", SEQ, out)
    return out


def read_all(bag_path):
    ts = k2b.make_typestore()
    msgs = {}
    with Reader(bag_path) as r:
        conns = {c.topic: c for c in r.connections}
        for c, t, raw in r.messages():
            msgs.setdefault(c.topic, []).append((t, ts.deserialize_cdr(raw, c.msgtype)))
    return conns, msgs


def tf_matrix(tf) -> np.ndarray:
    q = tf.transform.rotation
    x, y, z, w = q.x, q.y, q.z, q.w
    R = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    T = np.eye(4)
    T[:3, :3] = R
    v = tf.transform.translation
    T[:3, 3] = (v.x, v.y, v.z)
    return T


# --------------------------------------------------------------------------
# Parsing and geometry
# --------------------------------------------------------------------------

def test_parse_calib_tracking_keys(kitti_root):
    c = k2b.parse_calib(kitti_root / "training" / "calib" / f"{SEQ}.txt")
    assert c.P2.shape == (3, 4) and c.P2[0, 3] == pytest.approx(44.85728)
    assert c.R0_rect.shape == (3, 3) and c.R0_rect[0, 0] == pytest.approx(0.9999239)
    assert c.Tr_velo_cam.shape == (3, 4) and c.Tr_velo_cam[2, 3] == pytest.approx(-0.2717806)


def test_parse_calib_object_keys(tmp_path):
    f = tmp_path / "c.txt"
    f.write_text(CALIB.replace("R_rect", "R0_rect:").replace("Tr_velo_cam", "Tr_velo_to_cam:"))
    c = k2b.parse_calib(f)
    assert c.R0_rect[0, 0] == pytest.approx(0.9999239)


def test_parse_labels_drops_dontcare(kitti_root):
    labels = k2b.parse_labels(kitti_root / "training" / "label_02" / f"{SEQ}.txt")
    assert sorted(labels) == [0, 2]
    assert [l.type for l in labels[0]] == ["Car", "Pedestrian"]
    assert labels[0][0].location == (-4.55, 1.80, 13.75)


def test_quat_roundtrip():
    rng = np.random.default_rng(1)
    for _ in range(50):
        R = k2b.nearest_rotation(rng.normal(size=(3, 3)))
        tf = type("TF", (), {})()
        x, y, z, w = k2b.quat_from_matrix(R)
        q = type("Q", (), dict(x=x, y=y, z=z, w=w))
        v = type("V", (), dict(x=0.0, y=0.0, z=0.0))
        tf.transform = type("T", (), dict(rotation=q, translation=v))
        np.testing.assert_allclose(tf_matrix(tf)[:3, :3], R, atol=1e-12)


# --------------------------------------------------------------------------
# End-to-end bag contents
# --------------------------------------------------------------------------

def test_counts_and_missing_scan(bag):
    _, msgs = read_all(bag)
    assert len(msgs[k2b.TOPIC_IMAGE]) == N_FRAMES
    assert len(msgs[k2b.TOPIC_INFO]) == N_FRAMES
    assert len(msgs[k2b.TOPIC_GT]) == N_FRAMES
    assert len(msgs[k2b.TOPIC_POINTS]) == N_FRAMES - 1
    assert len(msgs[k2b.TOPIC_TF_STATIC]) == 1


def test_ignores_macos_metadata_files(kitti_root, tmp_path):
    """macOS writes ._<name> AppleDouble files next to real ones on exFAT."""
    split = kitti_root / "training"
    junk = b"\x00\x05\x16\x07\x00\x02\x00\x00Mac OS X        "
    for p in (split / "image_02" / SEQ / "._000000.png",
              split / "velodyne" / SEQ / "._000000.bin",
              split / "calib" / f"._{SEQ}.txt",
              split / "label_02" / f"._{SEQ}.txt"):
        p.write_bytes(junk)

    assert k2b.frame_ids(split, SEQ) == list(range(N_FRAMES))
    counts = k2b.convert_sequence(kitti_root, "training", SEQ, tmp_path / "bag")
    assert counts[k2b.TOPIC_IMAGE] == N_FRAMES
    assert counts[k2b.TOPIC_POINTS] == N_FRAMES - 1


def test_timestamps_identical_across_topics(bag):
    _, msgs = read_all(bag)
    t0 = k2b.DEFAULT_START_TIME_S * 1_000_000_000
    for topic in (k2b.TOPIC_IMAGE, k2b.TOPIC_INFO, k2b.TOPIC_POINTS, k2b.TOPIC_GT):
        for bag_t, m in msgs[topic]:
            header_t = m.header.stamp.sec * 1_000_000_000 + m.header.stamp.nanosec
            assert header_t == bag_t
            assert (bag_t - t0) % k2b.FRAME_PERIOD_NS == 0
    stamps = {topic: [t for t, _ in msgs[topic]] for topic in msgs}
    assert stamps[k2b.TOPIC_IMAGE] == stamps[k2b.TOPIC_INFO] == stamps[k2b.TOPIC_GT]
    assert t0 + MISSING_SCAN * k2b.FRAME_PERIOD_NS not in stamps[k2b.TOPIC_POINTS]


def test_image_and_cloud_roundtrip(bag, kitti_root):
    _, msgs = read_all(bag)
    split = kitti_root / "training"
    _, img = msgs[k2b.TOPIC_IMAGE][0]
    assert (img.width, img.height, img.encoding, img.header.frame_id) == (IMG_W, IMG_H, "bgr8", k2b.CAM_FRAME)
    expected = cv2.imread(str(split / "image_02" / SEQ / "000000.png"))
    np.testing.assert_array_equal(img.data.reshape(IMG_H, IMG_W, 3), expected)

    _, pc = msgs[k2b.TOPIC_POINTS][0]
    assert pc.header.frame_id == k2b.VELO_FRAME
    assert [f.name for f in pc.fields] == ["x", "y", "z", "intensity"]
    got = np.frombuffer(pc.data.tobytes(), dtype="<f4").reshape(-1, 4)
    np.testing.assert_array_equal(got, np.fromfile(split / "velodyne" / SEQ / "000000.bin", dtype="<f4").reshape(-1, 4))


def test_gt_boxes(bag):
    _, msgs = read_all(bag)
    _, frame0 = msgs[k2b.TOPIC_GT][0]
    _, frame1 = msgs[k2b.TOPIC_GT][1]
    assert frame0.header.frame_id == k2b.RECT_FRAME
    assert len(frame0.detections) == 2 and len(frame1.detections) == 0

    car = frame0.detections[0]
    assert car.id == "0" and car.results[0].hypothesis.class_id == "Car"
    c = car.bbox.center.position
    assert (c.x, c.y, c.z) == pytest.approx((-4.55, 1.80 - 2.00 / 2, 13.75))  # bottom -> center
    s = car.bbox.size
    assert (s.x, s.y, s.z) == pytest.approx((4.43, 2.00, 1.82))  # l, h, w
    q = car.bbox.center.orientation
    assert 2 * np.arctan2(q.y, q.w) == pytest.approx(-2.11)
    assert q.x == q.z == 0.0


def test_tf_static_is_latched(bag):
    conns, _ = read_all(bag)
    qos = conns[k2b.TOPIC_TF_STATIC].ext.offered_qos_profiles
    assert qos[0].durability == QosDurability.TRANSIENT_LOCAL


def test_tf_and_camera_info_reproduce_kitti_projection(bag, kitti_root):
    """TF velodyne->camera_02 then camera_info K must equal the KITTI chain
    P2 * R0_rect * Tr_velo_cam on the same points."""
    _, msgs = read_all(bag)
    tfs = {(t.header.frame_id, t.child_frame_id): t for t in msgs[k2b.TOPIC_TF_STATIC][0][1].transforms}
    T_velo_rect = tf_matrix(tfs[(k2b.VELO_FRAME, k2b.RECT_FRAME)])
    T_rect_cam2 = tf_matrix(tfs[(k2b.RECT_FRAME, k2b.CAM_FRAME)])
    T_cam2_velo = np.linalg.inv(T_velo_rect @ T_rect_cam2)

    _, info = msgs[k2b.TOPIC_INFO][0]
    assert info.header.frame_id == k2b.CAM_FRAME
    P_ros = info.p.reshape(3, 4)
    np.testing.assert_array_equal(P_ros[:, 3], 0.0)

    calib = k2b.parse_calib(kitti_root / "training" / "calib" / f"{SEQ}.txt")
    P_kitti = calib.P2 @ k2b.T_rect_velo(calib)

    rng = np.random.default_rng(2)
    X = np.vstack([rng.uniform([5, -10, -2], [60, 10, 2], (200, 3)).T, np.ones(200)])
    uv_ros = P_ros @ (T_cam2_velo @ X)
    uv_kitti = P_kitti @ X
    uv_ros = uv_ros[:2] / uv_ros[2]
    uv_kitti = uv_kitti[:2] / uv_kitti[2]
    # Residual comes only from orthonormalizing KITTI's rotation for the
    # quaternion; it must stay well under a pixel.
    assert np.abs(uv_ros - uv_kitti).max() < 0.05


@pytest.mark.skipif(shutil.which("ros2") is None, reason="ros2 CLI not on PATH")
def test_ros2_bag_info_reads_bag(bag):
    out = subprocess.run(["ros2", "bag", "info", str(bag)], capture_output=True, text=True, check=True).stdout
    assert "vision_msgs/msg/Detection3DArray" in out
    assert f"Messages:          {4 * N_FRAMES - 1 + 1}" in out
