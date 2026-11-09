__all__ = [
           "DetectorConstruction_v2", 
           ]


import ROOT

from typing import List
from prettytable import PrettyTable
from pprint import pprint
from tqdm import tqdm

from GaugiKernel.constants import *
from GaugiKernel import Cpp
from GaugiKernel.macros import *

from geometry.v2.PhysicalVolume   import Plates
from CaloCell.CaloDefs            import CaloSampling
from geometry.v2.ECAL             import getLArBarrelCfg, getAtlasEmbVolumesCfg, getAtlasPseCfg, getAtlasEmbEndCfg
from geometry.v2.ECAL             import getAtlasPsbVolumesCfg, ATLAS_PS_ELECTRODE_MIXTURE
from geometry.v2.TILE             import getTileBarrelCfg, getTileExtendedCfg
from geometry.v2.TILE             import getAtlasTileGapCfg, getAtlasTileGapVolumesCfg, ATLAS_TILE_GAP_MIXTURES
from geometry.v2.EMEC             import getLArEMECCfg, getAtlasEmecVolumesCfg
from geometry.v2.HEC              import getHECCfg, getAtlasHecPassiveCfg
from geometry.v2.DeadMaterials    import getDMVolumesCfg, getCrackVolumesCfg, getAtlasEndcapCryostatCfg
from geometry.v2.AtlasBarrelFront import ATLAS_BARREL_FRONT_MIXTURES, ATLAS_BARREL_FRONT_FIELD_RADIUS
from geometry.v2.AtlasBarrelCryostat import ATLAS_BARREL_CRYOSTAT_MIXTURES
from geometry.v2.AtlasFCal        import ATLAS_FCAL_MIXTURES
from geometry.v2.DeadMaterials    import getAtlasFcalCfg
from geometry.v2.AtlasFCal        import ATLAS_FCAL_CELL_MATERIALS
from geometry.v2.FCAL             import getAtlasFcalCellsCfg
#from geometry.detectors.Tracking      import *


def flatten(nested_list : List) -> List:
  """Flatten a nested list."""
  result = []
  for item in nested_list:
    if isinstance(item, list):
      result.extend(flatten(item))
    else:
      result.append(item)
  return result


