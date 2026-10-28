/**
 * @class RootStreamNtupleMaker
 * @brief This class is responsible for creating an ntuple from ROOT files.
 *
 * Reads reconstructed objects (Electrons, Clusters, Rings) and truth info
 * and writes them into a flat TTree structure using EDM converters.
 */
#include "CaloCell/CaloCellContainer.h"
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/SeedContainer.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"
#include "Egamma/ElectronContainer.h"
#include "EventInfo/EventInfoConverter.h"
#include "EventInfo/SeedConverter.h"
#include "TruthParticle/TruthParticleConverter.h"
#include "CaloCluster/CaloClusterConverter.h"
#include "CaloRings/CaloRingsConverter.h"
#include "Egamma/ElectronConverter.h"
#include "RootStreamNtupleMaker.h"
#include "GaugiKernel/EDM.h"
#include "GaugiKernel/BranchSpec.h"

using namespace SG;
using namespace Gaugi;

static inline std::vector<Gaugi::BranchSpec> getSpecsFor(
    const std::map<std::pair<std::string, std::string>, std::vector<Gaugi::BranchSpec>> &groups,
    const std::string &edm,
    const std::string &key)
{
  auto it = groups.find({edm, key});
  if (it != groups.end()) return it->second;

  for (const auto &[pair, specs] : groups) {
    if (pair.first == edm) {
      if (pair.second == key || 
          pair.second == "*" ||
          pair.second + "s" == key || 
          key + "s" == pair.second ||
          (pair.second == "Clusters" && key == "CaloClusters") ||
          (pair.second == "CaloClusters" && key == "Clusters") ||
          (pair.second == "Events" && key == "EventInfo") ||
          (pair.second == "EventInfo" && key == "Events")) {
        return specs;
      }
    }
  }
  return {};
}

RootStreamNtupleMaker::RootStreamNtupleMaker(std::string name) : IMsgService(name),
                                                                 Algorithm()
{
  declareProperty("InputEventKey", m_eventKey = "EventInfo");
  declareProperty("InputTruthKey", m_truthKey = "Particles");
  declareProperty("InputSeedsKey", m_seedsKey = "Seeds");
  declareProperty("InputClusterKey", m_clusterKey = "Clusters");
  declareProperty("InputRingerKeys", m_ringerKeys = {"Rings"});
  declareProperty("InputRingerL0Key", m_ringerL0Key = "RingsL0");
  declareProperty("InputTruthClusterKey", m_truthClusterKey = "TruthClusters");
  declareProperty("InputTruthRingerKeys", m_truthRingerKeys = {"TruthRings"});
  declareProperty("InputTruthElectronKey", m_truthElectronKey = "TruthElectrons");
  declareProperty("InputElectronKey", m_electronKey = "Electrons");
  declareProperty("OutputLevel", m_outputLevel = 0);
  declareProperty("OutputNtupleName", m_outputNtupleName = "events");
  declareProperty("Schema", m_schema = {});
}

RootStreamNtupleMaker::~RootStreamNtupleMaker()
{
}

