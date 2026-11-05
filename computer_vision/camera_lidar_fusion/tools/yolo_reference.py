#!/usr/bin/env python3
"""Write reference fixtures for detector_cpp's test_reference.

Runs the exported ONNX model through Ultralytics' own predict (letterbox,
decode, NMS, scale back to image pixels) on KITTI frames, and saves the Car and
Pedestrian boxes. test_reference.cpp runs the C++ pipeline on the same frames
and requires the same boxes within ~1 px, which checks preprocessing and
decoding against what the model really expects.

Runs in the pixi `export` environment:

    pixi run yolo-reference --kitti-root "/Volumes/Extreme SSD/kitti_tracking"

Only the box numbers are committed. KITTI images can't be redistributed, so the
C++ test reads the frames from the data path and skips when they're missing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT / "models" / "yolo11n_384x1280.onnx"
FIXTURE_DIR = PROJECT_ROOT / "src" / "detector_cpp" / "test" / "data"
# 0000 is 1242x375 (pad_x 4) and 0016 is 1224x370 (pad_x 5).
DEFAULT_FRAMES = ["0000/000000", "0016/000000"]

# Must match test_reference.cpp.
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.5
KEEP_CLASSES = [0, 2]  # COCO person, car


def fixture_path(frame: str) -> Path:
    seq, idx = frame.split("/")
    return FIXTURE_DIR / f"reference_{seq}_{idx}.txt"


def format_fixture(frame: str, image_wh: tuple[int, int], model_name: str, ultralytics_version: str,
                   rows: list[tuple[int, float, list[float]]]) -> str:
    """One `class_id score x1 y1 x2 y2` row per box, highest score first; `#` lines are comments."""
    lines = [
        f"# Ultralytics {ultralytics_version} predict, model {model_name}",
        f"# frame {frame} ({image_wh[0]}x{image_wh[1]}), conf {CONF_THRESHOLD}, iou {IOU_THRESHOLD}, "
        f"classes {' '.join(map(str, KEEP_CLASSES))}",
        "# class_id score x1 y1 x2 y2 (image pixels)",
    ]
    for cls, score, (x1, y1, x2, y2) in sorted(rows, key=lambda r: -r[1]):
        lines.append(f"{cls} {score:.4f} {x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Write detector_cpp reference fixtures with Ultralytics predict.")
    p.add_argument("--kitti-root", type=Path, default=PROJECT_ROOT / "data" / "kitti_tracking",
                   help="folder that contains training/ (default: data/kitti_tracking)")
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--frames", nargs="+", default=DEFAULT_FRAMES, metavar="SEQ/FRAME")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.model.is_file():
        raise SystemExit(f"{args.model} not found; run `pixi run export-yolo` first")

    import cv2
    import onnxruntime
    import ultralytics
    from ultralytics import YOLO

    _, _, h, w = onnxruntime.InferenceSession(str(args.model)).get_inputs()[0].shape
    model = YOLO(str(args.model), task="detect")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    for frame in args.frames:
        image = args.kitti_root / "training" / "image_02" / f"{frame}.png"
        if not image.is_file():
            raise SystemExit(f"{image} not found")
        # Read the frame here, the same way test_reference.cpp does (BGR).
        # Ultralytics silently skips a path it can't read.
        bgr = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if bgr is None:
            raise SystemExit(f"can't read {image}; on macOS, check that the app running this "
                             "has Removable Volumes access (Privacy & Security > Files & Folders)")
        result = model.predict(bgr, imgsz=[h, w], conf=CONF_THRESHOLD, iou=IOU_THRESHOLD,
                               classes=KEEP_CLASSES, device="cpu", verbose=False)[0]
        boxes = result.boxes
        rows = list(zip(boxes.cls.int().tolist(), boxes.conf.tolist(), boxes.xyxy.tolist()))
        image_h, image_w = result.orig_shape
        out = fixture_path(frame)
        out.write_text(format_fixture(frame, (image_w, image_h), args.model.name, ultralytics.__version__, rows))
        print(f"{out.relative_to(PROJECT_ROOT)}: {len(rows)} boxes")


if __name__ == "__main__":
    main()
