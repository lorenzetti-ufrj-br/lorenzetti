#include "src/LArAccordionTool.h"
#include "src/EmbAtlasSampling.h"
#include "G4Step.hh"
#include "G4Material.hh"
#include "TVector3.h"
#include <cmath>
#include <algorithm>

LArAccordionTool::LArAccordionTool( std::string name )
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

  declareProperty( "EmbMode"          , m_embMode = 0 );
  declareProperty( "EmbSampling"      , m_embSampling = 0 );
  declareProperty( "EmbRegion"        , m_embRegion = 0 );
  declareProperty( "EmbZShift"        , m_embZShift = 0.0f );
  declareProperty( "PsbR0"            , m_psbR0 = 0.0f );
  declareProperty( "EmbSampSeg"       , m_embSampSeg = false );

  declareProperty( "AtlasBarrelEc"    , m_atlasBarrelEc = 0 );
  declareProperty( "AtlasLArSampling" , m_atlasLArSampling = 0 );
  declareProperty( "AtlasLArRegion"   , m_atlasLArRegion = 0 );
  declareProperty( "CellAtlasEtaIndex", m_cellAtlasEtaIndex );
  declareProperty( "PhiShift"         , m_phiShift = 0.0f );
}

StatusCode LArAccordionTool::initialize()
{
  m_nPhiBins = m_phiBins.empty() ? 0 : m_phiBins.size() - 1;
  return StatusCode::SUCCESS;
}

StatusCode LArAccordionTool::preExecute( SG::EventContext &, xAOD::CaloHitCollection *collection ) const
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

CellIdentification LArAccordionTool::identify( const G4Step *step ) const
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
  float phi = vpos.Phi();

  const bool sampSeg = m_embSampSeg && m_embMode == 1 && m_embSampling > 0;
  const G4ThreeVector rpos = 0.5 * ( pos + step->GetPostStepPoint()->GetPosition() );
  const float rradius = rpos.perp();
  if( !sampSeg && !(rradius > m_rMin && rradius <= m_rMax) ) return cell;
  if( !(rpos.z() > m_zMin && rpos.z() <= m_zMax) ) return cell;

  int etaBin = -1, phiBin = -1;
  if( sampSeg ){
    int region, sampling, ieta;
    if( !embSampSeg( pos.x(), pos.y(), pos.z(), region, sampling, ieta ) ) return cell;
    if( sampling != m_embSampling || region != m_embRegion ) return cell;
    etaBin = ieta - ( ( m_embSampling == 1 && m_embRegion == 0 ) ? 1 : 0 );
    if( etaBin < 0 || etaBin >= (int)m_cellEta.size() ) return cell;
    phiBin = findPhi( phi );
    if( phiBin < 0 ) return cell;
  } else if( m_embMode > 0 ){
    etaBin = embFindCell( pos.x(), pos.y(), pos.z() );
    if( etaBin < 0 ) return cell;
    phiBin = findPhi( phi );
    if( phiBin < 0 ) return cell;
  } else {
    return cell;
  }

  unsigned bin = m_nPhiBins * etaBin + phiBin;

  cell.isValid = true;
  cell.hashId = hash(bin);
  cell.etaBin = etaBin;
  cell.phiBin = phiBin;
  cell.eta = (etaBin >= 0 && etaBin < (int)m_cellEta.size()) ? m_cellEta[etaBin] : vpos.PseudoRapidity();
  cell.phi = phi;
  cell.sampling = m_sampling;
  cell.detector = m_detector;

  // ATLAS identification fields
  cell.atlasSubdet = 1; // EMB
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

int LArAccordionTool::psbGapCell( double x, double y, double z ) const
{
  static const double mod[8][6] = { {286.4, 56, 56, -25., 4.987, 4.2}, {295.74, 64, 64, -12., 4.621, 0.3},
                                    {321.1, 72, 72, 0., 4.46, 0.9}, {356.8, 80, 80, 0., 4.46, 0.9},
                                    {404.8, 88, 88, 0., 4.6, 0.9}, {478.4, 104, 104, 0., 4.6, 0.95},
                                    {563.2, 128, 128, 0., 4.4, 1.05}, {380.6, 86, 87, 0., 4.4, 0.95} };
  static const double cmm = 1 - 0.0026, eps = 0.007, zmin = 3.0, cathode = 0.270;
  static double endModule[8], firstCathode[8], pitch[8], tiltTan[8];
  static int ncell[8], ngap[8];
  static const bool init = [](){
    for( int i = 0; i < 8; ++i ){
      endModule[i] = (i == 0 ? zmin : endModule[i-1]) + (mod[i][0]*cmm + 2*eps) + eps;
      firstCathode[i] = (i == 0 ? zmin : endModule[i-1]) + mod[i][5]*cmm + cathode*cmm/2. + 2*eps;
      pitch[i] = mod[i][4]*cmm;
      tiltTan[i] = std::tan( mod[i][3]*M_PI/180. );
      ncell[i] = (i < 7) ? 8 : 5;
      ngap[i] = (i < 7) ? (int)( (mod[i][1] + 0.1)/ncell[i] ) : 18;
    }
    return true;
  }();
  (void)init;
  const double z2 = std::fabs( z );
  if( z2 < zmin || z2 > endModule[7] ) return -1;
  int module = 0;
  for( int i = 1; i < 8; ++i ){
    if( firstCathode[i] >= z2 ) break;
    module++;
  }
  const double dist = std::sqrt( x*x + y*y ) - m_psbR0;
  double deltaz = z2 - ( firstCathode[module] + dist*tiltTan[module] );
  if( deltaz < 0 ){
    if( module > 0 ){
      module--;
      deltaz = z2 - ( firstCathode[module] + dist*tiltTan[module] );
    }else{
      deltaz = 0;
    }
  }
  const int gap = (int)( deltaz/pitch[module] );
  int etaBin = gap/ngap[module];
  if( etaBin >= ncell[module] ) etaBin = ncell[module] - 1;
  for( int i = 0; i < module; ++i ) etaBin += ncell[i];
  if( etaBin < 0 || etaBin > 60 ) return -1;
  return etaBin;
}

