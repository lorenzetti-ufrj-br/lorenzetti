#include "CaloCell/CaloCellContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"
#include "EventInfo/EventInfoContainer.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "Egamma/ElectronContainer.h"

#include "CaloCell/CaloCellConverter.h"
#include "CaloCell/CaloDetDescriptorConverter.h"
#include "CaloCluster/CaloClusterConverter.h"
#include "CaloRings/CaloRingsConverter.h"
#include "EventInfo/EventInfoConverter.h"
#include "EventInfo/SeedConverter.h"
#include "TruthParticle/TruthParticleConverter.h"
#include "Egamma/ElectronConverter.h"
#include "TTree.h"
#include "RootStreamAODMaker.h"
#include "GaugiKernel/EDM.h"


using namespace SG;
using namespace Gaugi;



/**
 * @class RootStreamAODMaker
 * @brief Serializes reconstruction objects to a ROOT file (AOD format).
 * 
 * This algorithm gathers various EDM objects (EventInfo, TruthParticles,
 * CaloClusters, CaloRings, Electrons, etc.) from StoreGate and writes them
 * into a TTree. It uses "Converter" helper classes to translate transient
 * xAOD objects into persistent struct-based representations.
 * 
 * Properties:
 * - Input*Key: Keys for objects in StoreGate.
 * - Output*Key: Branch names in the output TTree.
 * - NtupleName: Name of the TTree.
 * - DumpCells: If true, also dumps detailed cell information (heavy).
 */
RootStreamAODMaker::RootStreamAODMaker( std::string name ) : 
  IMsgService(name),
  Algorithm()
{
  declareProperty( "InputEventKey"           , m_inputEventKey="EventInfo"                );
  declareProperty( "InputSeedsKey"           , m_inputSeedsKey="Seeds"                    );
  declareProperty( "InputTruthKey"           , m_inputTruthKey="Particles"                );

  declareProperty( "InputCellsKey"           , m_inputCellsKey="Cells"                    );
  declareProperty( "InputClusterKey"         , m_inputClusterKey="Clusters"               );
  declareProperty( "InputRingerKey"          , m_inputRingerKey="Rings"                   );
  declareProperty( "InputElectronKey"        , m_inputElectronKey="Electrons"             );
  declareProperty( "InputRingerL0Key"        , m_inputRingerL0Key="RingsL0"              );

  declareProperty( "InputTruthCellsKey"      , m_inputTruthCellsKey="TruthCells"          );
  declareProperty( "InputTruthClusterKey"    , m_inputTruthClusterKey="TruthClusters"     );
  declareProperty( "InputTruthRingerKey"     , m_inputTruthRingerKey="TruthRings"         );
  declareProperty( "InputTruthElectronKey"   , m_inputTruthElectronKey="TruthElectrons"   );


  declareProperty( "OutputEventKey"          , m_outputEventKey="EventInfo"           );
  declareProperty( "OutputSeedsKey"          , m_outputSeedsKey="Seeds"               );
  declareProperty( "OutputTruthKey"          , m_outputTruthKey="Particles"           );

  declareProperty( "OutputCellsKey"          , m_outputCellsKey="Cells"               );
  declareProperty( "OutputClusterKey"        , m_outputClusterKey="Clusters"          );
  declareProperty( "OutputRingerKey"         , m_outputRingerKey="Rings"              );
  declareProperty( "OutputElectronKey"       , m_outputElectronKey="Electrons"        );
  declareProperty( "OutputRingerL0Key"       , m_outputRingerL0Key="RingsL0"          );

  declareProperty( "OutputTruthCellsKey"     , m_outputTruthCellsKey="TruthCells"     );
  declareProperty( "OutputTruthClusterKey"   , m_outputTruthClusterKey="TruthClusters");
  declareProperty( "OutputTruthRingerKey"    , m_outputTruthRingerKey="TruthRings"    );
  declareProperty( "OutputTruthElectronKey"  , m_outputTruthElectronKey="TruthElectrons"  );

  declareProperty( "OutputLevel"             , m_outputLevel=1                        );
  declareProperty( "NtupleName"              , m_ntupleName="physics"                 );
  declareProperty( "DumpCells"               , m_dumpCells=false                      );
}

//!=====================================================================

RootStreamAODMaker::~RootStreamAODMaker()
{;}

//!=====================================================================

