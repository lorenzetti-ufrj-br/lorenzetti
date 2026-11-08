/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
#include "FCalFrozenShowerModel.h"

#include "G4FastTrack.hh"
#include "G4FastStep.hh"
#include "G4Track.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4Electron.hh"
#include "G4Gamma.hh"
#include "G4Neutron.hh"
#include "G4EventManager.hh"
#include "G4UserSteppingAction.hh"
#include "G4VSolid.hh"
#include "G4AffineTransform.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4AutoLock.hh"
#include "Randomize.hh"
#include "G4RandomTools.hh"
#include <stdexcept>

// See FCalFrozenShowerModel.h. Line references are to LArFastShower.cxx and LArG4ShowerLibSvc.cxx of the Athena release 23.0.14.

namespace { G4Mutex libMutex = G4MUTEX_INITIALIZER; }

std::map<std::string, std::map<int, std::shared_ptr<const FCalShowerLib>>> FCalFrozenShowerModel::loadLibraries( const std::string &dir )
{
  static std::map<std::string, std::map<std::string, std::map<int, std::shared_ptr<const FCalShowerLib>>>> cache;
  G4AutoLock lock( &libMutex );
  auto it = cache.find( dir );
  if( it != cache.end() ) return it->second;
  std::map<std::string, std::map<int, std::shared_ptr<const FCalShowerLib>>> out;
  for( const char *det : {"FCAL1", "FCAL2"} ){
    for( int pdg : {11, 22, 2112} ){
      const std::string file = dir + "/LArG4ShowerLib." + det + "." + std::to_string(pdg) + ".root";
      auto lib = std::make_shared<const FCalShowerLib>( file );
      if( lib->detector() != det || lib->particle() != pdg )
        throw std::runtime_error( "FCalFrozenShowerModel: " + file + " is " + lib->detector() + " " + std::to_string(lib->particle()) );
      // the library key is the detector plus the PDG code of the file (LArG4ShowerLibSvc.cxx:81): 11, 22, 2112
      out[det][lib->particle()] = lib;
    }
  }
  cache[dir] = out;
  return out;
}

FCalFrozenShowerModel::FCalFrozenShowerModel( const std::string &name, G4Region *region, const Config &config,
                                              const std::map<int, std::shared_ptr<const FCalShowerLib>> &libraries )
  : G4VFastSimulationModel( name, region ), m_config( config ), m_libraries( libraries )
{}

// the library is looked up with the signed PDG code (LArG4ShowerLibSvc.cxx:140-161): none for e+ (-11)
const FCalShowerLib* FCalFrozenShowerModel::library( int pdg ) const
{
  auto it = m_libraries.find( pdg );
  return it == m_libraries.end() ? nullptr : it->second.get();
}

// flagToShowerLib, minEneToShowerLib, maxEneToShowerLib (LArFastShower.cxx:363-408), with the flags of LArG4FastSimulationConfig.py:
// e+-, gamma and neutron on, pions off
bool FCalFrozenShowerModel::energyLimits( const G4ParticleDefinition &particle, double &emin, double &emax ) const
{
  if( &particle == G4Electron::ElectronDefinition() || particle.GetPDGEncoding() == -11 ){ emin = m_config.eMin; emax = m_config.eMax; return true; }
  if( &particle == G4Gamma::GammaDefinition()   ){ emin = m_config.gMin; emax = m_config.gMax; return true; }
  if( &particle == G4Neutron::NeutronDefinition() ){ emin = m_config.nMin; emax = m_config.nMax; return true; }
  return false;
}

// IsApplicable (LArFastShower.cxx:83-104)
G4bool FCalFrozenShowerModel::IsApplicable( const G4ParticleDefinition &particle )
{
  double emin, emax;
  return energyLimits( particle, emin, emax ) && library( particle.GetPDGEncoding() ) != nullptr;
}

// ForcedAccept (LArFastShower.cxx:416-438), with the eta of the position of the particle
bool FCalFrozenShowerModel::forcedAccept( const G4FastTrack &fastTrack ) const
{
  const double eta = fastTrack.GetPrimaryTrack()->GetPosition().eta();
  if( !m_config.containHigh && ( eta > m_config.absHighEta || eta < -m_config.absHighEta ) ) return true;
  if( !m_config.containCrack && ( ( eta > m_config.absCrackEta1 && eta < m_config.absCrackEta2 ) ||
                                  ( eta < -m_config.absCrackEta1 && eta > -m_config.absCrackEta2 ) ) ) return true;
  if( !m_config.containLow && ( eta < m_config.absLowEta || eta > -m_config.absLowEta ) ) return true;
  return false;
}

