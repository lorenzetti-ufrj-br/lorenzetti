#ifndef ConstrainedOptimalFilter_h
#define ConstrainedOptimalFilter_h

#include "GaugiKernel/AlgTool.h"
#include "GaugiKernel/EDM.h"
#include "TMatrixD.h"
#include "TVectorD.h"

// Forward declaration of the CPS reference pulse shape. The full header is included
// only in the .cxx so the ROOT dictionary generator never parses it.
namespace cps {
  class TextFilePulseShape;
}



/**
 * @class ConstrainedOptimalFilter
 * @brief AlgTool for signal reconstruction using a Constrained Optimal Filter.
 *
 * Reconstructs the amplitude and time of the signal from the digitized
 * samples using the Optimal Filtering technique with additional constraints
 * (e.g., pedestal constraints).
 */
class ConstrainedOptimalFilter : public Gaugi::AlgTool
{

  public:
    /** Constructor **/
    ConstrainedOptimalFilter( std::string name );
    virtual ~ConstrainedOptimalFilter();
    virtual StatusCode initialize() override;
    virtual StatusCode finalize() override;
    void GeneratePulse(  std::vector<float> &pulse) const;

    /**
     * @brief Apply the filter to the cell.
     * @param ctx Event context.
     * @param edm Pointer to the CaloDetDescriptor (cell).
     */
    virtual StatusCode execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const override;

  private:

    /*! optimal filter weights */
    int m_startSamplingBC;
    std::string m_pulsepath;
    /*! Reference pulse shape, provided by the CPS library */
    cps::TextFilePulseShape *m_pulseShape;
    float m_threshold;
    int m_nsamples;
    float m_samplingRate;
};

#endif




