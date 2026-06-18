#ifndef PulseGenerator_h
#define PulseGenerator_h

#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/AlgTool.h"
#include "GaugiKernel/EDM.h"
#include "TRandom3.h"

// Forward declarations of the CPS (Calorimetry Pulse Simulator) types. The full
// headers are included only in the .cxx so the ROOT dictionary generator never
// parses them.
namespace cps {
  class TextFilePulseShape;
  class Digitizer;
}


/**
 * @class PulseGenerator
 * @brief Tool to simulate the electronic pulse shape.
 *
 * This tool takes the energy deposit in a cell and generates a time-sampled
 * electronic pulse. The pulse shape sampling and digitization are delegated to
 * the CPS library (cps::TextFilePulseShape + cps::Digitizer); this tool keeps the
 * bunch-crossing accumulation and adds electronic noise/deformation using ROOT's
 * TRandom3 to preserve reproducibility against previous results.
 */
class PulseGenerator : public Gaugi::AlgTool
{

  public:
    /** Constructor **/
    PulseGenerator( std::string name );
    virtual ~PulseGenerator();
    
    virtual StatusCode initialize() override;
    virtual StatusCode finalize() override;

    /**
     * @brief Execute the pulse generation for a specific cell.
     * @param ctx Event context.
     * @param edm Pointer to the CaloDetDescriptor (the cell).
     * @return Status code indicating success or failure.
     */
    virtual StatusCode execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const override;

    


  private:

    void GenerateDeterministicPulse(  std::vector<float> &pulse,  float amplitude, float phase, float lag) const;
    void AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStddev) const;


    /*! Number of samples to be generated */
    int m_nsamples;
    int m_startSamplingBC;
    float m_pedestal;
    float m_deformationMean;
    float m_deformationStd;
    float m_samplingRate;
    float m_noiseMean;
    float m_noiseStd;

    // new for including cell defects
    bool m_doDefects;
    bool m_deadModules;
    std::vector<std::vector<int>> m_cellHash;
    std::vector<float> m_noiseFactor;
    std::vector<std::vector<int>> m_noisyEvents;

    /*! Reference pulse shape and digitizer, provided by the CPS library */
    cps::TextFilePulseShape *m_pulseShape;
    cps::Digitizer *m_digitizer;

    /*! The shaper configuration path */
    std::string m_shaperFile;
    /*! Output level message */
    int m_outputLevel;
    /*! Random generator */
    mutable TRandom3 m_rng;
};

#endif




