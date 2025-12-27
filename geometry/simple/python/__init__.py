
__all__ = ['flatten']



def flatten(l):
    o = []
    for item in l:
        if type(item) is list:
            o.extend(item)
        else:
            o.append(item)
    return o


from .detectors import Tracking
__all__.extend(Tracking.__all__)
from .detectors.Tracking import *

from .detectors import ECAL
__all__.extend(ECAL.__all__)
from .detectors.ECAL import *

from .detectors import TILE
__all__.extend(TILE.__all__)
from .detectors.TILE import *

from .detectors import EMEC
__all__.extend(EMEC.__all__)
from .detectors.EMEC import *

from .detectors import HEC
__all__.extend(HEC.__all__)
from .detectors.HEC import *

from .detectors import DeadMaterials
__all__.extend(DeadMaterials.__all__)
from .detectors.DeadMaterials import *

from . import ATLASConstruction
__all__.extend(ATLASConstruction.__all__)
from .ATLASConstruction import *




