#include "src/CaloBirksLawTool.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "G4Track.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include <cmath>

using namespace CLHEP;

CaloBirksLawTool::CaloBirksLawTool( std::string name )
  : IMsgService(name), ICaloEnergyModifierTool(name)
{
  declareProperty( "BirksLArK", m_birksLArK = 0.05832 );
}

float CaloBirksLawTool::modifyEnergy( const G4Step *step, CellIdentification &, float currentEnergy ) const
{
  if( !step ) return currentEnergy;
  const double baseEnergy = (currentEnergy > 0.0f) ? (double)currentEnergy : step->GetTotalEnergyDeposit();
  const double edep = baseEnergy * ( step->GetTrack() ? step->GetTrack()->GetWeight() : 1. );
  const double length = step->GetStepLength();
  const G4Material *material = step->GetPreStepPoint()->GetMaterial();
  if( !material || edep <= 0 || length <= 0 ) return (float)edep;
  const G4String &name = material->GetName();

  if( name == "PLASTIC SCINTILLATOR" ){
    const double charge = step->GetPreStepPoint()->GetCharge();
    if( charge == 0. ) return (float)edep;
    double kB = 0.02002 * g / (MeV * cm2);
    if( std::abs(charge) > 1.0 ) kB *= 7.2 / 12.6;
    const double dedx = edep / length / material->GetDensity();
    return (float)( edep / (1. + kB * dedx) );
  }

  if( name == "liquidArgon" ){
    const double dE = edep / MeV;
    const double dX = length / cm;
    if( dX < 1e-5 ) return (float)edep;
    const double kOverField = m_birksLArK / 10.;
    double dEdX = dE / dX;
    const double corrected = dE * (1 + kOverField * 1.51) / (1 + kOverField * dEdX / 1.396);
    if( dEdX > 12000.0 ) dEdX = 12000.0;
    const double kHIP = (dEdX > 969.) ? 0.000754 * dEdX + 0.2692 : 1.0;
    return (float)( corrected * kHIP * MeV );
  }

  return (float)edep;
}
