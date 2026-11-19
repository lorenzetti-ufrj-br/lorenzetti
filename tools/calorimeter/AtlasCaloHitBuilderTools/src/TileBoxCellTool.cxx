#include "src/TileBoxCellTool.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "TVector3.h"
#include <cmath>
#include <algorithm>

TileBoxCellTool::TileBoxCellTool( std::string name )
  : IMsgService(name), ICaloCellIdentifierTool(name)
{
  declareProperty( "Sampling"            , m_sampling = 0 );
  declareProperty( "Segment"             , m_segment = 0 );
  declareProperty( "Detector"            , m_detector = 0 );
  declareProperty( "ZMin"                , m_zMin = 0.0f );
  declareProperty( "ZMax"                , m_zMax = 0.0f );
  declareProperty( "RMin"                , m_rMin = 0.0f );
  declareProperty( "RMax"                , m_rMax = 0.0f );
  declareProperty( "ActiveEnergyOnly"    , m_activeEnergyOnly = false );
  declareProperty( "BcDuration"          , m_bc_duration = 25.0f );
  declareProperty( "BcidStart"           , m_bcid_start = -7 );
  declareProperty( "BcidEnd"             , m_bcid_end = 7 );
  declareProperty( "TileDualReadout"     , m_tileDualReadout = 0 );

  declareProperty( "PhiBins"             , m_phiBins );
  declareProperty( "CellEta"             , m_cellEta );
  declareProperty( "CellDeltaEta"        , m_cellDeltaEta );
  declareProperty( "CellBoxRMin"         , m_cellBoxRMin );
  declareProperty( "CellBoxRMax"         , m_cellBoxRMax );
  declareProperty( "CellBoxZMin"         , m_cellBoxZMin );
  declareProperty( "CellBoxZMax"         , m_cellBoxZMax );
  declareProperty( "CellBoxIndex"        , m_cellBoxIndex );

  declareProperty( "CellNPmt"            , m_cellNPmt );
  declareProperty( "SpecialModule"       , m_specialModule );
  declareProperty( "SpecialNPmt"         , m_specialNPmt );

  declareProperty( "ReplaceSection"      , m_replaceSection = 0 );
  declareProperty( "ReplaceTower"        , m_replaceTower = 0 );
  declareProperty( "ReplaceSampling"     , m_replaceSampling = 0 );
  declareProperty( "ReplaceRCentre"      , m_replaceRCentre = 0.0f );
  declareProperty( "ReplaceZCentre"      , m_replaceZCentre = 0.0f );
  declareProperty( "ReplaceCollectionKey", m_replaceCollectionKey = "" );
  declareProperty( "ReplaceHashBase"     , m_replaceHashBase = 0 );

  declareProperty( "CellAtlasSection"    , m_cellAtlasSection );
  declareProperty( "CellAtlasTower"      , m_cellAtlasTower );
  declareProperty( "CellAtlasSampling"   , m_cellAtlasSampling );
  declareProperty( "CellRCentre"         , m_cellRCentre );
  declareProperty( "CellZCentre"         , m_cellZCentre );
}

StatusCode TileBoxCellTool::initialize()
{
  m_nPhiBins = m_phiBins.empty() ? 0 : m_phiBins.size() - 1;
  return StatusCode::SUCCESS;
}

StatusCode TileBoxCellTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
{
  if( !collection ) return StatusCode::FAILURE;
  if( m_phiBins.size() < 2 || m_cellEta.empty() ) return StatusCode::SUCCESS;

  float deltaPhi = std::abs(m_phiBins[1] - m_phiBins[0]);

  for ( unsigned cell = 0; cell < m_cellEta.size(); ++cell ){
    for ( unsigned phiBin = 0; phiBin < m_nPhiBins; ++phiBin ){
      if( !m_replaceCollectionKey.empty() && tileNPmt( cell, phiBin ) == 0 ) continue;
      float phiCenter = m_phiBins[phiBin] + deltaPhi / 2;
      unsigned bin = m_nPhiBins * cell + phiBin;
      auto *hit = new xAOD::CaloHit( m_cellEta[cell], phiCenter, m_cellDeltaEta[cell], deltaPhi, hash(bin),
                                     (CaloSampling)m_sampling,
                                     (Detector)m_detector,
                                     m_bc_duration, m_bcid_start, m_bcid_end );
      hit->setDualReadout( m_tileDualReadout > 0 );
      if( !collection->insert( hit->hash(), hit) ){
        MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist.");
        delete hit;
        return StatusCode::FAILURE;
      }
    }
  }
  return StatusCode::SUCCESS;
}

