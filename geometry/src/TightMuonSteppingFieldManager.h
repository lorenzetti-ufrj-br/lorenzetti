// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Atlas/G4AtlasTools/src) for --atlas-run4 (F41 conserto 27); changes: none.
/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/

#ifndef TightMuonSteppingFieldManager_H
#define TightMuonSteppingFieldManager_H

/** @class TightMuonSteppingFieldManager TightMuonSteppingFieldManager.h
 *
 *  @brief G4FieldManager that sets tight stepping for muons; caches global
 *   values for other particles
 *
 *  @author Zach Marshall
 *  @date   2016-06-01
 */

#include "G4FieldManager.hh"
class G4Track;
class G4Field;
class G4ChordFinder;
class G4MagneticField;

class TightMuonSteppingFieldManager : public G4FieldManager
{
 public:
  /// Constructor
  TightMuonSteppingFieldManager(G4Field *detectorField=0, G4ChordFinder *pChordFinder=0, G4bool b=true);

  /// Simple constructor
  TightMuonSteppingFieldManager(G4MagneticField *detectorMagneticField);

  /// Simple destructor
  virtual ~TightMuonSteppingFieldManager() {}

  /// The one interesting method
  virtual void ConfigureForTrack(const G4Track *) override final;

 private:
  /** Parameters of the stepper.  This is to cache the global ones; the muon ones will be hard-coded */
  double m_globalDeltaChord;
  double m_globalDeltaOneStep;
  double m_globalDeltaIntersection;
  double m_globalMinEps;
  double m_globalMaxEps;

};

#endif