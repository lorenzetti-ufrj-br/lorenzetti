#include "src/CaloStandardHitRecorderTool.h"
#include "CaloHit/CaloHitCollection.h"
#include "GaugiKernel/DataHandle.h"

CaloStandardHitRecorderTool::CaloStandardHitRecorderTool( std::string name )
  : IMsgService(name), ICaloHitRecorderTool(name)
{
  declareProperty( "OutputCollectionKey", m_collectionKey = "CaloHitCollection" );
  declareProperty( "NoiseStd"            , m_noiseStd = 0.0f );
}

StatusCode CaloStandardHitRecorderTool::record( SG::EventContext &ctx, const G4Step *,
                                                const CellIdentification &cell, float energy,
                                                const CellTiming &timing ) const
{
  if( !cell.isValid ) return StatusCode::SUCCESS;

  xAOD::CaloHit *hit = nullptr;
  if( cell.isReplaced ){
    SG::ReadHandle<xAOD::CaloHitCollection> replaced( cell.replaceCollectionKey, ctx );
    if( !replaced.isValid() || !replaced->retrieve( cell.replaceHash, hit ) ){
      MSG_FATAL( "No hit of the replacement cell in " << cell.replaceCollectionKey << " for hash " << cell.replaceHash );
      return StatusCode::FAILURE;
    }
  } else {
    SG::ReadHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );
    if( !collection.isValid() ){
      MSG_FATAL( "It's not possible to retrieve the CaloHitCollection using this key: " << m_collectionKey );
      return StatusCode::FAILURE;
    }
    if( !collection->retrieve( cell.hashId, hit ) ){
      MSG_FATAL( "It is not possible to retrieve the hit for hash " << cell.hashId );
      return StatusCode::FAILURE;
    }
  }

  if( hit ){
    hit->fillAt( timing.hitTime, 1 * m_noiseStd, energy );
    if( hit->dualReadout() && cell.hasDualReadout ){
      hit->fillPmtAt( timing.time0, energy * cell.pmtWeight0, timing.time1, energy * cell.pmtWeight1 );
    }
  }

  return StatusCode::SUCCESS;
}
