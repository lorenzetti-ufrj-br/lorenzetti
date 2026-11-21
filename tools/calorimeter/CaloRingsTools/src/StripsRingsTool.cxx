#include "StripsRingsTool.h"
#include "G4Kernel/CaloPhiRange.h"
#include <cmath>
#include <algorithm>

using namespace Gaugi;

RingSetStrips::RingSetStrips(const std::vector<CaloSampling> &samplings, unsigned nrings, float deta, float dphi, int axis)
    : RingSetBase(samplings, nrings, deta, dphi),
      m_axis(axis)
{
}

void RingSetStrips::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center)
{
  if (isValid(cell)) {
    int nStrips = static_cast<int>(m_rings.size());
    int midPoint = nStrips / 2;

    float dphi = CaloPhiRange::diff(phi_center, cell->phi());
    bool phiPositive = (dphi > 0.0f);

    double delta = 0.0;
    if (m_axis) {
      delta = dphi / m_dphi;
    } else {
      delta = (eta_center - cell->eta()) / m_deta;
    }

    int index = std::copysign(static_cast<int>(std::floor(delta + 0.5)), delta);
    unsigned int stripIdx = 0;

    if (!phiPositive) {
      stripIdx = midPoint - (index * 2);
      if (stripIdx > 100000) {
        stripIdx = 0;
      }
    } else {
      stripIdx = midPoint - (index * 2 + 1);
      if (stripIdx > 100000) {
        stripIdx = 0;
      }
    }

    if (stripIdx < static_cast<unsigned int>(nStrips)) {
      m_rings[stripIdx] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

StripsRingsTool::StripsRingsTool(std::string name)
    : IMsgService(name),
      CaloRingsBaseTool(name),
      m_axis(0)
{
  declareProperty("Axis", m_axis = 0);
}

StatusCode StripsRingsTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const
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

  std::vector<RingSetStrips> vec_rs;
  vec_rs.reserve(m_nRings.size());
  for (size_t rs = 0; rs < m_nRings.size(); ++rs) {
    std::vector<CaloSampling> samplings;
    for (auto samp : m_layerRings[rs]) {
      samplings.push_back(static_cast<CaloSampling>(samp));
    }
    vec_rs.emplace_back(samplings, m_nRings[rs], m_detaRings[rs], m_dphiRings[rs], m_axis);
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