// CheckContainment (LArFastShower.cxx:253-333)
bool FCalFrozenShowerModel::checkContainment( const G4FastTrack &fastTrack ) const
{
  const G4Track *track = fastTrack.GetPrimaryTrack();
  const FCalShowerLib *lib = library( track->GetDefinition()->GetPDGEncoding() );
  if( !lib ) return true;   // getContainmentZ and R return 0 without library: no check
  const G4ThreeVector dir = track->GetMomentumDirection(), pos0 = track->GetPosition();
  const G4ThreeVector ortho = dir.orthogonal(), cross = dir.cross( ortho );
  const double Z = lib->getContainmentZ( track ), R = lib->getContainmentR( track );
  if( Z == 0.0 && R == 0.0 ) return true;
  const double Zmx = Z / 3;
  const int cosPhi[4] = {1, 0, -1, 0}, sinPhi[4] = {0, 1, 0, -1};
  const G4VSolid *solid = fastTrack.GetEnvelopeSolid();
  const G4AffineTransform *t = fastTrack.GetAffineTransformation();
  G4ThreeVector p = pos0; t->ApplyPointTransform( p );
  if( solid->Inside( p ) == kOutside ) return false;
  p = pos0 + Z * dir; t->ApplyPointTransform( p );
  if( solid->Inside( p ) == kOutside ) return false;
  for( int i = 0; i < 4; ++i ){
    p = pos0 + Zmx * dir + R * cosPhi[i] * ortho + R * sinPhi[i] * cross;
    t->ApplyPointTransform( p );
    if( solid->Inside( p ) == kOutside ) return false;
  }
  return true;
}

// ModelTrigger (LArFastShower.cxx:106-158): kinetic energy strictly inside the limits, then ForcedAccept, then the containment
G4bool FCalFrozenShowerModel::ModelTrigger( const G4FastTrack &fastTrack )
{
  const G4Track *track = fastTrack.GetPrimaryTrack();
  const double e = track->GetKineticEnergy();
  double emin, emax;
  if( !energyLimits( *track->GetDefinition(), emin, emax ) || !( e > emin && e < emax ) ) return false;
  if( forcedAccept( fastTrack ) ) return true;
  return checkContainment( fastTrack );
}

// DoIt, UseShowerLib (LArFastShower.cxx:161-251) and LArG4ShowerLibSvc::getShower (LArG4ShowerLibSvc.cxx:172-229)
void FCalFrozenShowerModel::DoIt( const G4FastTrack &fastTrack, G4FastStep &fastStep )
{
  fastStep.KillPrimaryTrack();
  fastStep.SetPrimaryTrackPathLength( 0.0 );
  const G4Track *track = fastTrack.GetPrimaryTrack();
  const FCalShowerLib *lib = library( track->GetDefinition()->GetPDGEncoding() );
  if( !lib ) return;
  // Athena draws with CLHEP::RandGaussZiggurat, not in the CLHEP of Geant4: the same Gaussian, mean 0 and sigma 2.5, with G4RandGauss
  const int randomShift = (int)( G4RandGauss::shoot( 0., 2.5 ) + 0.5 );
  std::vector<FCalShowerLib::Spot> shower;
  if( !lib->getShower( track, randomShift, shower ) ) return;
  const G4ThreeVector position = track->GetPosition(), direction = track->GetMomentumDirection();
  const double time = track->GetGlobalTime() / ns - ( position.mag() / CLHEP::c_light ) / ns;
  G4UserSteppingAction *stepping = G4EventManager::GetEventManager()->GetUserSteppingAction();
  if( !stepping ) return;
  for( const auto &spot : shower ){
    G4ThreeVector p = spot.position;
    p.rotateUz( direction );
    // a spot is a G4Step without touchable: CaloHitMaker::isShowerSpot
    G4Step step;
    step.GetPreStepPoint()->SetPosition( p + position );
    step.GetPreStepPoint()->SetGlobalTime( ( spot.time + time ) * ns );
    step.GetPostStepPoint()->SetPosition( p + position );
    step.GetPostStepPoint()->SetGlobalTime( ( spot.time + time ) * ns );
    step.SetTotalEnergyDeposit( spot.energy );
    stepping->UserSteppingAction( &step );
  }
}
