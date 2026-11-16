
__all__ = ["CaloSampling", "Detector"]

from GaugiKernel import EnumStringification


class Detector(EnumStringification):
  LAR     = 0
  TILE    = 1
  TTEM    = 2
  TTHEC   = 3
  FCALEM  = 5
  FCALHAD = 6


#
# NOTE: If you change something here, you must do the same at enumeration.h
#
class CaloSampling(EnumStringification):
    PSB       = 0
    PSE       = 1
    EMB1      = 2
    EMB2      = 3
    EMB3      = 4
    TileCal1  = 5
    TileCal2  = 6
    TileCal3  = 7
    TileExt1  = 8
    TileExt2  = 9
    TileExt3  = 10
    EMEC1     = 11
    EMEC2     = 12
    EMEC3     = 13
    HEC1      = 14
    HEC2      = 15
    HEC3      = 16
    # First sampling of the ATLAS-like HEC (--atlas-hec; not used by default). Outside the range of the others so that
    # the hash (sampling + 17 side) 1e7 + segment 1e6 + bin stays unique (see enumeration.h).
    HEC0      = 60
    # The three modules of the ATLAS FCal with its cells (--atlas-fcal-cells; not used by default), one cell per tile of the
    # ATLAS FCal, outside the range of the others for the same reason as HEC0 (see enumeration.h).
    FCAL1     = 61
    FCAL2     = 62
    FCAL3     = 63


