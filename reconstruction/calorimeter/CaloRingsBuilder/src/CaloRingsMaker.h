#ifndef CaloRingsMaker_h
#define CaloRingsMaker_h

#include "CaloCell/enumeration.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/Algorithm.h"
#include "CaloRings/CaloRingsContainer.h"
#include "CaloCluster/CaloClusterContainer.h"


/**
 * @class RingSet
 * @brief Helper class to manage a set of rings for a specific layer.
 * 
 * accumulating energy in concentric rings centered around a specific point.
 */
class RingSet{
  
    public:
      /*! Constructor */
      RingSet( std::vector<CaloSampling> &samplings , unsigned nrings, float deta, float dphi );
      /*! Destructor */
      RingSet()=default;
      
      /**
       * @brief Add the cell energy to the correct ring position.
       * 
       * Checks validity of the cell (sampling) and calculates its distance
       * to the center to assign energy to the appropriate ring.
       * 
       * @param cell Pointer to the calorimeter cell.
       * @param eta_center Eta of the ring center.
       * @param phi_center Phi of the ring center.
       */
      void push_back( const xAOD::CaloCell *cell, float eta_center, float phi_center );
      
      /*! Get the ringer shaper pattern for this RingSet */
      const std::vector<float>& rings() const;
      
      /*! The number of rings in this RingSet */
      size_t size() const;
      
      /**
       * @brief Check if cell belongs to this RingSet's samplings.
       * @return true if valid, false otherwise.
       */
      bool isValid( const xAOD::CaloCell*) const;
      
      /*! Zeroize all energy values */
      void clear();


    private:

      std::vector<float> m_rings;
      /*! Delta eta */
      float m_deta;
      /*! Delta phi */
      float m_dphi;
      /*! Sampling layer */
      std::vector<CaloSampling> m_samplings;
  };





/**
 * @class CaloRingsMaker
 * @brief Algorithm to build RingSets from CaloClusters.
 * 
 * This algorithm creates the "Rings" feature set used for electron identification.
 * It iterates over clusters and computes energy sums in concentric rings for
 * each calorimeter layer.
 */
class CaloRingsMaker : public Gaugi::Algorithm
{
  public:


    /** Constructor **/
    CaloRingsMaker( std::string );
    
    virtual ~CaloRingsMaker();
    
    virtual StatusCode initialize() override;

    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
    
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    
    /*! Execute in ComponentAccumulator */
    virtual StatusCode execute( SG::EventContext &ctx, int /*evt*/ ) const override;

    /*! Post-execution step to create rings */
    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
    
    virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode finalize() override;



  private:
 
    int m_maxRingSets;    
    int m_maxRingsAccumulated;

    const xAOD::CaloCell* maxCell( const xAOD::CaloCluster*   , RingSet & ) const;
   
    std::string m_histPath;

    std::string m_clusterKey;
    std::string m_ringerKey;

    std::vector<float>  m_detaRings;
    std::vector<float>  m_dphiRings;
    std::vector<int>    m_nRings;
    std::vector<float>  m_etaRange;

    std::vector<std::vector<int>>    m_layerRings;

    int m_outputLevel;
    bool m_doForward;

    bool m_DoSigmaCut;
    float m_SigmaCut;
};

#endif




