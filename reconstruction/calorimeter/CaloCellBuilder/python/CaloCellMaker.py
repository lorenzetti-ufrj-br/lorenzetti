

__all__ = ["CaloCellMaker"]


from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.macros import *
import ROOT


class CaloCellMaker( Cpp ):

  def __init__( self, name, sampling, 
                InputHitsKey        : str="Hits",
                OutputCollectionKey : str="Collection",
                OutputLevel         : int=LoggingLevel.toC('INFO'),
                DetailedHistograms  : bool=False,
                HistogramPath       : str="/Hists/Cells" ): 

    Cpp.__init__(self, ROOT.CaloCellMaker(name) )
    self.Tools = []
    self.PulseGenerator = None

    self.setProperty( "InputHitsKey"            , InputHitsKey                )
    self.setProperty( "OutputCollectionKey"     , OutputCollectionKey         )
    self.setProperty( "EtaBins"                 , sampling.sensitive().EtaBins)
    self.setProperty( "PhiBins"                 , sampling.sensitive().PhiBins)
    self.setProperty( "ZMin"                    , sampling.volume().ZMin      )
    self.setProperty( "ZMax"                    , sampling.volume().ZMax      )
    self.setProperty( "Z"                       , sampling.sv.pv.Z            )
    self.setProperty( "Sampling"                , sampling.Sampling           )
    self.setProperty( "Segment"                 , sampling.sensitive().Segment)
    self.setProperty( "Detector"                , sampling.Detector           )
    # Cells given by a table (ATLAS-like HEC, geometry/python/v1/HEC.py): the eta and delta eta of each cell, in the
    # order of the hits. Only set when present (setProperty cannot convert an empty list); without them, the grid.
    cells = getattr( sampling.sensitive(), "Cells", None )
    if cells:
      self.setProperty( "CellEta"               , [float(x) for x in cells["Eta"]]      )
      self.setProperty( "CellDeltaEta"          , [float(x) for x in cells["DeltaEta"]] )
    # Cells given one by one (the ATLAS FCal, geometry/python/v2/FCAL.py): local hash, centre and widths of each cell
    tiles = getattr( sampling, "Tiles", None )
    if tiles:
      self.setProperty( "CellBin"               , [int(x) for x in tiles["Bin"]]        )
      self.setProperty( "CellEta"               , [float(x) for x in tiles["Eta"]]      )
      self.setProperty( "CellPhi"               , [float(x) for x in tiles["Phi"]]      )
      self.setProperty( "CellDeltaEta"          , [float(x) for x in tiles["DeltaEta"]] )
      self.setProperty( "CellDeltaPhi"          , [float(x) for x in tiles["DeltaPhi"]] )
    self.setProperty( "BunchIdStart"            , sampling.BunchIdStart       )
    self.setProperty( "BunchIdEnd"              , sampling.BunchIdEnd         )
    self.setProperty( "BunchDuration"           , 25                          )
    self.setProperty( "DetailedHistograms"      , DetailedHistograms          )
    self.setProperty( "HistogramPath"           , HistogramPath               )
    self.setProperty( "OutputLevel"             , OutputLevel                 )


  def core(self):
    # Attach all tools before return the core
    for tool in self.Tools:
      self._core.push_back(tool.core())
    self._core.setPulseGenerator(self.PulseGenerator.core())
    return self._core


  def __add__( self, tool ):
    self.Tools += tool
    return self
  

