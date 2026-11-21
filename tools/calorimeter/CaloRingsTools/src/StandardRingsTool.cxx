#include "StandardRingsTool.h"
#include "G4Kernel/CaloPhiRange.h"
#include <cmath>
#include <algorithm>

using namespace Gaugi;

void RingSet::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center)
{
  if (isValid(cell)) {
    float deta = std::abs(eta_center - cell->eta()) / m_deta;
    float dphi = std::abs(CaloPhiRange::diff(phi_center, cell->phi())) / m_dphi;
    float deltaGreater = std::max(deta, dphi);
    int i = static_cast<unsigned int>(std::round(deltaGreater));
    if (i < static_cast<int>(m_rings.size())) {
      m_rings[i] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

StandardRingsTool::StandardRingsTool(std::string name)
    : IMsgService(name),
      CaloRingsBaseTool(name)
{
}

StatusCode StandardRingsTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const
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

  std::vector<RingSet> vec_rs;
  vec_rs.reserve(m_nRings.size());
  for (size_t rs = 0; rs < m_nRings.size(); ++rs) {
    std::vector<CaloSampling> samplings;
    for (auto samp : m_layerRings[rs]) {
      samplings.push_back(static_cast<CaloSampling>(samp));
    }
    vec_rs.emplace_back(samplings, m_nRings[rs], m_detaRings[rs], m_dphiRings[rs]);
  }

  for (auto &rs : vec_rs) {
    rs.clear();
    const auto *hotCell = maxCell(clus, rs);
    float center_eta = hotCell ? hotCell->eta() : clus->eta();
    float center_phi = hotCell ? hotCell->phi() : clus->phi();

    for (const auto *cell : clus->cells()) {
      if (!passSigmaCut(cell)) continue;
      rs.push_back(cell, center_eta, center_phi);
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
