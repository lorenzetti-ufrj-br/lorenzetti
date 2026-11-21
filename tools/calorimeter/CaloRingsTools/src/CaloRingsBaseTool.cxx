#include "CaloRingsBaseTool.h"
#include <numeric>

using namespace Gaugi;

CaloRingsBaseTool::CaloRingsBaseTool(std::string name)
    : IMsgService(name),
      Tool(),
      m_doSigmaCut(false),
      m_sigmaCut(2.0f),
      m_maxRingsAccumulated(0),
      m_outputLevel(1)
{
  declareProperty("DeltaEtaRings", m_detaRings = {});
  declareProperty("DeltaPhiRings", m_dphiRings = {});
  declareProperty("NRings", m_nRings = {});
  declareProperty("LayerRings", m_layerRings = {});
  declareProperty("DoSigmaCut", m_doSigmaCut = false);
  declareProperty("SigmaCut", m_sigmaCut = 2.0f);
  declareProperty("OutputLevel", m_outputLevel = 1);
}

StatusCode CaloRingsBaseTool::initialize()
{
  setMsgLevel((MSG::Level)m_outputLevel);
  m_maxRingsAccumulated = std::accumulate(m_nRings.begin(), m_nRings.end(), 0);
  return StatusCode::SUCCESS;
}

StatusCode CaloRingsBaseTool::finalize()
{
  return StatusCode::SUCCESS;
}

const xAOD::CaloCell* CaloRingsBaseTool::maxCell(const xAOD::CaloCluster *clus, const RingSetBase &rs) const
{
  const xAOD::CaloCell *maxCell = nullptr;
  if (!clus) return nullptr;

  for (const auto *cell : clus->cells()) {
    if (!rs.isValid(cell)) continue;
    if (!passSigmaCut(cell)) continue;
    if (!maxCell || cell->e() > maxCell->e()) {
      maxCell = cell;
    }
  }
  return maxCell;
}

bool CaloRingsBaseTool::passSigmaCut(const xAOD::CaloCell *cell) const
{
  if (!m_doSigmaCut) return true;
  if (!cell || !cell->descriptor()) return false;
  return (cell->e() > m_sigmaCut * cell->descriptor()->sigma());
}
