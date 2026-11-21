#include "src/LArHecModuleTool.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "TVector3.h"
#include <cmath>
#include <algorithm>

LArHecModuleTool::LArHecModuleTool( std::string name )
  : IMsgService(name), ICaloCellIdentifierTool(name)
{
  declareProperty( "Sampling"         , m_sampling = 0 );
  declareProperty( "Segment"          , m_segment = 0 );
  declareProperty( "Detector"         , m_detector = 0 );
  declareProperty( "ZMin"             , m_zMin = 0.0f );
  declareProperty( "ZMax"             , m_zMax = 0.0f );
  declareProperty( "RMin"             , m_rMin = 0.0f );
  declareProperty( "RMax"             , m_rMax = 0.0f );
  declareProperty( "ActiveEnergyOnly" , m_activeEnergyOnly = false );
  declareProperty( "BcDuration"       , m_bc_duration = 25.0f );
  declareProperty( "BcidStart"        , m_bcid_start = -7 );
  declareProperty( "BcidEnd"          , m_bcid_end = 7 );

  declareProperty( "PhiBins"          , m_phiBins );
  declareProperty( "CellEta"          , m_cellEta );
  declareProperty( "CellDeltaEta"     , m_cellDeltaEta );
  declareProperty( "CellBoxRMin"      , m_cellBoxRMin );
  declareProperty( "CellBoxRMax"      , m_cellBoxRMax );
  declareProperty( "CellBoxZMin"      , m_cellBoxZMin );
  declareProperty( "CellBoxZMax"      , m_cellBoxZMax );
  declareProperty( "CellBoxIndex"     , m_cellBoxIndex );
  declareProperty( "CellRadiusModules", m_cellRadiusModules = 32 );

  declareProperty( "AtlasBarrelEc"    , m_atlasBarrelEc = 0 );
  declareProperty( "AtlasLArSampling" , m_atlasLArSampling = 0 );
  declareProperty( "AtlasLArRegion"   , m_atlasLArRegion = 0 );
  declareProperty( "CellAtlasEtaIndex", m_cellAtlasEtaIndex );
  declareProperty( "PhiShift"         , m_phiShift = 0.0f );
}

StatusCode LArHecModuleTool::initialize()
{
  m_nPhiBins = m_phiBins.empty() ? 0 : m_phiBins.size() - 1;
  return StatusCode::SUCCESS;
}

StatusCode LArHecModuleTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
{
  if( !collection ) return StatusCode::FAILURE;
  if( m_phiBins.size() < 2 || m_cellEta.empty() ) return StatusCode::SUCCESS;

  float deltaPhi = std::abs(m_phiBins[1] - m_phiBins[0]);

  for ( unsigned cell = 0; cell < m_cellEta.size(); ++cell ){
    for ( unsigned phiBin = 0; phiBin < m_nPhiBins; ++phiBin ){
      float phiCenter = m_phiBins[phiBin] + deltaPhi / 2;
      unsigned bin = m_nPhiBins * cell + phiBin;
      auto *hit = new xAOD::CaloHit( m_cellEta[cell], phiCenter, m_cellDeltaEta[cell], deltaPhi, hash(bin),
                                     (CaloSampling)m_sampling,
                                     (Detector)m_detector,
                                     m_bc_duration, m_bcid_start, m_bcid_end );
      if( !collection->insert( hit->hash(), hit) ){
        MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist.");
        delete hit;
        return StatusCode::FAILURE;
      }
    }
  }
  return StatusCode::SUCCESS;
}

