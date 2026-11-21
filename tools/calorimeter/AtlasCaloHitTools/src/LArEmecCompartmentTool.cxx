#include "src/LArEmecCompartmentTool.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "TVector3.h"
#include <cmath>
#include <algorithm>

static inline double emecZ( int zTable ) { return zTable * 1.0E-4 * 10.; } // 1e-4 cm to mm

LArEmecCompartmentTool::LArEmecCompartmentTool( std::string name )
  : IMsgService(name), ICaloCellIdentifierTool(name)
{
  declareProperty( "Sampling"          , m_sampling = 0 );
  declareProperty( "Segment"           , m_segment = 0 );
  declareProperty( "Detector"          , m_detector = 0 );
  declareProperty( "ZMin"              , m_zMin = 0.0f );
  declareProperty( "ZMax"              , m_zMax = 0.0f );
  declareProperty( "RMin"              , m_rMin = 0.0f );
  declareProperty( "RMax"              , m_rMax = 0.0f );
  declareProperty( "ActiveEnergyOnly"  , m_activeEnergyOnly = false );
  declareProperty( "BcDuration"        , m_bc_duration = 25.0f );
  declareProperty( "BcidStart"         , m_bcid_start = -7 );
  declareProperty( "BcidEnd"           , m_bcid_end = 7 );

  declareProperty( "PhiBins"           , m_phiBins );
  declareProperty( "CellEta"           , m_cellEta );
  declareProperty( "CellDeltaEta"      , m_cellDeltaEta );

  declareProperty( "EmecCompartment"   , m_emecCompartment = 0 );
  declareProperty( "EmecEtaScale"      , m_emecEtaScale = 0.0f );
  declareProperty( "EmecEtaOffset"     , m_emecEtaOffset = 0.0f );
  declareProperty( "EmecMaxEta"        , m_emecMaxEta = 0 );
  declareProperty( "EmecFocalShift"    , m_emecFocalShift = 0.0f );
  declareProperty( "EmecZSep12"        , m_emecZSep12 );
  declareProperty( "EmecZSep23"        , m_emecZSep23 );
  declareProperty( "EmecZInner"        , m_emecZInner );
  declareProperty( "EmecWheelRMin"     , m_emecWheelRMin );
  declareProperty( "EmecWheelRMax"     , m_emecWheelRMax );
  declareProperty( "EmecWheelZMin"     , m_emecWheelZMin );
  declareProperty( "EmecWheelZMax"     , m_emecWheelZMax );

  declareProperty( "AtlasBarrelEc"     , m_atlasBarrelEc = 0 );
  declareProperty( "AtlasLArSampling"  , m_atlasLArSampling = 0 );
  declareProperty( "AtlasLArRegion"    , m_atlasLArRegion = 0 );
  declareProperty( "CellAtlasEtaIndex" , m_cellAtlasEtaIndex );
  declareProperty( "PhiShift"          , m_phiShift = 0.0f );
}

StatusCode LArEmecCompartmentTool::initialize()
{
  m_nPhiBins = m_phiBins.empty() ? 0 : m_phiBins.size() - 1;
  return StatusCode::SUCCESS;
}

StatusCode LArEmecCompartmentTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
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

