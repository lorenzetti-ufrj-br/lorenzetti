#include "ConstrainedOptimalFilterTool.h"
#include "CaloCell/CaloDetDescriptor.h"
#include <fstream>
#include <cmath>

using namespace Gaugi;

ConstrainedOptimalFilterTool::ConstrainedOptimalFilterTool( std::string name ) : 
  IMsgService(name),
  Tool(),
  m_startSamplingBC(0),
  m_shaperResolution(0),
  m_threshold(0.0),
  m_shaperZeroIndex(0),
  m_nsamples(0),
  m_samplingRate(25),
  m_outputLevel(1)
{
  declareProperty( "PulsePath"        , m_pulsepath       );
  declareProperty( "Threshold"        , m_threshold=0.0   );
  declareProperty( "NSamples"         , m_nsamples=0      );
  declareProperty( "StartSamplingBC"  , m_startSamplingBC );
  declareProperty( "SamplingRate"     , m_samplingRate=25 ); 
  declareProperty( "OutputLevel"      , m_outputLevel=1   );
}

void ConstrainedOptimalFilterTool::ReadShaper( std::string filepath )
{
  std::ifstream file;
  m_timeSeries.clear();
  m_shaper.clear();
  file.open(filepath);
  if (file) {
     int i=0;
     float a, b;
     while (file >> a >> b)
     {
        m_timeSeries.push_back(a);
        m_shaper.push_back(b);
        if (a == 0.0) m_shaperZeroIndex = i;
        i++;
     }
  } else {
    MSG_FATAL( "Invalid shaper path: " << filepath );
  }
  file.close();
  m_shaperResolution = m_shaper.size() > 2 ? m_timeSeries[1] - m_timeSeries[0] : m_timeSeries[0];
}

ConstrainedOptimalFilterTool::~ConstrainedOptimalFilterTool()
{}

StatusCode ConstrainedOptimalFilterTool::initialize()
{
  setMsgLevel( (MSG::Level)m_outputLevel );
  ReadShaper( m_pulsepath );
  return StatusCode::SUCCESS;
}

StatusCode ConstrainedOptimalFilterTool::finalize()
{
  return StatusCode::SUCCESS;
}

void ConstrainedOptimalFilterTool::GeneratePulse( std::vector<float> &pulse ) const
{
  pulse.clear();
  for( int sample=0; sample < m_nsamples; ++sample)
  {
    int i = m_shaperZeroIndex + (sample + m_startSamplingBC)*(m_samplingRate/m_shaperResolution);

    if (i < 0 || i >= int(m_shaper.size())){
      pulse.push_back(0.0);
    }else{
      pulse.push_back( m_shaper[i] );
    }
  }
}

StatusCode ConstrainedOptimalFilterTool::execute( SG::EventContext &/*ctx*/, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  auto pulse = cell->pulse();

  std::vector<float> ofweightsEnergy;
  TVectorD g(m_nsamples);
  TMatrixD V(m_nsamples, m_nsamples);
  TMatrixD L(m_nsamples + 1, m_nsamples + 1);

  std::vector<float> ref_pulse;
  GeneratePulse(ref_pulse);
  for(int sample=0; sample < m_nsamples; ++sample)
    g(sample) = ref_pulse[sample];

  for(int i=0; i < m_nsamples; ++i)
    for(int j=0; j < m_nsamples; ++j)
      V(i, j) = std::exp(-std::abs(i - j) / 2.0);

  for(int i=0; i < m_nsamples; ++i)
    for(int j=0; j < m_nsamples; ++j)
      L(i, j) = V(i, j);

  for(int i=0; i < m_nsamples; ++i){
    L(i, m_nsamples) = -1.0;
    L(m_nsamples, i) = -1.0;
  }
  L(m_nsamples, m_nsamples) = 0.0;

  TVectorD g_ext(m_nsamples + 1);
  for(int i=0; i < m_nsamples; ++i)
    g_ext(i) = g(i);
  g_ext(m_nsamples) = 0.0;

  TMatrixD L_inv = L.Invert();
  TVectorD a_ext = L_inv * g_ext;
  double denom = 0.0;
  for(int i=0; i < m_nsamples; ++i)
    denom += a_ext(i) * g(i);

  if (denom == 0.0) {
    MSG_ERROR("Denominador nulo no ConstrainedOptimalFilter");
    return StatusCode::FAILURE;
  }

  for(int i=0; i < m_nsamples; ++i)
    ofweightsEnergy.push_back(a_ext(i) / denom);

  float energy = 0.0f;
  for( unsigned sample=0; sample < pulse.size(); ++sample)
    energy += pulse[sample]*ofweightsEnergy[sample];

  cell->setE(energy);
  cell->setTau(0.0f);
  return StatusCode::SUCCESS;
}
