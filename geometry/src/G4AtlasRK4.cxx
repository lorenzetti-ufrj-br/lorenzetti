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
// $Id: G4AtlasRK4.cc,v 1.12 2006/06/29 18:23:37 gunter Exp $
// GEANT4 tag $Name: geant4-09-02 $
//
// Changes:
//   2018.01.29 J.A.:  Ensure that momentum is correct in Stepper call
// -------------------------------------------------------------------

#include "G4AtlasRK4.h"
#include <iostream>
#include <iomanip>

////////////////////////////////////////////////////////////////
// Constructor sets the number of variables (must be 6)
////////////////////////////////////////////////////////////////

G4AtlasRK4::G4AtlasRK4(G4EquationOfMotion* EqRhs, G4int )
  : G4MagIntegratorStepper(EqRhs, 6),
    m_fractionMom( fDefaultMF ),
    m_cof(0.0),
    m_mom(0.0),
    m_imom(1.0)
{
  m_fEq          =  dynamic_cast<G4Mag_EqRhs*>(GetEquationOfMotion());
  m_field[0] = 0.0;
  m_field[1] = 0.0;
  m_field[2] = 0.0;
  // G4MagIntegratorStepper::SetIntegrationOrder(4);
}

////////////////////////////////////////////////////////////////
// Destructor
////////////////////////////////////////////////////////////////

G4AtlasRK4::~G4AtlasRK4()
{
}

////////////////////////////////////////////////////////////////
// Integration in one  step
////////////////////////////////////////////////////////////////

void
G4AtlasRK4::Stepper
(const G4double P[],const G4double dPdS[],G4double Step,G4double Po[],G4double Err[])
{
  G4double R[4] = {   P[0],   P[1] ,    P[2],  P[7] };
  G4double A[3] = {dPdS[0], dPdS[1], dPdS[2]};

  // CheckPosition( .. ) ?
  m_iPoint[0]=P[0]; m_iPoint[1]=P[1]; m_iPoint[2]=P[2];

  G4double S  =     Step   ;
  G4double S5 =  .5*Step   ;
  G4double S4 = .25*Step   ;
  G4double S6 =     Step/6.;

  // CheckCachedMomentum( P, m_mom );  // Check if it is fixed - i.e. already (always) ok.

  // Check momentum magnitude (squared) against previous value
  G4double startMom2 = (P[3]*P[3]+P[4]*P[4]+P[5]*P[5]);
  G4double  prevMom2 = m_mom * m_mom;

  bool changedMag = std::fabs(startMom2 - prevMom2)
                           > m_fractionMom * std::min(prevMom2,startMom2);
  if( changedMag ) {
     // John A  added, in order to emulate effect of call to changed/derived RHS
     m_mom   = sqrt(startMom2);
     m_imom  = 1./m_mom;
     m_cof   = m_fEq->FCof()*m_imom;
  }

  getField(R);

  // Point 1
  //
  G4double K1[3] = {m_imom*dPdS[3],m_imom*dPdS[4],m_imom*dPdS[5]};

  // Point2
  //
  G4double p[4] = {R[0]+S5*(A[0]+S4*K1[0]),
       R[1]+S5*(A[1]+S4*K1[1]),
       R[2]+S5*(A[2]+S4*K1[2]),
       P[7]                   }; getField(p);

  G4double A2[3] = {A[0]+S5*K1[0],A[1]+S5*K1[1],A[2]+S5*K1[2]};
  G4double K2[3] = {(A2[1]*m_field[2]-A2[2]*m_field[1])*m_cof,
        (A2[2]*m_field[0]-A2[0]*m_field[2])*m_cof,
        (A2[0]*m_field[1]-A2[1]*m_field[0])*m_cof};

  m_mPoint[0]=p[0]; m_mPoint[1]=p[1]; m_mPoint[2]=p[2];

  // Point 3 with the same magnetic field
  //
  G4double A3[3] = {A[0]+S5*K2[0],A[1]+S5*K2[1],A[2]+S5*K2[2]};
  G4double K3[3] = {(A3[1]*m_field[2]-A3[2]*m_field[1])*m_cof,
        (A3[2]*m_field[0]-A3[0]*m_field[2])*m_cof,
        (A3[0]*m_field[1]-A3[1]*m_field[0])*m_cof};

  // Point 4
  //
  p[0] = R[0]+S*(A[0]+S5*K3[0]);
  p[1] = R[1]+S*(A[1]+S5*K3[1]);
  p[2] = R[2]+S*(A[2]+S5*K3[2]);             getField(p);

  G4double A4[3] = {A[0]+S*K3[0],A[1]+S*K3[1],A[2]+S*K3[2]};
  G4double K4[3] = {(A4[1]*m_field[2]-A4[2]*m_field[1])*m_cof,
        (A4[2]*m_field[0]-A4[0]*m_field[2])*m_cof,
        (A4[0]*m_field[1]-A4[1]*m_field[0])*m_cof};

  // New position
  //
  Po[0] = R[0]+S*(A[0]+S6*(K1[0]+K2[0]+K3[0]));
  Po[1] = R[1]+S*(A[1]+S6*(K1[1]+K2[1]+K3[1]));
  Po[2] = R[2]+S*(A[2]+S6*(K1[2]+K2[2]+K3[2]));

  m_fPoint[0]=Po[0]; m_fPoint[1]=Po[1]; m_fPoint[2]=Po[2];

  // New direction
  //
  Po[3] = A[0]+S6*(K1[0]+K4[0]+2.*(K2[0]+K3[0]));
  Po[4] = A[1]+S6*(K1[1]+K4[1]+2.*(K2[1]+K3[1]));
  Po[5] = A[2]+S6*(K1[2]+K4[2]+2.*(K2[2]+K3[2]));

  // Errors
  //
  Err[3] = S*fabs(K1[0]-K2[0]-K3[0]+K4[0]);
  Err[4] = S*fabs(K1[1]-K2[1]-K3[1]+K4[1]);
  Err[5] = S*fabs(K1[2]-K2[2]-K3[2]+K4[2]);
  Err[0] = S*Err[3]                       ;
  Err[1] = S*Err[4]                       ;
  Err[2] = S*Err[5]                       ;
  Err[3]*= m_mom                          ;
  Err[4]*= m_mom                          ;
  Err[5]*= m_mom                          ;

  // Normalize momentum
  //
  G4double endMom2 = Po[3]*Po[3]+Po[4]*Po[4]+Po[5]*Po[5];
  G4double normRatio = sqrt( startMom2 / endMom2 );
  Po[3] *= normRatio ;
  Po[4] *= normRatio ;
  Po[5] *= normRatio ;
  Po[7] =P[7];
}


