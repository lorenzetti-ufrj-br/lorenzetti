#include "ConstrainedOptimalFilter.h"
#include "CaloCell/CaloDetDescriptor.h"

#include "cps/TextFilePulseShape.h"
#include "cps/AnalogPulse.h"
#include "cps/Digitizer.h"

using namespace Gaugi;


/**
 * @class ConstrainedOptimalFilter
 * @brief Calculates energy and time using the Constrained Optimal Filtering method.
 * 
 * This tool reconstructs the cell energy from the digitized samples. Unlike the 
 * standard OF, it calculates the weights dynamically or uses specific constraints
 * (e.g. baseline restoration) to minimize noise and pileup effects. It builds the
 * autocorrelation matrix and solves the linear system to find the amplitude.
 * 
 * Properties:
 * - PulsePath: Path to the reference pulse shape file.
 * - Threshold: Minimum amplitude threshold for processing.
 * - NSamples: Number of samples used in the filter.
 */
ConstrainedOptimalFilter::ConstrainedOptimalFilter( std::string name ) :
  IMsgService(name),
  AlgTool(),
  m_pulseShape(nullptr)
{
  declareProperty( "PulsePath"        , m_pulsepath       );
  declareProperty( "Threshold"        , m_threshold=0.0   );
  declareProperty( "NSamples"         , m_nsamples=0      );
  declareProperty( "StartSamplingBC"  , m_startSamplingBC );
  declareProperty( "SamplingRate"     , m_samplingRate=25 );
  declareProperty( "OutputLevel"      , m_outputLevel=1   );
}

//!=====================================================================

ConstrainedOptimalFilter::~ConstrainedOptimalFilter()
{
  delete m_pulseShape;
}

//!=====================================================================

StatusCode ConstrainedOptimalFilter::initialize()
{
  setMsgLevel(m_outputLevel);
  m_pulseShape = new cps::TextFilePulseShape( m_pulsepath.c_str() );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode ConstrainedOptimalFilter::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Executes the COF algorithm.
 * 
 * 1. Generates the reference pulse.
 * 2. Builds the covariance matrix (H).
 * 3. Inverts the matrix to solve for the amplitude (a_hat).
 * 4. Applies an iterative procedure to select valid samples (passing threshold).
 * 5. Re-calculates the final energy using the selected samples.
 */
StatusCode ConstrainedOptimalFilter::execute( SG::EventContext &/*ctx*/, Gaugi::EDM *edm ) const
{
  std::vector<float> refpulse;
  GeneratePulse(refpulse);
  TMatrixD H(m_nsamples, m_nsamples);
  TMatrixD saveH(m_nsamples, m_nsamples);
  int extraZeros = int(m_nsamples / 2);
  std::vector<float> fullVector;
  for (int i = 0; i < extraZeros; i++) fullVector.push_back(0.0);
  for (auto element : refpulse) fullVector.push_back(element);
  for (int i = 0; i < extraZeros; i++) fullVector.push_back(0.0);
  
  for (int line = 0; line < m_nsamples; line++){
    int firstIndex = fullVector.size() / 2 - line;
    for (int col = 0; col < m_nsamples; col++){
      H[line][col] = fullVector[firstIndex + col];
      saveH[line][col] = fullVector[firstIndex + col];
    }
  }

  auto *cell = static_cast<xAOD::CaloDetDescriptor*>(edm); 
  auto pulse = cell->pulse();
  TVectorD tpulse(m_nsamples);
  for (int i = 0; i< m_nsamples; i++) tpulse[i] = pulse[i];
  auto invH =  H.T().Invert();
  auto a_hat = invH*tpulse;
  
  std::vector<bool> passedSamples(m_nsamples); 
  int totalSamples = 0;
  int newCentralSample = 0;
  for (int i = 0; i<m_nsamples; i++){
    if (a_hat[i] >= m_threshold){
      passedSamples[i] = true;
      totalSamples++;
      if (i < m_nsamples/2) newCentralSample++;
    }
    else passedSamples[i] = false;
  } 
  if (!passedSamples[m_nsamples/2]){
    passedSamples[m_nsamples/2] = true; //always accept the central samples
    totalSamples++;
  }

  TMatrixD G(totalSamples, m_nsamples);
  TMatrixD saveG(totalSamples, m_nsamples);
  int k = 0;
  for (int i = 0; i<m_nsamples; i++){
    if (passedSamples[i]){
      for (int j = 0; j < m_nsamples; j++) {
        G[k][j]= saveH[i][j];
        saveG[k][j] = saveH[i][j];
      }
      k++;
    }
  }
  auto a_hat_hat = ((saveG*G.T()).Invert())*saveG*tpulse;
  cell->setE(a_hat_hat[newCentralSample]);
  return StatusCode::SUCCESS;
}

/**
 * @brief Builds the reference (unit-amplitude, zero-phase) pulse used by the filter.
 *
 * The shape sampling is delegated to CPS; samples whose shape time falls outside the
 * reference pulse are set to zero (matching the original behavior).
 */
void ConstrainedOptimalFilter::GeneratePulse(  std::vector<float> &pulse) const
{
  pulse.resize( m_nsamples );

  cps::AnalogPulse analogPulse( m_pulseShape, /*amplitude*/ 1.0, /*pedestal*/ 0.0,
                                /*phase*/ 0.0, /*deformationLevel*/ 0, /*noiseMean*/ 0, /*noiseStdDev*/ 0 );
  cps::Digitizer digitizer( m_nsamples, m_samplingRate, m_startSamplingBC * m_samplingRate );
  std::vector<double> samples = digitizer.Digitize( &analogPulse );

  const double tMin = m_pulseShape->GetTMin();
  const double tMax = m_pulseShape->GetTMax();

  for (int i = 0; i < m_nsamples; i++) {
    double shapeTime = (i + m_startSamplingBC) * m_samplingRate;
    if (shapeTime < tMin || shapeTime > tMax){
      pulse[i] = 0;
      continue;
    }
    pulse[i] = (float)samples[i];
  }
}
