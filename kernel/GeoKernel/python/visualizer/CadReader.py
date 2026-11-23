"""
CadReader.py - Reads and inspects detector CAD / GDML geometries using ROOT TGeoManager.
"""

from typing import Any, Dict, List, Optional
import os


class CadReader:
    """Provides CAD and GDML geometry inspection via ROOT TGeoManager."""

    def __init__(self, cad_or_gdml_path: str = "") -> None:
        self.path: str = os.path.abspath(cad_or_gdml_path) if cad_or_gdml_path else ""
        self.loaded: bool = False
        self._geo_manager: Any = None

    def load(self, path: Optional[str] = None) -> bool:
        """Loads geometry file into ROOT TGeoManager if ROOT is available."""
        if path:
            self.path = os.path.abspath(path)
        if not self.path or not os.path.isfile(self.path):
            return False

        try:
            import ROOT
            ROOT.TGeoManager.Import(self.path)
            self._geo_manager = ROOT.gGeoManager
            self.loaded = bool(self._geo_manager)
            return self.loaded
        except Exception:
            self.loaded = False
            return False

    def inspect(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Inspects CAD or GDML file and returns summary metadata."""
        if path:
            self.path = os.path.abspath(path)
        if not self.path or not os.path.isfile(self.path):
            return {"loaded": False, "error": f"File not found: {self.path}"}
        if not self.load():
            return {"loaded": False, "error": "Failed to load geometry into ROOT TGeoManager"}
        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Returns node count and top volume info."""
        if not self.loaded or not self._geo_manager:
            return {"loaded": False, "source": self.path}

        top = self._geo_manager.GetTopVolume()
        return {
            "loaded": True,
            "source": self.path,
            "top_volume": top.GetName(),
            "nodes_count": top.GetNodes().GetEntries() if top.GetNodes() else 0,
        }
