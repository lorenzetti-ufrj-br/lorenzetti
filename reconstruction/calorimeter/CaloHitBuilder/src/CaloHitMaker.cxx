#include "CaloHitMaker.h"
#include "CaloHit/CaloHitCollection.h"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4ThreeVector.hh"
#include "G4Track.hh"
#include "G4Material.hh"
#include "CLHEP/Units/SystemOfUnits.h"

using namespace Gaugi;
using namespace SG;

CaloHitMaker::CaloHitMaker( std::string name )
  : IMsgService(name), Algorithm()
{
  declareProperty( "OutputCollectionKey" , m_collectionKey = "Hits" );
  declareProperty( "SamplingNoiseStd"    , m_noiseStd = 0.0f );
  declareProperty( "DetailedHistograms"  , m_detailedHistograms = false );
  declareProperty( "HistogramPath"       , m_histPath = "Expert" );
  declareProperty( "ActiveEnergyOnly"    , m_activeEnergyOnly = false );
  declareProperty( "RMin"                , m_rMin = 0.0f );
  declareProperty( "RMax"                , m_rMax = 0.0f );
  declareProperty( "ZMin"                , m_zMin = 0.0f );
  declareProperty( "ZMax"                , m_zMax = 0.0f );

  declareProperty( "CellIdentifier"      , m_cellIdentifier = nullptr );
  declareProperty( "EnergyModifiers"     , m_energyModifiers );
  declareProperty( "TimeCorrection"      , m_timeCorrection = nullptr );
  declareProperty( "HitRecorders"        , m_hitRecorders );
}

StatusCode CaloHitMaker::initialize()
{
  if( m_cellIdentifier ) m_cellIdentifier->initialize();
  for( auto *mod : m_energyModifiers ) if( mod ) mod->initialize();
  if( m_timeCorrection ) m_timeCorrection->initialize();
  for( auto *rec : m_hitRecorders ) if( rec ) rec->initialize();
  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::bookHistograms( SG::EventContext & ) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::pre_execute( SG::EventContext &ctx ) const
{
  SG::WriteHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );
  collection.record( std::unique_ptr<xAOD::CaloHitCollection>(new xAOD::CaloHitCollection()) );

  if( m_cellIdentifier ){
    auto *cellTool = static_cast<ICaloCellIdentifierTool*>(m_cellIdentifier);
    return cellTool->preExecute( ctx, collection.ptr() );
  }
  return StatusCode::SUCCESS;
}

bool CaloHitMaker::passFilter( const G4Step *step ) const
{
  if( !step ) return false;
  const G4StepPoint *preP = step->GetPreStepPoint();
  if( !preP ) return false;

  // Shower spots (frozen showers without physical touchable) pass through envelope
  if( !preP->GetTouchable() ) return true;

  if( m_activeEnergyOnly ){
    const G4Material *material = preP->GetMaterial();
    if( !material ) return false;
    const G4String &matName = material->GetName();
    if( matName != "liquidArgon" && matName != "PLASTIC SCINTILLATOR" && matName != "ATLAS_TILE_PVT" )
      return false;
  }

  if( m_rMin > 0.0f || m_rMax > 0.0f || m_zMin != 0.0f || m_zMax != 0.0f ){
    const G4StepPoint *postP = step->GetPostStepPoint();
    const G4ThreeVector rpos = postP ? 0.5 * ( preP->GetPosition() + postP->GetPosition() ) : preP->GetPosition();
    if( m_rMax > 0.0f ){
      const float r = rpos.perp();
      if( r < m_rMin || r > m_rMax ) return false;
    }
    if( m_zMin != 0.0f || m_zMax != 0.0f ){
      if( rpos.z() < m_zMin || rpos.z() > m_zMax ) return false;
    }
  }
  return true;
}

StatusCode CaloHitMaker::execute( SG::EventContext &ctx, const G4Step *step ) const
{
  if( !passFilter(step) ) return StatusCode::SUCCESS;
  if( !m_cellIdentifier ) return StatusCode::SUCCESS;

  auto *cellTool = static_cast<ICaloCellIdentifierTool*>(m_cellIdentifier);
  CellIdentification cell = cellTool->identify(step);
  if( !cell.isValid ) return StatusCode::SUCCESS;

  float edep = (float)step->GetTotalEnergyDeposit() * (step->GetTrack() ? (float)step->GetTrack()->GetWeight() : 1.0f);
  for( const auto *tool : m_energyModifiers ){
    auto *modTool = static_cast<const ICaloEnergyModifierTool*>(tool);
    edep = modTool->modifyEnergy(step, cell, edep);
  }
  if( edep <= 0.0f ) return StatusCode::SUCCESS;

  CellTiming timing;
  if( m_timeCorrection ){
    auto *timeTool = static_cast<const ICaloTimeCorrectionTool*>(m_timeCorrection);
    timing = timeTool->computeTime(step, cell);
  } else {
    timing.hitTime = (float)(step->GetPreStepPoint()->GetGlobalTime() / CLHEP::ns);
    timing.globalTime = timing.hitTime;
    timing.time0 = timing.hitTime;
    timing.time1 = timing.hitTime;
  }

  for( const auto *tool : m_hitRecorders ){
    auto *recTool = static_cast<const ICaloHitRecorderTool*>(tool);
    recTool->record(ctx, step, cell, edep, timing);
  }

  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::execute( SG::EventContext &, int ) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::post_execute( SG::EventContext & ) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::fillHistograms( SG::EventContext & ) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloHitMaker::finalize()
{
  if( m_cellIdentifier ) m_cellIdentifier->finalize();
  for( auto *mod : m_energyModifiers ) if( mod ) mod->finalize();
  if( m_timeCorrection ) m_timeCorrection->finalize();
  for( auto *rec : m_hitRecorders ) if( rec ) rec->finalize();
  return StatusCode::SUCCESS;
}
