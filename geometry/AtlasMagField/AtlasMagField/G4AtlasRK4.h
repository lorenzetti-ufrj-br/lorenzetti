// Ported to Lorenzetti from the ATLAS Geant4 (gitlab.cern.ch/atlas-simulation-team/geant4, tag v10.6.3.4, the geant4.10.6.patch03.atlasmt04 of the
// reference production) for --atlas-run4 (F41 conserto 27): the stepper AtlasRK4 of the ATLAS simulation (Sim.G4Stepper), absent from the public
// Geant4 11; changes: file names (G4AtlasRK4.h, G4AtlasRK4.cxx).
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
// $Id: G4AtlasRK4.hh,v 1.10 2006/06/29 18:21:55 gunter Exp $
// GEANT4 tag $Name: geant4-09-02 $
//
//
// class G4AtlasRK4
//
// Class description:
//
// Integrate the equations of the motion of a particle in a magnetic field
// using  4th Runge-Kutta-Nystrem method with errors estimation
// (ATL-SOFT-PUB-2009-01)
// History:
// - Created: I.Gavrilenko   15.05.2009
// -------------------------------------------------------------------

#ifndef G4ATLASRK4_HH
#define G4ATLASRK4_HH

#include "G4MagIntegratorStepper.hh"
#include "G4Mag_EqRhs.hh"

class G4AtlasRK4 : public G4MagIntegratorStepper
{
public:

  ////////////////////////////////////////////////////////////////
  // Public methods:
  ////////////////////////////////////////////////////////////////

  G4AtlasRK4(G4EquationOfMotion *EquationMotion, G4int numberOfVariables = 6);

  ~G4AtlasRK4() ;

  // Virtual methods:
  void Stepper(const G4double P   [],
         const G4double dPdS[],
               G4double step  ,
               G4double Po  [],
                     G4double Err []); //  override final;

  G4int     IntegratorOrder() const {return 4;} // override final;
  G4double  DistChord() const; //  override final;

  void ComputeRightHandSide(const G4double P[],G4double dPdS[]); // override final;

  // Auxiliary values & methods
  // Optimisation for reduced recalculation of momentum magnitude & related parameters
  static constexpr G4double fMaximumMF = 1.0e-4; // Mininum value for fraction of Momentum
  static constexpr G4double fDefaultMF = 1.0e-7; // Default value for fraction of Momentum

  // Get/Set accuracy parameter for cached magnitude of momentum
  G4double GetChangeFraction() const { return m_fractionMom; }
  void     SetChangeFraction(G4double val) { if( 0.0 <= val && val < fMaximumMF ) { m_fractionMom= val; } }

private:

  ////////////////////////////////////////////////////////////////
  // Private methods
  ////////////////////////////////////////////////////////////////

  void getField   (const G4double P[]);

  bool CheckCachedMomentum( const double PosMom[6],
                                  double savedMom,
                                    bool reportError= true );
  bool CheckFieldValue(     const G4double Position[3],
                                  G4double expectedValue[3],
                                      bool reportError= true );
  bool CheckFieldPosition(  const G4double Position[3],
                            const G4double lastPosition[3],
                                       bool reportError= true );

  ////////////////////////////////////////////////////////////////
  // Private data
  ////////////////////////////////////////////////////////////////

  // Invariates: Parameters of integration
  G4Mag_EqRhs*      m_fEq         ;
  G4double          m_fractionMom ;  // fraction of momentum - for change larger than this
                                     //  the Norm | mom | is recalculated.

  // State - dependant on last track and location
  mutable  G4double m_field    [3];
  mutable  G4double m_cof         ;
  mutable  G4double m_mom         ;
  mutable  G4double m_imom        ;
  mutable  G4double m_iPoint   [3];
  mutable  G4double m_mPoint   [3];
  mutable  G4double m_fPoint   [3];

  mutable  G4double m_location [3];  // position of last call to getField()
};

////////////////////////////////////////////////////////////////
// Inline methods
////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////
// Get new magnetic field withOUT testing distance from previous call
////////////////////////////////////////////////////////////////

inline void G4AtlasRK4::getField (const G4double P[])
{
  m_location[0] = P[0];
  m_location[1] = P[1];
  m_location[2] = P[2];
  m_fEq->GetFieldValue(P,m_field);
}

#endif  // G4ATLASRK4_HH
