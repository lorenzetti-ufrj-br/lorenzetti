#include "CustomRingsTool.h"
#include "G4Kernel/CaloPhiRange.h"
#include <cmath>
#include <algorithm>
#include <numeric>

using namespace Gaugi;

RingSetCustom::RingSetCustom(const std::vector<CaloSampling> &samplings, int nRings, float deta, float dphi, int nShifts)
    : RingSetBase(samplings, nRings, deta, dphi),
      m_nShifts(nShifts)
{
}

void RingSetCustom::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int shift_idx)
{
  if (!isValid(cell)) return;

  const int total_rings = static_cast<int>(m_rings.size());
  const int rings_per_seed = (m_nShifts > 0) ? (total_rings / m_nShifts) : total_rings;
  const int offset = shift_idx * rings_per_seed;

  const float deta = std::abs(eta_center - cell->eta()) / m_deta;
  const float dphi = std::abs(CaloPhiRange::diff(phi_center, cell->phi())) / m_dphi;
  const float deltaGreater = std::max(deta, dphi);

  const int i = static_cast<int>(std::round(deltaGreater)) + offset;

  if (i < total_rings) {
    m_rings[i] += cell->e() / std::cosh(std::abs(eta_center));
  }
}

CustomRingsTool::CustomRingsTool(std::string name)
    : IMsgService(name),
      CaloRingsBaseTool(name),
      m_ringsShiftEta({0.0f}),
      m_ringsShiftPhi({0.0f})
{
  declareProperty("RingsShiftEta", m_ringsShiftEta = {0.0f});
  declareProperty("RingsShiftPhi", m_ringsShiftPhi = {0.0f});
}

StatusCode CustomRingsTool::initialize()
{
  setMsgLevel((MSG::Level)m_outputLevel);

  if (m_ringsShiftEta.size() != m_ringsShiftPhi.size()) {
    MSG_ERROR("RingsShiftEta and RingsShiftPhi must have the same size! ("
              << m_ringsShiftEta.size() << " vs " << m_ringsShiftPhi.size() << ")");
    return StatusCode::FAILURE;
  }

  const int nShifts = static_cast<int>(m_ringsShiftEta.size());
  m_maxRingsAccumulated = std::accumulate(m_nRings.begin(), m_nRings.end(), 0) * nShifts;
  return StatusCode::SUCCESS;
}

std::vector<std::pair<float, float>> CustomRingsTool::getSeeds(float c_eta, float c_phi, const RingSetCustom &rs) const
{
  std::vector<std::pair<float, float>> seeds;
  seeds.reserve(m_ringsShiftEta.size());
  for (size_t i = 0; i < m_ringsShiftEta.size(); ++i) {
    seeds.emplace_back(c_eta + m_ringsShiftEta[i] * rs.deta(), c_phi + m_ringsShiftPhi[i] * rs.dphi());
  }
  return seeds;
}

StatusCode CustomRingsTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const
{
  auto *rings = dynamic_cast<xAOD::CaloRings*>(edm);
  if (!rings) {
    MSG_ERROR("EDM object provided is not xAOD::CaloRings!");
    return StatusCode::FAILURE;
  }

  const auto *clus = rings->caloCluster();
  if (!clus) {
    MSG_ERROR("CaloCluster parent link not found in CaloRings!");
    return StatusCode::FAILURE;
  }

  const int nShifts = static_cast<int>(m_ringsShiftEta.size());
  std::vector<RingSetCustom> vec_rs;
  vec_rs.reserve(m_nRings.size());
  for (size_t rs = 0; rs < m_nRings.size(); ++rs) {
    std::vector<CaloSampling> samplings;
    for (auto samp : m_layerRings[rs]) {
      samplings.push_back(static_cast<CaloSampling>(samp));
    }
    vec_rs.emplace_back(samplings, m_nRings[rs] * nShifts, m_detaRings[rs], m_dphiRings[rs], nShifts);
  }

  for (auto &rs : vec_rs) {
    rs.clear();
    const auto *hotCell = maxCell(clus, rs);
    float base_eta = hotCell ? hotCell->eta() : clus->eta();
    float base_phi = hotCell ? hotCell->phi() : clus->phi();
    auto seeds = getSeeds(base_eta, base_phi, rs);

    for (const auto *cell : clus->cells()) {
      if (!passSigmaCut(cell)) continue;
      for (int i = 0; i < nShifts; ++i) {
        rs.push_back(cell, seeds[i].first, seeds[i].second, i);
      }
    }
  }

  std::vector<float> ref_rings;
  ref_rings.reserve(m_maxRingsAccumulated);
  for (const auto &rs : vec_rs) {
    ref_rings.insert(ref_rings.end(), rs.rings().begin(), rs.rings().end());
  }

  rings->setRings(ref_rings);
  return StatusCode::SUCCESS;
}
