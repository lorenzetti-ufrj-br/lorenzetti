/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
#include "AtlasDeadMaterialShower.h"

#include "G4FastTrack.hh"
#include "G4FastStep.hh"
#include "G4Track.hh"
#include "G4Electron.hh"
#include "G4Positron.hh"
#include "G4PionPlus.hh"
#include "G4PionMinus.hh"
#include "G4Gamma.hh"
#include "G4Neutron.hh"
#include "G4MuonPlus.hh"
#include "G4MuonMinus.hh"
#include <cmath>

// See AtlasDeadMaterialShower.h; DeadMaterialShower.cxx of the Athena release 23.0.14.

AtlasDeadMaterialShower::AtlasDeadMaterialShower( const std::string &name, G4Region *region, double highEnergy, double lowEnergy,
                                                  double zCutoff )
  : G4VFastSimulationModel( name, region ), m_highEnergy( highEnergy ), m_lowEnergy( lowEnergy ), m_zCutoff( zCutoff )
{}

G4bool AtlasDeadMaterialShower::IsApplicable( const G4ParticleDefinition &p )
{
  return &p == G4Electron::ElectronDefinition() || &p == G4Positron::PositronDefinition() || &p == G4PionPlus::PionPlusDefinition() ||
         &p == G4PionMinus::PionMinusDefinition() || &p == G4Gamma::GammaDefinition() || &p == G4Neutron::NeutronDefinition();
}

G4bool AtlasDeadMaterialShower::ModelTrigger( const G4FastTrack &fastTrack )
{
  const G4Track *track = fastTrack.GetPrimaryTrack();
  if( std::fabs( track->GetPosition().z() ) < m_zCutoff ){
    return track->GetKineticEnergy() < m_lowEnergy &&
           ( track->GetDefinition() == G4Electron::Definition() || track->GetDefinition() == G4Positron::Definition() );
  }
  if( track->GetKineticEnergy() > m_highEnergy || track->GetDefinition() == G4MuonPlus::Definition() ||
      track->GetDefinition() == G4MuonMinus::Definition() ) return false;
  return true;
}

void AtlasDeadMaterialShower::DoIt( const G4FastTrack&, G4FastStep &fastStep )
{
  fastStep.KillPrimaryTrack();
  fastStep.SetPrimaryTrackPathLength( 0.0 );
}
