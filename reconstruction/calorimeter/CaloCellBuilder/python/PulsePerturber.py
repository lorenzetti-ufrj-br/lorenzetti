"""
PulsePerturber backward-compatibility module.

This module re-exports PulsePerturberCfg and get_cells_from_brl from CaloCellTools.
"""

from CaloCellTools import PulsePerturberCfg, get_cells_from_brl

__all__ = ["PulsePerturberCfg", "get_cells_from_brl"]
