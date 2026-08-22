
from traitlets.config.configurable import Configurable
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
    

def PulsePerturberCfg( 
  name      : str,
  BadRunListFile  : str,
  OutputLevel     : int=LoggingLevel.toC('INFO'), 
  NoiseMean       : float=0,
  NoiseStd        : float=0,
  InputEventKey   : str="Events"
  ) -> Configurable:

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

      return Configurable(
        ROOT.PulsePerturber,
        name,
        OutputLevel=OutputLevel,
        NoiseMean=NoiseMean,
        NoiseStd=NoiseStd,
        InputEventKey=InputEventKey,
        DeadModules=dead_modules,
        Cells=cells,
        NoiseStdFactor=noise_factor,
        EventNumberRange=events
      )
