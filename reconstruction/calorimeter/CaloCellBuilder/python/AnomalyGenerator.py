
__all__ = ["AnomalyGenerator", "get_cells_from_brl"]


import ROOT, json
from typing import List
from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.macros import *


def get_cells_from_brl( path : str) -> List[int]:
  with open(path, 'r') as f:
    d = json.load(f)
    cells = []
    for run in d['runs']:
      if not run["DeadModules"]:
        cells.extend( run['Cells'] )
    return set(cells)
    


class AnomalyGenerator( Cpp ):


  def __init__( self, name      : str,
                BadRunListFile  : str,
                OutputLevel     : int=LoggingLevel.toC('INFO'), 
                NoiseMean       : float=0,
                NoiseStd        : float=0,
                InputEventKey   : str="Events"
              ):
                
    Cpp.__init__(self, ROOT.AnomalyGenerator(name) )
    self.setProperty( "OutputLevel"     , OutputLevel       )
    self.setProperty( "NoiseMean"       , NoiseMean         )
    self.setProperty( "NoiseStd"        , NoiseStd          )
    self.setProperty( "InputEventKey"   , InputEventKey     )

    with open(BadRunListFile, 'r') as f:
      d = json.load(f)      
      events = []
      dead_modules = []
      noise_factor = []
      cells = []
      for run in d['runs']:
        events.append( [run['StartEventNumber'], run['EndEventNumber']] ) 
        dead_modules.append( run['DeadModules'] )
        noise_factor.append( run['NoiseStdFactor'] ) 
        cells.append( run['Cells'] )
          
      self.setProperty( "DeadModules"       , dead_modules )
      self.setProperty( "Cells"             , cells        )
      self.setProperty( "NoiseStdFactor"    , noise_factor )
      self.setProperty( "EventNumberRange"  , events       )

 