#include "CaloCell/CaloDetDescriptor.h"
#include "PulseGeneratorTool.h"
#include "Randomize.hh"
#include "TRandom.h"

using namespace Gaugi;

PulseGeneratorTool::PulseGeneratorTool( std::string name ) : 
  IMsgService(name),
  Tool(),
  m_shaperZeroIndex(0),
  m_shaperResolution(0),
  m_rng(0)
{
  declareProperty( "ShaperFile"       , m_shaperFile=""         );
  declareProperty( "Pedestal"         , m_pedestal = 0          );
  declareProperty( "DeformationMean"  , m_deformationMean=0     );
  declareProperty( "DeformationStd"   , m_deformationStd=0      );
  declareProperty( "SamplingRate"     , m_samplingRate=25       );  
  declareProperty( "OutputLevel"      , m_outputLevel=1         );
  declareProperty( "NoiseMean"        , m_noiseMean=0           );
  declareProperty( "NoiseStd"         , m_noiseStd=0            );
  declareProperty( "NSamples"         , m_nsamples=7            );
  declareProperty( "StartSamplingBC"  , m_startSamplingBC=0     );
}

PulseGeneratorTool::~PulseGeneratorTool()
{}

StatusCode PulseGeneratorTool::initialize()
{
  setMsgLevel( (MSG::Level)m_outputLevel );
  MSG_DEBUG( "Reading shaper values from: " << m_shaperFile << " and " << m_nsamples << " samples.");
  ReadShaper( m_shaperFile );
  return StatusCode::SUCCESS;
}

StatusCode PulseGeneratorTool::finalize()
{
  return StatusCode::SUCCESS;
}

void PulseGeneratorTool::ReadShaper( std::string filepath )
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

void PulseGeneratorTool::GenerateDeterministicPulse( std::vector<float> &pulse,  float amplitude, float phase, float lag) const
{
  pulse.clear();
  for( int sample=0; sample < m_nsamples; ++sample)
  {
    int i = m_shaperZeroIndex + (sample + m_startSamplingBC)*(m_samplingRate/m_shaperResolution) + 
            (phase/m_shaperResolution) - (lag/m_shaperResolution);

    if (i < 0 || i >= int(m_shaper.size())){
      pulse.push_back(m_pedestal);
    }else{
      pulse.push_back( amplitude*m_shaper[i] + m_pedestal );
    }
  }
}

void PulseGeneratorTool::AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStddev) const
{
  for( auto &value : pulse ){
    value += m_rng.Gaus(noiseMean, noiseStddev);
  }
}

StatusCode PulseGeneratorTool::execute( SG::EventContext &/*ctx*/, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);
  std::vector<float> pulse_sum(m_nsamples, 0.0);
  float noiseStd = m_noiseStd;

  for (int bcid = cell->bcid_start(); bcid <= cell->bcid_end(); ++bcid)
  {
    float edep = cell->edep(bcid);
    if (edep > 0.0)
    {
      float lag = bcid * m_samplingRate;
      float phase = 0.0;
      float deformation = 0.0;
      std::vector<float> pulse;

      GenerateDeterministicPulse(pulse, edep, phase + deformation, lag);
      for (int sample = 0; sample < m_nsamples; ++sample) {
        pulse_sum[sample] += pulse[sample];
      }
    }
  }

  AddGaussianNoise(pulse_sum, m_noiseMean, noiseStd);
  cell->setPulse(pulse_sum);
  return StatusCode::SUCCESS;
}
