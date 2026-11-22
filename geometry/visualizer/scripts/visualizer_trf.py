#!/usr/bin/env python3
"""
visualizer_trf.py - Command-line interface for the Lorenzetti detector visualizer.
"""

import argparse
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
for p in [_ROOT, os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from visualizer import launch_visualizer, export_vector_pdf


def main() -> None:
    """Parses arguments and starts the visualizer web server or exports vector PDF."""
    default_geo = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../GALTIC/data/galtic_geometry.json")
    )

    parser = argparse.ArgumentParser(
        description="Lorenzetti Visualizer: Interactive 3D Detector Visualization and Vector PDF Export"
    )
    parser.add_argument(
        "-f", "--geo-file",
        default=default_geo,
        help="Path to geometry JSON file (default: GALTIC/data/galtic_geometry.json)",
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
        # Fallback to atlas_v1.json if galtic_geometry.json not yet generated
        alt_geo = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../GALTIC/data/atlas_v1.json")
        )
        if os.path.isfile(alt_geo):
            args.geo_file = alt_geo
        else:
            print(f"Error: Geometry file not found at '{args.geo_file}'.")
            sys.exit(1)

    if args.export_pdf:
        print(f"Exporting 100% vector PDF ({args.view}) to: {args.export_pdf}")
        export_vector_pdf(args.geo_file, args.export_pdf, view=args.view)
        print("Export completed successfully.")
        return

    launch_visualizer(args.geo_file, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
