/**
 * @class RootStreamNtupleMaker
 * @brief This class is responsible for creating an ntuple from ROOT files.
 *
 * The RootStreamNtupleMaker class reads data from ROOT files and creates an ntuple
 * with the specified branches. It initializes the necessary variables, books the histograms,
 * and fills the ntuple with the data from the ROOT file. It also provides functions for
 * initializing, finalizing, and executing the ntuple creation process.
 */
#include "CaloCell/CaloCellContainer.h"
#include "EventInfo/EventInfoContainer.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"
#include "Egamma/ElectronContainer.h"
#include "CaloCell/CaloCellConverter.h"
#include "CaloCell/CaloDetDescriptorConverter.h"
#include "EventInfo/EventInfoConverter.h"
#include "TruthParticle/TruthParticleConverter.h"
#include "CaloCluster/CaloClusterConverter.h"
#include "CaloRings/CaloRingsConverter.h"
#include "Egamma/ElectronConverter.h"
#include "RootStreamNtupleMaker.h"
#include "GaugiKernel/EDM.h"


using namespace SG;
using namespace Gaugi;



/**
 * @class RootStreamNtupleMaker
 * @brief Dumps flat Ntuples for analysis (ML training, performance studies).
 * 
 * Unlike the AOD/ESD makers which serialize EDM objects, this algorithm flatterns
 * the data into simple floating-point branches (e.g. `cl_et`, `cl_eta`, `cl_rings`, etc.).
 * This is the standard format used for training neural networks (e.g. Ringer) or
 * plotting variables in ROOT.
 * 
 * Properties:
 * - Input*Key: Keys to retrieve objects to dump.
 * - OutputNtupleName: Name of the output TTree.
 */
RootStreamNtupleMaker::RootStreamNtupleMaker( std::string name ) : 
  IMsgService(name),
  Algorithm()
{
  declareProperty( "InputEventKey"      , m_eventKey="EventInfo"          );
  declareProperty( "InputTruthKey"      , m_truthKey="Particles"          );
  declareProperty( "InputSeedsKey"      , m_seedsKey="Seeds"              );
  declareProperty( "InputClusterKey"    , m_clusterKey="Clusters"         );
  declareProperty( "InputRingerKey"     , m_ringerKey="Rings"             );
  declareProperty( "InputRingerL0Key"   , m_ringerL0Key="RingsL0"         );
  declareProperty( "InputTruthClusterKey", m_truthClusterKey="TruthClusters");
  declareProperty( "InputTruthRingerKey" , m_truthRingerKey="TruthRings"   );
  declareProperty( "InputTruthElectronKey", m_truthElectronKey="TruthElectrons");
  declareProperty( "InputElectronKey"   , m_electronKey="Electrons"       );
  declareProperty( "OutputLevel"        , m_outputLevel=0                 );
  declareProperty( "OutputNtupleName"   , m_outputNtupleName="events"     );
}

//!=====================================================================

RootStreamNtupleMaker::~RootStreamNtupleMaker()
{}

//!=====================================================================

