"""Tests for tools/merge_compile_commands.py."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import merge_compile_commands as mcc  # noqa: E402


def write_db(path: Path, files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"directory": str(path.parent), "command": f"c++ -c {f}", "file": f}
                                for f in files]))


def test_merges_every_package(tmp_path):
    write_db(tmp_path / "detector_cpp" / "compile_commands.json", ["yolo.cpp", "test_yolo.cpp"])
    write_db(tmp_path / "fusion_cpp" / "compile_commands.json", ["projection.cpp"])
    (tmp_path / "kitti_bringup").mkdir()  # no compiled sources, no database

    assert mcc.merge(tmp_path) == 3
    merged = json.loads((tmp_path / "compile_commands.json").read_text())
    assert sorted(e["file"] for e in merged) == ["projection.cpp", "test_yolo.cpp", "yolo.cpp"]


def test_rerun_does_not_merge_its_own_output(tmp_path):
    write_db(tmp_path / "detector_cpp" / "compile_commands.json", ["yolo.cpp"])
    mcc.merge(tmp_path)
    assert mcc.merge(tmp_path) == 1
