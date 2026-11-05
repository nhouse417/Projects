#!/usr/bin/env python3
"""Export YOLO11n to ONNX for the detector_cpp node.

Runs in the pixi `export` environment (Ultralytics + PyTorch, no ROS):

    pixi run export-yolo                    # models/yolo11n_384x1280.onnx
    pixi run export-yolo --imgsz 384 1248   # another static input size (H W)

The first run downloads yolo11n.pt (~5 MB) from Ultralytics' GitHub releases
into models/. Ultralytics code and weights are AGPL-3.0; models/ is gitignored.

The graph has a static input [1, 3, H, W] and outputs raw candidates
[1, 84, N]: cx, cy, w, h in model-input pixels, then 80 sigmoided class scores,
no objectness, no NMS. detector_cpp does the decode and NMS itself.
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
STRIDES = (8, 16, 32)
NUM_COCO_CLASSES = 80


def expected_candidates(h: int, w: int) -> int:
    """One candidate per grid cell at each stride: 384x1280 -> 160x48 + 80x24 + 40x12 = 10,080."""
    return sum((h // s) * (w // s) for s in STRIDES)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export YOLO11n to ONNX for detector_cpp.")
    p.add_argument("--weights", default="yolo11n.pt",
                   help="Ultralytics weights file in models/ (downloaded if missing)")
    p.add_argument("--imgsz", type=int, nargs=2, default=[384, 1280], metavar=("H", "W"),
                   help="static model input size; both sides must divide by the largest stride (32)")
    p.add_argument("--out", type=Path,
                   help="output path (default: models/<weights stem>_<H>x<W>.onnx)")
    return p.parse_args(argv)


def check_graph(path: Path, h: int, w: int) -> None:
    """Fail loudly if the exported graph isn't the [1, 3, H, W] -> [1, 84, N] contract."""
    import onnx

    model = onnx.load(str(path))
    dims = lambda v: [d.dim_value or d.dim_param for d in v.type.tensor_type.shape.dim]  # noqa: E731
    in_shape, out_shape = dims(model.graph.input[0]), dims(model.graph.output[0])
    want_in = [1, 3, h, w]
    want_out = [1, 4 + NUM_COCO_CLASSES, expected_candidates(h, w)]
    if in_shape != want_in or out_shape != want_out:
        raise SystemExit(f"unexpected graph shapes: input {in_shape} (want {want_in}), "
                         f"output {out_shape} (want {want_out})")

    meta = {p.key: p.value for p in model.metadata_props}
    print(f"wrote {path}")
    print(f"  input  {model.graph.input[0].name} {in_shape}")
    print(f"  output {model.graph.output[0].name} {out_shape}")
    print(f"  opset  {model.opset_import[0].version}")
    for key in ("imgsz", "stride", "task"):
        print(f"  {key:6} {meta.get(key)}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    h, w = args.imgsz
    if h % max(STRIDES) or w % max(STRIDES):
        raise SystemExit(f"--imgsz {h} {w}: both sides must be multiples of {max(STRIDES)}")

    from ultralytics import YOLO  # slow import, after argument checks

    MODELS_DIR.mkdir(exist_ok=True)
    out = args.out or MODELS_DIR / f"{Path(args.weights).stem}_{h}x{w}.onnx"

    model = YOLO(MODELS_DIR / args.weights)
    # nms is left unset: in Ultralytics 8.4, None means external NMS (raw
    # candidates out), while False would ask for an NMS-free head.
    exported = model.export(format="onnx", imgsz=[h, w], dynamic=False, simplify=True,
                            batch=1, device="cpu")
    Path(exported).replace(out)
    check_graph(out, h, w)


if __name__ == "__main__":
    main()
