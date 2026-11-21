#ifndef OptimalFilterTool_h
#define OptimalFilterTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include <vector>

/**
 * @class OptimalFilterTool
 * @brief Tool for signal reconstruction using standard Optimal Filtering (OF).
 * 
 * Uses pre-calculated weights to estimate the energy and time from the
 * digitized samples.
 */
class OptimalFilterTool : public Gaugi::Tool
{
  public:
    /** Constructor **/
    OptimalFilterTool( std::string name );
    virtual ~OptimalFilterTool();
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
    int m_outputLevel;
};

using OptimalFilter = OptimalFilterTool;

#endif
