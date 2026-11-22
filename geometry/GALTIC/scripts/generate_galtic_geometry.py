#!/usr/bin/env python3
"""
generate_galtic_geometry.py - Generates canonical galtic_geometry.json.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../../.."))
_GALTIC_PY = os.path.abspath(os.path.join(_SCRIPT_DIR, "../python"))
_GEOMETRY_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))

for p in [_REPO_ROOT, _GEOMETRY_DIR, _GALTIC_PY, os.path.join(_REPO_ROOT, "build/python")]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from GALTIC import GalticDetectorConstruction


def main() -> None:
    """Generates the canonical galtic_geometry.json file."""
    output_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/galtic_geometry.json")
    )
    print(f"Generating canonical GALTIC geometry: {output_path}")

    det = GalticDetectorConstruction("GALTIC")
    det.save(output_path)

    # Also keep atlas_v1.json as a symlink or copy for backward compatibility
    compat_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/atlas_v1.json")
    )
    det.save(compat_path)

    print(f"Success! Generated {len(det.samplings)} sampling layers and {len(det.dead_materials)} dead material volumes.")


if __name__ == "__main__":
    main()