int LArAccordionTool::embFindCell( double x, double y, double z ) const
{
  if( m_embMode == 3 ) return psbGapCell( x, y, z );
  if( m_embMode == 2 && m_embZShift != 0 ) z = std::copysign( std::fabs(z) - m_embZShift, z );
  const double mag = std::sqrt( x*x + y*y + z*z );
  double eta;
  if( mag == 0 ) eta = 0;
  else if( mag == z ) eta = 1.0E72;
  else if( mag == -z ) eta = -1.0E72;
  else eta = 0.5 * std::log( (mag + z) / (mag - z) );
  const double aeta = std::fabs( eta );
  const double deta = 0.025, etaMaxS1 = 1.4, etaMax = 1.475;
  int ieta = -1, first = 0, last = -1;
  if( m_embMode == 2 ){
    ieta = (int)( aeta * 40. - 60. );
    if( ieta == 12 && aeta < 1.801 ) ieta = 11;
    first = 0; last = 11;
  }else if( m_embSampling == 0 ){
    if( !(aeta < 1.525) ) return -1;
    ieta = (int)( aeta / deta ); first = 0; last = 60;
  }else if( m_embRegion == 0 ){
    if( !(aeta < etaMaxS1) ) return -1;
    if     ( m_embSampling == 1 ){ ieta = (int)( aeta / deta * 8. );        first = 1; last = 447; }
    else if( m_embSampling == 2 ){ ieta = (int)( aeta / deta );             first = 0; last = 55;  }
    else if( m_embSampling == 3 ){ ieta = ( (int)( aeta / deta ) ) / 2;     first = 0; last = 26;  }
  }else if( m_embRegion == 1 ){
    if( !(aeta >= etaMaxS1 && aeta < etaMax) ) return -1;
    if     ( m_embSampling == 1 ){ ieta = (int)( (aeta - etaMaxS1) / deta ); first = 0; last = 2; }
    else if( m_embSampling == 2 ){ ieta = 0;                                 first = 0; last = 0; }
  }
  if( ieta < first || ieta > last ) return -1;
  return ieta - first;
}

