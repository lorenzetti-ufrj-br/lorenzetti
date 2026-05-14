__all__ = ["RootStreamNtupleMaker"]

from GaugiKernel import Cpp
from GaugiKernel.macros import *
import ROOT

class RootStreamNtupleMaker( Cpp ):

  def __init__( self, name,
                InputEventKey    : str,
                InputTruthKey    : str,
                InputSeedsKey    : str,
                InputClusterKey  : str,
                InputRingerKey   : str,
                InputRingerL0Key : str,
                InputTruthClusterKey : str,
                InputTruthRingerKey  : str,
                InputTruthElectronKey : str,
                InputElectronKey : str,
                OutputLevel      : int=0, 
                OutputNtupleName : str="events",
              ): 
    
    Cpp.__init__(self, ROOT.RootStreamNtupleMaker(name))
    self.setProperty( "InputEventKey"   , InputEventKey   )
    self.setProperty( "InputTruthKey"   , InputTruthKey   )
    self.setProperty( "InputSeedsKey"   , InputSeedsKey   )
    self.setProperty( "InputClusterKey" , InputClusterKey )
    self.setProperty( "InputRingerKey"  , InputRingerKey  )
    self.setProperty( "InputRingerL0Key", InputRingerL0Key)
    self.setProperty( "InputTruthClusterKey" , InputTruthClusterKey )
    self.setProperty( "InputTruthRingerKey"  , InputTruthRingerKey  )
    self.setProperty( "InputTruthElectronKey", InputTruthElectronKey)
    self.setProperty( "InputElectronKey", InputElectronKey)
    self.setProperty( "OutputNtupleName", OutputNtupleName)
    self.setProperty( "OutputLevel"     , OutputLevel     )

  

