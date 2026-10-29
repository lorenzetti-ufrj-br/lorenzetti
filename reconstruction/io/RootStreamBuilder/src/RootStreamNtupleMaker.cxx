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
  std::vector<xAOD::CaloRings_t> rings_bufs(m_ringerKeys.size());
  std::vector<std::vector<float> *> rings_ptrs(m_ringerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarRings(m_ringerKeys.size());
  xAOD::Electron_t el_buf;
  xAOD::ElectronNtupleScalars el_scalars;
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

  for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
    auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
    if (!customSchema || !spR.empty()) {
      ringsCnv.book_ntuple(tree, rings_bufs[i], rings_ptrs[i], scalarRings[i], spR, "cl_rings_" + m_ringerKeys[i]);
    }
  }

  auto spEl = getSpecsFor(groups, "Electron", m_electronKey);
  if (!customSchema || !spEl.empty()) {
    electronCnv.book_ntuple(tree, el_buf, el_scalars, spEl, "el_");
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

  std::vector<SG::ReadHandle<xAOD::CaloRingsContainer>> ringer_containers;
  for (const auto &key : m_ringerKeys)
    ringer_containers.emplace_back(key, ctx);

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
  std::vector<xAOD::CaloRings_t> rings_bufs(m_ringerKeys.size());
  std::vector<std::vector<float> *> rings_ptrs(m_ringerKeys.size(), nullptr);
  std::vector<std::map<std::string, float>> scalarRings(m_ringerKeys.size());
  xAOD::Electron_t el_buf;
  xAOD::ElectronNtupleScalars el_scalars;
  xAOD::Seed_t seed_buf;
  xAOD::TruthParticleNtupleBuffers truth_buf;
  truth_buf.init();

  bool customSchema = !m_schema.empty();
  auto groups = Gaugi::parseSchema(m_schema);

  auto spEvt = getSpecsFor(groups, "EventInfo", m_eventKey);
  auto spClus = getSpecsFor(groups, "CaloCluster", m_clusterKey);
  auto spEl = getSpecsFor(groups, "Electron", m_electronKey);
  auto spSeed = getSpecsFor(groups, "Seed", m_seedsKey);
  auto spMC = getSpecsFor(groups, "TruthParticle", m_truthKey);

  if (!customSchema || !spEvt.empty()) eventCnv.book_ntuple(tree, event_buf, spEvt, "");
  if (!customSchema || !spClus.empty()) clusterCnv.book_ntuple(tree, clus_buf, spClus, "cl_");
  for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
    auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
    if (!customSchema || !spR.empty()) ringsCnv.book_ntuple(tree, rings_bufs[i], rings_ptrs[i], scalarRings[i], spR, "cl_rings_" + m_ringerKeys[i]);
  }
  if (!customSchema || !spEl.empty()) electronCnv.book_ntuple(tree, el_buf, el_scalars, spEl, "el_");
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
