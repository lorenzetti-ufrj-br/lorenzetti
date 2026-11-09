/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Utilities/G4FastSimulation/src/SimpleFastKiller.cxx) for --atlas-run4
// (F41 conserto 27); changes: the constructor takes the region.

#include "SimpleFastKiller.h"
#include "G4FastStep.hh"

SimpleFastKiller::SimpleFastKiller( const std::string &name, G4Region *region )
  : G4VFastSimulationModel( name, region )
{
}

void SimpleFastKiller::DoIt( const G4FastTrack &, G4FastStep &fastStep )
{
  fastStep.KillPrimaryTrack();
  fastStep.SetPrimaryTrackPathLength(0.0);
}
