#include "src/CaloGridCellTool.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "TVector3.h"
#include <cmath>
#include <algorithm>

CaloGridCellTool::CaloGridCellTool( std::string name )
  : IMsgService(name), ICaloCellIdentifierTool(name)
{
  declareProperty( "EtaBins"         , m_etaBins );
  declareProperty( "PhiBins"         , m_phiBins );
  declareProperty( "Sampling"        , m_sampling = 0 );
  declareProperty( "Segment"         , m_segment = 0 );
  declareProperty( "Detector"        , m_detector = 0 );
  declareProperty( "ZMin"            , m_zMin = 0.0f );
  declareProperty( "ZMax"            , m_zMax = 0.0f );
  declareProperty( "RMin"            , m_rMin = 0.0f );
  declareProperty( "RMax"            , m_rMax = 0.0f );
  declareProperty( "ActiveEnergyOnly", m_activeEnergyOnly = false );
  declareProperty( "BcDuration"      , m_bc_duration = 25.0f );
  declareProperty( "BcidStart"       , m_bcid_start = -7 );
  declareProperty( "BcidEnd"         , m_bcid_end = 7 );
}

StatusCode CaloGridCellTool::initialize()
{
  m_nEtaBins = m_etaBins.empty() ? 0 : m_etaBins.size() - 1;
  m_nPhiBins = m_phiBins.empty() ? 0 : m_phiBins.size() - 1;
  return StatusCode::SUCCESS;
}

StatusCode CaloGridCellTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
{
  if( !collection ) return StatusCode::FAILURE;
  if( m_etaBins.size() < 2 || m_phiBins.size() < 2 ) return StatusCode::SUCCESS;

  float deltaEta = std::abs(m_etaBins[1] - m_etaBins[0]);
  float deltaPhi = std::abs(m_phiBins[1] - m_phiBins[0]);

  for ( unsigned etaBin = 0; etaBin < m_nEtaBins; ++etaBin ){
    for ( unsigned phiBin = 0; phiBin < m_nPhiBins; ++phiBin ){
      float etaCenter = m_etaBins[etaBin] + deltaEta / 2;
      float phiCenter = m_phiBins[phiBin] + deltaPhi / 2;
      unsigned bin = m_nPhiBins * etaBin + phiBin;
      auto *hit = new xAOD::CaloHit( etaCenter, phiCenter, deltaEta, deltaPhi, hash(bin), 
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

CellIdentification CaloGridCellTool::identify( const G4Step *step ) const
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
  auto vpos = TVector3( pos.x(), pos.y(), pos.z() );
  float eta = vpos.PseudoRapidity();
  float phi = vpos.Phi();

  const G4ThreeVector rpos = 0.5 * ( pos + step->GetPostStepPoint()->GetPosition() );
  const float rradius = rpos.perp();
  if( !(rradius > m_rMin && rradius <= m_rMax) ) return cell;
  if( !(rpos.z() > m_zMin && rpos.z() <= m_zMax) ) return cell;

  int etaBin = find( m_etaBins, eta );
  if( etaBin < 0 ) return cell;

  int phiBin = findPhi( phi );
  if( phiBin < 0 ) return cell;

  unsigned int bin = m_nPhiBins * etaBin + phiBin;

  cell.isValid = true;
  cell.hashId = hash(bin);
  cell.etaBin = etaBin;
  cell.phiBin = phiBin;
  cell.eta = eta;
  cell.phi = phi;
  cell.sampling = m_sampling;
  cell.detector = m_detector;
  return cell;
}

int CaloGridCellTool::find( const std::vector<float> &vec, float value ) const
{
  auto binIterator = std::adjacent_find( vec.begin(), vec.end(), [=](float left, float right){ return left < value and value <= right; } );
  if ( binIterator == vec.end() ) return -1;
  return binIterator - vec.begin();
}

int CaloGridCellTool::findPhi( float phi ) const
{
  int bin = find( m_phiBins, phi );
  if( bin < 0 ) bin = find( m_phiBins, phi + 2 * M_PI );
  if( bin < 0 ) bin = find( m_phiBins, phi - 2 * M_PI );
  return bin;
}

unsigned long int CaloGridCellTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}
