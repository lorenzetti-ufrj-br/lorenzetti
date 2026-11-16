/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Utilities/G4FastSimulation/src/SimpleFastKiller.h) for --atlas-run4
// (F41 conserto 27): the fast simulation model of the region BeampipeFwdCut (Sim.BeamPipeSimMode = FastSim, set by the PhaseII campaign);
// changes: the constructor also takes the region (G4VFastSimulationModel(name, region)), as the Lorenzetti models are created.

#ifndef SimpleFastKiller_h
#define SimpleFastKiller_h

#include "G4VFastSimulationModel.hh"

class SimpleFastKiller : public G4VFastSimulationModel
{
  public:
    SimpleFastKiller( const std::string &name, G4Region *region );
    ~SimpleFastKiller() {}
    G4bool IsApplicable( const G4ParticleDefinition & ) override final { return true; }
    G4bool ModelTrigger( const G4FastTrack & ) override final { return true; }
    void DoIt( const G4FastTrack &, G4FastStep & ) override final;
};

#endif
