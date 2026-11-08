__all__ = ["PhysicalVolume", "ProductionCuts", "Plates"]

from GaugiKernel import Logger
from GaugiKernel.macros import MSG_FATAL
from GaugiKernel.constants import um
from GaugiKernel import EnumStringification



class Plates(EnumStringification):
  Horizontal = 0
  Vertical   = 1
  # One G4Polycone of AbsorberMaterial (dead material only) with the planes ZPlanes, RMinPlanes, RMaxPlanes.
  Polycone   = 2


#
# Geant4 physical volume dimensions
#
class PhysicalVolume(Logger):

    __allow_keys = [
                      "Name",
                      "Plates",
                      "AbsorberMaterial",
                      "GapMaterial",
                      "NofLayers",
                      "AbsorberThickness",
                      "GapThickness",
                      "LayerClearance",
                      "AbsorberSplitZ",
                      "AbsorberMaterial2",
                      "AbsorberThickness2",
                      "RMin",
                      "RMax",
                      "ZSize",
                      "X",
                      "Y",
                      "Z",
                      "Visualization",
                      "Color",
                      "ZPlanes",
                      "RMinPlanes",
                      "RMaxPlanes",
                      "InSolenoidField",
                   ]

    # Constructor
    def __init__(self, **kw):

        Logger.__init__(self)
        # Empty space (envelope material) added to each layer after the gap, only for
        # Plates.Vertical: layer = absorber + gap + clearance. Default 0 keeps the original layout.
        self.LayerClearance = 0
        # Horizontal plates only: for |z| > AbsorberSplitZ the absorber is AbsorberMaterial2 with AbsorberThickness2, in
        # layers of the same thickness (the gap takes the rest). 0 (the default) keeps one absorber in the whole volume.
        self.AbsorberSplitZ = 0
        self.AbsorberMaterial2 = ""
        self.AbsorberThickness2 = 0
        # Plates.Polycone only: z, inner and outer radius of each plane.
        self.ZPlanes = []; self.RMinPlanes = []; self.RMaxPlanes = []
        # Placed inside the volume of the solenoid field (built with UseSolenoidField) instead of the world.
        self.InSolenoidField = False
        for key, value in kw.items():
          if key in self.__allow_keys:
            setattr(self, key, value )
          else:
            MSG_FATAL( self, "Property with name %s is not allow for %s object", key, self.__class__.__name__)

        self.ZMin = self.Z - self.ZSize / 2
        self.ZMax = self.Z + self.ZSize / 2
        self.Cuts = ProductionCuts()

    def name(self):
      return self.Name.replace('::','_')


# https://acode-browser1.usatlas.bnl.gov/lxr/source/athena/Simulation/G4Atlas/G4AtlasTools/python/G4PhysicsRegionConfig.py
class ProductionCuts(Logger):
  def __init__(self, GammaCut =  700*um, ElectronCut = 700*um, PositronCut = 700*um, PhotonCut = 700*um):
    self.GammaCut=GammaCut; self.ElectronCut=ElectronCut; self.PositronCut=PositronCut; self.PhotonCut=PhotonCut


