
#include "CaloCell/CaloDetDescriptor.h"
#include "PulseGenerator.h"
#include "Randomize.hh"
#include "TRandom.h"
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/EventInfoConverter.h"

using namespace Gaugi;


PulseGenerator::PulseGenerator( std::string name ) : 
  IMsgService(name),
  AlgTool(),
  m_shaperZeroIndex(0),
  m_shaperResolution(0),
  m_rng(0)
{


  // new for including cell defects
  declareProperty( "doDefects"          , m_doDefects=false                 );
  declareProperty( "deadModules"        , m_deadModules=false               );
  declareProperty( "cellHash"           , m_cellHash={}                     );
  declareProperty( "noiseFactor"        , m_noiseFactor={}                  );
  declareProperty( "noisyEvents"        , m_noisyEvents={}                  );
}

//!=====================================================================

PulseGenerator::~PulseGenerator()
{;}

//!=====================================================================

StatusCode PulseGenerator::initialize()
{
  setMsgLevel( (MSG::Level)m_outputLevel );
  MSG_INFO("artificial anomalies will be applied to some cell signals")
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode PulseGenerator::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode PulseGenerator::execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  auto pulse = cell->pulse();
  auto pulse_size = pulse.size();

  // access event number of this specific event
  SG::ReadHandle<xAOD::EventInfoContainer> event("Events", ctx);
  xAOD::EventInfo_t event_t;
  xAOD::EventInfoConverter cnv;
  cnv.convert( (**event.ptr()).front(), event_t);
  int eventNumber = event_t.eventNumber;

  std::size_t index = 0;  // Initialize index

  for (auto group : m_cellHash ) {
    for (auto hash : group){
      unsigned long int detector_part = static_cast<unsigned long int>(cell->hash() / 1e7);
      MSG_DEBUG("detector part: "<<detector_part<<" vs hash: "<<hash);
      // only introduce defects for specific cells and specific events
      if ((detector_part == static_cast<unsigned long int>(hash)) && 
          (eventNumber >= m_noisyEvents[index][0]) && 
          (eventNumber <= m_noisyEvents[index][1]))
      {
        if (m_deadModules){
          MSG_INFO("perturbed event: "<<eventNumber)
          MSG_INFO("events concerned by noise: "<<m_noisyEvents[index])
          MSG_INFO("perturbed cell hash: "<<cell->hash()<<" vs "<<hash);
          MSG_INFO("pulse sum : "<<pulse_sum << " with mean " << m_noiseMean << " and std " << m_noiseStd);
          MSG_INFO("simulating dead cell, setting pulse to zero");
          pulse.assign(pulse_size, 0.0);
          cell->edep(0, 0.0); // reset energy deposit
          cell->setE(0.0); // reset estimated energy
          MSG_INFO("pulse sum after noise: "<<pulse_sum);
          MSG_INFO("cell energy after noise: "<<cell->e());
        }else{
          MSG_INFO("perturbed event: "<<eventNumber)
          MSG_INFO("events concerned by noise: "<<m_noisyEvents[index])
          MSG_INFO("increasing noise for cell with hash id: "<<cell->hash());
          // Add gaussian noise with increased noiseStd
          AddGaussianNoise(pulse, m_noiseMean, m_noiseFactor[index]*m_noiseStd);  
          MSG_INFO("pulse sum after noise: "<<pulse_sum);
          MSG_INFO("cell energy after noise: "<<cell->e());
        }
  
        cell->setAnomalous(true);
        // Add the integrated pulse centered in the bunch crossing zero
        cell->setPulse( pulse_sum );
      }
    }
    ++index;
  }
  
  
  
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

void PulseGenerator::AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStd) const
{
  for ( auto &value : pulse )
    value += m_rng.Gaus( noiseMean, noiseStd );
}

//!=====================================================================






