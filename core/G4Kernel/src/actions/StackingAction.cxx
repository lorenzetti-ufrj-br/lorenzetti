#include "G4Kernel/actions/StackingAction.h"
#include "G4Kernel/AtlasG4Settings.h"

#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "G4Gamma.hh"
#include "G4Neutron.hh"
#include "G4VTouchable.hh"
#include "G4VPhysicalVolume.hh"
#include "G4LogicalVolume.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <cstdlib>

// See StackingAction.h. Line references are to AthenaStackingAction.cxx of the Athena release 23.0.14.

bool StackingAction::isLArTree( const G4LogicalVolume *lv )
{
  auto it = m_larTree.find( lv );
  if( it != m_larTree.end() ) return it->second;
  bool lar = false;
  const std::string &name = lv->GetName();
  for( const auto &prefix : AtlasG4Settings::instance().larTreeVolumes )
    if( name.compare( 0, prefix.size(), prefix ) == 0 ){ lar = true; break; }
  m_larTree[lv] = lar;
  return lar;
}

G4ClassificationOfNewTrack StackingAction::ClassifyNewTrack( const G4Track *track )
{
  const G4ParticleDefinition *def = track->GetDefinition();
  const int pdg = std::abs( def->GetPDGEncoding() );
  // neutrinos (:61-63)
  if( pdg == 12 || pdg == 14 || pdg == 16 ) return fKill;
  // photons below 50 eV of total energy (:65-70)
  if( def == G4Gamma::GammaDefinition() && track->GetTotalEnergy() < 0.00005 * MeV ) return fKill;
  // neutron Russian roulette (:77-92)
  if( def == G4Neutron::NeutronDefinition() && track->GetWeight() < 10. && track->GetKineticEnergy() < 2. * MeV ){
    if( G4UniformRand() > 1. / 10. ) return fKill;
    const_cast<G4Track*>( track )->SetWeight( 10. );
    return fUrgent;
  }
  // photon Russian roulette, only for photons born in the LAr tree (:94-110)
  if( def == G4Gamma::GammaDefinition() && track->GetOriginTouchable() && track->GetWeight() < 10. &&
      track->GetKineticEnergy() < 0.5 * MeV ){
    const G4VPhysicalVolume *pv = track->GetOriginTouchable()->GetVolume();
    if( pv && isLArTree( pv->GetLogicalVolume() ) ){
      if( G4UniformRand() > 1. / 10. ) return fKill;
      const_cast<G4Track*>( track )->SetWeight( 10. );
      return fUrgent;
    }
  }
  return fUrgent;
}
