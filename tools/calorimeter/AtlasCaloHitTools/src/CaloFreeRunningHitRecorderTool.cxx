#include "src/CaloFreeRunningHitRecorderTool.h"
#include "src/freerunning/CaloFreeRunningHitList.h"
#include "GaugiKernel/DataHandle.h"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4ThreeVector.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include "CLHEP/Units/PhysicalConstants.h"
#include <cmath>

CaloFreeRunningHitRecorderTool::CaloFreeRunningHitRecorderTool( std::string name )
  : IMsgService(name), ICaloHitRecorderTool(name)
{
  declareProperty( "FreeRunningListKey" , m_listKey = "FreeRunningHits" );
  declareProperty( "FreeRunningBinning" , m_binning = true );
  declareProperty( "Subdet"             , m_subdet = 0 );
  declareProperty( "AtlasBarrelEc"      , m_atlasBarrelEc = 1 );
  declareProperty( "AtlasLArSampling"   , m_atlasLArSampling = 0 );
  declareProperty( "AtlasLArRegion"     , m_atlasLArRegion = 0 );
  declareProperty( "AtlasLArPart"       , m_atlasLArPart = 1 );

  declareProperty( "CellAtlasEtaIndex"  , m_cellAtlasEtaIndex );
  declareProperty( "NPhiBins"           , m_nPhiBins = 64 );
  declareProperty( "PhiBins"            , m_phiBins );
  declareProperty( "CellEta"            , m_cellEta );

  declareProperty( "CellAtlasSection"   , m_cellAtlasSection );
  declareProperty( "CellAtlasTower"     , m_cellAtlasTower );
  declareProperty( "CellAtlasSampling"  , m_cellAtlasSampling );
  declareProperty( "CellRCentre"        , m_cellRCentre );
  declareProperty( "CellZCentre"        , m_cellZCentre );
  declareProperty( "ReplaceSection"     , m_replaceSection = 0 );
  declareProperty( "ReplaceTower"       , m_replaceTower = 0 );
  declareProperty( "ReplaceSampling"    , m_replaceSampling = 0 );
  declareProperty( "ReplaceRCentre"     , m_replaceRCentre = 0.0f );
  declareProperty( "ReplaceZCentre"     , m_replaceZCentre = 0.0f );

  declareProperty( "FCalModule"         , m_fcalModule = 0 );
  declareProperty( "FCalCopyEtaIndex"   , m_fcalCopyEtaIndex );
  declareProperty( "FCalCopyPhiIndex"   , m_fcalCopyPhiIndex );
  declareProperty( "FCalCopyEta"        , m_fcalCopyEta );
  declareProperty( "FCalCopyPhi"        , m_fcalCopyPhi );
}

StatusCode CaloFreeRunningHitRecorderTool::initialize()
{
  return StatusCode::SUCCESS;
}

StatusCode CaloFreeRunningHitRecorderTool::finalize()
{
  return StatusCode::SUCCESS;
}

StatusCode CaloFreeRunningHitRecorderTool::record( SG::EventContext &ctx, const G4Step *step,
                                                   const CellIdentification &cell, float energy,
                                                   const CellTiming &timing ) const
{
  if( !cell.isValid || energy <= 0.0f ) return StatusCode::SUCCESS;

  SG::ReadHandle<CaloFreeRunningHitList> list( m_listKey, ctx );
  if( !list.isValid() ){
    MSG_FATAL( "It's not possible to retrieve the CaloFreeRunningHitList using this key: " << m_listKey );
    return StatusCode::FAILURE;
  }

  int subdet = ( cell.atlasSubdet > 0 ) ? cell.atlasSubdet : m_subdet;
  if( subdet == 0 ){
    fillTile( list.ptr(), step, cell, energy, timing );
  } else {
    fillLAr( list.ptr(), step, cell, energy, timing );
  }

  return StatusCode::SUCCESS;
}