////////////////////////////////////////////////////////////////
// Estimate the maximum distance from the curve to the chord
////////////////////////////////////////////////////////////////

G4double
G4AtlasRK4::DistChord() const
{
  G4double ax = m_fPoint[0]-m_iPoint[0];
  G4double ay = m_fPoint[1]-m_iPoint[1];
  G4double az = m_fPoint[2]-m_iPoint[2];
  G4double dx = m_mPoint[0]-m_iPoint[0];
  G4double dy = m_mPoint[1]-m_iPoint[1];
  G4double dz = m_mPoint[2]-m_iPoint[2];
  G4double d2 = (ax*ax+ay*ay+az*az)    ;

  if(d2!=0.) {
    G4double  s = (ax*dx+ay*dy+az*dz)/d2;
    dx         -= (s*ax)                ;
    dy         -= (s*ay)                ;
    dz         -= (s*az)                ;
  }
  return sqrt(dx*dx+dy*dy+dz*dz);
}

/////////////////////////////////////////////////////////////////////////////////
// Derivatives calculation - caching the momentum value
/////////////////////////////////////////////////////////////////////////////////

void
G4AtlasRK4::ComputeRightHandSide(const G4double P[],G4double dPdS[])
{
  // Virtual method called at the start of integration
  //  Not used inside G4AtlasRK4 - only by other classes to obtain dPdS
  G4double P4vec[4]= { P[0], P[1], P[2], P[7] }; // Time is P[7]
  getField(P4vec);
  m_mom   = std::sqrt(P[3]*P[3]+P[4]*P[4]+P[5]*P[5])     ;
  m_imom  = 1./m_mom                                ;
  m_cof   = m_fEq->FCof()*m_imom                    ;

  // m_cachedMom = true                                ; // Caching the value
  dPdS[0] = P[3]*m_imom                             ; // dx /ds
  dPdS[1] = P[4]*m_imom                             ; // dy /ds
  dPdS[2] = P[5]*m_imom                             ; // dz /ds
  dPdS[3] = m_cof*(P[4]*m_field[2]-P[5]*m_field[1]) ; // dPx/ds
  dPdS[4] = m_cof*(P[5]*m_field[0]-P[3]*m_field[2]) ; // dPy/ds
  dPdS[5] = m_cof*(P[3]*m_field[1]-P[4]*m_field[0]) ; // dPz/ds
}

