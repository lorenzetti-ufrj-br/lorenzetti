

__all__ = ["CaloHitMaker"]


from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.macros import *
import ROOT


class CaloHitMaker( Cpp ):


  def __init__( self, name, sampling,
                OutputCollectionKey  : str    = "Hits",
                OutputLevel          : int    = LoggingLevel.toC('INFO'),
                DetailedHistograms   : bool   = False,
                HistogramPath        : str    = "/CaloHitMaker",
                SamplingNoiseStd     : float  = 0,
                ActiveEnergyOnly     : bool   = False,
                BirksLaw             : bool   = False,
                AtlasHitTime         : bool   = False,
                TileDualReadout      : int    = 0,
                FreeRunningHits      : bool   = False,
                FreeRunningListKey   : str    = "FreeRunningHits",
                FreeRunningBinning   : bool   = True,
                EmecChargeCollection : bool   = False,
                EmecChargeTables     : str    = "",
                EmecChargeFieldMap   : str    = "",
                EmecChargeHVMap      : str    = "",
              ):
                    
    Cpp.__init__(self, ROOT.CaloHitMaker(name) )
    self.Tools = []
    self.setProperty( "OutputCollectionKey"     , OutputCollectionKey         )
    self.setProperty( "EtaBins"                 , sampling.sensitive().EtaBins)
    self.setProperty( "PhiBins"                 , sampling.sensitive().PhiBins)
    self.setProperty( "RMin"                    , sampling.volume().RMin      )
    self.setProperty( "RMax"                    , sampling.volume().RMax      )
    self.setProperty( "ZMin"                    , sampling.volume().ZMin      )
    self.setProperty( "ZMax"                    , sampling.volume().ZMax      )
    self.setProperty( "Sampling"                , sampling.Sampling           )
    self.setProperty( "Segment"                 , sampling.sensitive().Segment)
    self.setProperty( "Detector"                , sampling.Detector           )
    self.setProperty( "BunchIdStart"            , sampling.BunchIdStart       )
    self.setProperty( "BunchIdEnd"              , sampling.BunchIdEnd         )
    self.setProperty( "BunchDuration"           , 25                          )
    self.setProperty( "SamplingNoiseStd"        , SamplingNoiseStd            )
    # Keep only the energy deposited in the active medium (liquid argon, scintillator)
    self.setProperty( "ActiveEnergyOnly"        , ActiveEnergyOnly            )
    # Apply Birks' law in the scintillator and in the liquid argon (ATLAS constants)
    self.setProperty( "BirksLaw"                , BirksLaw                    )
    # Bunch crossing of the hits from the time of the ATLAS simulation (time of flight from the interaction point taken out)
    self.setProperty( "AtlasHitTime"            , AtlasHitTime                )
    # Dual readout of the tile cells (two PMTs per cell): 0 = off, 1 = ATLAS U-shape, 2 = linear sharing
    self.setProperty( "TileDualReadout"         , TileDualReadout             )
    # Free-running hits (simu_trf.py --free-running-hits): every deposit of the ATLAS cells also goes to a list written in the
    # layout of the ATLAS HITS ntuple (CaloFreeRunningHitWriter), per PMT in the tile and per cell in the LAr and the FCal; with
    # FreeRunningBinning the deposits are summed in the time bins of the ATLAS simulation (TileSimHit, LArG4SimpleSD).
    self.setProperty( "FreeRunningHits"         , FreeRunningHits             )
    self.setProperty( "FreeRunningListKey"      , FreeRunningListKey          )
    self.setProperty( "FreeRunningBinning"      , FreeRunningBinning          )
    # Cells given as (r, z) boxes instead of the eta x phi grid (ATLAS tile cells, geometry/python/v1/TILE.py).
    # Without them (the default) the properties stay empty and the eta x phi grid is used. Only set when present:
    # setProperty cannot convert an empty list.
    cells = getattr( sampling.sensitive(), "Cells", None )
    if cells:
      self.setProperty( "CellEta"               , [float(x) for x in cells["Eta"]]      )
      self.setProperty( "CellDeltaEta"          , [float(x) for x in cells["DeltaEta"]] )
      if "BoxRMin" in cells:
        self.setProperty( "CellBoxRMin"         , [float(x) for x in cells["BoxRMin"]]  )
        self.setProperty( "CellBoxRMax"         , [float(x) for x in cells["BoxRMax"]]  )
        self.setProperty( "CellBoxZMin"         , [float(x) for x in cells["BoxZMin"]]  )
        self.setProperty( "CellBoxZMax"         , [float(x) for x in cells["BoxZMax"]]  )
        self.setProperty( "CellBoxIndex"        , [int(x) for x in cells["BoxCell"]]    )
      # ATLAS-like EM end-cap (geometry/python/v1/EMEC.py): the compartment of this maker, its eta index, the tables
      # of the compartment boundaries and the volumes of its wheel (see CaloHitMaker::emecFindCell)
      if "EmecCompartment" in cells:
        self.setProperty( "EmecCompartment"     , int(cells["EmecCompartment"])           )
        self.setProperty( "EmecEtaScale"        , float(cells["EmecEtaScale"])            )
        self.setProperty( "EmecEtaOffset"       , float(cells["EmecEtaOffset"])           )
        self.setProperty( "EmecMaxEta"          , int(cells["EmecMaxEta"])                )
        self.setProperty( "EmecFocalShift"      , float(cells["EmecFocalShift"])          )
        for key in ("EmecZSep12", "EmecZSep23", "EmecZInner"):   # integers, 1e-4 cm
          self.setProperty( key                 , [int(x) for x in cells[key]]             )
        for key in ("EmecWheelRMin", "EmecWheelRMax", "EmecWheelZMin", "EmecWheelZMax"):
          self.setProperty( key                 , [float(x) for x in cells[key]]           )
        # charge collection of the ATLAS EM end-cap (simu_trf.py --atlas-emec-charge-collection; F41 conserto 29)
        if EmecChargeCollection:
          self.setProperty( "EmecChargeCollection", True                                  )
          self.setProperty( "EmecChargeTables"    , EmecChargeTables                      )
          self.setProperty( "EmecChargeFieldMap"  , EmecChargeFieldMap                    )
          self.setProperty( "EmecChargeHVMap"     , EmecChargeHVMap                       )
      # ATLAS-like barrel EM (geometry/python/v1/ECAL.py): sampling and region of the dictionary read by this maker
      # (see CaloHitMaker::embFindCell)
      if "EmbSampling" in cells:
        self.setProperty( "EmbMode"             , int(cells["EmbMode"])                   )
        self.setProperty( "EmbSampling"         , int(cells["EmbSampling"])               )
        self.setProperty( "EmbRegion"           , int(cells["EmbRegion"])                 )
        # end-cap presampler moved with the ATLAS end-cap of the simulation (--atlas-run4; F41 conserto 27)
        if "EmbZShift" in cells:
          self.setProperty( "EmbZShift"         , float(cells["EmbZShift"])               )
      # ATLAS-like barrel EM with the sampling boundaries and rules of the ATLAS simulation (F41 conserto 18)
      if "EmbSampSeg" in cells:
        self.setProperty( "EmbSampSeg"          , bool(cells["EmbSampSeg"])               )
      # ATLAS-like barrel presampler, cell from the gap of the electrode (EmbMode = 3): radius of the middle of the active layer
      if "PsbR0" in cells:
        self.setProperty( "PsbR0"               , float(cells["PsbR0"])                   )
      # radius on the axis of the module (ATLAS-like HEC, geometry/python/v1/HEC.py); absent: r
      if "RadiusModules" in cells:
        self.setProperty( "CellRadiusModules"   , int(cells["RadiusModules"])           )
      # ATLAS-like LAr cells (F41 conserto 19): fields of the ATLAS identifier of this maker and the dictionary eta index
      # of each cell; part and barrel_ec choose the point of the step for the ATLAS time (CaloHitMaker::larHitTime), and all of
      # them give the identifier of the free-running hits (CaloHitMaker::freeRunningLAr)
      if "AtlasLArPart" in cells:
        self.setProperty( "AtlasLArPart"        , int(cells["AtlasLArPart"])              )
        self.setProperty( "AtlasBarrelEc"       , int(cells["AtlasBarrelEc"])             )
        self.setProperty( "AtlasLArSampling"    , int(cells["AtlasLArSampling"])          )
        self.setProperty( "AtlasLArRegion"      , int(cells["AtlasLArRegion"])            )
        self.setProperty( "CellAtlasEtaIndex"   , [int(x) for x in cells["AtlasEtaIndex"]] )
      # ATLAS gap and ITC cells (F41 conserto 21; geometry/python/v1/TILE.py, getAtlasTileGapCfg)
      if "NPmt" in cells:
        self.setProperty( "CellNPmt"            , [int(x) for x in cells["NPmt"]]          )
      if "UShapePart" in cells:
        self.setProperty( "UShapePart"          , int(cells["UShapePart"])                )
        self.setProperty( "UShapeLayer"         , int(cells["UShapeLayer"])               )
      if "SpecialModule" in cells:
        self.setProperty( "SpecialModule"       , [int(x) for x in cells["SpecialModule"]] )
        self.setProperty( "SpecialNPmt"         , [int(x) for x in cells["SpecialNPmt"]]   )
      if "ReplaceSection" in cells:
        self.setProperty( "ReplaceSection"      , int(cells["ReplaceSection"])            )
        self.setProperty( "ReplaceTower"        , int(cells["ReplaceTower"])              )
        self.setProperty( "ReplaceSampling"     , int(cells["ReplaceSampling"])           )
        self.setProperty( "ReplaceRCentre"      , float(cells["ReplaceRCentre"])          )
        self.setProperty( "ReplaceZCentre"      , float(cells["ReplaceZCentre"])          )
      if "ReplaceCollectionKey" in cells:
        self.setProperty( "ReplaceCollectionKey", str(cells["ReplaceCollectionKey"])      )
        self.setProperty( "ReplaceHashBase"     , int(cells["ReplaceHashBase"])           )
      # ATLAS identifier fields (free-running hits) and (r, z) centre (ATLAS time, CaloHitMaker::tileTime) of each ATLAS tile cell
      if "AtlasSection" in cells:
        self.setProperty( "CellAtlasSection"    , [int(x) for x in cells["AtlasSection"]]  )
        self.setProperty( "CellAtlasTower"      , [int(x) for x in cells["AtlasTower"]]    )
        self.setProperty( "CellAtlasSampling"   , [int(x) for x in cells["AtlasSampling"]] )
        self.setProperty( "CellRCentre"         , [float(x) for x in cells["RCentre"]]     )
        self.setProperty( "CellZCentre"         , [float(x) for x in cells["ZCentre"]]     )
    # Half-absorber shift of the phi edges of the ATLAS-like LAr cells (already in PhiBins) and the Birks constant of the
    # liquid argon of this sampling (0.0486 in the HEC); absent: 0 and 0.05832 (F41 conserto 19)
    phi_shift = getattr( sampling.sensitive(), "PhiShift", None )
    if phi_shift:
      self.setProperty( "PhiShift"              , float(phi_shift)            )
    # ATLAS FCal with its electrodes (F41 conserto 22; geometry/python/v1/FCAL.py): module, side, logical volume of the gaps
    # and the cell and tile centre of each copy number (CaloHitMaker::fcalStep)
    fcal_module = getattr( sampling, "Module", None )
    if fcal_module:
      self.setProperty( "FCalModule"            , int(fcal_module)                         )
      self.setProperty( "FCalSide"              , int(sampling.Side)                       )
      self.setProperty( "FCalGapVolume"         , sampling.GapVolume                       )
      self.setProperty( "FCalCopyEtaIndex"      , [int(x) for x in sampling.CopyEtaIndex]  )
      self.setProperty( "FCalCopyPhiIndex"      , [int(x) for x in sampling.CopyPhiIndex]  )
      self.setProperty( "FCalCopyEta"           , [float(x) for x in sampling.CopyEta]     )
      self.setProperty( "FCalCopyPhi"           , [float(x) for x in sampling.CopyPhi]     )
      self.setProperty( "FCalCopyDeltaEta"      , [float(x) for x in sampling.CopyDeltaEta] )
      self.setProperty( "FCalCopyDeltaPhi"      , [float(x) for x in sampling.CopyDeltaPhi] )
      # grid indices and position of each electrode, for the spots of the frozen showers (F41 conserto 23)
      self.setProperty( "FCalCopyI"             , [int(x) for x in sampling.CopyI]         )
      self.setProperty( "FCalCopyJ"             , [int(x) for x in sampling.CopyJ]         )
      self.setProperty( "FCalCopyX"             , [float(x) for x in sampling.X]           )
      self.setProperty( "FCalCopyY"             , [float(x) for x in sampling.Y]           )
    birks_k = getattr( sampling.sensitive(), "BirksLArK", None )
    if birks_k:
      self.setProperty( "BirksLArK"             , float(birks_k)              )
    self.setProperty( "DetailedHistograms"      , DetailedHistograms          )
    self.setProperty( "HistogramPath"           , HistogramPath               )
    self.setProperty( "OutputLevel"             , OutputLevel                 )

 

  def core(self):
    # Attach all tools before return the core
    for tool in self.Tools:
      self._core.push_back(tool.core())
    return self._core


  def __add__( self, tool ):
    self.Tools += tool
    return self
  

