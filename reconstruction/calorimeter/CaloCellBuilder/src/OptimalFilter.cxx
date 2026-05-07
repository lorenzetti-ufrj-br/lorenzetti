#include "OptimalFilter.h"
#include "CaloCell/CaloDetDescriptor.h"

using namespace Gaugi;


/**
 * @class OptimalFilter
 * @brief Reconstructs cell energy and time using fixed Optimal Filter weights.
 * 
 * Applies the standard Optimal Filtering technique (OF2 usually) where the
 * energy and time are linear combinations of the digitized samples. The weights
 * are pre-calculated to minimize noise and pileup.
 * 
 * Properties:
 * - WeightsEnergy: Vector of weights for energy estimation.
 * - WeightsTime: Vector of weights for time estimation.
 */
OptimalFilter::OptimalFilter( std::string name ) : 
  IMsgService(name),
  AlgTool()
{
  declareProperty( "WeightsEnergy"    , m_ofweightsEnergy={}  );
  declareProperty( "WeightsTime"      , m_ofweightsTime={}    );
  declareProperty( "OutputLevel"      , m_outputLevel=1       );
}

//!=====================================================================

OptimalFilter::~OptimalFilter()
{}

//!=====================================================================

StatusCode OptimalFilter::initialize()
{
  setMsgLevel(m_outputLevel);
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode OptimalFilter::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Calculates Energy and Time.
 * 
 * Computes the dot product of the pulse samples with the energy/time weights.
 * Sets the reconstructed Energy and Tau in the cell object.
 */
StatusCode OptimalFilter::execute( SG::EventContext &/*ctx*/, Gaugi::EDM *edm ) const
{

  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  auto pulse = cell->pulse();
  float energy=0.0;
  float tau=0.0, EneTau=0.0;

  // Energy estimation
  if( m_ofweightsEnergy.size() != pulse.size() ){
    MSG_ERROR( "The ofweightsEnergy size its different than the pulse size." );
    return StatusCode::FAILURE;
  }else{
    for( unsigned sample=0; sample < pulse.size(); ++sample) 
      energy += pulse[sample]*m_ofweightsEnergy[sample];
  }

  // Time estimation
  if( m_ofweightsTime.size() != pulse.size() ){
    MSG_ERROR( "The ofweightsTime size its different than the pulse size." );
    return StatusCode::FAILURE;
  }
  else{
    for( unsigned sample=0; sample < pulse.size(); ++sample){
      EneTau += pulse[sample]*m_ofweightsTime[sample];
    }
    tau = EneTau/energy;
  }

  cell->setE(energy);
  cell->setTau(tau);
  return StatusCode::SUCCESS;
}


