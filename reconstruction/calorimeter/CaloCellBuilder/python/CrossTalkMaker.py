__all__ = ["CrossTalkMaker"]

from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.macros import *
from CaloCellBuilder import CrossTalkFlags as flags
import ROOT

class CrossTalkMaker( Cpp ):

  def __init__( self, name          : str, 
                InputCollectionKey  : str="Cells",
                OutputCollectionKey : str="XTCells",
                MinEnergy           : float=flags.MinEnergy,
                AmpCapacitive       : float=flags.AmpCapacitive,
                AmpInductive        : float=flags.AmpInductive,
                AmpResistive        : float=flags.AmpResistive,
                HistogramPath       : str="/CrossTalkMaker",
                OutputLevel         : int=LoggingLevel.toC('INFO'),
                ):

    Cpp.__init__(self, ROOT.CrossTalkMaker(name) )
    self.Tools = []
    self.setProperty( "OutputLevel"           , OutputLevel         )
    self.setProperty( "InputCollectionKey"    , InputCollectionKey  )
    self.setProperty( "OutputCollectionKey"   , OutputCollectionKey )
    self.setProperty( "MinEnergy"             , MinEnergy           )
    self.setProperty( "AmpCapacitive"         , AmpCapacitive       )
    self.setProperty( "AmpInductive"          , AmpInductive        )
    self.setProperty( "AmpResistive"          , AmpResistive        )
    self.setProperty( "HistogramPath"         , HistogramPath       )

 
  def core(self):
    # Attach all tools before return the core
    for tool in self.Tools:
      self._core.push_back(tool.core())
    return self._core


  def __add__( self, tool ):
    self.Tools += tool
    return self
