#!/usr/bin/env python3
"""
generate_atlas_geometry.py - Generates canonical atlas_geometry.json for ATLAS v2.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../../.."))
_ATLAS_PY = os.path.abspath(os.path.join(_SCRIPT_DIR, "../python"))
_GEOMETRY_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))

for p in [_REPO_ROOT, _GEOMETRY_DIR, _ATLAS_PY, os.path.join(_REPO_ROOT, "build/python")]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

# Mock ROOT if not available
if "ROOT" not in sys.modules:
    try:
        import ROOT
    except ImportError:
        from unittest.mock import MagicMock
        sys.modules["ROOT"] = MagicMock()

from ATLAS.v2.AtlasCfg import getAtlasAllSamplings, getAtlasAllDeadMaterials
import json


def main() -> None:
    """Generates the canonical atlas_geometry.json file."""
    output_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/atlas_geometry.json")
    )
    print(f"Generating canonical ATLAS v2 geometry: {output_path}")

    samplings = getAtlasAllSamplings()
    dead_materials = getAtlasAllDeadMaterials()

    data = {
        "metadata": {
            "version": "2.0",
            "detector": "ATLAS",
            "description": "ATLAS Calorimeter official canonical geometry specification (v2)",
        },
        "volumes": [s.to_dict() for s in samplings] + [dm.to_dict() for dm in dead_materials],
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Success! Generated {len(samplings)} sampling layers and {len(dead_materials)} dead material volumes at {output_path}.")


if __name__ == "__main__":
    main()
