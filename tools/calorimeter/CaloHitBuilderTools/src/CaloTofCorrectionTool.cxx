#include "src/CaloTofCorrectionTool.h"
#include "G4Step.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include "CLHEP/Units/PhysicalConstants.h"

CaloTofCorrectionTool::CaloTofCorrectionTool( std::string name )
  : IMsgService(name), ICaloTimeCorrectionTool(name)
{
  declareProperty( "ApplyTof", m_applyTof = true );
}

CellTiming CaloTofCorrectionTool::computeTime( const G4Step *step, const CellIdentification & ) const
{
  CellTiming timing;
  if( !step ) return timing;

  const G4StepPoint *preP = step->GetPreStepPoint();
  double tglobal = preP->GetGlobalTime() / CLHEP::ns;
  double tof = preP->GetPosition().mag() / CLHEP::c_light;
  double thit = tglobal - (m_applyTof ? tof : 0.0);

  timing.hitTime = (float)thit;
  timing.globalTime = (float)tglobal;
  timing.time0 = (float)thit;
  timing.time1 = (float)thit;
  timing.hasDualReadoutTime = false;
  return timing;
}