StatusCode RootStreamNtupleMaker::initialize()
{
  CHECK_INIT();
  //setMsgLevel( (MSG::Level)m_outputLevel );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamNtupleMaker::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Books the analysis TTree.
 * 
 * Defines all branches: event info, cluster variables, shower shapes,
 * rings, electron MC truth, etc.
 */
StatusCode RootStreamNtupleMaker::bookHistograms( EventContext &ctx ) const
{
  MSG_INFO("Booking ttree...");
  auto store = ctx.getStoreGateSvc();
  store->cd();

  int eventNumber             = -1;
  int runNumber               = -1;
  float avgmu                 = -1;
  float cl_eta                = 0;
  float cl_phi                = 0;
  float cl_e                  = 0;
  float cl_et                 = 0;
  float cl_deta               = 0;
  float cl_dphi               = 0;
  float cl_e0                 = 0;
  float cl_e1                 = 0;
  float cl_e2                 = 0;
  float cl_e3                 = 0;
  float cl_ehad1              = 0;
  float cl_ehad2              = 0;
  float cl_ehad3              = 0;
  float cl_etot               = 0;
  float cl_e233               = 0;
  float cl_e237               = 0;
  float cl_e277               = 0;
  float cl_emaxs1             = 0;
  float cl_emaxs2             = 0;
  float cl_e2tsts1            = 0;
  float cl_reta               = 0;
  float cl_rphi               = 0;
  float cl_rhad               = 0;
  float cl_rhad1              = 0;
  float cl_eratio             = 0;
  float cl_f0                 = 0;
  float cl_f1                 = 0;
  float cl_f2                 = 0;
  float cl_f3                 = 0;
  float cl_weta2              = 0;
  float cl_secondR            = 0;
  float cl_lambdaCenter       = 0;
  float cl_secondLambda       = 0;
  float cl_fracMax            = 0;
  float cl_lateralMom         = 0;
  float cl_longitudinalMom    = 0;
  std::vector<float>*cl_rings   = nullptr;
  std::vector<float>*cl_ringsL0 = nullptr;
  float truth_cl_eta             = 0;
  float truth_cl_phi             = 0;
  float truth_cl_e               = 0;
  float truth_cl_et              = 0;
  float truth_cl_deta            = 0;
  float truth_cl_dphi            = 0;
  float truth_cl_e0              = 0;
  float truth_cl_e1              = 0;
  float truth_cl_e2              = 0;
  float truth_cl_e3              = 0;
  float truth_cl_ehad1           = 0;
  float truth_cl_ehad2           = 0;
  float truth_cl_ehad3           = 0;
  float truth_cl_etot            = 0;
  float truth_cl_e233            = 0;
  float truth_cl_e237            = 0;
  float truth_cl_e277            = 0;
  float truth_cl_emaxs1          = 0;
  float truth_cl_emaxs2          = 0;
  float truth_cl_e2tsts1         = 0;
  float truth_cl_reta            = 0;
  float truth_cl_rphi            = 0;
  float truth_cl_rhad            = 0;
  float truth_cl_rhad1           = 0;
  float truth_cl_eratio          = 0;
  float truth_cl_f0              = 0;
  float truth_cl_f1              = 0;
  float truth_cl_f2              = 0;
  float truth_cl_f3              = 0;
  float truth_cl_weta2           = 0;
  float truth_cl_secondR         = 0;
  float truth_cl_lambdaCenter    = 0;
  float truth_cl_secondLambda    = 0;
  float truth_cl_fracMax         = 0;
  float truth_cl_lateralMom      = 0;
  float truth_cl_longitudinalMom = 0;
  std::vector<float>*truth_cl_rings = nullptr;
  float truth_el_eta                = -1;
  float truth_el_et                 = -1;
  float truth_el_phi                = -1;
  bool truth_el_tight               = false;
  bool truth_el_medium              = false;
  bool truth_el_loose               = false;
  bool truth_el_vloose              = false;
  float el_eta                = -1;
  float el_et                 = -1;
  float el_phi                = -1;
  bool el_tight               = false;
  bool el_medium              = false;
  bool el_loose               = false;
  bool el_vloose              = false;
  float seed_eta              = 0;
  float seed_phi              = 0;
  std::vector<float> *mc_pdgid= nullptr;
  std::vector<float> *mc_eta= nullptr;
  std::vector<float> *mc_phi= nullptr;  
  std::vector<float> *mc_e= nullptr;  
  std::vector<float> *mc_et= nullptr; 



  TTree *tree = new TTree(m_outputNtupleName.c_str(), "");

  tree->Branch("EventNumber"            , &eventNumber);
  tree->Branch("RunNumber"              , &runNumber);  
  tree->Branch("avgmu"                  , &avgmu);  
  tree->Branch("cl_eta"                 , &cl_eta);
  tree->Branch("cl_phi"                 , &cl_phi);
  tree->Branch("cl_e"                   , &cl_e);
  tree->Branch("cl_et"                  , &cl_et);
  tree->Branch("cl_deta"                , &cl_deta);
  tree->Branch("cl_dphi"                , &cl_dphi);
  tree->Branch("cl_e0"                  , &cl_e0);
  tree->Branch("cl_e1"                  , &cl_e1);
  tree->Branch("cl_e2"                  , &cl_e2);
  tree->Branch("cl_e3"                  , &cl_e3);
  tree->Branch("cl_ehad1"               , &cl_ehad1);
  tree->Branch("cl_ehad2"               , &cl_ehad2);
  tree->Branch("cl_ehad3"               , &cl_ehad3);
  tree->Branch("cl_etot"                , &cl_etot);
  tree->Branch("cl_e233"                , &cl_e233);
  tree->Branch("cl_e237"                , &cl_e237);
  tree->Branch("cl_e277"                , &cl_e277);
  tree->Branch("cl_emaxs1"              , &cl_emaxs1);
  tree->Branch("cl_emaxs2"              , &cl_emaxs2);
  tree->Branch("cl_e2tsts1"             , &cl_e2tsts1);
  tree->Branch("cl_reta"                , &cl_reta);
  tree->Branch("cl_rphi"                , &cl_rphi);
  tree->Branch("cl_rhad"                , &cl_rhad);
  tree->Branch("cl_rhad1"               , &cl_rhad1);
  tree->Branch("cl_eratio"              , &cl_eratio);
  tree->Branch("cl_f0"                  , &cl_f0);
  tree->Branch("cl_f1"                  , &cl_f1);
  tree->Branch("cl_f2"                  , &cl_f2);
  tree->Branch("cl_f3"                  , &cl_f3);
  tree->Branch("cl_weta2"               , &cl_weta2);
  tree->Branch("cl_rings"               , &cl_rings);
  tree->Branch("cl_ringsL0"             , &cl_ringsL0);
  tree->Branch("cl_secondR"             , &cl_secondR);
  tree->Branch("cl_lambdaCenter"        , &cl_lambdaCenter);
  tree->Branch("cl_secondLambda"        , &cl_secondLambda);
  tree->Branch("cl_fracMax"             , &cl_fracMax);
  tree->Branch("cl_lateralMom"          , &cl_lateralMom);
  tree->Branch("cl_longitudinalMom"     , &cl_longitudinalMom);
  tree->Branch("el_eta"                 , &el_eta);
  tree->Branch("el_et"                  , &el_et);
  tree->Branch("el_phi"                 , &el_phi);
  tree->Branch("el_tight"               , &el_tight);
  tree->Branch("el_medium"              , &el_medium);
  tree->Branch("el_loose"               , &el_loose);
  tree->Branch("el_vloose"              , &el_vloose);

  tree->Branch("truth_cl_eta"              , &truth_cl_eta);
  tree->Branch("truth_cl_phi"              , &truth_cl_phi);
  tree->Branch("truth_cl_e"                , &truth_cl_e);
  tree->Branch("truth_cl_et"               , &truth_cl_et);
  tree->Branch("truth_cl_deta"             , &truth_cl_deta);
  tree->Branch("truth_cl_dphi"             , &truth_cl_dphi);
  tree->Branch("truth_cl_e0"               , &truth_cl_e0);
  tree->Branch("truth_cl_e1"               , &truth_cl_e1);
  tree->Branch("truth_cl_e2"               , &truth_cl_e2);
  tree->Branch("truth_cl_e3"               , &truth_cl_e3);
  tree->Branch("truth_cl_ehad1"            , &truth_cl_ehad1);
  tree->Branch("truth_cl_ehad2"            , &truth_cl_ehad2);
  tree->Branch("truth_cl_ehad3"            , &truth_cl_ehad3);
  tree->Branch("truth_cl_etot"             , &truth_cl_etot);
  tree->Branch("truth_cl_e233"             , &truth_cl_e233);
  tree->Branch("truth_cl_e237"             , &truth_cl_e237);
  tree->Branch("truth_cl_e277"             , &truth_cl_e277);
  tree->Branch("truth_cl_emaxs1"           , &truth_cl_emaxs1);
  tree->Branch("truth_cl_emaxs2"           , &truth_cl_emaxs2);
  tree->Branch("truth_cl_e2tsts1"          , &truth_cl_e2tsts1);
  tree->Branch("truth_cl_reta"             , &truth_cl_reta);
  tree->Branch("truth_cl_rphi"             , &truth_cl_rphi);
  tree->Branch("truth_cl_rhad"             , &truth_cl_rhad);
  tree->Branch("truth_cl_rhad1"            , &truth_cl_rhad1);
  tree->Branch("truth_cl_eratio"           , &truth_cl_eratio);
  tree->Branch("truth_cl_f0"               , &truth_cl_f0);
  tree->Branch("truth_cl_f1"               , &truth_cl_f1);
  tree->Branch("truth_cl_f2"               , &truth_cl_f2);
  tree->Branch("truth_cl_f3"               , &truth_cl_f3);
  tree->Branch("truth_cl_weta2"            , &truth_cl_weta2);
  tree->Branch("truth_cl_rings"            , &truth_cl_rings);
  tree->Branch("truth_cl_secondR"          , &truth_cl_secondR);
  tree->Branch("truth_cl_lambdaCenter"     , &truth_cl_lambdaCenter);
  tree->Branch("truth_cl_secondLambda"     , &truth_cl_secondLambda);
  tree->Branch("truth_cl_fracMax"          , &truth_cl_fracMax);
  tree->Branch("truth_cl_lateralMom"       , &truth_cl_lateralMom);
  tree->Branch("truth_cl_longitudinalMom"  , &truth_cl_longitudinalMom);
  tree->Branch("truth_el_eta"              , &truth_el_eta);
  tree->Branch("truth_el_et"               , &truth_el_et);
  tree->Branch("truth_el_phi"              , &truth_el_phi);
  tree->Branch("truth_el_tight"            , &truth_el_tight);
  tree->Branch("truth_el_medium"           , &truth_el_medium);
  tree->Branch("truth_el_loose"            , &truth_el_loose);
  tree->Branch("truth_el_vloose"           , &truth_el_vloose);
  tree->Branch("seed_eta"               , &seed_eta);
  tree->Branch("seed_phi"               , &seed_phi);
  tree->Branch("mc_pdgid"               , &mc_pdgid);
  tree->Branch("mc_eta"                 , &mc_eta);
  tree->Branch("mc_phi"                 , &mc_phi);
  tree->Branch("mc_e"                   , &mc_e);
  tree->Branch("mc_et"                  , &mc_et);
  

  store->add(tree);
  return StatusCode::SUCCESS; 
}

//!=====================================================================

StatusCode RootStreamNtupleMaker::pre_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamNtupleMaker::execute( EventContext &/*ctx*/, const G4Step * /*step*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode RootStreamNtupleMaker::execute( EventContext &ctx, int evt ) const
{
  return StatusCode::SUCCESS;
}

//!===================================    ==================================

StatusCode RootStreamNtupleMaker::post_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Fills the TTree.
 * 
 * For each electron in the container, it retrieves the associated cluster, rings, and truth particle.
 * It flattens their properties into the linked variables and calls `tree->Fill()`.
 * Thus, one entry in the tree corresponds to one Electron candidate.
 */
StatusCode RootStreamNtupleMaker::fillHistograms( EventContext &ctx ) const
{
  MSG_INFO("fill ttree...");

  SG::ReadHandle<xAOD::EventInfoContainer> event_container( m_eventKey, ctx );
  if( !event_container.isValid() )
  {
    MSG_FATAL("It's not possible to read the xAOD::EventInfoContainer from this Context using this key " << m_eventKey );
  }

  SG::ReadHandle<xAOD::CaloRingsContainer> ringer_container( m_ringerKey, ctx );
  if( !ringer_container.isValid() )
  {
    MSG_FATAL("It's not possible to read the xAOD::CaloRingsContainer from this Context using this key " << m_ringerKey );
  }

  SG::ReadHandle<xAOD::ElectronContainer> electron_container( m_electronKey, ctx );
  if( !electron_container.isValid() )
  {
    MSG_FATAL("It's not possible to read the xAOD::ElectronContainer from this Context using this key " << m_electronKey );
  }

  SG::ReadHandle<xAOD::SeedContainer> seed_container( m_seedsKey, ctx );
  if( !seed_container.isValid() )
  {
    MSG_FATAL("It's not possible to read the xAOD::SeedContainer from this Context using this key " << m_seedsKey );
  }

  SG::ReadHandle<xAOD::TruthParticleContainer> truth_container( m_truthKey, ctx );
  if( !truth_container.isValid() )
  {
    MSG_FATAL("It's not possible to read the xAOD::TruthParticleContainer from this Context using this key " << m_truthKey );
  }

  SG::ReadHandle<xAOD::CaloRingsContainer> ringerL0_container( m_ringerL0Key, ctx );
  SG::ReadHandle<xAOD::CaloClusterContainer> truth_cluster_container( m_truthClusterKey, ctx );
  SG::ReadHandle<xAOD::CaloRingsContainer> truth_ringer_container( m_truthRingerKey, ctx );
  SG::ReadHandle<xAOD::ElectronContainer> truth_electron_container( m_truthElectronKey, ctx );

  auto store = ctx.getStoreGateSvc();
  store->cd();  
  TTree *tree = store->tree(m_outputNtupleName.c_str());

  MSG_INFO( "Link all branches..." << tree );

  int   runNumber          = 0;
  int   eventNumber        = 0;
  float avgmu              = 0;  
  float cl_eta             = 0;
  float cl_phi             = 0;
  float cl_e               = 0;
  float cl_et              = 0;
  float cl_deta            = 0;
  float cl_dphi            = 0;
  float cl_e0              = 0;
  float cl_e1              = 0;
  float cl_e2              = 0;
  float cl_e3              = 0;
  float cl_ehad1           = 0;
  float cl_ehad2           = 0;
  float cl_ehad3           = 0;
  float cl_etot            = 0;
  float cl_e233            = 0;
  float cl_e237            = 0;
  float cl_e277            = 0;
  float cl_emaxs1          = 0;
  float cl_emaxs2          = 0;
  float cl_e2tsts1         = 0;
  float cl_reta            = 0;
  float cl_rphi            = 0;
  float cl_rhad            = 0;
  float cl_rhad1           = 0;
  float cl_eratio          = 0;
  float cl_f0              = 0;
  float cl_f1              = 0;
  float cl_f2              = 0;
  float cl_f3              = 0;
  float cl_weta2           = 0;
  float cl_secondR         = 0;
  float cl_lambdaCenter    = 0;
  float cl_secondLambda    = 0;
  float cl_fracMax         = 0;
  float cl_lateralMom      = 0;
  float cl_longitudinalMom = 0;
  float el_eta             = -1;
  float el_et              = -1;
  float el_phi             = -1;
  bool el_tight            = false;
  bool el_medium           = false;
  bool el_loose            = false;
  bool el_vloose           = false;
  std::vector<float> *cl_rings = nullptr;
  float seed_eta           = 0;
  float seed_phi           = 0;
  std::vector<float> *mc_pdgid= nullptr;
  std::vector<float> *mc_eta= nullptr;
  std::vector<float> *mc_phi= nullptr;
  std::vector<float> *mc_e= nullptr;
  std::vector<float> *mc_et= nullptr;

  std::vector<float> *cl_ringsL0 = nullptr;
  float truth_cl_eta             = 0;
  float truth_cl_phi             = 0;
  float truth_cl_e               = 0;
  float truth_cl_et              = 0;
  float truth_cl_deta            = 0;
  float truth_cl_dphi            = 0;
  float truth_cl_e0              = 0;
  float truth_cl_e1              = 0;
  float truth_cl_e2              = 0;
  float truth_cl_e3              = 0;
  float truth_cl_ehad1           = 0;
  float truth_cl_ehad2           = 0;
  float truth_cl_ehad3           = 0;
  float truth_cl_etot            = 0;
  float truth_cl_e233            = 0;
  float truth_cl_e237            = 0;
  float truth_cl_e277            = 0;
  float truth_cl_emaxs1          = 0;
  float truth_cl_emaxs2          = 0;
  float truth_cl_e2tsts1         = 0;
  float truth_cl_reta            = 0;
  float truth_cl_rphi            = 0;
  float truth_cl_rhad            = 0;
  float truth_cl_rhad1           = 0;
  float truth_cl_eratio          = 0;
  float truth_cl_f0              = 0;
  float truth_cl_f1              = 0;
  float truth_cl_f2              = 0;
  float truth_cl_f3              = 0;
  float truth_cl_weta2           = 0;
  float truth_cl_secondR         = 0;
  float truth_cl_lambdaCenter    = 0;
  float truth_cl_secondLambda    = 0;
  float truth_cl_fracMax         = 0;
  float truth_cl_lateralMom      = 0;
  float truth_cl_longitudinalMom = 0;
  std::vector<float> *truth_cl_rings = nullptr;
  float truth_el_eta             = -1;
  float truth_el_et              = -1;
  float truth_el_phi             = -1;
  bool truth_el_tight            = false;
  bool truth_el_medium           = false;
  bool truth_el_loose            = false;
  bool truth_el_vloose           = false;

  
  InitBranch( tree, "avgmu"                   , &avgmu             );
  InitBranch( tree, "EventNumber"             , &eventNumber       );
  InitBranch( tree, "RunNumber"               , &runNumber         );
  InitBranch( tree, "cl_eta"                  , &cl_eta            );
  InitBranch( tree, "cl_phi"                  , &cl_phi            );
  InitBranch( tree, "cl_e"                    , &cl_e              );
  InitBranch( tree, "cl_et"                   , &cl_et             );
  InitBranch( tree, "cl_deta"                 , &cl_deta           );
  InitBranch( tree, "cl_dphi"                 , &cl_dphi           );
  InitBranch( tree, "cl_e0"                   , &cl_e0             );
  InitBranch( tree, "cl_e1"                   , &cl_e1             );
  InitBranch( tree, "cl_e2"                   , &cl_e2             );
  InitBranch( tree, "cl_e3"                   , &cl_e3             );
  InitBranch( tree, "cl_ehad1"                , &cl_ehad1          );
  InitBranch( tree, "cl_ehad2"                , &cl_ehad2          );
  InitBranch( tree, "cl_ehad3"                , &cl_ehad3          );
  InitBranch( tree, "cl_etot"                 , &cl_etot           );
  InitBranch( tree, "cl_e233"                 , &cl_e233           );
  InitBranch( tree, "cl_e237"                 , &cl_e237           );
  InitBranch( tree, "cl_e277"                 , &cl_e277           );
  InitBranch( tree, "cl_emaxs1"               , &cl_emaxs1         );
  InitBranch( tree, "cl_emaxs2"               , &cl_emaxs2         );
  InitBranch( tree, "cl_e2tsts1"              , &cl_e2tsts1        );
  InitBranch( tree, "cl_reta"                 , &cl_reta           );
  InitBranch( tree, "cl_rphi"                 , &cl_rphi           );
  InitBranch( tree, "cl_rhad"                 , &cl_rhad           );
  InitBranch( tree, "cl_rhad1"                , &cl_rhad1          );
  InitBranch( tree, "cl_eratio"               , &cl_eratio         );
  InitBranch( tree, "cl_f0"                   , &cl_f0             );
  InitBranch( tree, "cl_f1"                   , &cl_f1             );
  InitBranch( tree, "cl_f2"                   , &cl_f2             );
  InitBranch( tree, "cl_f3"                   , &cl_f3             );
  InitBranch( tree, "cl_weta2"                , &cl_weta2          );
  InitBranch( tree, "cl_secondR"              , &cl_secondR        );
  InitBranch( tree, "cl_lambdaCenter"         , &cl_lambdaCenter   );
  InitBranch( tree, "cl_secondLambda"         , &cl_secondLambda   );
  InitBranch( tree, "cl_fracMax"              , &cl_fracMax        );
  InitBranch( tree, "cl_lateralMom"           , &cl_lateralMom     );
  InitBranch( tree, "cl_longitudinalMom"      , &cl_longitudinalMom);
  InitBranch( tree, "cl_rings"                , &cl_rings          );
  InitBranch( tree, "el_eta"                  , &el_eta            );
  InitBranch( tree, "el_et"                   , &el_et             );
  InitBranch( tree, "el_phi"                  , &el_phi            );
  InitBranch( tree, "el_tight"                , &el_tight          );
  InitBranch( tree, "el_medium"               , &el_medium         );
  InitBranch( tree, "el_loose"                , &el_loose          );
  InitBranch( tree, "el_vloose"               , &el_vloose         );    
  InitBranch( tree, "seed_eta"                , &seed_eta          );
  InitBranch( tree, "seed_phi"                , &seed_phi          );
  InitBranch( tree, "mc_pdgid"                , &mc_pdgid          );
  InitBranch( tree, "mc_eta"                  , &mc_eta            );
  InitBranch( tree, "mc_phi"                  , &mc_phi            );
  InitBranch( tree, "mc_e"                    , &mc_e              );
  InitBranch( tree, "mc_et"                   , &mc_et             );
  
  InitBranch( tree, "cl_ringsL0"              , &cl_ringsL0        );
  InitBranch( tree, "truth_cl_eta"               , &truth_cl_eta         );
  InitBranch( tree, "truth_cl_phi"               , &truth_cl_phi         );
  InitBranch( tree, "truth_cl_e"                 , &truth_cl_e           );
  InitBranch( tree, "truth_cl_et"                , &truth_cl_et          );
  InitBranch( tree, "truth_cl_deta"             , &truth_cl_deta        );
  InitBranch( tree, "truth_cl_dphi"             , &truth_cl_dphi        );
  InitBranch( tree, "truth_cl_e0"               , &truth_cl_e0          );
  InitBranch( tree, "truth_cl_e1"               , &truth_cl_e1          );
  InitBranch( tree, "truth_cl_e2"               , &truth_cl_e2          );
  InitBranch( tree, "truth_cl_e3"               , &truth_cl_e3          );
  InitBranch( tree, "truth_cl_ehad1"            , &truth_cl_ehad1       );
  InitBranch( tree, "truth_cl_ehad2"            , &truth_cl_ehad2       );
  InitBranch( tree, "truth_cl_ehad3"            , &truth_cl_ehad3       );
  InitBranch( tree, "truth_cl_etot"             , &truth_cl_etot        );
  InitBranch( tree, "truth_cl_e233"             , &truth_cl_e233        );
  InitBranch( tree, "truth_cl_e237"             , &truth_cl_e237        );
  InitBranch( tree, "truth_cl_e277"             , &truth_cl_e277        );
  InitBranch( tree, "truth_cl_emaxs1"           , &truth_cl_emaxs1      );
  InitBranch( tree, "truth_cl_emaxs2"           , &truth_cl_emaxs2      );
  InitBranch( tree, "truth_cl_e2tsts1"          , &truth_cl_e2tsts1     );
  InitBranch( tree, "truth_cl_reta"             , &truth_cl_reta        );
  InitBranch( tree, "truth_cl_rphi"             , &truth_cl_rphi        );
  InitBranch( tree, "truth_cl_rhad"             , &truth_cl_rhad        );
  InitBranch( tree, "truth_cl_rhad1"            , &truth_cl_rhad1       );
  InitBranch( tree, "truth_cl_eratio"           , &truth_cl_eratio      );
  InitBranch( tree, "truth_cl_f0"               , &truth_cl_f0          );
  InitBranch( tree, "truth_cl_f1"               , &truth_cl_f1          );
  InitBranch( tree, "truth_cl_f2"               , &truth_cl_f2          );
  InitBranch( tree, "truth_cl_f3"               , &truth_cl_f3          );
  InitBranch( tree, "truth_cl_weta2"            , &truth_cl_weta2       );
  InitBranch( tree, "truth_cl_rings"             , &truth_cl_rings       );
  InitBranch( tree, "truth_cl_secondR"          , &truth_cl_secondR     );
  InitBranch( tree, "truth_cl_lambdaCenter"     , &truth_cl_lambdaCenter);
  InitBranch( tree, "truth_cl_secondLambda"     , &truth_cl_secondLambda);
  InitBranch( tree, "truth_cl_fracMax"          , &truth_cl_fracMax     );
  InitBranch( tree, "truth_cl_lateralMom"       , &truth_cl_lateralMom  );
  InitBranch( tree, "truth_cl_longitudinalMom"  , &truth_cl_longitudinalMom);
  InitBranch( tree, "truth_el_eta"               , &truth_el_eta         );
  InitBranch( tree, "truth_el_et"                , &truth_el_et          );
  InitBranch( tree, "truth_el_phi"               , &truth_el_phi         );
  InitBranch( tree, "truth_el_tight"            , &truth_el_tight       );
  InitBranch( tree, "truth_el_medium"           , &truth_el_medium      );
  InitBranch( tree, "truth_el_loose"            , &truth_el_loose       );
  InitBranch( tree, "truth_el_vloose"           , &truth_el_vloose      );


  auto evt = (**event_container.ptr()).front();


  for (auto el : **electron_container.ptr() )
  
  {
    cl_rings->clear();
    mc_pdgid->clear();
    mc_eta->clear();
    mc_phi->clear();
    mc_e->clear();
    mc_et->clear();

    cl_ringsL0->clear();
    truth_cl_rings->clear();
    truth_cl_eta = 0;
    truth_cl_phi = 0;
    truth_cl_e = 0;
    truth_cl_et = 0;
    truth_cl_deta = 0;
    truth_cl_dphi = 0;
    truth_cl_e0 = 0;
    truth_cl_e1 = 0;
    truth_cl_e2 = 0;
    truth_cl_e3 = 0;
    truth_cl_ehad1 = 0;
    truth_cl_ehad2 = 0;
    truth_cl_ehad3 = 0;
    truth_cl_etot = 0;
    truth_cl_e233 = 0;
    truth_cl_e237 = 0;
    truth_cl_e277 = 0;
    truth_cl_emaxs1 = 0;
    truth_cl_emaxs2 = 0;
    truth_cl_e2tsts1 = 0;
    truth_cl_reta = 0;
    truth_cl_rphi = 0;
    truth_cl_rhad = 0;
    truth_cl_rhad1 = 0;
    truth_cl_eratio = 0;
    truth_cl_f0 = 0;
    truth_cl_f1 = 0;
    truth_cl_f2 = 0;
    truth_cl_f3 = 0;
    truth_cl_weta2 = 0;
    truth_cl_secondR = 0;
    truth_cl_lambdaCenter = 0;
    truth_cl_secondLambda = 0;
    truth_cl_fracMax = 0;
    truth_cl_lateralMom = 0;
    truth_cl_longitudinalMom = 0;

    truth_el_eta = -1;
    truth_el_et = -1;
    truth_el_phi = -1;
    truth_el_tight = false;
    truth_el_medium = false;
    truth_el_loose = false;
    truth_el_vloose = false;

    auto clus = el->caloCluster();


    const xAOD::CaloRings* cl_ringer = nullptr;
    for (auto ring : **ringer_container.ptr() )
    {
      if (ring->caloCluster() == clus)
      {
        cl_ringer = ring;
        break;
      } 
    }

    if(!cl_ringer)
    {
      MSG_WARNING("No rings found for cluster");
      continue;
    }

    const xAOD::CaloRings* cl_ringerL0 = nullptr;
    if (ringerL0_container.isValid()){
      for (auto ring : **ringerL0_container.ptr() )
      {
        if (ring->caloCluster() == clus)
        {
          cl_ringerL0 = ring;
          break;
        } 
      }
    }

    const xAOD::CaloCluster* truth_clus = nullptr;
    if (truth_cluster_container.isValid()){
      for (auto tr_cl : **truth_cluster_container.ptr() )
      {
        if (tr_cl->seed() == clus->seed())
        {
          truth_clus = tr_cl;
          break;
        } 
      }
    }

    const xAOD::CaloRings* truth_ringer = nullptr;
    if (truth_clus && truth_ringer_container.isValid()){
      for (auto ring : **truth_ringer_container.ptr() )
      {
        if (ring->caloCluster() == truth_clus)
        {
          truth_ringer = ring;
          break;
        } 
      }
    }

    const xAOD::Electron* truth_el = nullptr;
    if (truth_electron_container.isValid()){
      for (auto tr_el : **truth_electron_container.ptr() )
      {
        if (tr_el->caloCluster() && tr_el->caloCluster()->seed() == clus->seed())
        {
          truth_el = tr_el;
          break;
        } 
      }
    }


    avgmu              = evt->averageInteractionsPerCrossing();
    runNumber          = evt->runNumber();
    eventNumber        = evt->eventNumber();
    cl_eta             = clus->eta();
    cl_phi             = clus->phi();
    cl_e               = clus->e();
    MSG_INFO("Cluster energy: " << cl_e);
    cl_et              = clus->et();
    cl_deta            = clus->deltaEta();
    cl_dphi            = clus->deltaPhi();
    cl_e0              = clus->e0();
    cl_e1              = clus->e1();
    cl_e2              = clus->e2();
    cl_e3              = clus->e3();
    cl_ehad1           = clus->ehad1();
    cl_ehad2           = clus->ehad2();
    cl_ehad3           = clus->ehad3();
    cl_etot            = clus->etot();
    cl_e233            = clus->e233();
    cl_e237            = clus->e237();
    cl_e277            = clus->e277();
    cl_emaxs1          = clus->emaxs1();
    cl_emaxs2          = clus->emaxs2();
    cl_e2tsts1         = clus->e2tsts1();
    cl_reta            = clus->reta();
    cl_rphi            = clus->rphi();
    cl_rhad            = clus->rhad();
    cl_rhad1           = clus->rhad1();
    cl_eratio          = clus->eratio();
    cl_f0              = clus->f0();
    cl_f1              = clus->f1();
    cl_f2              = clus->f2();
    cl_f3              = clus->f3();
    cl_weta2           = clus->weta2();
    cl_secondR         = clus->secondR();
    cl_lambdaCenter    = clus->lambdaCenter();
    cl_secondLambda    = clus->secondLambda();
    cl_fracMax         = clus->fracMax();
    cl_lateralMom      = clus->lateralMom();
    cl_longitudinalMom = clus->longitudinalMom();
    for (auto ring : cl_ringer->rings()) cl_rings->push_back(ring);
    
    if (cl_ringerL0) {
      for (auto ring : cl_ringerL0->rings()) cl_ringsL0->push_back(ring);
    }
    
    if (truth_clus) {
      truth_cl_eta = truth_clus->eta();
      truth_cl_phi = truth_clus->phi();
      truth_cl_e   = truth_clus->e();
      truth_cl_et  = truth_clus->et();
      truth_cl_deta            = truth_clus->deltaEta();
      truth_cl_dphi            = truth_clus->deltaPhi();
      truth_cl_e0              = truth_clus->e0();
      truth_cl_e1              = truth_clus->e1();
      truth_cl_e2              = truth_clus->e2();
      truth_cl_e3              = truth_clus->e3();
      truth_cl_ehad1           = truth_clus->ehad1();
      truth_cl_ehad2           = truth_clus->ehad2();
      truth_cl_ehad3           = truth_clus->ehad3();
      truth_cl_etot            = truth_clus->etot();
      truth_cl_e233            = truth_clus->e233();
      truth_cl_e237            = truth_clus->e237();
      truth_cl_e277            = truth_clus->e277();
      truth_cl_emaxs1          = truth_clus->emaxs1();
      truth_cl_emaxs2          = truth_clus->emaxs2();
      truth_cl_e2tsts1         = truth_clus->e2tsts1();
      truth_cl_reta            = truth_clus->reta();
      truth_cl_rphi            = truth_clus->rphi();
      truth_cl_rhad            = truth_clus->rhad();
      truth_cl_rhad1           = truth_clus->rhad1();
      truth_cl_eratio          = truth_clus->eratio();
      truth_cl_f0              = truth_clus->f0();
      truth_cl_f1              = truth_clus->f1();
      truth_cl_f2              = truth_clus->f2();
      truth_cl_f3              = truth_clus->f3();
      truth_cl_weta2           = truth_clus->weta2();
      truth_cl_secondR         = truth_clus->secondR();
      truth_cl_lambdaCenter    = truth_clus->lambdaCenter();
      truth_cl_secondLambda    = truth_clus->secondLambda();
      truth_cl_fracMax         = truth_clus->fracMax();
      truth_cl_lateralMom      = truth_clus->lateralMom();
      truth_cl_longitudinalMom = truth_clus->longitudinalMom();
    }
    
    if (truth_ringer) {
      for (auto ring : truth_ringer->rings()) truth_cl_rings->push_back(ring);
    }
    
    if (truth_el) {
      truth_el_eta = truth_el->eta();
      truth_el_et  = truth_el->et();
      truth_el_phi = truth_el->phi();
      truth_el_tight  = truth_el->isTight();
      truth_el_medium = truth_el->isMedium();
      truth_el_loose  = truth_el->isLoose();
      truth_el_vloose = truth_el->isVeryLoose();
    }
    el_tight           = el->isTight();
    el_medium          = el->isMedium();
    el_loose           = el->isLoose();
    el_vloose          = el->isVeryLoose(); 
    el_et              = el->et();
    el_eta             = el->eta();
    el_phi             = el->phi();


    auto seed = clus->seed();

    seed_eta = seed->eta();
    seed_phi = seed->phi();
    for (auto mc : **truth_container.ptr() )
    {
      if (mc->seedid() == seed->id())
      {
        MSG_INFO("Found mc particle with PDGID: " << mc->pdgid());
        mc_pdgid->push_back(mc->pdgid());
        mc_eta->push_back(mc->eta());
        mc_phi->push_back(mc->phi());
        mc_e->push_back(mc->e());
        mc_et->push_back(mc->et());
      }
    }




    tree->Fill();
         
  } //each cluster should be 1 entry on ntuple file
   
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

template <class T>
void RootStreamNtupleMaker::InitBranch(TTree* fChain, std::string branch_name, T* param) const
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


