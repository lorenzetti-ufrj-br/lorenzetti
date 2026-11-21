#include "CaloRingsMaker.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloRings/CaloRings.h"
#include "TH2F.h"
#include <cmath>

using namespace Gaugi;
using namespace SG;

CaloRingsMaker::CaloRingsMaker(std::string name)
    : Algorithm(),
      IMsgService(name),
      m_outputLevel(1)
{
  declareProperty("OutputRingerKey", m_ringerKey = "Rings");
  declareProperty("InputClusterKey", m_clusterKey = "Clusters");
  declareProperty("EtaRange", m_etaRange = {0.0f, 2.5f});
  declareProperty("HistogramPath", m_histPath = "Expert/Rings");
  declareProperty("OutputLevel", m_outputLevel = 1);
  declareProperty("Tools", m_tools = {});
}

StatusCode CaloRingsMaker::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);

  for (auto *tool : m_tools) {
    if (tool && tool->initialize().isFailure()) {
      MSG_ERROR("Failed to initialize tool: " << tool->name());
      return StatusCode::FAILURE;
    }
  }

  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::finalize()
{
  for (auto *tool : m_tools) {
    if (tool && tool->finalize().isFailure()) {
      MSG_ERROR("Failed to finalize tool: " << tool->name());
      return StatusCode::FAILURE;
    }
  }
  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::bookHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::pre_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::execute(SG::EventContext &ctx, int /*evt*/) const
{
  return post_execute(ctx);
}

StatusCode CaloRingsMaker::post_execute(SG::EventContext &ctx) const
{
  SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
  ringer.record(std::make_unique<xAOD::CaloRingsContainer>());

  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);
  if (!clusters.isValid()) {
    MSG_WARNING("CaloClusterContainer with key '" << m_clusterKey << "' is invalid in EventContext!");
    return StatusCode::SUCCESS;
  }

  uint32_t clus_idx = 0;
  for (const auto *clus : *clusters) {
    if (!clus) {
      clus_idx++;
      continue;
    }

    if (std::abs(clus->eta()) < m_etaRange[0] || std::abs(clus->eta()) >= m_etaRange[1]) {
      clus_idx++;
      continue;
    }

    auto *rings = new xAOD::CaloRings();
    rings->setEta(clus->eta());
    rings->setPhi(clus->phi());
    rings->setCaloCluster(m_clusterKey, clus_idx, clus);

    for (auto *tool : m_tools) {
      if (tool) {
        if (tool->execute(ctx, rings).isFailure()) {
          MSG_ERROR("Failed to decorate CaloRings with tool " << tool->name() << " for cluster " << clus_idx);
          delete rings;
          return StatusCode::FAILURE;
        }
      }
    }

    ringer->push_back(rings);
    clus_idx++;
  }

  return StatusCode::SUCCESS;
}

StatusCode CaloRingsMaker::fillHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}