void CaloFreeRunningHitRecorderTool::fillTile( const CaloFreeRunningHitList *list, const G4Step *,
                                               const CellIdentification &cell, float energy,
                                               const CellTiming &timing ) const
{
  const double timeCut = 350.5, lateHitTime = 99995.;

  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  int phiBin = cell.phiBin;
  double phiCentre = ( phiBin >= 0 && phiBin + 1 < (int)m_phiBins.size() ) ?
                     0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] ) : 0.0;
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  double moduleCentre = std::remainder( (module + 0.5) * modWidth, twoPi );
  const bool replaced = cell.isReplaced || ( cell.tileNPmt == 0 );
  int cellIdx = cell.cell >= 0 ? cell.cell : cell.etaBin;
  int section  = replaced ? m_replaceSection  : ( cellIdx >= 0 && cellIdx < (int)m_cellAtlasSection.size() ? m_cellAtlasSection[cellIdx] : 0 );
  int tower    = replaced ? m_replaceTower    : ( cellIdx >= 0 && cellIdx < (int)m_cellAtlasTower.size() ? m_cellAtlasTower[cellIdx] : 0 );
  int sampling = replaced ? m_replaceSampling : ( cellIdx >= 0 && cellIdx < (int)m_cellAtlasSampling.size() ? m_cellAtlasSampling[cellIdx] : 0 );
  double rCell = replaced ? (double)m_replaceRCentre : ( cellIdx >= 0 && cellIdx < (int)m_cellRCentre.size() ? (double)m_cellRCentre[cellIdx] : 0.0 );
  double zCell = replaced ? (double)m_replaceZCentre : ( cellIdx >= 0 && cellIdx < (int)m_cellZCentre.size() ? (double)m_cellZCentre[cellIdx] : 0.0 );
  int side     = ( zCell >= 0 || (section == 1 && sampling == 2 && tower == 0) ) ? +1 : -1;
  auto pmtId = [&]( int pmt ) -> long long {
    unsigned long long id = (2ULL << 61) | ((unsigned long long)section << 58) | ((unsigned long long)(side > 0 ? 2 : 0) << 54)
                          | ((unsigned long long)module << 46) | ((unsigned long long)tower << 40)
                          | ((unsigned long long)sampling << 36) | ((unsigned long long)pmt << 34);
    return (long long)id;
  };

  double tglobal = timing.globalTime;
  double t = timing.hitTime;
  double dtUp = timing.time1 - timing.hitTime;
  double dtDown = timing.time0 - timing.hitTime;
  if( t + dtUp > timeCut || t + dtDown > timeCut ){
    t = lateHitTime;
    dtUp = dtDown = 0.0;
  }
  double delta = m_binning ? ( ( t > -75.25 && t < 75.25 ) ? 0.5 : 5.0 ) : 0.0;

  double eta = ( cellIdx >= 0 && cellIdx < (int)m_cellEta.size() ) ? m_cellEta[cellIdx] : cell.eta;
  float w0 = cell.pmtWeight0;
  float w1 = cell.pmtWeight1;
  if( w1 * energy > 0 ) list->add( pmtId(1), w1 * energy, t + dtUp,   tglobal, eta, moduleCentre, sampling, side, module, tower, delta );
  if( w0 * energy > 0 ) list->add( pmtId(0), w0 * energy, t + dtDown, tglobal, eta, moduleCentre, sampling, side, module, tower, delta );
}

