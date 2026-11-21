#ifndef ConstrainedOptimalFilterTool_h
#define ConstrainedOptimalFilterTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include "TMatrixD.h"
#include "TVectorD.h"
#include <vector>
#include <string>

/**
 * @class ConstrainedOptimalFilterTool
 * @brief Tool for signal reconstruction using a Constrained Optimal Filter.
 * 
 * Reconstructs the amplitude and time of the signal from the digitized
 * samples using the Optimal Filtering technique with additional constraints
 * (e.g., pedestal constraints).
 */
class ConstrainedOptimalFilterTool : public Gaugi::Tool
{
  public:
    /** Constructor **/
    ConstrainedOptimalFilterTool( std::string name );
    virtual ~ConstrainedOptimalFilterTool();
    virtual StatusCode initialize() override;
    virtual StatusCode finalize() override;
    void ReadShaper( std::string filepath );
    void GeneratePulse( std::vector<float> &pulse ) const;

    /**
     * @brief Apply the filter to the cell.
     * @param ctx Event context.
     * @param edm Pointer to the CaloDetDescriptor (cell).
     */
    virtual StatusCode execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const override;

  private:
    int m_startSamplingBC;
    std::string m_pulsepath;
    std::vector<float> m_shaper;
    float m_shaperResolution;
    std::vector<float> m_timeSeries;
    float m_threshold;
    int m_shaperZeroIndex;
    int m_nsamples;
    float m_samplingRate;
    int m_outputLevel;
};

using ConstrainedOptimalFilter = ConstrainedOptimalFilterTool;

#endif
