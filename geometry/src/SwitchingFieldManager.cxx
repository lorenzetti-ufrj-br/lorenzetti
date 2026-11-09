// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Atlas/G4AtlasTools/src) for --atlas-full-field (F41 conserto 33);
// changes: none.
/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/

#include "G4ThreeVector.hh"
#include "G4Field.hh"
#include "SwitchingFieldManager.h"
#include "G4ChordFinder.hh"
#include "G4Track.hh"
#include "G4MuonPlus.hh"
#include "G4MuonMinus.hh"

SwitchingFieldManager::SwitchingFieldManager( G4Field* detectorField )
   :  G4FieldManager( detectorField ),
      m_savedField( detectorField )
{}

SwitchingFieldManager::~SwitchingFieldManager()
{}

void SwitchingFieldManager::ConfigureForTrack(const G4Track * track)
{
   assert(  GetDetectorField() == m_savedField
         || GetDetectorField() == nullptr );

   const bool isMuonTrack = (track->GetDefinition()==G4MuonPlus::Definition() ||
                             track->GetDefinition()==G4MuonMinus::Definition() );

   const G4ThreeVector position = track->GetPosition();
   const G4double r2XY = position.x()*position.x() + position.y()*position.y();
   const G4double  Z = position.z();

   const G4double r2Min = (m_radiusXYmin + m_offset)*(m_radiusXYmin + m_offset);
   const G4double r2Max = (m_radiusXYmax - m_offset)*(m_radiusXYmax - m_offset);

   const bool inSide = (r2XY > r2Min) && (r2XY < r2Max) && (fabs(Z) < m_Zmax - m_offset);

   if ( inSide && DoesFieldExist() && !isMuonTrack )
      ChangeDetectorField( nullptr );
   else if ( !inSide && !DoesFieldExist() )
      ChangeDetectorField( m_savedField );
}

G4FieldManager* SwitchingFieldManager::Clone() const
{
   G4Field* cloneField = m_savedField->Clone();
   auto clone= new SwitchingFieldManager( cloneField );

   clone->SetMinimumEpsilonStep( this->GetMinimumEpsilonStep() );
   clone->SetMaximumEpsilonStep( this->GetMaximumEpsilonStep() );
   clone->SetDeltaOneStep(       this->GetDeltaOneStep() );
   clone->SetDeltaIntersection(  this->GetDeltaIntersection()  );
   clone->GetChordFinder()->SetDeltaChord( this->GetChordFinder()->GetDeltaChord() );

   return clone;
}