void CaloFreeRunningHitRecorderTool::fillLAr( const CaloFreeRunningHitList *list, const G4Step *step,
                                              const CellIdentification &cell, float energy,
                                              const CellTiming & ) const
{
  const double cLight = CLHEP::c_light;   // mm/ns
  int subdet = ( cell.atlasSubdet > 0 ) ? cell.atlasSubdet : m_subdet;

  if( subdet == 4 || m_fcalModule > 0 ){
    int fcalMod = ( cell.atlasModule > 0 ) ? cell.atlasModule : m_fcalModule;
    const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
    bool isSpot = ( cell.atlasSource == 1 ) || ( preP->GetTouchable() == nullptr );
    int posNeg = cell.atlasSide != 0 ? cell.atlasSide : ( preP->GetPosition().z() > 0 ? 2 : -2 );
    int etaIndex = cell.etaBin;
    int phiIndex = cell.phiBin;
    const unsigned long long id32 = (1ULL << 29) | (5ULL << 26) | ((unsigned long long)(posNeg > 0 ? 1 : 0) << 25)
                                  | ((unsigned long long)(fcalMod - 1) << 23)
                                  | ((unsigned long long)etaIndex << 17)
                                  | ((unsigned long long)phiIndex << 13);
    const long long cellID = (long long)( id32 << 32 );

    double t = 0.0, tglobal = 0.0;
    if( isSpot ){
      t = preP->GetGlobalTime() / CLHEP::ns;
      tglobal = t + preP->GetPosition().mag() / CLHEP::c_light;
    } else {
      const G4ThreeVector mid = 0.5 * ( preP->GetPosition() + postP->GetPosition() );
      tglobal = 0.5 * ( preP->GetGlobalTime() + postP->GetGlobalTime() ) / CLHEP::ns;
      t = tglobal - mid.mag() / CLHEP::c_light;
    }

    int timeBin = -1;
    if( m_binning ){
      if     ( t < 0.   ) timeBin = 0;
      else if( t < 10.  ) timeBin = (int)( t / 2.5 );
      else if( t < 50.  ) timeBin = 4 + (int)( ( t - 10. ) / 5. );
      else if( t < 100. ) timeBin = 12 + (int)( ( t - 50. ) / 25. );
      else                timeBin = 14;
    }

    int source = isSpot ? 1 : 0;
    list->addLAr( cellID, energy / CLHEP::MeV, t, tglobal, cell.eta, cell.phi, fcalMod, posNeg, 0, 4, timeBin, source );
    return;
  }

  // EMB / EMEC / HEC
  const int nPhi = m_nPhiBins > 0 ? m_nPhiBins : ( (int)m_phiBins.size() > 1 ? (int)m_phiBins.size() - 1 : 64 );
  const int phiIndex = ( cell.phiBin + nPhi / 2 ) % nPhi;
  int cellIdx = cell.cell >= 0 ? cell.cell : cell.etaBin;
  const int etaIndex = ( cellIdx >= 0 && cellIdx < (int)m_cellAtlasEtaIndex.size() ) ? m_cellAtlasEtaIndex[cellIdx] : cell.etaBin;
  unsigned long long id32 = 0;
  int det = 0;
  if( m_atlasLArPart == 1 ){
    static const int beValues[6] = {-3, -2, -1, 1, 2, 3};
    int beIndex = -1;
    for( int k = 0; k < 6; ++k ) if( beValues[k] == m_atlasBarrelEc ) beIndex = k;
    if( beIndex < 0 ){ MSG_FATAL( "AtlasBarrelEc " << m_atlasBarrelEc << " is not a LArEM barrel_ec" ); }
    id32 = (1ULL << 29) | (3ULL << 26) | ((unsigned long long)beIndex << 23) | ((unsigned long long)m_atlasLArSampling << 21)
         | ((unsigned long long)m_atlasLArRegion << 18) | ((unsigned long long)etaIndex << 9) | ((unsigned long long)phiIndex << 1);
    det = ( std::abs(m_atlasBarrelEc) == 1 ) ? 1 : 2;
  }else{
    id32 = (1ULL << 29) | (4ULL << 26) | ((unsigned long long)(m_atlasBarrelEc > 0 ? 1 : 0) << 25)
         | ((unsigned long long)m_atlasLArSampling << 23) | ((unsigned long long)m_atlasLArRegion << 22)
         | ((unsigned long long)etaIndex << 18) | ((unsigned long long)phiIndex << 12);
    det = 3;
  }
  const long long cellID = (long long)( id32 << 32 );

  const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
  double tglobal = 0.0, mag = 0.0;
  if( std::abs(m_atlasBarrelEc) == 1 && m_atlasLArPart == 1 ){
    tglobal = preP->GetGlobalTime() / CLHEP::ns;
    mag = preP->GetPosition().mag();
  }else{
    tglobal = 0.5 * ( preP->GetGlobalTime() + postP->GetGlobalTime() ) / CLHEP::ns;
    mag = ( 0.5 * ( preP->GetPosition() + postP->GetPosition() ) ).mag();
  }
  const double t = tglobal - mag / cLight;
  int timeBin = -1;
  if( m_binning ){
    if     ( t < 0.   ) timeBin = 0;
    else if( t < 10.  ) timeBin = (int)( t / 2.5 );
    else if( t < 50.  ) timeBin = 4 + (int)( ( t - 10. ) / 5. );
    else if( t < 100. ) timeBin = 12 + (int)( ( t - 50. ) / 25. );
    else                timeBin = 14;
  }

  double phiCentre = 0.0;
  if( cell.phiBin >= 0 && cell.phiBin + 1 < (int)m_phiBins.size() ){
    phiCentre = std::remainder( 0.5 * ( m_phiBins[cell.phiBin] + m_phiBins[cell.phiBin+1] ), 2 * M_PI );
  } else {
    phiCentre = cell.phi;
  }
  double cellEta = ( cellIdx >= 0 && cellIdx < (int)m_cellEta.size() ) ? (double)m_cellEta[cellIdx] : (double)cell.eta;

  list->addLAr( cellID, energy / CLHEP::MeV, t, tglobal, cellEta, phiCentre, m_atlasLArSampling, m_atlasBarrelEc,
                m_atlasLArRegion, det, timeBin );
}