class DetectorConstruction_v2( Cpp ):

  def __init__( self, 
                name              : str, 
                UseMagneticField  : bool=False,
                UseSolenoidField  : bool=False,
                CutOnPhi          : bool=False,
                TileAtlasGeometry : bool=False,
                TileAtlasCells    : bool=False,
                AtlasMaterialInFront : bool=False,
                TileAtlasItc      : bool=False,
                AtlasEmb          : bool=False,
                AtlasEmbCells     : bool=False,
                AtlasEndcapCryostat : bool=False,
                AtlasBarrelCryostat : bool=False,
                AtlasHec          : bool=False,
                AtlasEmec         : bool=False,
                AtlasFcal         : bool=False,
                AtlasFcalCells    : bool=False,
                AtlasFcalElectrodes : str="",
                AtlasFcalFrozenShowers : bool=False,
                AtlasFcalShowerLibDir : str="",
                AtlasG4           : bool=False,
                TileAtlasGap      : bool=False,
                AtlasRun4         : bool=False,
                AtlasRun4Geometry : str="",
                AtlasFieldMap     : str="",
                AtlasForwardShielding : bool=False,
                AtlasFullField    : bool=False,
                AtlasBarrelGapServices : bool=False,
                TileAtlasRun4     : bool=False,
                AtlasEmecArgonFraction : bool=False,
              ):

    Cpp.__init__(self, ROOT.DetectorConstruction_v2(name) )
    # The EMEC of the ATLAS Run 4 geometry of the simulation leaves the crack between its wheels to the transversal bars of ATLAS
    # (geometry/python/v1/EMEC.py; F41 conserto 27)
    import geometry.v2.EMEC as _emec
    _emec.EMEC_ATLAS_CRACK_EDGES_INSIDE = bool(AtlasRun4)
    # The argon fraction of the ATLAS accordion in the bands of the ATLAS-like EMEC (geometry/python/v1/EMEC.py; F41 conserto 37)
    if AtlasEmecArgonFraction and not AtlasEmec:
      raise ValueError("AtlasEmecArgonFraction needs AtlasEmec.")
    _emec.EMEC_ATLAS_ARGON_FRACTION = bool(AtlasEmecArgonFraction)

    self.setProperty( "UseMagneticField", UseMagneticField  )
    # 2 T field only inside the ATLAS central solenoid volume (R < 1.23 m, |z| < 2.9 m);
    # cannot be combined with UseMagneticField (2 T in the whole world).
    self.setProperty( "UseSolenoidField", UseSolenoidField  )
    self.setProperty( "CutOnPhi"        , CutOnPhi          )

    self.samplings = []
    self.volumes = []
    # Modules of the ATLAS FCal with their electrodes (AtlasFcalCells; geometry/python/v1/FCAL.py): built by AddFCalModule;
    # their hit makers record one hit per tile in the hit collection and, with the free-running hits, feed LArHitFCAL (CaloHitBuilder)
    self.fcal_modules = []
    # Mixtures defined by the geometry (name: (density in g/cm3, {element symbol: mass fraction})).
    self.mixtures = {}
    # With AtlasEmbCells and AtlasMaterialInFront the material in front of the barrel accordion is that of ATLAS, piece by
    # piece (geometry/python/v1/DeadMaterials.py, getAtlasBarrelFrontCfg; F41 conserto 17c): the solenoid field volume
    # ends at r = 1229 mm, where the coil starts, and the warm inner wall of the cryostat sits inside it.
    atlas_barrel_front = AtlasEmbCells and AtlasMaterialInFront
    if atlas_barrel_front:
      self.mixtures.update( ATLAS_BARREL_FRONT_MIXTURES )
      self.setProperty( "SolenoidFieldRadius", ATLAS_BARREL_FRONT_FIELD_RADIUS )
    # With it and AtlasBarrelCryostat, the outer part of the barrel cryostat is also that of ATLAS, piece by piece
    # (geometry/python/v1/AtlasBarrelCryostat.py; F41 conserto 14b).
    atlas_cryostat_pieces = atlas_barrel_front and AtlasBarrelCryostat
    if atlas_cryostat_pieces:
      self.mixtures.update( ATLAS_BARREL_CRYOSTAT_MIXTURES )
    # Center
    
    #volumes.extend( getPixelBarrelCfg()   )
    # Barrel EM calorimeter with the ATLAS absorber composition (lead 1.53/1.13 mm, steel, glue and electrode) and depth
    # (see geometry/python/v1/ECAL.py). The same value must be used in simulation and digitization.
    # With AtlasEmbCells (needs AtlasEmb) the three layers end at |z| = 3165 mm as in ATLAS (steps along |eta| = 1.475 near
    # the inner radius) and have the cells of the ATLAS identifier dictionary (see geometry/python/v1/ECAL.py); their
    # volumes are built from getAtlasEmbVolumesCfg. The same value must be used in simulation and digitization.
    if AtlasEmbCells and not AtlasEmb:
      raise ValueError("AtlasEmbCells needs AtlasEmb.")
    self.samplings.extend( getLArBarrelCfg(atlas_emb=AtlasEmb, atlas_emb_cells=AtlasEmbCells)   )
    if AtlasEmbCells:
      self.volumes.extend( getAtlasEmbVolumesCfg() )
      # the modules of the ATLAS barrel presampler with their electrodes (the maker volume is an envelope)
      self.volumes.extend( getAtlasPsbVolumesCfg() )
      self.mixtures.update( ATLAS_PS_ELECTRODE_MIXTURE )
      # behind the end of the barrel: dead argon, LArElectronics, conical cold wall and, with the barrel cryostat, the end
      # wall of the cold vessel down to r = 1565.5 mm (see geometry/python/v1/ECAL.py)
      self.volumes.extend( getAtlasEmbEndCfg(atlas_barrel_cryostat=AtlasBarrelCryostat,
                                             atlas_barrel_front=atlas_barrel_front) )
    # ATLAS-like tile calorimeter (tiles normal to the beam line, 18 mm period, ATLAS layer radii and z extent;
    # see geometry/python/v1/TILE.py). The same value must be used in simulation and digitization. With it the
    # dead material next to the tile calorimeter (inner aluminium shell, ITC block) follows the ATLAS z extent.
    # ATLAS tile cells (A1-A16, BC1-BC8, B9, D0-D6) instead of the eta x phi grid; needs TileAtlasGeometry.
    if TileAtlasCells and not TileAtlasGeometry:
      raise ValueError("TileAtlasCells needs TileAtlasGeometry.")
    self.samplings.extend( getTileBarrelCfg(atlas_geometry=TileAtlasGeometry, atlas_cells=TileAtlasCells)  )
    # Material in front of the barrel electromagnetic calorimeter as in ATLAS (solenoid, cryostat wall and the material
    # between the presampler and the accordion; see geometry/python/v1/DeadMaterials.py). Simulation only.
    # Outer part of the barrel cryostat as in ATLAS instead of the two 100 mm aluminium shells; needs TileAtlasItc, whose
    # services leave room for the step of the warm vessel (see geometry/python/v1/DeadMaterials.py). Simulation only.
    if AtlasBarrelCryostat and not TileAtlasItc:
      raise ValueError("AtlasBarrelCryostat needs TileAtlasItc.")
    self.volumes.extend( getDMVolumesCfg(tile_atlas_geometry=TileAtlasGeometry, atlas_material_in_front=AtlasMaterialInFront,
                                         atlas_barrel_cryostat=AtlasBarrelCryostat, atlas_emb_cells=AtlasEmbCells) )
    # Right side (A)
    self.samplings.extend( getTileExtendedCfg(atlas_geometry=TileAtlasGeometry, atlas_cells=TileAtlasCells,
                                              atlas_gap=TileAtlasGap)    )
    # EMEC as in ATLAS: two wheels with the nominal z, composition and cells of ATLAS (see geometry/python/v1/EMEC.py).
    # The cells depend on it: the same value must be used in simulation and digitization.
    self.samplings.extend( getLArEMECCfg(atlas_emec=AtlasEmec) )
    # HEC as in ATLAS: four samplings (HEC0-HEC3) in two wheels with the nominal z, plates and cells of ATLAS (see
    # geometry/python/v1/HEC.py). The cells depend on it: the same value must be used in simulation and digitization.
    self.samplings.extend( getHECCfg(atlas_hec=AtlasHec) )
    # The gap between the tile barrel and the extended barrel as in ATLAS (plug of the ITC and services) instead of the
    # aluminium block; needs TileAtlasGeometry (see geometry/python/v1/DeadMaterials.py). Simulation only.
    self.volumes.extend( getCrackVolumesCfg(tile_atlas_geometry=TileAtlasGeometry, tile_atlas_itc=TileAtlasItc,
                                            atlas_barrel_cryostat=AtlasBarrelCryostat, atlas_emec=AtlasEmec,
                                            atlas_emb_cells=AtlasEmbCells, atlas_cryostat_pieces=atlas_cryostat_pieces,
                                            tile_atlas_gap=TileAtlasGap) )
    # Left side (B)
    self.samplings.extend( getTileExtendedCfg(left_side = True, atlas_geometry=TileAtlasGeometry, atlas_cells=TileAtlasCells,
                                              atlas_gap=TileAtlasGap) )
    self.samplings.extend( getLArEMECCfg(left_side=True, atlas_emec=AtlasEmec) )
    self.samplings.extend( getHECCfg(left_side=True, atlas_hec=AtlasHec) )
    self.volumes.extend( getCrackVolumesCfg(left_side=True, tile_atlas_geometry=TileAtlasGeometry, tile_atlas_itc=TileAtlasItc,
                                            atlas_barrel_cryostat=AtlasBarrelCryostat, atlas_emec=AtlasEmec,
                                            atlas_emb_cells=AtlasEmbCells, atlas_cryostat_pieces=atlas_cryostat_pieces,
                                            tile_atlas_gap=TileAtlasGap) )
    # ATLAS gap and crack scintillators (E1-E4), active ITC (C10, D4) and the plates of the nominal extended barrel
    # (geometry/python/v1/TILE.py; F41 conserto 21). Simulation only.
    if TileAtlasGap:
      self.mixtures.update( ATLAS_TILE_GAP_MIXTURES )
      self.samplings.extend( getAtlasTileGapCfg() + getAtlasTileGapCfg(left_side=True) )
      self.volumes.extend( getAtlasTileGapVolumesCfg() + getAtlasTileGapVolumesCfg(left_side=True) )
    # Outer cylinders of the end-cap cryostats as in ATLAS (warm and cold vessels and the liquid argon between the EMEC
    # and the cold vessel; see geometry/python/v1/DeadMaterials.py). Simulation only.
    if AtlasEndcapCryostat:
      self.volumes.extend( getAtlasEndcapCryostatCfg() )
      self.volumes.extend( getAtlasEndcapCryostatCfg(left_side=True) )
    # Passive volumes of the ATLAS-like HEC: the first copper plate of each wheel and the liquid argon between the wheels.
    if AtlasHec:
      self.volumes.extend( getAtlasHecPassiveCfg() )
      self.volumes.extend( getAtlasHecPassiveCfg(left_side=True) )
    # Forward calorimeter of ATLAS as passive material, without cells (geometry/python/v1/AtlasFCal.py; F41 conserto 20).
    # Simulation only.
    # With AtlasFcalCells (needs AtlasFcal) the modules are built as in ATLAS, a tube of absorber with one liquid argon gap per
    # electrode and the cable troughs, the electrodes read from the CSV file AtlasFcalElectrodes (the table LArFCalElectrodes
    # of the ATLAS geometry database, geometry/data/LArFCalElectrodes-06.csv; F41 conserto 22).
    if AtlasFcalCells and not AtlasFcal:
      raise ValueError("AtlasFcalCells needs AtlasFcal.")
    if AtlasFcal:
      self.mixtures.update( ATLAS_FCAL_MIXTURES )
      self.volumes.extend( getAtlasFcalCfg(cells=AtlasFcalCells) )
    if AtlasFcalCells:
      if not AtlasFcalElectrodes:
        raise ValueError("AtlasFcalCells needs the file of the FCal electrodes (AtlasFcalElectrodes).")
      self.mixtures.update( ATLAS_FCAL_CELL_MATERIALS )
      self.fcal_modules = getAtlasFcalCellsCfg( AtlasFcalElectrodes )
    # Frozen showers of the ATLAS FCal (needs AtlasFcalCells; geometry/src/FCalFrozenShowerModel.h; F41 conserto 23), with the libraries
    # of the directory AtlasFcalShowerLibDir (default geometry/data/LArG4ShowerLibData/MC23_v1, those of the Athena release 23.0.14)
    if AtlasFcalFrozenShowers and not AtlasFcalCells:
      raise ValueError("AtlasFcalFrozenShowers needs AtlasFcalCells.")
    self.setProperty( "FCalFrozenShowers", AtlasFcalFrozenShowers )
    if AtlasFcalFrozenShowers:
      import os
      libdir = AtlasFcalShowerLibDir or os.path.join( os.environ.get('LORENZETTI_GEOMETRY_DATA_DIR', ''), 'LArG4ShowerLibData', 'MC23_v1' )
      self.setProperty( "FCalShowerLibDir", libdir )
    # Volumes of the ATLAS-like EMEC (radial bands and steps of the two wheels); their cells come from the samplings.
    if AtlasEmec:
      self.volumes.extend( getAtlasEmecVolumesCfg() )
      self.volumes.extend( getAtlasEmecVolumesCfg(left_side=True) )
    self.samplings = flatten(self.samplings)
    self.AtlasG4 = AtlasG4
    # With AtlasEmbCells the end-cap presampler is that of ATLAS (|z| = 3622-3626 mm, in a cavity of DM::Crack::EM, with the
    # cells of the dictionary; geometry/python/v1/ECAL.py) instead of the one of EMEC.py.
    if AtlasEmbCells:
      self.samplings = [s for s in self.samplings if s.Sampling != CaloSampling.PSE]
      self.samplings.extend( getAtlasPseCfg() + getAtlasPseCfg(left_side=True) )
    # The ATLAS Run 4 geometry of the simulation (geometry/python/v1/AtlasRun4.py; F41 conserto 27): the LAr end-cap (presampler, EMEC,
    # HEC, FCal) 45 mm further from the interaction point, where the ATLAS simulation places it, with its cells. Needs the ATLAS-like
    # end-cap and barrel options.
    self.AtlasRun4 = AtlasRun4
    if AtlasRun4:
      if not (AtlasEmec and AtlasHec and AtlasEmbCells and AtlasFcalCells and AtlasEndcapCryostat):
        raise ValueError("AtlasRun4 needs AtlasEmec, AtlasHec, AtlasEmbCells, AtlasFcalCells and AtlasEndcapCryostat.")
      from geometry.v2.AtlasRun4 import shiftLArEndcap
      shiftLArEndcap( self.volumes, self.samplings, self.fcal_modules )
      # The end-cap cryostats are those of the ATLAS geometry, imported with the inner detector and the beam pipe from the GeoModel dump
      # AtlasRun4Geometry (default: LORENZETTI_ATLAS_RUN4_GEOMETRY; geometry/scripts/atlas_run4_dumpgeo.sh writes it): the block of the
      # EM crack, the cylinders of the end-cap cryostat of AtlasEndcapCryostat and the liquid argon between the HEC wheels (the bath of the
      # cryostat, LAr::Endcap::Cryostat::EmecHecLAr, in ATLAS) leave
      self.volumes = [ v for v in self.volumes if not v.Name.startswith( ('DM::Crack::EM', 'DM::EndcapCryostat', 'DM::HEC::WheelGap') ) ]
      import os
      geometry = AtlasRun4Geometry or os.environ.get( 'LORENZETTI_ATLAS_RUN4_GEOMETRY', '' )
      if not geometry:
        raise ValueError("AtlasRun4 needs the GeoModel dump of the ATLAS geometry (AtlasRun4Geometry or LORENZETTI_ATLAS_RUN4_GEOMETRY).")
      self.setProperty( "AtlasRun4", True )
      self.setProperty( "AtlasRun4Geometry", geometry )
      # The field of the ATLAS simulation: the map of the production (default: LORENZETTI_FIELD_MAP), instead of UseSolenoidField or
      # UseMagneticField
      fieldmap = AtlasFieldMap or os.environ.get( 'LORENZETTI_FIELD_MAP', '' )
      if not fieldmap:
        raise ValueError("AtlasRun4 needs the field map of ATLAS (AtlasFieldMap or LORENZETTI_FIELD_MAP; bfieldmap_7730_20400_14m.root).")
      if UseMagneticField:
        raise ValueError("AtlasRun4 has the field of ATLAS: UseMagneticField cannot be set.")
      self.setProperty( "AtlasFieldMap", fieldmap )
    # The ATLAS material outside the calorimeters (F41 conserto 32), from the same dump: the whole MuonSys and the girders, fingers,
    # saddles and end plates of the tile calorimeter. Needs AtlasRun4.
    if AtlasForwardShielding:
      if not AtlasRun4:
        raise ValueError("AtlasForwardShielding needs AtlasRun4 (the GeoModel dump of the ATLAS geometry of the simulation).")
      self.setProperty( "AtlasForwardShielding", True )
    # The field of the ATLAS simulation as in the production (F41 conserto 33): the map in the whole world and only the muons in the field
    # inside the barrel EM calorimeter. Needs AtlasForwardShielding (outside the calorimeters there is the ATLAS material).
    if AtlasFullField:
      if not AtlasForwardShielding:
        raise ValueError("AtlasFullField needs AtlasForwardShielding (the ATLAS material outside the calorimeters).")
      self.setProperty( "AtlasFullField", True )
    # The dead material of ATLAS in the gap between the barrel and the extended barrel (F41 conserto 34), imported from the same dump instead
    # of the services of conserto 11 (DM::ITC::Services, boxes with 5% of aluminium). Needs AtlasForwardShielding.
    if AtlasBarrelGapServices:
      if not AtlasForwardShielding:
        raise ValueError("AtlasBarrelGapServices needs AtlasForwardShielding.")
      self.volumes = [ v for v in self.volumes if not v.Name.startswith( 'DM::ITC::Services' ) ]
      self.setProperty( "AtlasBarrelGapServices", True )
    # The extended barrel, ITC, gap and crack of the tile calorimeter where the ATLAS simulation of Run 4 places them (F41 conserto 35,
    # geometry/python/v1/AtlasRun4.py), with their cells. Needs AtlasRun4 and TileAtlasGap.
    if TileAtlasRun4:
      if not (AtlasRun4 and TileAtlasGap):
        raise ValueError("TileAtlasRun4 needs AtlasRun4 and TileAtlasGap.")
      from geometry.v2.AtlasRun4 import shiftTileEndcap
      shiftTileEndcap( self.volumes, self.samplings )
      self.setProperty( "TileAtlasRun4", True )
    
  
  # Geant4 settings of the ATLAS production (F41 conserto 24; Athena release 23.0.14, G4PhysicsRegionConfig.py and
  # G4GeometryToolConfig.py): the production cuts of the ATLAS regions (gamma, e-, e+; proton 1 mm everywhere): EMB (the accordion,
  # LAr::EMB::STAC) and EMEC (LAr::EMEC::Mother) 0.1 mm, FCAL (LAr::FCAL::LiquidArgonC, the modules and the argon between them) 0.03 mm,
  # everything else 1 mm (HEC, presamplers, dead material, tile: GeneralCut).
  @staticmethod
  def atlasCut( name ):
    from geometry.v2.PhysicalVolume import ProductionCuts
    if name.startswith(('LAr::EMB1', 'LAr::EMB2', 'LAr::EMB3', 'LAr::EMEC')):
      c = 0.1
    elif name.startswith(('LAr::FCAL', 'DM::FCal')):
      c = 0.03
    else:
      c = 1.0
    return ProductionCuts( GammaCut = c, ElectronCut = c, PositronCut = c, PhotonCut = 1.0 )   # PhotonCut is the proton cut

  # Lorenzetti volumes that stand for volumes of the LAr tree of the ATLAS geometry (physical volume names beginning with "LAr", where
  # the photon Russian roulette acts): the LAr calorimeters and presamplers (LAr::, the HEC FCal::HEC and DM::HEC, the argon between the
  # FCal modules DM::FCal), the barrel cryostat with its walls, solenoid (cylinders of LAr::Barrel::Cryostat in the GeoModel geometry)
  # and argon (DM::Barrel, DM::BarrelCryostat, DM::EMBEnd), the endcap cryostat (DM::EndcapCryostat, DM::Crack::EM). Not: tile, ITC.
  ATLAS_LAR_TREE = [ 'LAr::', 'FCal::HEC', 'DM::HEC', 'DM::FCal', 'DM::Barrel', 'DM::EMBEnd', 'DM::EndcapCryostat', 'DM::Crack::EM' ]

  def compile(self):
    # Create all volumes inside of the detector
    if self.AtlasG4:
      self.setProperty( "AtlasG4", True )
      self.setProperty( "LArTreeVolumes", self.ATLAS_LAR_TREE )
      # the endcap cryostat of ATLAS (LAr::Endcap::Cryostat cylinders and cones of the region DeadMaterial): the dead material shower
      dm = sorted( { pv.Name for pv in self.volumes if pv.Name.startswith('DM::EndcapCryostat') } )
      if dm: self.setProperty( "DeadMaterialVolumes", dm )
      for pv in self.volumes: pv.Cuts = self.atlasCut( pv.Name )
      for samp in self.samplings: samp.volume().Cuts = self.atlasCut( samp.volume().Name )
      for fm in self.fcal_modules: fm.Cuts = self.atlasCut( fm.Name )
    
    from ROOT.std import vector
    for name, (density, fractions) in self.mixtures.items():
      symbols = vector('string')(); values = vector('double')()
      for s, f in fractions.items(): symbols.push_back(s); values.push_back(f)
      self._core.AddMixture( name, density, symbols, values )

    volumes = [pv for pv in self.volumes]
    # The envelopes of the ATLAS-like EMEC and barrel (Envelope = True) only give the limits of their hit makers: not built.
    volumes.extend( [samp.volume() for samp in self.samplings if not getattr(samp.volume(), 'Envelope', False)] )
    # Each volume once: hit makers that share a volume (the two regions of a sampling of the ATLAS-like HEC) would build it twice, one
    # copy on top of the other (fixed in F41 conserto 27; present since conserto 15)
    unique = {}
    for pv in volumes: unique.setdefault( id(pv), pv )
    volumes = list( unique.values() )
          
    for pv in tqdm( volumes, desc="Compiling  volumes...", ncols=70):
      self._core.AddVolume( pv.Name, pv.Plates, pv.AbsorberMaterial, pv.GapMaterial, 
                             # layer
                             pv.NofLayers, 
                             pv.AbsorberThickness, 
                             pv.GapThickness,
                             pv.LayerClearance,
                             # dimensions
                             pv.RMin, pv.RMax, pv.ZSize, 
                             pv.X, pv.Y, pv.Z,
                             # production cuts
                             pv.Cuts.ElectronCut, 
                             pv.Cuts.PositronCut, 
                             pv.Cuts.GammaCut, 
                             pv.Cuts.PhotonCut
                             )
      if pv.AbsorberSplitZ > 0:
        self._core.SetAbsorberSplit( pv.Name, pv.AbsorberSplitZ, pv.AbsorberMaterial2, pv.AbsorberThickness2 )
      if pv.Plates == Plates.Polycone:
        zs = vector('double')(); r0 = vector('double')(); r1 = vector('double')()
        for z, a, b in zip(pv.ZPlanes, pv.RMinPlanes, pv.RMaxPlanes): zs.push_back(z); r0.push_back(a); r1.push_back(b)
        self._core.SetPolycone( pv.Name, zs, r0, r1 )
      if pv.InSolenoidField:
        self._core.SetInSolenoidField( pv.Name )

    # Modules of the ATLAS FCal with their electrodes (F41 conserto 22)
    def dvec( values ):
      v = vector('double')()
      for x in values: v.push_back(x)
      return v
    for fm in self.fcal_modules:
      self._core.AddFCalModule( fm.Name, fm.Absorber, fm.RodMaterial, fm.TroughMaterial,
                                fm.RMin, fm.RMax, fm.Z, fm.HalfZ, fm.GapRMin, fm.GapRMax, fm.RodR,
                                fm.TroughRMin, fm.TroughRMax, fm.TroughSPhi, fm.TroughDPhi, dvec(fm.TroughAngles),
                                dvec(fm.X), dvec(fm.Y),
                                fm.Cuts.ElectronCut, fm.Cuts.PositronCut, fm.Cuts.GammaCut, fm.Cuts.PhotonCut )

  def summary(self):

      print('Display all calorimeter samplings...')
      t = PrettyTable(["Name", "Plates", "z",'Zmin','Zmax', "Rmin", 
                       "Rmax", "abso","gap", "deta", "dphi", "EtaMin", 
                       "EtaMax", "N_bins", "Container"])
      # Add all volumes that came from a sampling detector and has a sensitive parameter
      for samp in self.samplings:
        pv = samp.volume(); sv = samp.sensitive()
        t.add_row( [pv.Name,
                    Plates.tostring(pv.Plates),pv.ZSize,pv.ZMin,pv.ZMax,pv.RMin,pv.RMax,
                    pv.AbsorberMaterial,pv.GapMaterial,
                    round(sv.DeltaEta,4) ,
                    round(sv.DeltaPhi,4) ,
                    sv.EtaMin,sv.EtaMax, 
                    len(sv.EtaBins)*len(sv.PhiBins) if sv.DeltaEta else len(sv.ZBins)*len(sv.PhiBins)  ,
                    samp.CollectionKey
                  ])
      print(t)
      print('Display all non-sensitive volumes...')
      t = PrettyTable(["Name", "Plates", "z",'Zmin','Zmax', "Rmin", 
                       "Rmax", "abso","gap"])
      # Add ither volumes that not came from a sampling detector (extra volumes only)
      for pv in self.volumes:
        t.add_row([pv.Name, Plates.tostring(pv.Plates),pv.ZSize, pv.ZMin, pv.ZMax, 
                   pv.RMin, pv.RMax, pv.AbsorberMaterial, pv.GapMaterial]) 
      print(t)

  
  
  def get_ui_commands(self) -> List[str]:

    commands = [
     "/vis/open OGL 600x600-0+0"
    ,"/vis/viewer/set/autoRefresh false"
    ,"/vis/verbose errors"
    ,"/vis/drawVolume"
    ,"/vis/viewer/set/viewpointVector 1 0 0"
    ,"/vis/viewer/set/lightsVector 1 0 0"
    ,"/vis/viewer/set/style wireframe"
    ,"/vis/viewer/set/auxiliaryEdge true"
    ,"/vis/viewer/set/lineSegmentsPerCircle 100"
    ,"/vis/scene/add/trajectories smooth"
    ,"/vis/modeling/trajectories/create/drawByCharge"
    ,"/vis/modeling/trajectories/drawByCharge-0/default/setDrawStepPts true"
    ,"/vis/modeling/trajectories/drawByCharge-0/default/setStepPtsSize 2"
    ,"/vis/scene/endOfEventAction accumulate"
    ,"/vis/geometry/set/visibility World 0 false"
    ,"#/vis/geometry/set/visibility World 0 true"
    ,"/vis/ogl/set/displayListLimit 10000000"
    ]
  
    def _add_volume_vis_commands(name, color, visualization) -> List[str]:
      vis_command = [
         f"/vis/geometry/set/colour {name} 0 {color}"
        ,f"/vis/geometry/set/colour {name}_Layer 0 {color}"
        ,f"/vis/geometry/set/colour {name}_Abso 0 {color}"
        ,f"/vis/geometry/set/colour {name}_Gap 0 {color}"
        ,f"/vis/geometry/set/visibility {name} 0 {visualization}"
        ,f"/vis/geometry/set/visibility {name}_Layer 0 {visualization}"
        ,f"/vis/geometry/set/visibility {name}_Abso 0 {visualization}"
        ,f"/vis/geometry/set/visibility {name}_Gap 0 {visualization}"
      ]
      return vis_command

    for samp in self.samplings:
      vol = samp.volume()
      if getattr(vol, 'Envelope', False): continue
      commands.extend( _add_volume_vis_commands( vol.name(), vol.Color, 'true' if vol.Visualization else 'false') )
    for vol in self.volumes:
      commands.extend( _add_volume_vis_commands( vol.name(), vol.Color, 'true' if vol.Visualization else 'false') )

    commands.extend( [
             "/vis/viewer/set/autoRefresh true"
            ,"/vis/verbose warnings"
            ])

    return commands




if __name__ == "__main__":
    atlas = DetectorConstruction_v2("ATLAS")
    atlas.summary()
    #atlas.compile()
    #pprint(atlas.create_visualization_commands())





