// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Atlas/G4AtlasTools/src) for --atlas-run4 (F41 conserto 27); changes: none.
/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/

#include "TightMuonSteppingFieldManager.h"
#include "G4Track.hh"
#include "G4ChordFinder.hh"
#include "G4MuonPlus.hh"
#include "G4MuonMinus.hh"

/// Normal constructor
TightMuonSteppingFieldManager::TightMuonSteppingFieldManager(G4Field *detectorField, G4ChordFinder *pChordFinder, G4bool b)
 : G4FieldManager(detectorField,pChordFinder,b)
 , m_globalDeltaChord(-1.)
 , m_globalDeltaOneStep(-1.)
 , m_globalDeltaIntersection(-1.)
 , m_globalMinEps(-1.)
 , m_globalMaxEps(-1.)
{}

/// Simple constructor
TightMuonSteppingFieldManager::TightMuonSteppingFieldManager(G4MagneticField *detectorMagneticField)
 : G4FieldManager(detectorMagneticField) 
 , m_globalDeltaChord(-1.)
 , m_globalDeltaOneStep(-1.)
 , m_globalDeltaIntersection(-1.)
 , m_globalMinEps(-1.)
 , m_globalMaxEps(-1.)
{}

/// The one interesting method
void TightMuonSteppingFieldManager::ConfigureForTrack(const G4Track * track)
{
  // If they have not been set yet, get the settings for the global field manager
  if (m_globalDeltaChord<0){
    m_globalDeltaChord = GetChordFinder()->GetDeltaChord();
    m_globalDeltaOneStep = GetDeltaOneStep();
    m_globalDeltaIntersection = GetDeltaIntersection();
    m_globalMinEps = GetMinimumEpsilonStep();
    m_globalMaxEps = GetMaximumEpsilonStep();
  }

  // If this is a muon, set tight parameters; otherwise go back to the defaults
  if (track->GetDefinition()==G4MuonPlus::Definition() ||
      track->GetDefinition()==G4MuonMinus::Definition() ){
    GetChordFinder()->SetDeltaChord(0.00000002);
    SetDeltaOneStep(0.000001);
    SetDeltaIntersection(0.00000002);
    SetMinimumEpsilonStep(0.0000009);
    SetMaximumEpsilonStep(0.000001);
  } else {
    GetChordFinder()->SetDeltaChord(m_globalDeltaChord);
    SetDeltaOneStep(m_globalDeltaOneStep);
    SetDeltaIntersection(m_globalDeltaIntersection);
    SetMinimumEpsilonStep(m_globalMinEps);
    SetMaximumEpsilonStep(m_globalMaxEps);
  }

}
