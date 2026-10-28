#include "RootStreamParquetMaker.h"
#include "GaugiKernel/EventContext.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/MsgStream.h"
#include "GaugiKernel/BranchSpec.h"
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

#include <arrow/api.h>
#include <arrow/io/file.h>
#include <parquet/arrow/writer.h>

#include <iostream>

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

struct RootStreamParquetMaker::Impl
{
  std::vector<std::shared_ptr<arrow::Field>> fields;
  std::vector<arrow::ArrayBuilder*> all_builders;

  xAOD::EventInfo_parquet event_parquet;
  xAOD::CaloCluster_parquet clus_parquet;
  xAOD::CaloCluster_parquet truth_clus_parquet;
  xAOD::CaloRings_parquet ringsL0_parquet;
  std::vector<xAOD::CaloRings_parquet> rings_parquets;
  std::vector<xAOD::CaloRings_parquet> truth_rings_parquets;
  xAOD::Electron_parquet el_parquet;
  xAOD::Electron_parquet truth_el_parquet;
  xAOD::Seed_parquet seed_parquet;
  xAOD::TruthParticle_parquet mc_parquet;
};

RootStreamParquetMaker::RootStreamParquetMaker(std::string name) : IMsgService(name),
                                                                   Algorithm()
{
  declareProperty("OutputFile", m_outputFile = "output.parquet");
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
  declareProperty("Schema", m_schema = {});
}

RootStreamParquetMaker::~RootStreamParquetMaker()
{
}

