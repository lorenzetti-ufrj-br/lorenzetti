
#include "CaloHit/CaloHitContainer.h"
#include "CaloHit/CaloHitCollection.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "G4Kernel/CaloPhiRange.h"

#include "CaloHitMerge.h"
#include "TVector3.h"
#include <cstdlib>
#include <cmath>
#include <algorithm>

#include "TCanvas.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TH2Poly.h"


using namespace Gaugi;
using namespace SG;


/**
 * @class CaloHitMerge
 * @brief Merges multiple CaloHit collections.
 * 
 * Collects `xAOD::CaloHitCollection` objects (pointers to hits) from different
 * sources and merges them into a single `xAOD::CaloHitContainer` (owning the hits).
 * This is typically the final step of hit generation before digitization.
 * 
 * Properties:
 * - InputCollectionKeys: Keys of collections to merge.
 * - OutputHitsKey: Key of the output container.
 */
CaloHitMerge::CaloHitMerge( std::string name ) : 
  IMsgService(name),
  Algorithm()
{
  declareProperty( "InputCollectionKeys"    , m_collectionKeys={}           );
  declareProperty( "OutputHitsKey"          , m_hitsKey="Hits"              );
  declareProperty( "FilterEmptyHits"        , m_filterEmptyHits=false       );
  declareProperty( "MinEnergy"              , m_minEnergy=0.0               );
  declareProperty( "OnlyRoI"                , m_onlyRoI=false               );
  declareProperty( "EtaWindow"              , m_etaWindow=0.4f              );
  declareProperty( "PhiWindow"              , m_phiWindow=0.4f              );
  declareProperty( "TruthKey"               , m_truthKey="Particles"        );
  declareProperty( "InputTruthKey"          , m_truthKey                    );
  declareProperty( "CellHashes"             , m_cellHashes={}               );
  declareProperty( "OutputLevel"            , m_outputLevel=1               );
}

//!=====================================================================

StatusCode CaloHitMerge::initialize()
{
  CHECK_INIT();
  setMsgLevel( m_outputLevel );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMerge::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMerge::bookHistograms( SG::EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMerge::pre_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================
 
StatusCode CaloHitMerge::execute( EventContext &/*ctx*/ , const G4Step * /*step*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================
// standlone execute
StatusCode CaloHitMerge::execute( EventContext &ctx, int /*evt*/ ) const
{
  return post_execute(ctx);
}

//!=====================================================================

/**
 * @brief Merges the collections.
 * 
 * Iterates over all input collections, creates new specific Hit objects
 * (copying data), and adds them to the output container.
 */
StatusCode CaloHitMerge::post_execute( EventContext &ctx ) const
{

  MSG_DEBUG( "Starting collection merge algorithm..." );
  MSG_DEBUG( "Creating HIT containers with key " << m_hitsKey);

  SG::WriteHandle<xAOD::CaloHitContainer> container( m_hitsKey , ctx );
  container.record( std::unique_ptr<xAOD::CaloHitContainer>(new xAOD::CaloHitContainer()) );
  float etot=0;

  bool hasParticles = false;
  SG::ReadHandle<xAOD::TruthParticleContainer> particles( m_truthKey, ctx );
  if (m_onlyRoI) {
    if (particles.isValid() && !particles->empty()) {
      hasParticles = true;
    }
  }
  bool keepCells = !m_cellHashes.empty();

  for ( auto key : m_collectionKeys ){

    MSG_DEBUG( "Reading all hits from collection with key " << key );
    SG::ReadHandle<xAOD::CaloHitCollection> collection( key, ctx );
    
    if( !collection.isValid() ){
      MSG_WARNING( "It's not possible to read the xAOD::CaloHitCollection from this Context using this key: " << key );
      continue;
    }

    MSG_DEBUG( "Creating new cells and attach the object into the container" );

    for (const auto &pair : **collection.ptr() )
    {
      const xAOD::CaloHit* const_hit = pair.second;
      if (!const_hit) {
        continue;
      }

      // Check if empty hit filtering is enabled
      if (m_filterEmptyHits && const_hit->edep() <= m_minEnergy) {
        continue;
      }

      // Check if Region of Interest (RoI) filtering is enabled
      if (m_onlyRoI) {
        bool match = false;
        if (hasParticles) {
          for (const auto &par : *particles) {
            float deltaEta = std::abs(par->eta() - const_hit->eta());
            float deltaPhi = std::abs(CaloPhiRange::diff(par->phi(), const_hit->phi()));
            if (deltaEta < m_etaWindow / 2.0f && deltaPhi < m_phiWindow / 2.0f) {
              match = true;
              break;
            }
          }
        }

        if (!match && keepCells) {
          if (std::find(m_cellHashes.begin(), m_cellHashes.end(), static_cast<int>(const_hit->hash())) != m_cellHashes.end()) {
            match = true;
          }
        }

        if (!match && (hasParticles || keepCells)) {
          continue; // Skip hit outside RoI
        }
      }
      
      // Create the truth cell 
      auto hit = new xAOD::CaloHit( const_hit->eta(),
                                    const_hit->phi(),
                                    const_hit->deltaEta(),
                                    const_hit->deltaPhi(),
                                    const_hit->hash(),
                                    const_hit->sampling(),
                                    const_hit->detector(),
                                    const_hit->bc_duration(),
                                    const_hit->bcid_start(),
                                    const_hit->bcid_end()
                                    );


      for ( int bcid = hit->bcid_start();  bcid <= hit->bcid_end(); ++bcid )
      {
        hit->edep( bcid, const_hit->edep(bcid) ); // truth energy for each bunch crossing
        hit->tof ( bcid, const_hit->tof(bcid) );  // truth time for each bunch crossing 
                                                  // (in fact, this time is the time from the signal at the
                                                  // moment its energy holds above 1*sigma noise threshold)
      }
      etot+=hit->edep();

      container->push_back( hit );
      
    }// Loop over all hits 
  }// Loop over all collections
  
  MSG_DEBUG( "Total of energy is " << etot << " MeV");
  MSG_DEBUG( "All collections were merged into two CaloHitContainer" );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMerge::fillHistograms( EventContext & /*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}