int LArAccordionTool::embSampSeg( double x, double y, double z, int &iregion, int &isampling, int &ieta ) const
{
  using EmbAtlasSampling::Rmax1;
  using EmbAtlasSampling::Rmax2;
  static const double Eta_max = 1.475, R_min_acc = 1500.024, R_max_acc = 1960., Z_min_acc = 4., Z_max_acc = 3150.;
  static const double R_min_highz = 1548., deltaz = 7., Dr_s12 = 1.1, Eta_max_s1 = 1.4, Eta_max_s3 = 1.325, deta = 0.025;
  static const double zmax1 = Z_max_acc - deltaz, zmax2 = Z_max_acc - 2.*deltaz, zmax3 = Z_max_acc - 3.*deltaz,
                      zmax4 = Z_max_acc - 4.*deltaz, zmax5 = Z_max_acc - 5.*deltaz, zmax6 = Z_max_acc - 6.*deltaz,
                      zmax7 = Z_max_acc - 7.*deltaz;
  static const double rmax1 = R_max_acc - deltaz, rmax2 = R_max_acc - 2.*deltaz, rmax3 = R_max_acc - 3.*deltaz,
                      rmax4 = R_max_acc - 4.*deltaz;
  static const double Z_max_lowr = std::sinh(Eta_max) * R_min_acc;
  static const double dzdr = (Z_max_acc - Z_max_lowr) / (R_min_highz - R_min_acc);

  iregion = -1; isampling = -1; ieta = -1;
  const double radius = std::sqrt( x*x + y*y );
  const double mag = std::sqrt( x*x + y*y + z*z );
  const double az = std::fabs( z );
  if( mag == 0 || mag == az ) return 0;
  const double aeta = 0.5 * std::log( (mag + az) / (mag - az) );

  if( radius < R_min_acc || radius > R_max_acc || aeta > Eta_max || az < Z_min_acc || az > Z_max_acc ) return 0;

  int iactive = 1;
  if( aeta < Eta_max_s1 ){
    const int istrip = (int)( aeta / deta * 8. );
    if( istrip < 0 || istrip >= 448 ) return 0;
    const double r12 = Rmax1[istrip];
    const int imid = (int)( aeta / deta );
    if( imid < 0 || imid >= 56 ) return 0;
    const double r23 = Rmax2[imid];
    iregion = 0;
    if( radius <= r12 ){
      isampling = 1; ieta = istrip;
      if( ieta == 0 ) iactive = 0;
    }else if( radius < (r12 + Dr_s12) ){
      isampling = 1; ieta = istrip; iactive = 0;
    }else{
      if( aeta < Eta_max_s3 ){
        if( radius <= r23 ){
          isampling = 2; ieta = imid;
        }else{
          if     ( az > zmax1 ){ isampling = 2; ieta = 55; }
          else if( az > zmax2 ){ isampling = 2; ieta = 54; }
          else if( az > zmax3 ){ isampling = 2; ieta = 53; }
          else if( az > zmax4 ){ isampling = 3; ieta = 26; }
          else if( aeta < 1.3 && az > zmax5 ){ isampling = 2; ieta = 52; }
          else if( aeta < 1.3 && az > zmax6 ){ isampling = 2; ieta = 51; }
          else if( radius > rmax4 && az < zmax5 && aeta > 1.2 ){
            if     ( radius > rmax1 ){ isampling = 2; ieta = 51; }
            else if( radius > rmax2 ){ isampling = 3; ieta = 25; }
            else if( radius > rmax3 ){
              if( az < zmax7 ){ isampling = 2; ieta = 50; }
              else            { isampling = 3; ieta = 25; }
            }else{
              if( aeta < 1.25 ){ isampling = 2; ieta = 49; }
              else             { isampling = 3; ieta = 25; }
            }
          }else{
            isampling = 3; ieta = imid / 2;
          }
        }
        if( isampling == 3 && az < zmax4 && ( radius < rmax4 || aeta < 1.2 ) ){
          const double etastr = ( imid % 2 == 0 ) ? 0.025 * imid : 0.025 * ( imid + 1 );
          const double delta = radius * ( std::sinh(etastr) - std::sinh(aeta) ) / std::cosh(etastr);
          double deltastr;
          if      ( aeta < 0.475 ) deltastr = 1.5;
          else if ( aeta < 0.80  ) deltastr = 2.75;
          else if ( aeta < 0.85  ) deltastr = 1.5;
          else if ( aeta < 1.1   ) deltastr = 2.75;
          else                     deltastr = 3.25;
          if( std::fabs(delta) < deltastr ){ isampling = 2; ieta = imid; }
        }
      }else{
        isampling = 2; ieta = imid;
        if     ( az > zmax1 ) ieta = 55;
        else if( az > zmax2 && aeta < 1.375 ) ieta = 54;
      }
    }
  }
  if( aeta >= Eta_max_s1 && aeta < Eta_max ){
    const double r12 = Rmax1[447];
    const double r23 = Z_max_acc / std::sinh(aeta);
    const double zmax = Z_max_lowr + dzdr * ( radius - R_min_acc );
    iregion = 1;
    if( radius <= r12 ){
      isampling = 1; ieta = (int)( (aeta - Eta_max_s1) / deta );
      if( az > zmax ) iactive = 0;
    }else if( radius < (r12 + Dr_s12) ){
      isampling = 1; ieta = (int)( (aeta - Eta_max_s1) / deta ); iactive = 0;
    }else if( radius <= r23 ){
      isampling = 2; ieta = 0;
      if( az > zmax ) iactive = 0;
    }else{
      isampling = 2; ieta = 0; iactive = 0;
    }
  }
  if( aeta > Eta_max ) iactive = 0;
  if( az > Z_max_acc || radius > R_max_acc || radius < R_min_acc || aeta > Eta_max ) iactive = 0;
  return iactive;
}

int LArAccordionTool::find( const std::vector<float> &vec, float value ) const
{
  auto binIterator = std::adjacent_find( vec.begin(), vec.end(), [=](float left, float right){ return left < value and value <= right; } );
  if ( binIterator == vec.end() ) return -1;
  return binIterator - vec.begin();
}

int LArAccordionTool::findPhi( float phi ) const
{
  int bin = find( m_phiBins, phi );
  if( bin < 0 ) bin = find( m_phiBins, phi + 2 * M_PI );
  if( bin < 0 ) bin = find( m_phiBins, phi - 2 * M_PI );
  return bin;
}

unsigned long int LArAccordionTool::hash( unsigned bin ) const
{
  if( m_zMin > 0 ){
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if( m_zMax < 0 ){
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}
