#include "src/LArFCalElectrodeTool.h"
#include "CaloHit/CaloHit.h"
#include "CaloHit/CaloHitCollection.h"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4ThreeVector.hh"
#include "G4VPhysicalVolume.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include "CLHEP/Units/PhysicalConstants.h"
#include <cmath>

LArFCalElectrodeTool::LArFCalElectrodeTool( std::string name )
  : IMsgService(name), ICaloCellIdentifierTool(name)
{
  declareProperty( "FCalModule"       , m_fcalModule = 0 );
  declareProperty( "FCalSide"         , m_fcalSide = 1 );
  declareProperty( "FCalGapVolume"    , m_fcalGapVolume = "" );
  declareProperty( "FCalCopyEtaIndex" , m_fcalCopyEtaIndex );
  declareProperty( "FCalCopyPhiIndex" , m_fcalCopyPhiIndex );
  declareProperty( "FCalCopyEta"      , m_fcalCopyEta );
  declareProperty( "FCalCopyPhi"      , m_fcalCopyPhi );
  declareProperty( "FCalCopyDeltaEta" , m_fcalCopyDeltaEta );
  declareProperty( "FCalCopyDeltaPhi" , m_fcalCopyDeltaPhi );
  declareProperty( "FCalCopyI"        , m_fcalCopyI );
  declareProperty( "FCalCopyJ"        , m_fcalCopyJ );
  declareProperty( "FCalCopyX"        , m_fcalCopyX );
  declareProperty( "FCalCopyY"        , m_fcalCopyY );
  declareProperty( "ActiveEnergyOnly" , m_activeEnergyOnly = false );
  declareProperty( "BcDuration"       , m_bc_duration = 25.0f );
  declareProperty( "BcidStart"        , m_bcid_start = -7 );
  declareProperty( "BcidEnd"          , m_bcid_end = 7 );
  declareProperty( "Sampling"         , m_sampling = 0 );
  declareProperty( "Detector"         , m_detector = 0 );
  declareProperty( "Segment"          , m_segment = 0 );
  declareProperty( "ZMin"             , m_zMin = 0.0 );
  declareProperty( "ZMax"             , m_zMax = 0.0 );
}

StatusCode LArFCalElectrodeTool::initialize()
{
  if( m_fcalModule > 0 ){
    if( m_fcalModule > 3 || m_fcalGapVolume.empty() || m_fcalCopyEtaIndex.empty() ||
        m_fcalCopyPhiIndex.size() != m_fcalCopyEtaIndex.size() || m_fcalCopyEta.size() != m_fcalCopyEtaIndex.size() ||
        m_fcalCopyPhi.size() != m_fcalCopyEtaIndex.size() || m_fcalCopyDeltaEta.size() != m_fcalCopyEtaIndex.size() ||
        m_fcalCopyDeltaPhi.size() != m_fcalCopyEtaIndex.size() ){
      MSG_FATAL( "FCalModule needs the cell, centre and width of every electrode (geometry/python/v2/FCAL.py)." );
      return StatusCode::FAILURE;
    }
    // centre and width of each tile, for the hits of the normal chain (one hit per tile)
    for( size_t k = 0; k < m_fcalCopyEtaIndex.size(); ++k ){
      const auto tile = std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] );
      m_fcalTileCentre.emplace( tile, std::make_pair( m_fcalCopyEta[k], m_fcalCopyPhi[k] ) );
      m_fcalTileWidth.emplace( tile, std::make_pair( m_fcalCopyDeltaEta[k], m_fcalCopyDeltaPhi[k] ) );
    }

    // tube map of FCAL_ChannelMap::add_tube (F41 conserto 23)
    if( !m_fcalCopyI.empty() ){
      const size_t n = m_fcalCopyEtaIndex.size();
      if( m_fcalCopyJ.size() != n || m_fcalCopyX.size() != n || m_fcalCopyY.size() != n || m_fcalCopyI.size() != n ){
        MSG_FATAL( "FCalCopyI, FCalCopyJ, FCalCopyX and FCalCopyY need one entry per electrode." );
        return StatusCode::FAILURE;
      }
      std::map<unsigned int, size_t> first;
      for( size_t k = 0; k < n; ++k ){
        const unsigned int key = ( (unsigned int)( m_fcalCopyJ[k] + 200 ) << 16 ) + (unsigned int)( m_fcalCopyI[k] + 200 );
        m_fcalTubeMap.emplace( key, std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] ) );
        first.emplace( key, k );
        m_fcalTileCentre.emplace( std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] ),
                                  std::make_pair( m_fcalCopyEta[k], m_fcalCopyPhi[k] ) );
      }
      m_fcalFirstTube  = first.begin()->first;
      m_fcalFirstTubeX = m_fcalCopyX[first.begin()->second];
      m_fcalFirstTubeY = m_fcalCopyY[first.begin()->second];
    }
  }

  return StatusCode::SUCCESS;
}

StatusCode LArFCalElectrodeTool::finalize()
{
  return StatusCode::SUCCESS;
}

StatusCode LArFCalElectrodeTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
{
  if( !collection ) return StatusCode::FAILURE;
  for( const auto &c : m_fcalTileCentre ){
    auto itW = m_fcalTileWidth.find( c.first );
    if( itW == m_fcalTileWidth.end() ) continue;
    const auto &w = itW->second;
    const unsigned bin = 16 * c.first.first + c.first.second;
    auto *hit = new xAOD::CaloHit( c.second.first, c.second.second, w.first, w.second, hash(bin),
                                   (CaloSampling)m_sampling, (Detector)m_detector,
                                   m_bc_duration, m_bcid_start, m_bcid_end );
    if( !collection->insert( hit->hash(), hit ) ){
      MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist." );
      delete hit;
      return StatusCode::FAILURE;
    }
  }
  return StatusCode::SUCCESS;
}

