#include "OptimalFilterTool.h"
#include "CaloCell/CaloDetDescriptor.h"

using namespace Gaugi;

OptimalFilterTool::OptimalFilterTool( std::string name ) : 
  IMsgService(name),
  Tool(),
  m_outputLevel(1)
{
  declareProperty( "WeightsEnergy"    , m_ofweightsEnergy={}  );
  declareProperty( "WeightsTime"      , m_ofweightsTime={}    );
  declareProperty( "OutputLevel"      , m_outputLevel=1       );
}

OptimalFilterTool::~OptimalFilterTool()
{}

StatusCode OptimalFilterTool::initialize()
{
  setMsgLevel((MSG::Level)m_outputLevel);
  return StatusCode::SUCCESS;
}

StatusCode OptimalFilterTool::finalize()
{
  return StatusCode::SUCCESS;
}

StatusCode OptimalFilterTool::execute( SG::EventContext &/*ctx*/, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  auto pulse = cell->pulse();
  float energy = 0.0f;
  float tau = 0.0f, EneTau = 0.0f;

  if( m_ofweightsEnergy.size() != pulse.size() ){
    MSG_ERROR( "The ofweightsEnergy size its different than the pulse size." );
    return StatusCode::FAILURE;
  } else {
    for( unsigned sample=0; sample < pulse.size(); ++sample) 
      energy += pulse[sample]*m_ofweightsEnergy[sample];
  }

  if( m_ofweightsTime.size() != pulse.size() ){
    MSG_ERROR( "The ofweightsTime size its different than the pulse size." );
    return StatusCode::FAILURE;
  } else {
    for( unsigned sample=0; sample < pulse.size(); ++sample){
      EneTau += pulse[sample]*m_ofweightsTime[sample];
    }
    tau = (energy != 0.0f) ? (EneTau / energy) : 0.0f;
  }

  cell->setE(energy);
  cell->setTau(tau);
  return StatusCode::SUCCESS;
}