////////////////////////////////////////////////////
// Check magnitude of momentum against saved value
////////////////////////////////////////////////////

bool
G4AtlasRK4::CheckCachedMomentum( const double PosMom[6],
                                       double savedMag,  // Saved momentum magnitude
                                       bool   reportError )
{
  constexpr G4double perThousand = 1.0e-3;
  bool ok= true;
  G4double new_mom2= (PosMom[3]*PosMom[3]+PosMom[4]*PosMom[4]+PosMom[5]*PosMom[5]);
  G4double new_mom=  std::sqrt(new_mom2);
  if( std::fabs(new_mom - savedMag ) > perThousand * std::min(savedMag,new_mom) ) {
     if( reportError ) {
        std::ostringstream errmsg;
        errmsg << " Nystrom::Stepper WARNING: momentum magnitude is invalid / has changed "
               << G4endl
               << " new value    (p-mag) = "   << new_mom << G4endl
               << " cached value (p-mag) = "  << savedMag   << G4endl;
        if( savedMag > 0.0 ) {
           errmsg << " ratio  (new/old) = " << new_mom / savedMag << G4endl;
        }
        G4Exception("G4AtlasRK4::CachedMomentum()", "GeomField0003",
                    JustWarning, errmsg);
     }
     ok= false;
  }
  return ok;
}

/////////////////////////////////////////////////////////////////
// Check that the field value is unchanged from 'last' evaluation
/////////////////////////////////////////////////////////////////

bool
G4AtlasRK4::CheckFieldValue( const G4double Position[3],
                                   G4double expectedValue[3],
                                       bool reportError )
{
  using std::setw;
  bool unchanged= true;

  getField(Position);
  double dx = m_field[0] - expectedValue[0];
  double dy = m_field[1] - expectedValue[1];
  double dz = m_field[2] - expectedValue[2];
  double magDiff2 = dx*dx+dy*dy+dz*dz;

  const double allowedDiff = 0.0;
  if( magDiff2 > 0.0 ) {    //  > allowedDiff * allowedDiff ) {
     unchanged= false;

     if( reportError ) {
        double magDif= std::sqrt( magDiff2 );
        std::ostringstream errmsg;
        errmsg << "NystromRK4::Stepper> ERROR> Incorrect field value - different of "
               << magDif <<  "( larger than allowed = " << allowedDiff << " ) "
               << G4endl;
        errmsg << "  Current location (x,y,z) : " << Position[0] << " " << Position[1]
               << "  " << Position[2] << " " << G4endl;
        errmsg << "Vectors of values: " << G4endl;
        char str100[100];
        sprintf( str100, "  %12s  %12s  %12s", "Original", "New", "Diff" );
        errmsg << str100 << G4endl;
        for ( int i=0; i < 3; i++) {
           errmsg << "  " << setw(12) << expectedValue[i]
                  << "  " << setw(12) << m_field[i]
                  << "  diff= " << setw(12) << m_field[i]-expectedValue[i] << G4endl;
        }
        G4Exception("G4AtlasRK4::CheckFieldValue()", "GeomField0003",
                    JustWarning, errmsg);
     }
  }
  return unchanged;
}

////////////////////////////////////////////////////////////////////////////
// Check that the location is (almost) unmoved from 'last' field evaluation
////////////////////////////////////////////////////////////////////////////

bool
G4AtlasRK4::CheckFieldPosition( const G4double Position[3],
                                const G4double lastPosition[3],
                                          bool reportError)
{
  bool ok= true;
  double dx = Position[0] - lastPosition[0];
  double dy = Position[1] - lastPosition[1];
  double dz = Position[2] - lastPosition[2];
  double distMag2 = dx*dx+dy*dy+dz*dz;

  const double m_magdistance2= 0.0;

  if( distMag2 > m_magdistance2) {
     ok= false;

     if( reportError )
     {
        const double allowedDist = std::sqrt( m_magdistance2 );
        std::ostringstream errmsg;

        double dist= std::sqrt( distMag2 );
        errmsg << " NystromRK4::Stepper> ERROR> Moved from correct field position by "
               << dist <<  "( larger than allowed = " << allowedDist << " ) ";
        G4Exception("G4AtlasRK4::CheckFieldPosition()", "GeomField0003",
                    JustWarning, errmsg);
     }
  }
  return ok;
}