CellIdentification TileBoxCellTool::identify( const G4Step *step ) const
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
  int etaBin = findCell( rradius, (float)rpos.z() );
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

  const int npmt = tileNPmt( etaBin, phiBin );
  cell.tileNPmt = npmt;
  cell.hasDualReadout = (m_tileDualReadout > 0);

  const bool replacedCell = !m_replaceCollectionKey.empty() && npmt == 0;
  if( replacedCell ){
    cell.isReplaced = true;
    cell.replaceCollectionKey = m_replaceCollectionKey;
    cell.replaceHash = (unsigned long int)m_replaceHashBase + phiBin;
  }

  // ATLAS identification fields
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] );
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  const bool replaced = ( npmt == 0 );
  int section = replaced ? m_replaceSection : (cell.etaBin < (int)m_cellAtlasSection.size() ? m_cellAtlasSection[cell.etaBin] : 0);
  int tower = replaced ? m_replaceTower : (cell.etaBin < (int)m_cellAtlasTower.size() ? m_cellAtlasTower[cell.etaBin] : 0);
  int samp = replaced ? m_replaceSampling : (cell.etaBin < (int)m_cellAtlasSampling.size() ? m_cellAtlasSampling[cell.etaBin] : 0);
  double zCell = replaced ? m_replaceZCentre : (cell.etaBin < (int)m_cellZCentre.size() ? m_cellZCentre[cell.etaBin] : 0.0);
  int side = ( zCell >= 0 || (section == 1 && samp == 2 && tower == 0) ) ? +1 : -1;

  cell.atlasSubdet = 0; // Tile
  cell.atlasSide = side;
  cell.atlasSampling = samp;
  cell.atlasRegion = section;
  cell.atlasModule = module;
  cell.atlasTower = tower;

  return cell;
}

int TileBoxCellTool::findCell( float radius, float z ) const
{
  for ( unsigned box = 0; box < m_cellBoxIndex.size(); ++box ){
    if( radius > m_cellBoxRMin[box] && radius <= m_cellBoxRMax[box] &&
        z > m_cellBoxZMin[box] && z <= m_cellBoxZMax[box] )
      return m_cellBoxIndex[box];
  }
  return -1;
}

int TileBoxCellTool::find( const std::vector<float> &vec, float value ) const
{
  auto binIterator = std::adjacent_find( vec.begin(), vec.end(), [=](float left, float right){ return left < value and value <= right; } );
  if ( binIterator == vec.end() ) return -1;
  return binIterator - vec.begin();
}

int TileBoxCellTool::findPhi( float phi ) const
{
  int bin = find( m_phiBins, phi );
  if( bin < 0 ) bin = find( m_phiBins, phi + 2 * M_PI );
  if( bin < 0 ) bin = find( m_phiBins, phi - 2 * M_PI );
  return bin;
}

unsigned long int TileBoxCellTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}

int TileBoxCellTool::tileNPmt( int cell, int phiBin ) const
{
  int npmt = ( cell >= 0 && cell < (int)m_cellNPmt.size() ) ? m_cellNPmt[cell] : 2;
  if( m_specialModule.empty() ) return npmt;
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] );
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  for( size_t i = 0; i < m_specialModule.size(); ++i )
    if( m_specialModule[i] == module ) return m_specialNPmt[i];
  return npmt;
}