CellIdentification LArEmecCompartmentTool::identify( const G4Step *step ) const
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

  int etaBin = -1, phiBin = -1;
  if( emecFindCell( pos.x(), pos.y(), pos.z(), etaBin, phiBin ) != m_emecCompartment )
    return cell;

  if( etaBin < 0 || phiBin < 0 ) return cell;

  unsigned bin = m_nPhiBins * etaBin + phiBin;

  cell.isValid = true;
  cell.hashId = hash(bin);
  cell.etaBin = etaBin;
  cell.phiBin = phiBin;
  cell.eta = (etaBin >= 0 && etaBin < (int)m_cellEta.size()) ? m_cellEta[etaBin] : 0.0f;
  cell.phi = (phiBin >= 0 && phiBin < (int)m_phiBins.size()) ? m_phiBins[phiBin] : 0.0f;
  cell.sampling = m_sampling;
  cell.detector = m_detector;

  // ATLAS identifier fields
  cell.atlasSubdet = 2; // EMEC
  const int nPhi = (int)m_nPhiBins;
  const int phiIndex = ( phiBin + nPhi / 2 ) % nPhi;
  const int etaIndex = (etaBin >= 0 && etaBin < (int)m_cellAtlasEtaIndex.size()) ? m_cellAtlasEtaIndex[etaBin] : etaBin;

  static const int beValues[6] = {-3, -2, -1, 1, 2, 3};
  int beIndex = -1;
  for( int k = 0; k < 6; ++k ) if( beValues[k] == m_atlasBarrelEc ) beIndex = k;
  if( beIndex >= 0 ){
    unsigned long long id32 = (1ULL << 29) | (3ULL << 26) | ((unsigned long long)beIndex << 23)
                            | ((unsigned long long)m_atlasLArSampling << 21)
                            | ((unsigned long long)m_atlasLArRegion << 18)
                            | ((unsigned long long)etaIndex << 9)
                            | ((unsigned long long)phiIndex << 1);
    cell.atlasCellID = (long long)( id32 << 32 );
  }

  return cell;
}

int LArEmecCompartmentTool::emecFindCell( double x, double y, double z, int &etaBin, int &phiBin ) const
{
  etaBin = -1; phiBin = -1;
  const double r = std::sqrt( x*x + y*y );
  bool inWheel = false;
  for ( unsigned box = 0; box < m_emecWheelRMin.size(); ++box ){
    if( r > m_emecWheelRMin[box] && r <= m_emecWheelRMax[box] && z > m_emecWheelZMin[box] && z <= m_emecWheelZMax[box] ){
      inWheel = true;
      break;
    }
  }
  if( !inWheel ) return 0;

  const double zf = std::abs(z) - (double)m_emecFocalShift;
  const double mag = std::sqrt( x*x + y*y + zf*zf );
  double eta;
  if( mag == 0 ) eta = 0;
  else if( mag == zf ) eta = 1.0E72;
  else if( mag == -zf ) eta = -1.0E72;
  else eta = 0.5 * std::log( (mag + zf) / (mag - zf) );

  int compartment = 0;
  if( m_emecCompartment <= 2 ){
    int ipad = (int)( (eta - 2.5) / 0.1 );
    if( ipad < 0 ) ipad = 0;
    if( ipad > 6 ) ipad = 6;
    compartment = ( zf < emecZ(m_emecZInner[ipad]) ) ? 1 : 2;
  }else{
    int ipad = (int)( (eta - 1.4) / 0.025 );
    if( ipad < 0 ) ipad = 0;
    if( ipad > 43 ) ipad = 43;
    if( zf < emecZ(m_emecZSep12[ipad]) ){
      if     ( eta > 2.4   ) compartment = 3;
      else if( eta > 2.0   ) compartment = 4;
      else if( eta > 1.8   ) compartment = 5;
      else if( eta > 1.5   ) compartment = 6;
      else if( eta > 1.425 ) compartment = 7;
      else                   compartment = 10;
    }else if( zf < emecZ(m_emecZSep23[ipad/2]) ){
      compartment = ( eta > 1.425 ) ? 8 : 11;
    }else{
      compartment = 9;
    }
  }
  if( compartment != m_emecCompartment ) return compartment;

  etaBin = (int)( eta * (double)m_emecEtaScale - (double)m_emecEtaOffset );
  if( etaBin < 0 ) etaBin = 0;
  if( etaBin > m_emecMaxEta ) etaBin = m_emecMaxEta;

  const int nPhi = (int)m_phiBins.size() - 1;
  double phi = std::atan2( y, x ) - m_phiShift;
  while( phi < 0 ) phi += 2 * M_PI;
  while( phi >= 2 * M_PI ) phi -= 2 * M_PI;
  int k = (int)std::floor( phi / ( 2 * M_PI / nPhi ) );
  if( k >= nPhi ) k = nPhi - 1;
  phiBin = ( k + nPhi / 2 ) % nPhi;
  return compartment;
}

unsigned long int LArEmecCompartmentTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}
