#include "src/TilePmtPropagationTimeTool.h"
#include "G4Step.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include "CLHEP/Units/PhysicalConstants.h"
#include <cmath>

TilePmtPropagationTimeTool::TilePmtPropagationTimeTool( std::string name )
  : IMsgService(name), ICaloTimeCorrectionTool(name)
{
  declareProperty( "PhiBins"       , m_phiBins );
  declareProperty( "CellRCentre"   , m_cellRCentre );
  declareProperty( "CellZCentre"   , m_cellZCentre );
  declareProperty( "ReplaceRCentre", m_replaceRCentre = 0.0f );
  declareProperty( "ReplaceZCentre", m_replaceZCentre = 0.0f );
}

CellTiming TilePmtPropagationTimeTool::computeTime( const G4Step *step, const CellIdentification &cell ) const
{
  CellTiming timing;
  if( !step ) return timing;

  if( cell.etaBin >= 0 && cell.etaBin < (int)m_cellRCentre.size() ){
    double tglobal = 0.0, tc = 0.0, dtUp = 0.0, dtDown = 0.0;
    tileTime( step, cell.etaBin, cell.phiBin, cell.tileNPmt, tglobal, tc, dtUp, dtDown );
    timing.hitTime = (float)tc;
    timing.globalTime = (float)tglobal;
    timing.time0 = (float)(tc + dtDown);
    timing.time1 = (float)(tc + dtUp);
    timing.hasDualReadoutTime = true;
    return timing;
  }

  const G4StepPoint *preP = step->GetPreStepPoint();
  double tglobal = preP->GetGlobalTime() / CLHEP::ns;
  double tof = preP->GetPosition().mag() / CLHEP::c_light;
  timing.hitTime = (float)(tglobal - tof);
  timing.globalTime = (float)tglobal;
  timing.time0 = timing.hitTime;
  timing.time1 = timing.hitTime;
  timing.hasDualReadoutTime = false;
  return timing;
}

void TilePmtPropagationTimeTool::tileTime( const G4Step *step, int cell, int phiBin, int npmt, double &tglobal, double &t, double &dtUp,
                                           double &dtDown ) const
{
  const double n = 1.59, tanPi64 = std::tan(M_PI / 64);
  const double cLight = CLHEP::c_light;   // mm/ns
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = (phiBin >= 0 && phiBin + 1 < (int)m_phiBins.size()) ? 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] ) : 0.0;
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  double moduleCentre = std::remainder( (module + 0.5) * modWidth, twoPi );
  const bool replaced = ( npmt == 0 );
  double rCell = replaced ? (double)m_replaceRCentre : (cell >= 0 && cell < (int)m_cellRCentre.size() ? (double)m_cellRCentre[cell] : 0.0);
  double zCell = replaced ? (double)m_replaceZCentre : (cell >= 0 && cell < (int)m_cellZCentre.size() ? (double)m_cellZCentre[cell] : 0.0);

  const G4ThreeVector post = step->GetPostStepPoint()->GetPosition();
  const G4ThreeVector pre  = step->GetPreStepPoint()->GetPosition();
  tglobal = step->GetPostStepPoint()->GetGlobalTime() / CLHEP::ns;
  double sinThCell = rCell / std::sqrt( rCell*rCell + zCell*zCell );
  double cosThHit = post.cosTheta();
  t = tglobal + ( rCell * ( n - 2.0 / sinThCell ) + post.mag() * ( 1.0 - n * std::sqrt( 1.0 - cosThHit*cosThHit ) ) ) / cLight;

  double phiLocal = std::remainder( pre.phi() - moduleCentre, twoPi );
  double rPre = pre.perp();
  double xLocal = rPre * std::cos(phiLocal), yLocal = rPre * std::sin(phiLocal);
  double halfWidth = xLocal * tanPi64;
  double dyUp = halfWidth - yLocal;
  double dyDown = halfWidth + yLocal;
  dtUp   = n * ( dyUp   - rCell * tanPi64 ) / cLight;
  dtDown = n * ( dyDown - rCell * tanPi64 ) / cLight;
  if( npmt == 1 || npmt == -1 ) dtUp = dtDown = 0.0;
}
