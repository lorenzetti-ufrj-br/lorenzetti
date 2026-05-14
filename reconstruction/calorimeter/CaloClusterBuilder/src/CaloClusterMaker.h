#ifndef CaloClusterMaker_h
#define CaloClusterMaker_h

#include "CaloCell/enumeration.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/Algorithm.h"
#include "CaloCell/CaloCellContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "EventInfo/SeedContainer.h"
#include "ShowerShapes.h"


/**
 * @class CaloClusterMaker
 * @brief Algorithm to reconstruct calorimeter clusters.
 * 
 * Uses a seed-based approach to group calorimeter cells into clusters.
 * It identifies the highest energy cell (seed) and aggregates surrounding cells
 * within a defined window.
 */
class CaloClusterMaker : public Gaugi::Algorithm
{

  public:
    /** Constructor **/
    CaloClusterMaker( std::string );
    
    virtual ~CaloClusterMaker();
    
    virtual StatusCode initialize() override;

    /*! Book all histograms into the current storegate */
    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    
    /*! Execute in step action step from geant core */
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    
    /*! Execute in ComponentAccumulator */
    virtual StatusCode execute( SG::EventContext &ctx , int /*evt*/ ) const override;
    
    /*! execute before start the step action */
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;

    /*! execute after the step action */
    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
    
    /*! fill histogram in the end */
    virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode finalize() override;



  private:
 
    
    void fillCluster( SG::EventContext &ctx,  xAOD::CaloCluster *clus, std::string key ) const;
    
    float dR( float eta1, float phi1, float eta2, float phi2 ) const;
 
    
      
    // input keys
    std::string m_cellsKey; 
    std::string m_seedKey;
    // output keys
    std::string m_clusterKey;

    float m_etaWindow;
    float m_phiWindow;
    bool m_doForwardMoments;
    std::string m_histPath;

    // Shower shaper calculator
    ShowerShapes *m_showerShapes;

    float m_minCenterEnergy;


};

#endif