bool LArFCalElectrodeTool::isShowerSpot( const G4Step *step ) const
{
  return step && ( step->GetPreStepPoint()->GetTouchable() == nullptr );
}

bool LArFCalElectrodeTool::fcalTileID( double x, double y, int &eta, int &phi ) const
{
  static const double spacing[3] = { 7.5, 8.179, 9.0 };
  if( m_fcalModule < 1 || m_fcalModule > 3 ) return false;
  const double tubeDx = spacing[m_fcalModule - 1] / 2., tubeDy = spacing[m_fcalModule - 1] * std::sqrt(3.) / 2.;
  int ktx = (int)( x / tubeDx );
  int kty = (int)( y / tubeDy );
  if( x < 0. ) ktx--;
  if( y < 0. ) kty--;
  const unsigned int firstId = m_fcalFirstTube;
  int ix = ktx + ( (int)( (firstId & 0xffff) - m_fcalFirstTubeX / tubeDx ) ) + 1;
  int iy = kty + ( (int)( (firstId >> 16) - m_fcalFirstTubeY / tubeDy ) ) + 1;
  const int isOddEven = ( ( (firstId >> 16) % 2 ) + ( firstId % 2 ) ) % 2;
  bool movex = false;
  if( ( iy % 2 ) != ( ( ix + isOddEven ) % 2 ) ){
    const double yc = y / tubeDy - kty - 0.5;
    if( std::fabs(yc) > 0.5 / std::sqrt(3) ){
      double xk = x / tubeDx - ktx;
      if( xk > 0.5 ) xk = 1 - xk;
      const double yn = 0.5 - xk * ( 1. / 3 );
      if( std::fabs(yc) > std::fabs(yn) ){
        if( yc > 0 ) iy++; else iy--;
      }else movex = true;
    }else movex = true;
    if( movex ){
      if( x / tubeDx - ktx > 0.5 ) ix++; else ix--;
    }
  }
  const unsigned int tubeID = ( (unsigned int)iy << 16 ) + (unsigned int)ix;
  auto it = m_fcalTubeMap.find( tubeID );
  if( it == m_fcalTubeMap.end() ) return false;
  eta = it->second.first;
  phi = it->second.second;
  return true;
}

unsigned long int LArFCalElectrodeTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}

CellIdentification LArFCalElectrodeTool::identify( const G4Step *step ) const
{
  CellIdentification cell;
  cell.isValid = false;
  if( !step ) return cell;

  if( isShowerSpot( step ) ){
    const G4StepPoint *preP = step->GetPreStepPoint();
    const G4ThreeVector pos = preP->GetPosition();
    if( !( pos.z() > m_zMin && pos.z() <= m_zMax ) ) return cell;
    int etaIndex = -1, phiIndex = -1;
    if( !fcalTileID( (float)pos.x(), (float)pos.y(), etaIndex, phiIndex ) ) return cell;
    cell.isValid = true;
    cell.cell = 16 * etaIndex + phiIndex;
    cell.etaBin = etaIndex;
    cell.phiBin = phiIndex;
    cell.hashId = hash( (unsigned)cell.cell );
    auto itC = m_fcalTileCentre.find( std::make_pair( etaIndex, phiIndex ) );
    if( itC != m_fcalTileCentre.end() ){
      cell.eta = itC->second.first;
      cell.phi = itC->second.second;
    }
    auto itW = m_fcalTileWidth.find( std::make_pair( etaIndex, phiIndex ) );
    if( itW != m_fcalTileWidth.end() ){
      cell.dEta = itW->second.first;
      cell.dPhi = itW->second.second;
    }
    cell.sampling = m_sampling;
    cell.detector = m_detector;
    cell.atlasModule = m_fcalModule;
    cell.atlasSide = pos.z() > 0 ? 2 : -2;
    cell.atlasSubdet = 4;
    cell.atlasSource = 1; // Shower spot indicator
    return cell;
  }

  const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
  const G4VPhysicalVolume *pv = preP->GetPhysicalVolume();
  if( !pv || pv->GetLogicalVolume()->GetName() != m_fcalGapVolume ) return cell;
  if( m_activeEnergyOnly ){
    const G4Material *material = preP->GetMaterial();
    if( !material || material->GetName() != "liquidArgon" ) return cell;
  }
  const int copy = pv->GetCopyNo();
  if( copy < 0 || copy >= (int)m_fcalCopyEtaIndex.size() ){
    MSG_FATAL( "FCal module " << m_fcalModule << ": copy number " << copy << " without a cell" );
    return cell;
  }
  int eta = m_fcalCopyEtaIndex[copy];
  int phi = m_fcalCopyPhiIndex[copy];
  cell.isValid = true;
  cell.cell = 16 * eta + phi;
  cell.hashId = hash( (unsigned)cell.cell );
  cell.etaBin = eta;
  cell.phiBin = phi;
  cell.eta = m_fcalCopyEta[copy];
  cell.phi = m_fcalCopyPhi[copy];
  cell.dEta = m_fcalCopyDeltaEta[copy];
  cell.dPhi = m_fcalCopyDeltaPhi[copy];
  cell.sampling = m_sampling;
  cell.detector = m_detector;
  cell.atlasModule = m_fcalModule;
  const G4ThreeVector mid = 0.5 * ( preP->GetPosition() + postP->GetPosition() );
  cell.atlasSide = mid.z() > 0 ? 2 : -2;
  cell.atlasSubdet = 4;
  cell.atlasSource = 0; // Normal step
  return cell;
}