StatusCode RootStreamParquetMaker::initialize()
{
  CHECK_INIT();
  m_impl = std::make_unique<Impl>();
  m_impl->rings_parquets.resize(m_ringerKeys.size());
  m_impl->truth_rings_parquets.resize(m_truthRingerKeys.size());

  xAOD::EventInfoConverter eventCnv;
  xAOD::CaloClusterConverter clusterCnv;
  xAOD::CaloRingsConverter ringsCnv;
  xAOD::ElectronConverter electronCnv;
  xAOD::SeedConverter seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  bool customSchema = !m_schema.empty();
  auto groups = Gaugi::parseSchema(m_schema);

  auto registerBlock = [&](const std::vector<arrow::ArrayBuilder*> &block_builders) {
    for (auto *b : block_builders) {
      m_impl->all_builders.push_back(b);
    }
  };

  // 1. EventInfo
  auto spEvt = getSpecsFor(groups, "EventInfo", m_eventKey);
  if (!customSchema || !spEvt.empty()) {
    eventCnv.book_parquet(m_impl->fields, m_impl->event_parquet, spEvt, "");
    registerBlock(m_impl->event_parquet.builders);
  }

  // 2. Clusters
  auto spClus = getSpecsFor(groups, "CaloCluster", m_clusterKey);
  if (!customSchema || !spClus.empty()) {
    clusterCnv.book_parquet(m_impl->fields, m_impl->clus_parquet, spClus, "cl_");
    registerBlock(m_impl->clus_parquet.builders);
  }

  // 3. TruthClusters
  auto spTruthClus = getSpecsFor(groups, "CaloCluster", m_truthClusterKey);
  if (!customSchema || !spTruthClus.empty()) {
    clusterCnv.book_parquet(m_impl->fields, m_impl->truth_clus_parquet, spTruthClus, "truth_cl_");
    registerBlock(m_impl->truth_clus_parquet.builders);
  }

  // 4. RingsL0
  auto spRingsL0 = getSpecsFor(groups, "CaloRings", m_ringerL0Key);
  if (!customSchema || !spRingsL0.empty()) {
    ringsCnv.book_parquet(m_impl->fields, m_impl->ringsL0_parquet, spRingsL0, "cl_ringsL0");
    registerBlock(m_impl->ringsL0_parquet.builders);
  }

  // 5. Rings
  for (size_t i = 0; i < m_ringerKeys.size(); ++i) {
    auto spR = getSpecsFor(groups, "CaloRings", m_ringerKeys[i]);
    if (!customSchema || !spR.empty()) {
      ringsCnv.book_parquet(m_impl->fields, m_impl->rings_parquets[i], spR, "cl_rings_" + m_ringerKeys[i]);
      registerBlock(m_impl->rings_parquets[i].builders);
    }
  }

  // 6. TruthRings
  for (size_t i = 0; i < m_truthRingerKeys.size(); ++i) {
    auto spTR = getSpecsFor(groups, "CaloRings", m_truthRingerKeys[i]);
    if (!customSchema || !spTR.empty()) {
      ringsCnv.book_parquet(m_impl->fields, m_impl->truth_rings_parquets[i], spTR, "truth_cl_rings_" + m_truthRingerKeys[i]);
      registerBlock(m_impl->truth_rings_parquets[i].builders);
    }
  }

  // 7. Electrons
  auto spEl = getSpecsFor(groups, "Electron", m_electronKey);
  if (!customSchema || !spEl.empty()) {
    electronCnv.book_parquet(m_impl->fields, m_impl->el_parquet, spEl, "el_");
    registerBlock(m_impl->el_parquet.builders);
  }

  // 8. TruthElectrons
  auto spTruthEl = getSpecsFor(groups, "Electron", m_truthElectronKey);
  if (!customSchema || !spTruthEl.empty()) {
    electronCnv.book_parquet(m_impl->fields, m_impl->truth_el_parquet, spTruthEl, "truth_el_");
    registerBlock(m_impl->truth_el_parquet.builders);
  }

  // 9. Seeds
  auto spSeed = getSpecsFor(groups, "Seed", m_seedsKey);
  if (!customSchema || !spSeed.empty()) {
    seedCnv.book_parquet(m_impl->fields, m_impl->seed_parquet, spSeed, "seed_");
    registerBlock(m_impl->seed_parquet.builders);
  }

  // 10. TruthParticles (MC)
  auto spMC = getSpecsFor(groups, "TruthParticle", m_truthKey);
  if (!customSchema || !spMC.empty()) {
    truthCnv.book_parquet(m_impl->fields, m_impl->mc_parquet, spMC, "mc_");
    registerBlock(m_impl->mc_parquet.builders);
  }

  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::bookHistograms(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::pre_execute(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::execute(SG::EventContext & /*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::execute(SG::EventContext & /*ctx*/, int /*evt*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::post_execute(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::fillHistograms(SG::EventContext &ctx) const
{
  SG::ReadHandle<xAOD::EventInfoContainer> event_container(m_eventKey, ctx);
  if (!event_container.isValid()) {
    MSG_FATAL("Cannot read xAOD::EventInfoContainer from " << m_eventKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::ElectronContainer> electron_container(m_electronKey, ctx);
  if (!electron_container.isValid()) {
    MSG_FATAL("Cannot read xAOD::ElectronContainer from " << m_electronKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::SeedContainer> seed_container(m_seedsKey, ctx);
  if (!seed_container.isValid()) {
    MSG_FATAL("Cannot read xAOD::SeedContainer from " << m_seedsKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::TruthParticleContainer> truth_container(m_truthKey, ctx);
  if (!truth_container.isValid()) {
    MSG_FATAL("Cannot read xAOD::TruthParticleContainer from " << m_truthKey);
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

  xAOD::EventInfoConverter eventCnv;
  xAOD::CaloClusterConverter clusterCnv;
  xAOD::CaloRingsConverter ringsCnv;
  xAOD::ElectronConverter electronCnv;
  xAOD::SeedConverter seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  auto evt = (*event_container).front();

  for (const auto el : *electron_container) {
    auto clus = el->caloCluster();
    auto seed = clus ? clus->seed() : nullptr;

    // EventInfo
    eventCnv.to_parquet(evt, m_impl->event_parquet);

    // Electron
    electronCnv.to_parquet(el, m_impl->el_parquet);

    // Cluster
    clusterCnv.to_parquet(clus, m_impl->clus_parquet);

    // Seed
    seedCnv.to_parquet(seed, m_impl->seed_parquet);

    // RingsL0
    const xAOD::CaloRings *cl_ringerL0 = nullptr;
    if (ringerL0_container.isValid() && clus) {
      for (auto ring : *ringerL0_container) {
        if (ring->caloCluster() == clus) {
          cl_ringerL0 = ring;
          break;
        }
      }
    }
    ringsCnv.to_parquet(cl_ringerL0, m_impl->ringsL0_parquet);

    // Other rings
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
      ringsCnv.to_parquet(ringMatch, m_impl->rings_parquets[i]);
    }

    // Truth Cluster matched by seed
    const xAOD::CaloCluster *truth_clus = nullptr;
    if (truth_cluster_container.isValid() && seed) {
      for (auto tr_cl : *truth_cluster_container) {
        if (tr_cl->seed() == seed) {
          truth_clus = tr_cl;
          break;
        }
      }
    }
    clusterCnv.to_parquet(truth_clus, m_impl->truth_clus_parquet);

    // Truth rings matched by truth_clus
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
      ringsCnv.to_parquet(truthRingMatch, m_impl->truth_rings_parquets[i]);
    }

    // Truth Electron matched by seed
    const xAOD::Electron *truth_el = nullptr;
    if (truth_electron_container.isValid() && seed) {
      for (auto tr_el : *truth_electron_container) {
        if (tr_el->caloCluster() && tr_el->caloCluster()->seed() == seed) {
          truth_el = tr_el;
          break;
        }
      }
    }
    electronCnv.to_parquet(truth_el, m_impl->truth_el_parquet);

    // MC Particles matched by seedid
    truthCnv.to_parquet(truth_container.ptr(), seed ? seed->id() : -1, m_impl->mc_parquet);
  }

  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::finalize()
{
  if (!m_impl) return StatusCode::SUCCESS;

  std::vector<std::shared_ptr<arrow::Array>> arrays;
  for (auto *b : m_impl->all_builders) {
    std::shared_ptr<arrow::Array> arr;
    PARQUET_THROW_NOT_OK(b->Finish(&arr));
    arrays.push_back(arr);
  }

  auto schema = arrow::schema(m_impl->fields);
  auto table = arrow::Table::Make(schema, arrays);

  PARQUET_ASSIGN_OR_THROW(auto outfile, arrow::io::FileOutputStream::Open(m_outputFile));
  PARQUET_THROW_NOT_OK(parquet::arrow::WriteTable(*table, arrow::default_memory_pool(), outfile));

  MSG_INFO("Successfully wrote " << m_outputFile);
  return StatusCode::SUCCESS;
}
