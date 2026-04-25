__all__ = ["RootStreamESDMaker"]

from GaugiKernel import Cpp
from GaugiKernel.macros import *
from RootStreamBuilder import RootStreamESDFlags as flags
import ROOT

class RootStreamESDMaker( Cpp ):

  def __init__( self, name,
                InputEventKey       : str,
                InputTruthKey       : str,
                InputCellsKey       : str,
                InputSeedsKey       : str,
                InputCellsTruthKey  : str,
                OutputEventKey      : str=None,
                OutputTruthKey      : str=None,
                OutputCellsKey      : str=None,
                OutputSeedsKey      : str=None,
                OutputCellsTruthKey : str=None,
                OutputLevel         : int=0, 
                NtupleName          : str="CollectionTree",
                EtaWindow           : float=flags.EtaWindow,
                PhiWindow           : float=flags.PhiWindow,
              ): 
    """
    @brief Algorithm to stream ESD Data to a ROOT file.

    ESD contains detailed information including all Calorimeter Cells,
    which makes it larger than AOD but necessary for full reconstruction study.
    This algo serializes the Event Context into a TTree.

    Properties:
    - InputEventKey: Key for the EventInfo container.
    - InputTruthKey: Key for the TruthParticle container.
    - InputCellsKey: Key for the CaloCell container.
    - InputSeedsKey: Key for the Seed container.
    - InputCellsTruthKey: Key for the CaloCellTruth container.
    - OutputEventKey: Key for the EventInfo container.
    - OutputTruthKey: Key for the TruthParticle container.
    - OutputCellsKey: Key for the CaloCell container.
    - OutputSeedsKey: Key for the Seed container.
    - OutputCellsTruthKey: Key for the CaloCellTruth container.
    - OutputLevel: Level of the output messages.
    - NtupleName: Name of the TTree.
    - EtaWindow: Eta window for the RoI.
    - PhiWindow: Phi window for the RoI.

    """
    Cpp.__init__(self, ROOT.RootStreamESDMaker(name))
    self.setProperty( "InputEventKey"       , InputEventKey                                                       )
    self.setProperty( "InputTruthKey"       , InputTruthKey                                                       )
    self.setProperty( "InputCellsKey"       , InputCellsKey                                                       )
    self.setProperty( "InputSeedsKey"       , InputSeedsKey                                                       )
    self.setProperty( "InputCellsTruthKey"  , InputCellsTruthKey                                                  )
    self.setProperty( "OutputEventKey"      , OutputEventKey if OutputEventKey else InputEventKey                 )
    self.setProperty( "OutputTruthKey"      , OutputTruthKey if OutputTruthKey else InputTruthKey                 )
    self.setProperty( "OutputCellsKey"      , OutputCellsKey if OutputCellsKey else InputCellsKey                 )
    self.setProperty( "OutputSeedsKey"      , OutputSeedsKey if OutputSeedsKey else InputSeedsKey                 )
    self.setProperty( "OutputCellsTruthKey" , OutputCellsTruthKey if OutputCellsTruthKey else InputCellsTruthKey  )
    self.setProperty( "OutputLevel"         , OutputLevel                                                         ) 
    self.setProperty( "NtupleName"          , NtupleName                                                          )
    self.setProperty( "EtaWindow"           , EtaWindow                                                           )
    self.setProperty( "PhiWindow"           , PhiWindow                                                           )

