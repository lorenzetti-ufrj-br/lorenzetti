
__all__ = ["AnomalyGenerator", "get_cells_with_defects"]


import ROOT, json
from typing import List
from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.macros import *
from RootStreamBuilder import RootStreamESDFlags as flags


def get_cells_with_defects( path : str) -> List[int]:
  with open(path, 'r') as f:
    d = json.load(f)
    cells = []
    for run in d['runs']:
      cells.extend( run['cells'] )
    return set(cells)
    


class AnomalyGenerator( Cpp ):


  def __init__( self, name      : str,
                BadRunListFile  : str,
                OutputLevel     : int=LoggingLevel.toC('INFO'), 
                NoiseMean       : float=0,
                NoiseStd        : float=0,
                DeadModules     : bool=False,
              ):
                
    Cpp.__init__(self, ROOT.AnomalyGenerator(name) )
    self.setProperty( "OutputLevel"     , OutputLevel       )
    self.setProperty( "NoiseMean"       , NoiseMean         )
    self.setProperty( "NoiseStd"        , NoiseStd          )
    self.setProperty( "DeadModules"     , DeadModules       )
   
    with open(BadRunListFile, 'r') as f:
      d = json.load(f)
      
      events = []
      modules = []
      noise_factor = []
      for run in d['runs']:
        events.append( [run['StartEventNumber'], run['EndEventNumber']] ) 
        modules.append( run['Modules'] )
        noise_factor.append( run['NoiseFactor'] ) 
          

    self.setProperty( "Modules"         , cellHash        )
    self.setProperty( "NoiseFactor"     , noiseFactor     )
    self.setProperty( "Events"          , noisyEvents     )

 
     