CellIdentification LArHecModuleTool::identify( const G4Step *step ) const
{
  CellIdentification cell;
  cell.isValid = false;
  if( !step ) return cell;

  if( m_activeEnergyOnly ){
    const G4Material *material = step->GetPreStepPoint()->GetMaterial();
    if( !material ) return cell;
    const G4String &materialName = material->GetName();
    if( materialName != "liquidArgon" && materialName != "PLASTIC SCINTILLATOR" && materialName != "ATLAS_TILE_PVT" )
      return cell;
  }

  G4ThreeVector pos = step->GetPreStepPoint()->GetPosition();
  const G4ThreeVector rpos = 0.5 * ( pos + step->GetPostStepPoint()->GetPosition() );
  const float rradius = rpos.perp();
  if( !(rradius > m_rMin && rradius <= m_rMax) ) return cell;
  if( !(rpos.z() > m_zMin && rpos.z() <= m_zMax) ) return cell;

  const float cellPhi = (float)rpos.phi();
  float rMod = cellRadius( rradius, cellPhi );
  int etaBin = findCell( rMod, (float)rpos.z() );
  if( etaBin < 0 ) return cell;

  int phiBin = findPhi( cellPhi );
  if( phiBin < 0 ) return cell;

  unsigned bin = m_nPhiBins * etaBin + phiBin;

  cell.isValid = true;
  cell.hashId = hash(bin);
  cell.etaBin = etaBin;
  cell.phiBin = phiBin;
  cell.eta = (etaBin >= 0 && etaBin < (int)m_cellEta.size()) ? m_cellEta[etaBin] : 0.0f;
  cell.phi = cellPhi;
  cell.sampling = m_sampling;
  cell.detector = m_detector;

  // ATLAS identifier fields
  cell.atlasSubdet = 3; // HEC
  const int nPhi = (int)m_nPhiBins;
  const int phiIndex = ( phiBin + nPhi / 2 ) % nPhi;
  const int etaIndex = (etaBin >= 0 && etaBin < (int)m_cellAtlasEtaIndex.size()) ? m_cellAtlasEtaIndex[etaBin] : etaBin;

  int pos_neg = (m_atlasBarrelEc > 0 ? 1 : 0);
  unsigned long long id32 = (1ULL << 29) | (4ULL << 26) | ((unsigned long long)pos_neg << 25)
                          | ((unsigned long long)m_atlasLArSampling << 23)
                          | ((unsigned long long)m_atlasLArRegion << 22)
                          | ((unsigned long long)etaIndex << 18)
                          | ((unsigned long long)phiIndex << 12);
  cell.atlasCellID = (long long)( id32 << 32 );

  return cell;
}

int LArHecModuleTool::findCell( float radius, float z ) const
{
  for ( unsigned box = 0; box < m_cellBoxIndex.size(); ++box ){
    if( radius > m_cellBoxRMin[box] && radius <= m_cellBoxRMax[box] &&
        z > m_cellBoxZMin[box] && z <= m_cellBoxZMax[box] )
      return m_cellBoxIndex[box];
  }
  return -1;
}

float LArHecModuleTool::cellRadius( float radius, float phi ) const
{
  if( m_cellRadiusModules <= 0 ) return radius;
  const double twoPi = 2 * M_PI, width = twoPi / m_cellRadiusModules;
  double phi0 = phi < 0 ? phi + twoPi : phi;
  int module = (int)std::floor( phi0 / width );
  if( module >= m_cellRadiusModules ) module = m_cellRadiusModules - 1;
  return (float)( radius * std::cos( phi0 - (module + 0.5) * width ) );
}

int LArHecModuleTool::find( const std::vector<float> &vec, float value ) const
{
  auto binIterator = std::adjacent_find( vec.begin(), vec.end(), [=](float left, float right){ return left < value and value <= right; } );
  if ( binIterator == vec.end() ) return -1;
  return binIterator - vec.begin();
}

int LArHecModuleTool::findPhi( float phi ) const
{
  int bin = find( m_phiBins, phi );
  if( bin < 0 ) bin = find( m_phiBins, phi + 2 * M_PI );
  if( bin < 0 ) bin = find( m_phiBins, phi - 2 * M_PI );
  return bin;
}

unsigned long int LArHecModuleTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}
