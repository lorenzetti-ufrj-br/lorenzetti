__all__ = ["Pileup"]

from GaugiKernel import Cpp
from GaugiKernel.macros import *
from ROOT import generator


class Pileup( Cpp ):

  __allow_keys = [
                "EtaMax",
                "PileupAvg",
                "PileupSigma",
                "PileupPerBunch",
                "BunchIdStart",
                "BunchIdEnd",
                "Select",
                "DeltaEta",
                "DeltaPhi",
                "PtMinCharged",
                "PtMinNeutral",
                "VertexSigmaZ",
                "VertexSigmaT",
                "OutputLevel",
                ]

  def __init__( self, name, gen, 
                EtaMax         : float=1.4,
                PileupAvg      : float=0,
                PileupSigma    : float=0,
                PileupPerBunch : float=-1,
                BunchIdStart   : int=-8,
                BunchIdEnd     : int=7,
                Select         : int=2,
                DeltaEta       : float=0.22,
                DeltaPhi       : float=0.22,
                PtMinCharged   : float=0.7,
                PtMinNeutral   : float=0.05,
                VertexSigmaZ   : float=56,
                VertexSigmaT   : float=200,
                OutputLevel    : int=0
              ): 
    
    Cpp.__init__(self, generator.Pileup(name, gen.core()))
    self.__gen = gen

    self.setProperty( "EtaMax"        , EtaMax         )
    self.setProperty( "PileupAvg"     , PileupAvg      )
    self.setProperty( "PileupSigma"   , PileupSigma    )
    self.setProperty( "PileupPerBunch", PileupPerBunch )
    self.setProperty( "BunchIdStart"  , BunchIdStart   )
    self.setProperty( "BunchIdEnd"    , BunchIdEnd     )
    self.setProperty( "Select"        , Select         )
    self.setProperty( "DeltaEta"      , DeltaEta       )
    self.setProperty( "DeltaPhi"      , DeltaPhi       )
    # Minimum pT (GeV) of the particles passed to the simulation. The charged cut stands in
    # for the solenoid field when it is not simulated; use 0 for both when the field is on.
    self.setProperty( "PtMinCharged"  , PtMinCharged   )
    self.setProperty( "PtMinNeutral"  , PtMinNeutral   )
    # Gaussian spread of each collision vertex along the beam (VertexSigmaZ, in mm) and in
    # time (VertexSigmaT, in ps). The C++ properties Sigma_z and Sigma_t are both in mm
    # (Sigma_t is c times the time spread), so the time is converted here.
    self.setProperty( "Sigma_z"       , VertexSigmaZ   )
    self.setProperty( "Sigma_t"       , VertexSigmaT * 1e-12 * 299792458.0 * 1e3 )


  def gun(self):
    return self.__gen


