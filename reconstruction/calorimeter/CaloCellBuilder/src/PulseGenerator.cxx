
#include "CaloCell/CaloDetDescriptor.h"
#include "PulseGenerator.h"
#include "Randomize.hh"
#include "TRandom.h"

#include "cps/TextFilePulseShape.h"
#include "cps/AnalogPulse.h"
#include "cps/Digitizer.h"


using namespace Gaugi;


/**
 * @class PulseGenerator
 * @brief Generates electronic pulse shapes for calorimeter cells.
 *
 * Simulates the response of the readout electronics to an energy deposit. The
 * reference shaper function and the time sampling are provided by the CPS library
 * (cps::TextFilePulseShape + cps::Digitizer); this tool accumulates the per-bunch
 * crossing contributions and adds electronic noise and random deformations.
 *
 * Properties:
 * - ShaperFile: File containing the reference pulse shape points.
 * - Pedestal: Baseline voltage.
 * - NoiseMean/Std: Electronic noise parameters.
 * - SamplingRate: Readout sampling rate (usually 25ns).
 */
PulseGenerator::PulseGenerator( std::string name ) :
  IMsgService(name),
  AlgTool(),
  m_pulseShape(nullptr),
  m_digitizer(nullptr),
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

//!=====================================================================

PulseGenerator::~PulseGenerator()
{
  delete m_digitizer;
  delete m_pulseShape;
}

//!=====================================================================

StatusCode PulseGenerator::initialize()
{
  setMsgLevel( (MSG::Level)m_outputLevel );
  MSG_DEBUG( "Reading shaper values from: " << m_shaperFile << " and " << m_nsamples << " samples.");
  m_pulseShape = new cps::TextFilePulseShape( m_shaperFile.c_str() );
  m_digitizer  = new cps::Digitizer( m_nsamples, m_samplingRate, m_startSamplingBC * m_samplingRate );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode PulseGenerator::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Generates the pulse for a cell.
 * 
 * Loops over bunch crossings and sums the contribution of energy deposits
 * from each BCID, weighted by the shaper function at the appropriate time lag.
 * Adds noise and sets the final pulse in the cell object.
 */
StatusCode PulseGenerator::execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const
{
  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm);

  auto pulse_size = m_nsamples;

  // Create an pulse with zeros with n samples
  std::vector<float> pulse_sum(pulse_size, 0.0);
  // Loop over each bunch crossing
  for ( int bcid = cell->bcid_start();  bcid <= cell->bcid_end(); ++bcid )
  {
    // Generate the pulse
    std::vector<float> pulse;
    // GenerateDeterministicPulse( pulse, cell->edep(bcid), 0, bcid*cell->bc_duration() ); // phase=0
    GenerateDeterministicPulse( pulse, cell->edep(bcid), cell->tof(bcid), bcid*cell->bc_duration() ); // phase='truth' tof
    // Accumulate into pulse sum (Sum all pulses)
    for ( int samp=0; samp < pulse_size; ++samp ){
      pulse_sum[samp] += pulse[samp];
    }

    cell->setPulse( bcid, pulse ); 
  }

  // Add gaussian noise
  AddGaussianNoise(pulse_sum, m_noiseMean, m_noiseStd);

  // Add the integrated pulse centered in the bunch crossing zero
  cell->setPulse( pulse_sum );
  cell->setSigma( m_noiseStd );

  return StatusCode::SUCCESS;
}

//!=====================================================================

void PulseGenerator::AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStd) const
{
  for ( auto &value : pulse )
    value += m_rng.Gaus( noiseMean, noiseStd );
}

//!=====================================================================

/**
 * @brief Generates the deterministic (noise-free) pulse for a single bunch crossing.
 *
 * The shape sampling is delegated to CPS: the energy deposit is the pulse amplitude
 * and the effective phase is the truth time-of-flight minus the bunch-crossing lag.
 * A random deformation (TRandom3) is added per sample, and samples whose shape time
 * falls outside the reference pulse are set to zero (matching the original behavior).
 */
void PulseGenerator::GenerateDeterministicPulse(  std::vector<float> &pulse,  float amplitude, float phase, float lag) const
{
  pulse.resize( m_nsamples );

  // CPS phase combines the truth tof and the bunch-crossing lag.
  const double cpsPhase = phase - lag;
  cps::AnalogPulse analogPulse( m_pulseShape, amplitude, m_pedestal, cpsPhase,
                                /*deformationLevel*/ 0, /*noiseMean*/ 0, /*noiseStdDev*/ 0 );
  std::vector<double> samples = m_digitizer->Digitize( &analogPulse );

  const double tMin = m_pulseShape->GetTMin();
  const double tMax = m_pulseShape->GetTMax();

  for (int i = 0; i < m_nsamples; i++) {
    // random deformation (normal from geant); drawn unconditionally to preserve the
    // RNG call sequence regardless of the range check below.
    float deformation = m_rng.Gaus(m_deformationMean, m_deformationStd);
    // Time at which the reference shape is evaluated for this sample.
    double shapeTime = (i + m_startSamplingBC) * m_samplingRate + cpsPhase;
    if (shapeTime < tMin || shapeTime > tMax){
      pulse[i] = 0;
      continue;
    }
    pulse[i] = (float)samples[i] + deformation;
  }
}






