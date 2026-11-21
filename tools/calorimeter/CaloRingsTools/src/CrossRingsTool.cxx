#include "CrossRingsTool.h"
#include "G4Kernel/CaloPhiRange.h"
#include <cmath>
#include <algorithm>

using namespace Gaugi;

void RingSetCross::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int cross_idx)
{
  int total_rings = static_cast<int>(m_rings.size());
  int rings_per_cross = total_rings / 4;
  int offset = cross_idx * rings_per_cross;
  if (isValid(cell)) {
    float deta = std::abs(eta_center - cell->eta()) / m_deta;
    float dphi = std::abs(CaloPhiRange::diff(phi_center, cell->phi())) / m_dphi;
    float deltaGreater = std::max(deta, dphi);
    int i = static_cast<unsigned int>(std::round(deltaGreater));
    i += offset;
    if (i < static_cast<int>(m_rings.size())) {
      m_rings[i] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

CrossRingsTool::CrossRingsTool(std::string name)
    : IMsgService(name),
      CaloRingsBaseTool(name),
      m_crossShift(3)
{
  declareProperty("CrossShift", m_crossShift = 3);
}

std::vector<SeedPosC> CrossRingsTool::getSeeds(float c_eta, float c_phi, const RingSetCross &rs) const
{
  std::vector<SeedPosC> seeds;
  float deltaEta = rs.deta() * m_crossShift;
  float deltaPhi = rs.dphi() * m_crossShift;

  seeds.push_back({c_eta + deltaEta, c_phi}); // Top    [0]
  seeds.push_back({c_eta - deltaEta, c_phi}); // Bottom [1]
  seeds.push_back({c_eta, c_phi - deltaPhi}); // Left   [2]
  seeds.push_back({c_eta, c_phi + deltaPhi}); // Right  [3]

  return seeds;
}

StatusCode CrossRingsTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const
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

  std::vector<RingSetCross> vec_rs;
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
    float base_eta = hotCell ? hotCell->eta() : clus->eta();
    float base_phi = hotCell ? hotCell->phi() : clus->phi();
    auto seeds = getSeeds(base_eta, base_phi, rs);

    for (const auto *cell : clus->cells()) {
      if (!passSigmaCut(cell)) continue;
      for (int i = 0; i < 4; ++i) {
        rs.push_back(cell, seeds[i].eta, seeds[i].phi, i);
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
