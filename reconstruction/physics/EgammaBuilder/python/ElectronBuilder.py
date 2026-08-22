__all__ = ['ElectronBuilderCfg']

import ROOT
from GaugiKernel import Configurable


def getIsEMCuts( wpname : str) -> list[float]:
		
    etHadCut = {
      'loose'  : [0.1218],
			'medium' : [0.0270375],
			'tight'  : [0.0270375],
			'vloose' : [0.157]
    }
	    
		rEtaCut = {
      'loose'  : [0.57],
	    'medium' : [0.814625],
	    'tight'  : [0.83125],
	    'vloose' : [0.752]
    }

		eRatioCut = {
      'loose'  : [0.47],  	
      'medium' : [0.57],
      'tight'  : [0.65],
      'vloose' : [0.52]
    }
	
		return [etHadCut[wpname],rEtaCut[wpname],eRatioCut[wpname]]
		


def ElectronBuilderCfg( name             : str, 
                        InputClusterKey  : str,
                        OutputElectronKey: str,
                        OutputLevel      : int=0, 
                      ) -> Configurable:

  return Configurable( 
    ROOT.ElectronMaker,
    name,
    InputClusterKey    = InputClusterKey, 
    OutputElectronKey  = OutputElectronKey,
    OutputLevel        = OutputLevel,
    # central cuts
    TightCuts          = getIsEMCuts('tight'),
    MediumCuts         = getIsEMCuts('medium'),
    LooseCuts          = getIsEMCuts('loose'),
    VLooseCuts         = getIsEMCuts('vloose'),
    # forward cuts
    SecondLambdaCuts     = [4500,4500,2800],
    LateralMomCuts       = [0.69,0.64,0.64],
    LongMomCuts          = [0.55,0.29,0.24],
    FracMaxCuts          = [0.22,0.23,0.39],
    SecondRCuts          = [3900,3300,3000],
    LambdaCenterCuts     = [255,255,250]
  )