StatusCode RootStreamAODMaker::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::bookHistograms( SG::EventContext &ctx ) const
{
  auto store = ctx.getStoreGateSvc();
  std::vector<xAOD::EventInfo_t           > container_event;
  std::vector<xAOD::Seed_t                > container_seeds;
  std::vector<xAOD::TruthParticle_t       > container_truth;

  std::vector<xAOD::CaloCell_t            > container_cells;
  std::vector<xAOD::CaloDetDescriptor_t   > container_descriptor;
  std::vector<xAOD::CaloCluster_t         > container_clus;
  std::vector<xAOD::CaloRings_t           > container_rings;
  std::vector<xAOD::CaloRings_t           > container_ringsL0;
  std::vector<xAOD::Electron_t            > container_electron;

  std::vector<xAOD::CaloCell_t            > container_cells_truth;
  std::vector<xAOD::CaloCluster_t         > container_clus_truth;
  std::vector<xAOD::CaloRings_t           > container_rings_truth;
  std::vector<xAOD::Electron_t            > container_electron_truth;



  store->cd();
  TTree *tree = new TTree(m_ntupleName.c_str(), "");

  tree->Branch( ("EventInfoContainer_"     + m_outputEventKey).c_str()          , &container_event      );
  tree->Branch( ("SeedContainer_"          + m_outputSeedsKey).c_str()          , &container_seeds      );
  tree->Branch( ("TruthParticleContainer_" + m_outputTruthKey).c_str()          , &container_truth      );


  tree->Branch( ("CaloRingsContainer_"     + m_outputRingerKey).c_str()         , &container_rings      );
  tree->Branch( ("CaloRingsContainer_"     + m_outputRingerL0Key).c_str()       , &container_ringsL0    );
  tree->Branch( ("CaloClusterContainer_"   + m_outputClusterKey).c_str()        , &container_clus       );
  tree->Branch( ("ElectronContainer_"      + m_outputElectronKey).c_str()       , &container_electron   );
  
  tree->Branch( ("CaloClusterContainer_"   + m_outputTruthClusterKey).c_str()   , &container_clus_truth );
  tree->Branch( ("CaloRingsContainer_"     + m_outputTruthRingerKey).c_str()    , &container_rings_truth);
  tree->Branch( ("ElectronContainer_"      + m_outputTruthElectronKey).c_str()  , &container_electron_truth);
  
  if(m_dumpCells){
    tree->Branch(  ("CaloCellContainer_"          + m_outputCellsKey).c_str()          , &container_cells                  );
    tree->Branch(  ("CaloDetDescriptorContainer_" + m_outputCellsKey).c_str()          , &container_descriptor             );
    tree->Branch(  ("CaloCellContainer_"          + m_outputTruthCellsKey).c_str()     , &container_cells_truth            );
  }


  store->add( tree );
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::pre_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::execute( EventContext &/*ctx*/, const G4Step * /*step*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::execute( EventContext &/*ctx*/, int /*evt*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::post_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamAODMaker::fillHistograms( EventContext &ctx ) const
{
  return serialize(ctx);
}

//!=====================================================================


template <class T>
void RootStreamAODMaker::InitBranch(TTree* fChain, std::string branch_name, T* param) const
{
  std::string bname = branch_name;
  if (fChain->GetAlias(bname.c_str()))
     bname = std::string(fChain->GetAlias(bname.c_str()));

  if (!fChain->FindBranch(bname.c_str()) ) {
    MSG_WARNING( "unknown branch " << bname );
    return;
  }
  fChain->SetBranchStatus(bname.c_str(), 1.);
  fChain->SetBranchAddress(bname.c_str(), param);
}

//!=====================================================================

StatusCode RootStreamAODMaker::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Performs the serialization.
 * 
 * 1. Retrieves objects (EventInfo, Truth, Seeds, Clusters, Rings, Electrons) from StoreGate.
 * 2. Converts them to their persistent structs using `xAOD::*Converter`.
 * 3. Pushes the structs into the vectors linked to the TTree branches.
 * 4. Fills the TTree.
 */
StatusCode RootStreamAODMaker::serialize( EventContext &ctx ) const
{
  

  auto store = ctx.getStoreGateSvc();

  store->cd();
  TTree *tree = store->tree(m_ntupleName);
 
  std::vector<xAOD::CaloDetDescriptor_t > *container_descriptor       = nullptr;
  std::vector<xAOD::CaloCell_t          > *container_cells            = nullptr;
  std::vector<xAOD::CaloCluster_t       > *container_clus             = nullptr;
  std::vector<xAOD::CaloRings_t         > *container_rings            = nullptr;
  std::vector<xAOD::CaloRings_t         > *container_ringsL0          = nullptr;
  std::vector<xAOD::EventInfo_t         > *container_event            = nullptr;
  std::vector<xAOD::Seed_t              > *container_seeds            = nullptr;
  std::vector<xAOD::TruthParticle_t     > *container_truth            = nullptr;
  std::vector<xAOD::Electron_t          > *container_electron         = nullptr;
  std::vector<xAOD::CaloCell_t          > *container_cells_truth      = nullptr;
  std::vector<xAOD::CaloCluster_t       > *container_clus_truth       = nullptr;
  std::vector<xAOD::CaloRings_t         > *container_rings_truth      = nullptr;
  std::vector<xAOD::Electron_t          > *container_electron_truth   = nullptr;

  MSG_DEBUG( "Link all branches..." );
  InitBranch( tree, ("EventInfoContainer_"     + m_outputEventKey).c_str()          , &container_event      );
  InitBranch( tree, ("SeedContainer_"          + m_outputSeedsKey).c_str()          , &container_seeds      );
  InitBranch( tree, ("TruthParticleContainer_" + m_outputTruthKey).c_str()          , &container_truth      );
  InitBranch( tree, ("CaloRingsContainer_"     + m_outputRingerKey).c_str()         , &container_rings      );
  InitBranch( tree, ("CaloRingsContainer_"     + m_outputRingerL0Key).c_str()       , &container_ringsL0    );
  InitBranch( tree, ("CaloClusterContainer_"   + m_outputClusterKey).c_str()        , &container_clus       );
  InitBranch( tree, ("ElectronContainer_"      + m_outputElectronKey).c_str()       , &container_electron   );
  InitBranch( tree, ("CaloRingsContainer_"     + m_outputTruthRingerKey).c_str()    , &container_rings_truth);
  InitBranch( tree, ("CaloClusterContainer_"   + m_outputTruthClusterKey).c_str()   , &container_clus_truth );
  InitBranch( tree, ("ElectronContainer_"      + m_outputTruthElectronKey).c_str()  , &container_electron_truth);

  if(m_dumpCells){
    InitBranch( tree,  ("CaloCellContainer_"          + m_outputCellsKey).c_str()      , &container_cells      );
    InitBranch( tree,  ("CaloDetDescriptorContainer_" + m_outputCellsKey).c_str()      , &container_descriptor );
    InitBranch( tree,  ("CaloCellContainer_"          + m_outputTruthCellsKey).c_str() , &container_cells_truth);
  }


  serializeEventInfo(ctx, m_inputEventKey, container_event);
  serializeSeeds(ctx, m_inputSeedsKey, container_seeds);
  serializeTruthParticle(ctx, m_inputTruthKey, container_truth);

  // digitalized clusters
  if(ctx.exist(m_inputClusterKey)){
    serializeCaloCluster(ctx, m_inputClusterKey, container_clus, container_cells, container_descriptor);
  }
  if(ctx.exist(m_inputRingerKey)){
    serializeCaloRings(ctx, m_inputRingerKey, container_rings);
  }
  if(ctx.exist(m_inputRingerL0Key)){
    serializeCaloRings(ctx, m_inputRingerL0Key, container_ringsL0);
  }
  if(ctx.exist(m_inputElectronKey)){
    serializeElectrons(ctx, m_inputElectronKey, container_electron);
  }
  
  // Truth clusters
  if(ctx.exist(m_inputTruthClusterKey)){
    serializeCaloCluster(ctx, m_inputTruthClusterKey, container_clus_truth, container_cells_truth, container_descriptor);
  }
  if(ctx.exist(m_inputTruthRingerKey)){
    serializeCaloRings(ctx, m_inputTruthRingerKey, container_rings_truth);
  }
  if(ctx.exist(m_inputTruthElectronKey)){
    serializeElectrons(ctx, m_inputTruthElectronKey, container_electron_truth);
  }
  

  
  tree->Fill();

  if(m_dumpCells){
    delete container_descriptor;
    delete container_cells     ;
    delete container_cells_truth;
  }
  delete container_clus      ;
  delete container_rings     ;
  delete container_ringsL0   ;
  delete container_event     ;
  delete container_truth     ;
  delete container_seeds     ;
  delete container_electron  ;
  delete container_rings_truth;
  delete container_clus_truth;
  delete container_electron_truth;

  return StatusCode::SUCCESS;
 
}


void RootStreamAODMaker::serializeCaloCluster( EventContext &ctx , 
                                               std::string key, 
                                               std::vector<xAOD::CaloCluster_t> *container_t,
                                               std::vector<xAOD::CaloCell_t> *container_cells_t,
                                               std::vector<xAOD::CaloDetDescriptor_t> *container_descriptor_t
                                              ) const
{
    SG::ReadHandle<xAOD::CaloClusterContainer> container( key, ctx );
  
    if( !container.isValid() )
    {
      MSG_FATAL("It's not possible to read the xAOD::CaloClusterContainer from this Context using this key " << key );
    }

    for (const auto clus : **container.ptr() ){
      xAOD::CaloCluster_t clus_t;
      xAOD::CaloClusterConverter cnv;
      cnv.convert( clus, clus_t );
      container_t->push_back(clus_t);

      if (m_dumpCells){
        serializeCells(clus, container_cells_t, container_descriptor_t);
      }

    }
}
                                            




void RootStreamAODMaker::serializeCells( const xAOD::CaloCluster *clus,
                                         std::vector<xAOD::CaloCell_t> *container_t,
                                         std::vector<xAOD::CaloDetDescriptor_t> *container_descriptor_t ) const
{

    std::map<unsigned long int, const xAOD::CaloCell*> cell_map;

    for(const auto&cell : clus->cells()){

      // to avoid duplicate cells for clusters
      if(cell_map.count(cell->descriptor()->hash())){
        continue;
      }
      cell_map[cell->descriptor()->hash()] = cell;

      { // serialize cell
        xAOD::CaloCell_t cell_t;
        xAOD::CaloCellConverter cnv;
        cnv.convert(cell, cell_t);
        container_t->push_back(cell_t);
      }
      
      { // serialize cell descriptor
        const xAOD::CaloDetDescriptor *det = cell->descriptor();
        xAOD::CaloDetDescriptor_t det_t;
        xAOD::CaloDetDescriptorConverter cnv;
        cnv.convert(det, det_t);
        container_descriptor_t->push_back(det_t);
      }
    }
}



void RootStreamAODMaker::serializeTruthParticle( EventContext &ctx , 
                                                 std::string key, 
                                                 std::vector<xAOD::TruthParticle_t> *container_t ) const
{
    SG::ReadHandle<xAOD::TruthParticleContainer> container( key, ctx );
  
    if( !container.isValid() )
    {
      MSG_FATAL("It's not possible to read the xAOD::TruthParticleContainer from this Context using this key " << key );
    }

    for (const auto par : **container.ptr() ){
      xAOD::TruthParticle_t par_t;
      xAOD::TruthParticleConverter cnv;
      cnv.convert( par, par_t );
      container_t->push_back(par_t);
    }
}




void RootStreamAODMaker::serializeEventInfo( EventContext &ctx , 
                                             std::string key, 
                                             std::vector<xAOD::EventInfo_t> *container_t ) const
{
    SG::ReadHandle<xAOD::EventInfoContainer> event(key, ctx);

    if( !event.isValid() ){
      MSG_FATAL( "It's not possible to read the xAOD::EventInfoContainer from this Context" );
    }

    xAOD::EventInfo_t event_t;
    xAOD::EventInfoConverter cnv;
    cnv.convert( (**event.ptr()).front(), event_t);
    container_t->push_back(event_t);
}



void RootStreamAODMaker::serializeSeeds( EventContext &ctx , 
                                        std::string key, 
                                        std::vector<xAOD::Seed_t> *container_t ) const
{
    MSG_DEBUG("Serialize Seed..");
    SG::ReadHandle<xAOD::SeedContainer> container( key, ctx );

    if( !container.isValid() )
    {
      MSG_FATAL("It's not possible to read the xAOD::SeedContainer from this Context using this key " << key );
    }

    for (const auto seed : **container.ptr() ){
      xAOD::Seed_t seed_t;
      xAOD::SeedConverter cnv;
      cnv.convert( seed, seed_t );
      container_t->push_back(seed_t);
    }
}




void RootStreamAODMaker::serializeCaloRings( EventContext &ctx , 
                                         std::string key, 
                                         std::vector<xAOD::CaloRings_t> *container_t ) const
{
    MSG_DEBUG("Serialize Rings...");
    SG::ReadHandle<xAOD::CaloRingsContainer> container( key, ctx );

    if( !container.isValid() )
    {
      MSG_FATAL("It's not possible to read the xAOD::CaloRingsContainer from this Context using this key " << key );

    }

    for (const auto rings : **container.ptr() ){
      xAOD::CaloRings_t rings_t;
      xAOD::CaloRingsConverter cnv;
      cnv.convert( rings , rings_t);
      container_t->push_back(rings_t);  
    }

}


void RootStreamAODMaker::serializeElectrons( EventContext &ctx , 
                                             std::string key, 
                                             std::vector<xAOD::Electron_t> *container_t ) const
{
    MSG_DEBUG("Serialize Electrons...");
    SG::ReadHandle<xAOD::ElectronContainer> container( key, ctx );
    if (!container.isValid() )
    {
      MSG_FATAL("It's not possible to read the xAOD::ElectronContainer using this key " << key);
      }

    for (const auto electron : **container.ptr() ){
      xAOD::Electron_t electron_t;
      xAOD::ElectronConverter cnv;
      cnv.convert(electron, electron_t);
      container_t->push_back(electron_t);
    }
  }


