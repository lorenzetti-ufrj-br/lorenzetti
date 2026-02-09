#ifndef OptimalFilter_h
#define OptimalFilter_h

#include "GaugiKernel/AlgTool.h"
#include "GaugiKernel/EDM.h"



/**
 * @class OptimalFilter
 * @brief AlgTool for signal reconstruction using standard Optimal Filtering (OF).
 * 
 * Uses pre-calculated weights to estimate the energy and time from the
 * digitized samples.
 */
class OptimalFilter : public Gaugi::AlgTool
{

  public:
    /** Constructor **/
    OptimalFilter( std::string name );
    virtual ~OptimalFilter();
    virtual StatusCode initialize() override;
    virtual StatusCode finalize() override;

    /**
     * @brief Apply the optimal filter to the cell.
     * @param ctx Event context.
     * @param edm Pointer to the CaloDetDescriptor (cell).
     */
    virtual StatusCode execute( SG::EventContext &ctx, Gaugi::EDM *edm ) const override;

  private:

    /*! optimal filter weights */
    std::vector<float> m_ofweightsEnergy;
    std::vector<float> m_ofweightsTime;
};

#endif




