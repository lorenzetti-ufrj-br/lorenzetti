#ifndef PulseGeneratorTool_h
#define PulseGeneratorTool_h

#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include "TRandom3.h"

/**
 * @class PulseGeneratorTool
 * @brief Tool to simulate the electronic pulse shape.
 * 
 * This tool takes the energy deposit in a cell and generates a time-sampled
 * electronic pulse (using a shaper function). It also adds electronic noise
 * and can simulate defects.
 */
class PulseGeneratorTool : public Gaugi::Tool
{
  public:
    /** Constructor **/
    PulseGeneratorTool( std::string name );
    virtual ~PulseGeneratorTool();
    
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
    void ReadShaper( std::string );
    void GenerateDeterministicPulse(  std::vector<float> &pulse,  float amplitude, float phase, float lag) const;
    void AddGaussianNoise( std::vector<float> &pulse, float noiseMean, float noiseStddev) const;

    /*! Number of samples to be generated */
    int m_nsamples;
    int m_startSamplingBC;
    int m_shaperZeroIndex;
    float m_shaperResolution;
    std::string m_shaperFile;
    float m_samplingRate;
    float m_pedestal;
    float m_deformationMean;
    float m_deformationStd;
    float m_noiseMean;
    float m_noiseStd;
    int m_outputLevel;
    std::vector<float> m_timeSeries;
    std::vector<float> m_shaper;
    mutable TRandom3 m_rng;
};

using PulseGenerator = PulseGeneratorTool;

#endif
