#!/usr/bin/env python3
"""
geoview_trf.py - Command-line interface for the GeoView detector visualization tool.
"""

import argparse
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from GeoView import launch_viewer, export_vector_pdf


def main() -> None:
    """Parses arguments and starts GeoView viewer or exports vector PDF."""
    parser = argparse.ArgumentParser(
        description="Lorenzetti GeoView: Interactive Web 3D Detector Visualization and Vector PDF Export"
    )
    parser.add_argument(
        "-f", "--geo-file",
        default=os.path.join(_ROOT, "geometry/GeoV1/data/atlas_v1.json"),
        help="Path to geometry_v1.json (default: geometry/GeoV1/data/atlas_v1.json)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="HTTP port for browser viewer (default: 8080)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch web browser",
    )
    parser.add_argument(
        "--export-pdf",
        type=str,
        default="",
        help="Directly export vector PDF to specified file path and exit",
    )
    parser.add_argument(
        "--view",
        choices=["rz", "rphi"],
        default="rz",
        help="View mode for vector PDF export ('rz' or 'rphi')",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.geo_file):
        print(f"Error: Geometry file not found at '{args.geo_file}'.")
        sys.exit(1)

    if args.export_pdf:
        print(f"Exporting 100% vector PDF ({args.view}) to: {args.export_pdf}")
        export_vector_pdf(args.geo_file, args.export_pdf, view=args.view)
        print("Export completed successfully.")
        return

    launch_viewer(args.geo_file, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
