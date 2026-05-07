#ifndef RootStreamAODMaker_h
#define RootStreamAODMaker_h

#include "CaloCell/enumeration.h"
#include "EventInfo/EventInfo.h"
#include "EventInfo/Seed.h"
#include "CaloRings/CaloRings.h"
#include "CaloCluster/CaloCluster.h"
#include "Egamma/Electron.h"
#include "TruthParticle/TruthParticle.h"
#include "Egamma/ElectronConverter.h"
#include "CaloCluster/CaloClusterConverter.h"
#include "CaloCell/CaloCellConverter.h"
#include "CaloCell/CaloDetDescriptorConverter.h"
#include "CaloRings/CaloRingsConverter.h"
#include "TruthParticle/TruthParticleConverter.h"
#include "EventInfo/EventInfoConverter.h"
#include "EventInfo/SeedConverter.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"



/**
 * @class RootStreamAODMaker
 * @brief Algorithm to stream AOD content to a ROOT file.
 * 
 * Serializes high-level reconstructed objects (Clusters, Electrons, Rings)
 * into a ROOT TTree for permanent storage.
 */
class RootStreamAODMaker : public Gaugi::Algorithm
{

  public:
    /** Constructor **/
    RootStreamAODMaker( std::string );
    
    virtual ~RootStreamAODMaker();
    
    virtual StatusCode initialize() override;

    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
    
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    
    virtual StatusCode execute( SG::EventContext &ctx , int /*evt*/ ) const override;

    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
    
    virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode finalize() override;



  private:
 

    StatusCode serialize( SG::EventContext &ctx ) const;

    template <class T> void InitBranch(TTree* fChain, std::string branch_name, T* param) const;
    

    void serializeCaloCluster( SG::EventContext &ctx , 
                               std::string key, 
                               std::vector<xAOD::CaloCluster_t> *container_t,
                               std::vector<xAOD::CaloCell_t> *container_cells_t,
                               std::vector<xAOD::CaloDetDescriptor_t> *container_descriptor_t
                              ) const;

    void serializeCaloRings( SG::EventContext &ctx , 
                             std::string key, 
                             std::vector<xAOD::CaloRings_t> *container_t ) const;

    void serializeElectrons( SG::EventContext &ctx , 
                             std::string key, 
                             std::vector<xAOD::Electron_t> *container_t ) const;

    void serializeEventInfo( SG::EventContext &ctx , 
                             std::string key, 
                             std::vector<xAOD::EventInfo_t> *container_t ) const;

    void serializeSeeds( SG::EventContext &ctx , 
                        std::string key, 
                        std::vector<xAOD::Seed_t> *container_t ) const;

    void serializeTruthParticle( SG::EventContext &ctx , 
                                 std::string key, 
                                 std::vector<xAOD::TruthParticle_t> *container_t ) const;

    void serializeCells( const xAOD::CaloCluster *clus,
                         std::vector<xAOD::CaloCell_t> *container_t,
                         std::vector<xAOD::CaloDetDescriptor_t> *container_descriptor_t ) const;

    std::string m_ntupleName;

    std::string m_inputCellsKey;
    std::string m_inputEventKey;
    std::string m_inputSeedsKey;
    std::string m_inputClusterKey;
    std::string m_inputRingerKey;
    std::string m_inputRingerL0Key;
    std::string m_inputTruthKey;
    std::string m_inputElectronKey;
    std::string m_inputTruthCellsKey;
    std::string m_inputTruthClusterKey;
    std::string m_inputTruthRingerKey;
    std::string m_inputTruthElectronKey;

    std::string m_outputCellsKey;
    std::string m_outputEventKey;
    std::string m_outputSeedsKey;
    std::string m_outputClusterKey;
    std::string m_outputRingerKey;
    std::string m_outputRingerL0Key;
    std::string m_outputTruthKey;
    std::string m_outputElectronKey;
    std::string m_outputTruthCellsKey;
    std::string m_outputTruthClusterKey;
    std::string m_outputTruthRingerKey;
    std::string m_outputTruthElectronKey;

    bool m_dumpCells;
    int m_outputLevel;
};

#endif

