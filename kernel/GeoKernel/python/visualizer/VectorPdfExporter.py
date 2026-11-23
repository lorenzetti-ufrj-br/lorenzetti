"""
VectorPdfExporter.py - Generates 100% mathematically vectorized PDF drawings of detectors.
Zero rasterization / infinite zoom capability using Matplotlib Agg backend.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

__all__ = ["VectorPdfExporter", "export_vector_pdf"]

COLOR_MAP: Dict[str, str] = {
    "PSB": "#FFA500",
    "EMB1": "#7FFFD4",
    "EMB2": "#6495ED",
    "EMB3": "#00FFFF",
    "PSE": "#FFA500",
    "EMEC1": "#7FFFD4",
    "EMEC2": "#6495ED",
    "EMEC3": "#00FFFF",
    "TileCal1": "#FA8072",
    "TileCal2": "#EE82EE",
    "TileCal3": "#FF4500",
    "TileExt1": "#FA8072",
    "TileExt2": "#EE82EE",
    "TileExt3": "#FF4500",
    "HEC1": "#FA8072",
    "HEC2": "#C71585",
    "HEC3": "#FF4500",
}


class VectorPdfExporter:
    """Renders parametric vector technical cross-sections to PDF."""

    def __init__(self, geometry_data_or_file: Union[str, Dict[str, Any], Any]) -> None:
        if hasattr(geometry_data_or_file, "to_dict"):
            self.data = geometry_data_or_file.to_dict()
        elif isinstance(geometry_data_or_file, str):
            with open(geometry_data_or_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        elif isinstance(geometry_data_or_file, dict):
            self.data = geometry_data_or_file
        else:
            self.data = {}

        self.volumes: List[Dict[str, Any]] = self.data.get("volumes", [])

    def export_rz_cut(
        self,
        output_filepath: str,
        show_cells: bool = True,
        show_labels: bool = True,
        symmetric: bool = True,
        figsize: Tuple[float, float] = (14.0, 8.0),
    ) -> None:
        """Generates longitudinal cut technical cross-section (R-Z plane)."""
        fig, ax = plt.subplots(figsize=figsize, dpi=300)
        scale = 0.001  # mm to meters

        for item in self.volumes:
            name = item.get("name", "Unknown")
            geom = item.get("geometry", {})
            readout = item.get("readout")

            z_size = geom.get("z_size", 0.0) * scale
            rmin = geom.get("rmin", 0.0) * scale
            rmax = geom.get("rmax", 0.0) * scale
            center = geom.get("center", [0.0, 0.0, 0.0])
            z_center = center[2] * scale

            zmin = z_center - z_size / 2.0
            width = z_size
            height = rmax - rmin

            sampling_name = readout.get("sampling", "") if readout else ""
            color = COLOR_MAP.get(sampling_name, "#B0B0B0" if not readout else "#87CEEB")
            alpha = 0.6 if readout else 0.35

            rect_pos = patches.Rectangle(
                (zmin, rmin), width, height,
                linewidth=0.8, edgecolor="#202020", facecolor=color, alpha=alpha
            )
            ax.add_patch(rect_pos)

            if symmetric:
                rect_neg = patches.Rectangle(
                    (zmin, -rmax), width, height,
                    linewidth=0.8, edgecolor="#202020", facecolor=color, alpha=alpha
                )
                ax.add_patch(rect_neg)

            if show_cells and readout and "delta_eta" in readout:
                deta = readout.get("delta_eta", 0.0)
                if deta > 0.0:
                    for eta in np.arange(-3.2, 3.2 + deta, deta):
                        if abs(eta) < 1e-4:
                            continue
                        theta = 2.0 * np.arctan(np.exp(-eta))
                        tan_theta = np.tan(theta)
                        if abs(tan_theta) > 1e-4:
                            z_inner = rmin / tan_theta
                            z_outer = rmax / tan_theta
                            if (zmin <= z_inner <= zmin + width) or (zmin <= z_outer <= zmin + width):
                                ax.plot([z_inner, z_outer], [rmin, rmax], color="#404040", linewidth=0.3, alpha=0.5)
                                if symmetric:
                                    ax.plot([z_inner, z_outer], [-rmin, -rmax], color="#404040", linewidth=0.3, alpha=0.5)

        ax.axhline(0, color="#101010", linestyle="--", linewidth=1.0, alpha=0.8, label="Beamline (Z axis)")
        ax.axvline(0, color="#808080", linestyle=":", linewidth=0.6, alpha=0.6)

        ax.set_xlabel("Longitudinal Coordinate Z [m]", fontsize=12, fontweight="bold")
        ax.set_ylabel("Radial Coordinate R [m]", fontsize=12, fontweight="bold")
        title = self.data.get("metadata", {}).get("detector", "Lorenzetti Detector")
        ax.set_title(f"{title} - Longitudinal Cross-Section (R-Z Cut)", fontsize=14, fontweight="bold")

        ax.set_xlim(-6.5, 6.5)
        ax.set_ylim(-4.8 if symmetric else 0.0, 4.8)
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.4)

        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
        fig.savefig(output_filepath, format="pdf", bbox_inches="tight")
        plt.close(fig)

    def export_rphi_cut(
        self,
        output_filepath: str,
        z_plane: float = 0.0,
        show_cells: bool = True,
        figsize: Tuple[float, float] = (10.0, 10.0),
    ) -> None:
        """Generates transverse cut technical cross-section (R-Phi plane)."""
        fig, ax = plt.subplots(figsize=figsize, dpi=300)
        scale = 0.001
        z_plane_mm = z_plane

        for item in self.volumes:
            name = item.get("name", "Unknown")
            geom = item.get("geometry", {})
            readout = item.get("readout")

            z_size = geom.get("z_size", 0.0)
            center = geom.get("center", [0.0, 0.0, 0.0])
            z_center = center[2]
            zmin = z_center - z_size / 2.0
            zmax = z_center + z_size / 2.0

            if not (zmin <= z_plane_mm <= zmax):
                continue

            rmin = geom.get("rmin", 0.0) * scale
            rmax = geom.get("rmax", 0.0) * scale

            sampling_name = readout.get("sampling", "") if readout else ""
            color = COLOR_MAP.get(sampling_name, "#B0B0B0" if not readout else "#87CEEB")
            alpha = 0.55 if readout else 0.3

            circ_outer = patches.Circle((0, 0), rmax, edgecolor="#202020", facecolor=color, alpha=alpha, linewidth=0.6)
            circ_inner = patches.Circle((0, 0), rmin, edgecolor="#202020", facecolor="white", linewidth=0.6)
            ax.add_patch(circ_outer)
            ax.add_patch(circ_inner)

            if show_cells and readout and "delta_phi" in readout:
                dphi = readout.get("delta_phi", 0.0)
                shift = readout.get("phi_shift", 0.0)
                if dphi > 0.0:
                    for phi in np.arange(shift, 2.0 * np.pi + shift, dphi):
                        x_in, y_in = rmin * np.cos(phi), rmin * np.sin(phi)
                        x_out, y_out = rmax * np.cos(phi), rmax * np.sin(phi)
                        ax.plot([x_in, x_out], [y_in, y_out], color="#404040", linewidth=0.3, alpha=0.4)

        ax.set_xlabel("Transverse X [m]", fontsize=12, fontweight="bold")
        ax.set_ylabel("Transverse Y [m]", fontsize=12, fontweight="bold")
        title = self.data.get("metadata", {}).get("detector", "Lorenzetti Detector")
        ax.set_title(f"{title} - Transverse Cross-Section (R-Phi Cut at Z = {z_plane:.1f} mm)", fontsize=14, fontweight="bold")

        ax.set_xlim(-4.6, 4.6)
        ax.set_ylim(-4.6, 4.6)
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.4)

        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
        fig.savefig(output_filepath, format="pdf", bbox_inches="tight")
        plt.close(fig)

    export_rz = export_rz_cut
    export_xy = export_rphi_cut


def export_vector_pdf(
    geometry_file: str,
    output_filepath: str,
    view: str = "rz",
    z_plane: float = 0.0,
    show_cells: bool = True,
) -> None:
    """Convenience function to export 100% vector PDF."""
    exporter = VectorPdfExporter(geometry_file)
    if view.lower() == "rphi":
        exporter.export_rphi_cut(output_filepath, z_plane=z_plane, show_cells=show_cells)
    else:
        exporter.export_rz_cut(output_filepath, show_cells=show_cells)
