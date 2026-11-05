#!/usr/bin/env python3
"""Merge colcon's per-package compile_commands.json into build/compile_commands.json.

colcon builds each package in build/<pkg>/ with its own compilation database.
Editors look for a single database, so `pixi run build` merges them. VS Code's
C/C++ extension (via C_Cpp.default.compileCommands) and clangd then find the
headers that pixi installs in .pixi/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def merge(build_dir: Path) -> int:
    """Write build_dir/compile_commands.json from build_dir/*/compile_commands.json; return the entry count."""
    entries = []
    for db in sorted(build_dir.glob("*/compile_commands.json")):
        entries.extend(json.loads(db.read_text()))
    (build_dir / "compile_commands.json").write_text(json.dumps(entries, indent=2) + "\n")
    return len(entries)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--build-dir", type=Path, default=Path("build"))
    args = ap.parse_args(argv)
    if not args.build_dir.is_dir():
        ap.error(f"{args.build_dir} not found; run colcon build first")
    n = merge(args.build_dir)
    print(f"{args.build_dir / 'compile_commands.json'}: {n} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
