#include "CaloHitPileupMerge.h"
#include "GaugiKernel/Timer.h"
#include "CaloHit/CaloHitConverter.h"
#include "EventInfo/EventInfoConverter.h"
#include "TTree.h"
#include "TChain.h"
#include <unordered_map>
#include <stdexcept> 

using namespace SG;
using namespace Gaugi;


/**
 * @class CaloHitPileupMerge
 * @brief Merges pileup events (minbias) into the signal event.
 * 
 * Simulates high-luminosity pileup by overlaying hits from pre-simulated
 * minimum-bias events onto the current hard-scatter signal event.
 * For each bunch crossing in [BunchIdStart, BunchIdEnd], Poisson(mu)
 * MinBias events are drawn from a single unified library and their
 * BC=0 energy deposits are added directly to the cell's edep dictionary
 * for that bunch crossing.
 */
CaloHitPileupMerge::CaloHitPileupMerge( std::string name ) : 
  IMsgService(name),
  Algorithm(),
  m_rng(128),
  m_startEntry(-1),
  m_currentEntry(-1)
{
  declareProperty( "InputHitsKey"        , m_inputHitsKey="Hits"                 );
  declareProperty( "OutputHitsKey"       , m_outputHitsKey="Hits_Merged"         );
  declareProperty( "InputEventKey"       , m_inputEventKey="Events"              );
  declareProperty( "OutputEventKey"      , m_outputEventKey="Events_Merged"      );
  declareProperty( "OutputLevel"         , m_outputLevel=1                       );
  declareProperty( "PileupAvg"           , m_pileupAvg=0.0f                      );
  declareProperty( "PileupSigma"         , m_pileupSigma=0.0f                    );
  declareProperty( "TruncMu"             , m_trunc_mu=1000.0f                    );
  declareProperty( "MergeMaxRetry"       , m_maxRetry=10                         );
  declareProperty( "Seed"                , m_seed=0.0f                           );
  declareProperty( "BunchIdStart"        , m_bcid_start=-21                      );
  declareProperty( "BunchIdEnd"          , m_bcid_end=4                          );
  declareProperty( "NtupleName"          , m_ntupleName="CollectionTree"         );
  declareProperty( "PileupFiles"         , m_pileupFiles={}                      );
  declareProperty( "StartEntry"          , m_startEntry=-1                       );
}

//!=====================================================================

CaloHitPileupMerge::~CaloHitPileupMerge()
{}

//!=====================================================================

