
__all__ = []

from . import v1
__all__.extend(v1.__all__)
from .v1 import *

from . import DetectorConstruction_v1
__all__.extend(DetectorConstruction_v1.__all__)
from .DetectorConstruction_v1 import *




from . import v2                     # the ATLAS detector (DetectorConstruction_v2); its builders stay in geometry.v2, not at the package level
from . import DetectorConstruction_v2
__all__.extend(DetectorConstruction_v2.__all__)
from .DetectorConstruction_v2 import *
