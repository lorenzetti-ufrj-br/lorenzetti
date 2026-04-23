
#include "CaloCell/CaloDetDescriptor.h"
#include "AnomalyGenerator.h"
#include "Randomize.hh"
#include "TRandom.h"
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/EventInfoConverter.h"

using namespace Gaugi;


/**
 * @class AnomalyGenerator
 * @brief Tool to inject anomalies and defects into the calorimeter simulation.
 * 
 * This tool allows the user to simulate dead modules (by zeroing out the pulse)
 * or noisy cells (by adding extra gaussian noise) based on configuration properties
 * and event numbers. This is useful for testing the robustness of reconstruction
 * algorithms against detector defects.
 * 
 * Properties:
 * - DeadModules: List of booleans indicating if a block of events/cells is dead.
 * - Cells: List of cell hashes to apply the anomaly to.
 * - NoiseMean/Std: Parameters for the gaussian noise injection.
 * - EventNumberRange: Range of event numbers where the anomaly is active.
 */
AnomalyGenerator::AnomalyGenerator( std::string name ) : 
  IMsgService(name),
  AlgTool(),
  m_rng(0)
{
  declareProperty( "DeadModules"      , m_deadModules={}        );
  declareProperty( "Cells"            , m_cells={}              );
  declareProperty( "NoiseMean"        , m_noiseMean=0           );
  declareProperty( "NoiseStd"         , m_noiseStd=0            );
  declareProperty( "NoiseStdFactor"   , m_noiseStdFactor={}     );
  declareProperty( "EventNumberRange" , m_eventNumberRange={}   );
  declareProperty( "InputEventKey"    , m_inputEventKey="EventInfo" );
  declareProperty( "OutputLevel"      , m_outputLevel=1         );

}

//!=====================================================================

AnomalyGenerator::~AnomalyGenerator()
{;}

//!=====================================================================

StatusCode AnomalyGenerator::initialize()
{
  setMsgLevel( (MSG::Level)m_outputLevel );
  MSG_INFO("artificial anomalies will be applied to some cell signals")
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode AnomalyGenerator::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Executes the anomaly injection.
 * 
 * Checks if the current event number and cell hash match any of the configured
 * anomaly rules. If a match is found, it either zeros the pulse (dead module)
 * or adds Gaussian noise.
 * 
 * @param ctx EventContext.
 * @param edm Pointer to the xAOD::CaloDetDescriptor (cell).
 */
StatusCode AnomalyGenerator::execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  auto pulse_sum = cell->pulse();
  auto pulse_size = pulse_sum.size();


  SG::ReadHandle<xAOD::EventInfoContainer> event(m_inputEventKey, ctx);
  if( !event.isValid() ){
    MSG_FATAL( "It's not possible to read the xAOD::EventInfoContainer from this Context" );
  }
  // get the old ones
  auto const_evt = (**event.ptr()).front();
  auto eventNumber = const_evt->eventNumber();
  

  for (std::size_t block = 0; block < m_eventNumberRange.size(); ++block ){

    if ( 
           (eventNumber >= m_eventNumberRange[block][0]) && 
           (eventNumber <= m_eventNumberRange[block][1])
       )
    {
      //MSG_INFO("event number "<<eventNumber<<" is in the range "<<m_eventNumberRange[block][0]<<" - "<<m_eventNumberRange[block][1]);
      unsigned long int id = m_deadModules[block] ? static_cast<unsigned long int>(cell->hash() / 1e7) : cell->hash();
      bool found = std::find(m_cells[block].begin(), m_cells[block].end(), id) != m_cells[block].end();
      //MSG_INFO("Is a dead module anomaly? "<< (m_deadModules[block] ? "yes":"no") );
      //MSG_INFO("checking cell with hash id: "<< id <<" ( found? " << (found?"yes":"no") <<" )");
      if (found) {

        if (m_deadModules[block]){
          MSG_INFO("perturbed event: "<<eventNumber);
          MSG_INFO("simulating dead cell, setting pulse to zero");
          pulse_sum.assign(pulse_size, 0.0);
          cell->edep(0, 0.0); // reset energy deposit
          cell->setE(0.0); // reset estimated energy
          MSG_INFO("pulse sum after noise: "<<pulse_sum);
          MSG_INFO("cell energy after noise: "<<cell->e());

        }else{
          MSG_INFO("perturbed event: "<<eventNumber);
          MSG_INFO("events concerned by noise: "<<m_eventNumberRange[block]);
          MSG_INFO("increasing noise for cell with hash id: "<<cell->hash());
          // Add gaussian noise with increased noiseStd
          AddGaussianNoise(pulse_sum, m_noiseMean, m_noiseStdFactor[block]*m_noiseStd);  
          MSG_INFO("pulse sum after noise: "<<pulse_sum);
          MSG_INFO("cell energy after noise: "<<cell->e());
        }

        cell->setAnomalous(true);
        // Add the integrated pulse centered in the bunch crossing zero
        cell->setPulse( pulse_sum );
        break;

      }// if cell in list
    }// if event number in range
  }// Loop over blocks of event numbers
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

void AnomalyGenerator::AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStd) const
{
  for ( auto &value : pulse )
    value += m_rng.Gaus( noiseMean, noiseStd );
}

//!=====================================================================