StatusCode RootStreamNtupleMaker::initialize()
{
  CHECK_INIT();
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::finalize()
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::bookHistograms(EventContext &ctx) const
{
  MSG_INFO("Booking ttree...");
  auto store = ctx.getStoreGateSvc();
  store->cd();

  TTree *tree = new TTree(m_outputNtupleName.c_str(), "");

  xAOD::EventInfoConverter eventCnv;
  xAOD::CaloClusterConverter clusterCnv;
  xAOD::CaloRingsConverter ringsCnv;
  xAOD::ElectronConverter electronCnv;
  xAOD::SeedConverter seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  xAOD::EventInfo_t event_buf;
  xAOD::CaloCluster_t clus_buf;
  xAOD::CaloCluster_t truth_clus_buf;
  xAOD::CaloRings_t ringsL0_buf;
  std::vector<float> *ringsL0_ptr = nullptr;
  std::map<std::string, float> scalarRingsL0;
  std::vector<xAOD::CaloRings_t> rings_bufs(m_ringerKeys.size());
  std::vector<std::vector<float> *> rings_ptrs(m_ringerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarRings(m_ringerKeys.size());
  std::vector<xAOD::CaloRings_t> truth_rings_bufs(m_truthRingerKeys.size());
  std::vector<std::vector<float> *> truth_rings_ptrs(m_truthRingerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarTruthRings(m_truthRingerKeys.size());
  xAOD::Electron_t el_buf;
  xAOD::ElectronNtupleScalars el_scalars;
  xAOD::Electron_t truth_el_buf;
  xAOD::ElectronNtupleScalars truth_el_scalars;
  xAOD::Seed_t seed_buf;
  xAOD::TruthParticleNtupleBuffers truth_buf;
  truth_buf.init();

  bool customSchema = !m_schema.empty();
  auto groups = Gaugi::parseSchema(m_schema);

  auto spEvt = getSpecsFor(groups, "EventInfo", m_eventKey);
  if (!customSchema || !spEvt.empty()) {
    eventCnv.book_ntuple(tree, event_buf, spEvt, "");
  }

  auto spClus = getSpecsFor(groups, "CaloCluster", m_clusterKey);
  if (!customSchema || !spClus.empty()) {
    clusterCnv.book_ntuple(tree, clus_buf, spClus, "cl_");
  }

  auto spTruthClus = getSpecsFor(groups, "CaloCluster", m_truthClusterKey);
  if (!customSchema || !spTruthClus.empty()) {
    clusterCnv.book_ntuple(tree, truth_clus_buf, spTruthClus, "truth_cl_");
  }

  auto spRingsL0 = getSpecsFor(groups, "CaloRings", m_ringerL0Key);
  if (!customSchema || !spRingsL0.empty()) {
    ringsCnv.book_ntuple(tree, ringsL0_buf, ringsL0_ptr, scalarRingsL0, spRingsL0, "cl_ringsL0");
  }

  for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
    auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
    if (!customSchema || !spR.empty()) {
      ringsCnv.book_ntuple(tree, rings_bufs[i], rings_ptrs[i], scalarRings[i], spR, "cl_rings_" + m_ringerKeys[i]);
    }
  }

  for (size_t i = 0; i < m_truthRingerKeys.size(); ++i) {
    auto spTR = getSpecsFor(groups, "CaloRings", m_truthRingerKeys[i]);
    if (!customSchema || !spTR.empty()) {
      ringsCnv.book_ntuple(tree, truth_rings_bufs[i], truth_rings_ptrs[i], scalarTruthRings[i], spTR, "truth_cl_rings_" + m_truthRingerKeys[i]);
    }
  }

  auto spEl = getSpecsFor(groups, "Electron", m_electronKey);
  if (!customSchema || !spEl.empty()) {
    electronCnv.book_ntuple(tree, el_buf, el_scalars, spEl, "el_");
  }

  auto spTruthEl = getSpecsFor(groups, "Electron", m_truthElectronKey);
  if (!customSchema || !spTruthEl.empty()) {
    electronCnv.book_ntuple(tree, truth_el_buf, truth_el_scalars, spTruthEl, "truth_el_");
  }

  auto spSeed = getSpecsFor(groups, "Seed", m_seedsKey);
  if (!customSchema || !spSeed.empty()) {
    seedCnv.book_ntuple(tree, seed_buf, spSeed, "seed_");
  }

  auto spMC = getSpecsFor(groups, "TruthParticle", m_truthKey);
  if (!customSchema || !spMC.empty()) {
    truthCnv.book_ntuple(tree, truth_buf, spMC, "mc_");
  }

  store->add(tree);
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::pre_execute(EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::execute(EventContext & /*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::execute(EventContext & /*ctx*/, int /*evt*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::post_execute(EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamNtupleMaker::fillHistograms(EventContext &ctx) const
{
  MSG_INFO("fill ttree...");

  SG::ReadHandle<xAOD::EventInfoContainer> event_container(m_eventKey, ctx);
  if (!event_container.isValid()) {
    MSG_FATAL("It's not possible to read the xAOD::EventInfoContainer from this Context using this key " << m_eventKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::ElectronContainer> electron_container(m_electronKey, ctx);
  if (!electron_container.isValid()) {
    MSG_FATAL("It's not possible to read the xAOD::ElectronContainer from this Context using this key " << m_electronKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::SeedContainer> seed_container(m_seedsKey, ctx);
  if (!seed_container.isValid()) {
    MSG_FATAL("It's not possible to read the xAOD::SeedContainer from this Context using this key " << m_seedsKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::TruthParticleContainer> truth_container(m_truthKey, ctx);
  if (!truth_container.isValid()) {
    MSG_FATAL("It's not possible to read the xAOD::TruthParticleContainer from this Context using this key " << m_truthKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::CaloRingsContainer> ringerL0_container(m_ringerL0Key, ctx);
  SG::ReadHandle<xAOD::CaloClusterContainer> truth_cluster_container(m_truthClusterKey, ctx);
  SG::ReadHandle<xAOD::ElectronContainer> truth_electron_container(m_truthElectronKey, ctx);

  std::vector<SG::ReadHandle<xAOD::CaloRingsContainer>> ringer_containers;
  for (const auto &key : m_ringerKeys)
    ringer_containers.emplace_back(key, ctx);

  std::vector<SG::ReadHandle<xAOD::CaloRingsContainer>> truth_ringer_containers;
  for (const auto &key : m_truthRingerKeys)
    truth_ringer_containers.emplace_back(key, ctx);

  auto store = ctx.getStoreGateSvc();
  store->cd();
  TTree *tree = store->tree(m_outputNtupleName.c_str());
  if (!tree) {
    MSG_FATAL("Could not find tree " << m_outputNtupleName);
    return StatusCode::FAILURE;
  }

  xAOD::EventInfoConverter eventCnv;
  xAOD::CaloClusterConverter clusterCnv;
  xAOD::CaloRingsConverter ringsCnv;
  xAOD::ElectronConverter electronCnv;
  xAOD::SeedConverter seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  xAOD::EventInfo_t event_buf;
  xAOD::CaloCluster_t clus_buf;
  xAOD::CaloCluster_t truth_clus_buf;
  xAOD::CaloRings_t ringsL0_buf;
  std::vector<float> *ringsL0_ptr = nullptr;
  std::map<std::string, float> scalarRingsL0;
  std::vector<xAOD::CaloRings_t> rings_bufs(m_ringerKeys.size());
  std::vector<std::vector<float> *> rings_ptrs(m_ringerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarRings(m_ringerKeys.size());
  std::vector<xAOD::CaloRings_t> truth_rings_bufs(m_truthRingerKeys.size());
  std::vector<std::vector<float> *> truth_rings_ptrs(m_truthRingerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarTruthRings(m_truthRingerKeys.size());
  xAOD::Electron_t el_buf;
  xAOD::ElectronNtupleScalars el_scalars;
  xAOD::Electron_t truth_el_buf;
  xAOD::ElectronNtupleScalars truth_el_scalars;
  xAOD::Seed_t seed_buf;
  xAOD::TruthParticleNtupleBuffers truth_buf;
  truth_buf.init();

  bool customSchema = !m_schema.empty();
  auto groups = Gaugi::parseSchema(m_schema);

  auto spEvt = getSpecsFor(groups, "EventInfo", m_eventKey);
  auto spClus = getSpecsFor(groups, "CaloCluster", m_clusterKey);
  auto spTruthClus = getSpecsFor(groups, "CaloCluster", m_truthClusterKey);
  auto spRingsL0 = getSpecsFor(groups, "CaloRings", m_ringerL0Key);
  auto spEl = getSpecsFor(groups, "Electron", m_electronKey);
  auto spTruthEl = getSpecsFor(groups, "Electron", m_truthElectronKey);
  auto spSeed = getSpecsFor(groups, "Seed", m_seedsKey);
  auto spMC = getSpecsFor(groups, "TruthParticle", m_truthKey);

  if (!customSchema || !spEvt.empty()) eventCnv.book_ntuple(tree, event_buf, spEvt, "");
  if (!customSchema || !spClus.empty()) clusterCnv.book_ntuple(tree, clus_buf, spClus, "cl_");
  if (!customSchema || !spTruthClus.empty()) clusterCnv.book_ntuple(tree, truth_clus_buf, spTruthClus, "truth_cl_");
  if (!customSchema || !spRingsL0.empty()) ringsCnv.book_ntuple(tree, ringsL0_buf, ringsL0_ptr, scalarRingsL0, spRingsL0, "cl_ringsL0");
  for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
    auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
    if (!customSchema || !spR.empty()) ringsCnv.book_ntuple(tree, rings_bufs[i], rings_ptrs[i], scalarRings[i], spR, "cl_rings_" + m_ringerKeys[i]);
  }
  for (size_t i = 0; i < m_truthRingerKeys.size(); ++i) {
    auto spTR = getSpecsFor(groups, "CaloRings", m_truthRingerKeys[i]);
    if (!customSchema || !spTR.empty()) ringsCnv.book_ntuple(tree, truth_rings_bufs[i], truth_rings_ptrs[i], scalarTruthRings[i], spTR, "truth_cl_rings_" + m_truthRingerKeys[i]);
  }
  if (!customSchema || !spEl.empty()) electronCnv.book_ntuple(tree, el_buf, el_scalars, spEl, "el_");
  if (!customSchema || !spTruthEl.empty()) electronCnv.book_ntuple(tree, truth_el_buf, truth_el_scalars, spTruthEl, "truth_el_");
  if (!customSchema || !spSeed.empty()) seedCnv.book_ntuple(tree, seed_buf, spSeed, "seed_");
  if (!customSchema || !spMC.empty()) truthCnv.book_ntuple(tree, truth_buf, spMC, "mc_");

  auto evt = (*event_container).front();
  eventCnv.to_ntuple(evt, event_buf);

  for (const auto el : *electron_container) {
    auto clus = el->caloCluster();
    auto seed = clus ? clus->seed() : nullptr;

    electronCnv.to_ntuple(el, el_buf, el_scalars);
    clusterCnv.to_ntuple(clus, clus_buf);
    seedCnv.to_ntuple(seed, seed_buf);

    const xAOD::CaloRings *cl_ringerL0 = nullptr;
    if (ringerL0_container.isValid() && clus) {
      for (auto ring : *ringerL0_container) {
        if (ring->caloCluster() == clus) {
          cl_ringerL0 = ring;
          break;
        }
      }
    }
    ringsCnv.to_ntuple(cl_ringerL0, ringsL0_buf, scalarRingsL0, spRingsL0);

    for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
      const xAOD::CaloRings *ringMatch = nullptr;
      if (ringer_containers[i].isValid() && clus) {
        for (auto ring : *ringer_containers[i]) {
          if (ring->caloCluster() == clus) {
            ringMatch = ring;
            break;
          }
        }
      }
      auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
      ringsCnv.to_ntuple(ringMatch, rings_bufs[i], scalarRings[i], spR);
    }

    const xAOD::CaloCluster *truth_clus = nullptr;
    if (truth_cluster_container.isValid() && seed) {
      for (auto tr_cl : *truth_cluster_container) {
        if (tr_cl->seed() == seed) {
          truth_clus = tr_cl;
          break;
        }
      }
    }
    clusterCnv.to_ntuple(truth_clus, truth_clus_buf);

    for (size_t i = 0; i < m_truthRingerKeys.size(); ++i) {
      const xAOD::CaloRings *truthRingMatch = nullptr;
      if (truth_ringer_containers[i].isValid() && truth_clus) {
        for (auto tr_ring : *truth_ringer_containers[i]) {
          if (tr_ring->caloCluster() == truth_clus) {
            truthRingMatch = tr_ring;
            break;
          }
        }
      }
      auto spTR = getSpecsFor(groups, "CaloRings", m_truthRingerKeys[i]);
      ringsCnv.to_ntuple(truthRingMatch, truth_rings_bufs[i], scalarTruthRings[i], spTR);
    }

    const xAOD::Electron *truth_el = nullptr;
    if (truth_electron_container.isValid() && seed) {
      for (auto tr_el : *truth_electron_container) {
        if (tr_el->caloCluster() && tr_el->caloCluster()->seed() == seed) {
          truth_el = tr_el;
          break;
        }
      }
    }
    electronCnv.to_ntuple(truth_el, truth_el_buf, truth_el_scalars);

    if (seed) {
      truthCnv.to_ntuple(truth_container.ptr(), seed->id(), truth_buf);
    } else {
      truth_buf.clear();
    }

    tree->Fill();
  }

  tree->ResetBranchAddresses();
  return StatusCode::SUCCESS;
}
