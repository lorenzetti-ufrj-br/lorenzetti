
__all__ = ["CaloFreeRunningHitWriter"]

from GaugiKernel import Cpp, LoggingLevel
import ROOT


class CaloFreeRunningHitWriter( Cpp ):
  """
  Writes the per-event free-running hit list as a flat ntuple with the layout of
  the ATLAS HITS ntuple (EventNumber, TileCalHit_*, LArHitEMB_*, LArHitEMEC_*,
  LArHitHEC_*, LArHitFCAL_*). One entry per event: the tile hits per PMT and the LAr and FCal hits per cell (and per time bin).
  """

  def __init__( self, name,
                InputListKey  : str = "FreeRunningHits",
                InputEventKey : str = "Events",
                NtupleName    : str = "CollectionTree",
                OutputLevel   : int = LoggingLevel.toC('INFO'),
                AtlasFormat   : bool = False,
              ):

    Cpp.__init__(self, ROOT.CaloFreeRunningHitWriter(name) )
    self.setProperty( "InputListKey"  , InputListKey  )
    self.setProperty( "InputEventKey" , InputEventKey )
    self.setProperty( "NtupleName"    , NtupleName    )
    self.setProperty( "OutputLevel"   , OutputLevel   )
    # format of the ATLAS HITS ntuple: LAr compressed and filtered as FilterHit_tf (with its layer defects), no tglobal (F41 conserto 25)
    self.setProperty( "AtlasFormat"   , AtlasFormat   )