StatusCode CaloHitPileupMerge::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);
  m_rng.SetSeed((unsigned int)m_seed);
  m_currentEntry = (m_startEntry >= 0) ? (long long)m_startEntry : -1;
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitPileupMerge::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitPileupMerge::bookHistograms( EventContext &ctx ) const
{
  MSG_INFO( "Loading MinBias pileup files..." );
  Read(ctx, m_pileupFiles, "minbias_chain");

  auto store = ctx.getStoreGateSvc();
  auto chain = (TChain*)store->decorator("minbias_chain");
  if (!chain || chain->GetListOfFiles()->GetEntries() == 0) {
    MSG_WARNING("No MinBias pileup files loaded into chain!");
  } else {
    MSG_INFO("MinBias chain initialized with " << chain->GetListOfFiles()->GetEntries() << " file(s).");
    chain->SetCacheSize(30 * 1024 * 1024); // 30 MB prefetch buffer for fast sequential streaming
  }

  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitPileupMerge::pre_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitPileupMerge::execute( EventContext &/*ctx*/, const G4Step * /*step*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitPileupMerge::execute( EventContext &ctx, int /*evt*/ ) const
{
  return post_execute(ctx);
}

//!=====================================================================

StatusCode CaloHitPileupMerge::post_execute( EventContext &ctx ) const
{
  Timer timer;
  timer.start();

  SG::ReadHandle<xAOD::CaloHitContainer> container(m_inputHitsKey, ctx);
  if (!container.isValid()) {
    MSG_FATAL("It's not possible to read xAOD::CaloHitContainer with key " << m_inputHitsKey);
    return StatusCode::FAILURE;
  }

  std::vector<xAOD::CaloHit*> vec_hits;
  unsigned retry = 0;
  float nPileupMean = 0.0f;

  while (retry < (unsigned)m_maxRetry) {
    try {
      MSG_INFO("Processing pileup merge (attempt " << retry + 1 << ")...");
      allocate(container, vec_hits);
      nPileupMean = merge(ctx, vec_hits);
      MSG_INFO("Pileup merge completed. Effective <mu>: " << nPileupMean);
      break;
    } catch (const std::runtime_error& e) {
      MSG_WARNING("Caught runtime exception during merge: " << e.what() << ". Retrying...");
      retry++;
      deallocate(vec_hits);
    }
  }

  if (retry >= (unsigned)m_maxRetry) {
    MSG_ERROR("Failed to merge pileup after " << m_maxRetry << " attempts!");
    return StatusCode::FAILURE;
  }

  // Record merged hits container
  {
    MSG_INFO("Writing merged hits container: " << m_outputHitsKey);
    SG::WriteHandle<xAOD::CaloHitContainer> hits(m_outputHitsKey, ctx);
    hits.record(std::make_unique<xAOD::CaloHitContainer>());
    for (auto* hit : vec_hits) {
      hits->push_back(hit);
    }
  }

  // Record merged EventInfo container
  {
    MSG_INFO("Writing merged event info: " << m_outputEventKey << " with avgmu=" << nPileupMean);
    SG::ReadHandle<xAOD::EventInfoContainer> event(m_inputEventKey, ctx);
    if (!event.isValid()) {
      std::string fallbackKey = (m_inputEventKey == "Events") ? "EventInfo" : "Events";
      SG::ReadHandle<xAOD::EventInfoContainer> fallbackEvent(fallbackKey, ctx);
      if (fallbackEvent.isValid()) {
        event = fallbackEvent;
      } else {
        MSG_FATAL("It's not possible to read xAOD::EventInfoContainer with key " << m_inputEventKey);
        return StatusCode::FAILURE;
      }
    }

    auto const_evt = (**event.ptr()).front();
    SG::WriteHandle<xAOD::EventInfoContainer> output_events(m_outputEventKey, ctx);
    output_events.record(std::make_unique<xAOD::EventInfoContainer>());
    auto evt = new xAOD::EventInfo();
    evt->setRunNumber(const_evt->runNumber());
    evt->setEventNumber(const_evt->eventNumber());
    evt->setTotalEnergy(const_evt->totalEnergy());
    evt->setAvgmu(nPileupMean);
    evt->setTotmu(nPileupMean * (m_bcid_end - m_bcid_start + 1));
    output_events->push_back(evt);
  }

  timer.stop();
  MSG_INFO("Event merged in " << timer.resume() << " seconds.");  
  return StatusCode::SUCCESS;
}

//!=====================================================================

float CaloHitPileupMerge::merge( EventContext &ctx, std::vector<xAOD::CaloHit*> &vec_hits ) const
{
  auto store = ctx.getStoreGateSvc();
  auto chain = (TChain*)store->decorator("minbias_chain");

  if (!chain || chain->GetEntries() == 0) {
    MSG_FATAL("MinBias TChain is empty or not loaded!");
    return 0.0f;
  }

  // 1. Activate only the branches needed for CaloHitContainer
  chain->SetBranchStatus("*", 0);
  std::string branch_name = "CaloHitContainer_" + m_inputHitsKey;
  chain->SetBranchStatus(branch_name.c_str(), 1);
  chain->SetBranchStatus((branch_name + ".*").c_str(), 1);

  std::vector<xAOD::CaloHit_t> *collection_hits = nullptr;
  InitBranch(chain, branch_name, &collection_hits);

  // 2. Hash map for O(1) cell lookup
  std::unordered_map<unsigned long int, xAOD::CaloHit*> hit_map;
  hit_map.reserve(vec_hits.size() * 2);
  for (auto* hit : vec_hits) {
    hit_map[hit->hash()] = hit;
  }

  // 3. Sample mu for this event
  float mu_event = (m_pileupSigma > 0.0f) ? (float)m_rng.Gaus(m_pileupAvg, m_pileupSigma) : m_pileupAvg;
  if (mu_event < 0.0f) mu_event = 0.0f;

  long long total_entries = chain->GetEntries();
  long long total_interactions = 0;
  int num_bunch_crossings = (m_bcid_end - m_bcid_start + 1);

  xAOD::CaloHitConverter cnv;

  // 4. Loop across the bunch-crossing window
  for (int bc = m_bcid_start; bc <= m_bcid_end; ++bc) {
    int n_pileup = poisson(mu_event);
    total_interactions += n_pileup;

    for (int k = 0; k < n_pileup; ++k) {
      if (m_currentEntry < 0) {
        m_currentEntry = m_rng.Integer(total_entries);
      } else {
        m_currentEntry = (m_currentEntry + 1) % total_entries;
      }

      if (chain->GetEntry(m_currentEntry) <= 0) {
        throw std::runtime_error("I/O error reading MinBias entry " + std::to_string(m_currentEntry));
      }

      if (!collection_hits) continue;

      for (const auto &hit_t : *collection_hits) {
        // Fast filter: only overlay pileup onto cells present in the signal event / RoI
        auto it = hit_map.find(hit_t.hash);
        if (it == hit_map.end()) continue;

        xAOD::CaloHit *hit_mb = nullptr;
        cnv.convert(hit_t, hit_mb);
        if (!hit_mb) continue;

        // Directly query the dictionary: returns energy at BC=0 (default parameter)
        float e_mb = hit_mb->edep();
        if (e_mb > 0.0f) {
          it->second->edep(bc, e_mb);
        }

        delete hit_mb;
      }
    }
    MSG_DEBUG("Bunch crossing " << bc << ": merged " << n_pileup << " MinBias interaction(s).");
  }

  delete collection_hits;
  return static_cast<float>(total_interactions) / static_cast<float>(num_bunch_crossings);
}

//!=====================================================================

void CaloHitPileupMerge::allocate( SG::ReadHandle<xAOD::CaloHitContainer> &container,
                                   std::vector<xAOD::CaloHit*> &vec_hits ) const
{
  MSG_INFO( "Cloning signal hits with size " << container.ptr()->size() << "...");
  vec_hits.reserve(container.ptr()->size());

  for (const auto* const_hit : **container.ptr()) {
    auto hit = const_hit->copy();
    hit->set_bcid_start(m_bcid_start);
    hit->set_bcid_end(m_bcid_end);
    vec_hits.push_back(hit);
  }
}

//!=====================================================================

void CaloHitPileupMerge::deallocate( std::vector<xAOD::CaloHit*> &vec_hits ) const
{
  for (auto* hit : vec_hits) {
    delete hit;
  }
  vec_hits.clear();
}

//!=====================================================================

StatusCode CaloHitPileupMerge::fillHistograms( SG::EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

template <class T>
TBranch* CaloHitPileupMerge::InitBranch(TTree* fChain, std::string branch_name, T* param) const
{
  std::string bname = branch_name;
  if (fChain->GetAlias(bname.c_str()))
     bname = std::string(fChain->GetAlias(bname.c_str()));

  if (!fChain->FindBranch(bname.c_str()) ) {
    MSG_FATAL( "unknown branch " << bname );
  }
  fChain->SetBranchStatus(bname.c_str(), 1.);
  fChain->SetBranchAddress(bname.c_str(), param);

  return fChain->GetBranch(bname.c_str());  
}

//!=====================================================================

int CaloHitPileupMerge::poisson(double nAvg) const
{
  if (nAvg <= 0.0) return 0;

  // Inverted transform sampling using exp(-nAvg)
  double rPoisson = m_rng.Uniform(0.0, 1.0) * exp(nAvg);
  double rSum  = 0.0;
  double rTerm = 1.0;

  for (int i = 0; i < (int)m_trunc_mu; ++i) {
    rSum += rTerm;
    if (rSum > rPoisson) return i;
    rTerm *= nAvg / (i + 1);
  }

  return (int)m_trunc_mu;
}

//!=====================================================================

void CaloHitPileupMerge::Read( EventContext &ctx, const std::vector<std::string> &paths, std::string name ) const
{
  auto store = ctx.getStoreGateSvc();
  TChain *chain = new TChain(m_ntupleName.c_str());

  for (const auto &path : paths) {
    if (path.empty()) continue;
    chain->Add(path.c_str());
  }

  store->decorate( name , chain );
}
