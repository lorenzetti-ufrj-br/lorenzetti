#include "CaloCrossRingsMaker.h"
#include "G4Kernel/CaloPhiRange.h"
#include <memory>

CaloCrossRingsMaker::CaloCrossRingsMaker(std::string name)
    : CaloRingsMaker(name), m_crossShift(1)
{
  declareProperty("CrossShift", m_crossShift);
}

std::vector<SeedPosC> CaloCrossRingsMaker::getSeeds(float c_eta, float c_phi, const RingSetCross &rs) const
{
  std::vector<SeedPosC> seeds;

  MSG_DEBUG("Calculating shift ...")
  float deltaEta = rs.deta() * m_crossShift;
  float deltaPhi = rs.dphi() * m_crossShift;
  MSG_DEBUG("Shift (eta,phi) (" << deltaEta << ", " << deltaPhi << ")");

  seeds.push_back({c_eta, c_phi});            // Center  [0]
  seeds.push_back({c_eta + deltaEta, c_phi}); // Top     [1]
  seeds.push_back({c_eta - deltaEta, c_phi}); // Bottom  [2]
  seeds.push_back({c_eta, c_phi - deltaPhi}); // Left    [3]
  seeds.push_back({c_eta, c_phi + deltaPhi}); // Right   [4]

  MSG_DEBUG("Calculating crosss position...");
  MSG_DEBUG("Center cell: (" << seeds[0].eta << ", " << seeds[0].phi << ")");
  MSG_DEBUG("Top:   (" << seeds[1].eta << ", " << seeds[1].phi << ")");
  MSG_DEBUG("Bottom:(" << seeds[2].eta << ", " << seeds[2].phi << ")");
  MSG_DEBUG("Left:  (" << seeds[3].eta << ", " << seeds[3].phi << ")");
  MSG_DEBUG("Right: (" << seeds[4].eta << ", " << seeds[4].phi << ")");

  return seeds;
}

void RingSetCross::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int cross_idx)
{
  int total_rings = (int)m_rings.size();
  int rings_per_cross = total_rings / 5;
  int offset = cross_idx * rings_per_cross;
  if (isValid(cell))
  {
    float deta = std::abs(eta_center - cell->eta()) / m_deta;
    float dphi = std::abs(CaloPhiRange::diff(phi_center, cell->phi())) / m_dphi;
    float deltaGreater = std::max(deta, dphi);
    int i = static_cast<unsigned int>(std::round(deltaGreater));
    i += offset;
    if (i < (int)m_rings.size())
    {
      m_rings[i] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

//!=====================================================================

StatusCode CaloCrossRingsMaker::post_execute(SG::EventContext &ctx) const
{
  SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
  ringer.record(std::unique_ptr<xAOD::CaloRingsContainer>(new xAOD::CaloRingsContainer()));

  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);

  std::vector<RingSetCross> vec_rs;

  MSG_DEBUG("Creating all RingSets...");
  MSG_DEBUG("DoSigmaCut is " << m_DoSigmaCut);
  MSG_DEBUG("SigmaCut is " << m_SigmaCut);
  for (int rs = 0; rs < (int)m_nRings.size(); ++rs)
  {
    std::vector<CaloSampling> samplings;
    for (auto samp : m_layerRings[rs])
    {
      samplings.push_back((CaloSampling)samp);
    }

    vec_rs.push_back(RingSetCross(samplings, m_nRings[rs], m_detaRings[rs], m_dphiRings[rs]));
  }

  for (auto *clus : **clusters.ptr())
  {
    MSG_INFO("Creating the Cross CaloRings for this cluster...");

    if ((std::abs(clus->eta()) < m_etaRange[0]) || (std::abs(clus->eta()) >= m_etaRange[1]))
    {
      MSG_DEBUG("Skipping cluster outside of the eta range... " << clus->eta()
                                                                << " is out of:" << m_etaRange[0] << "," << m_etaRange[1]);
      continue;
    }

    auto rings = new xAOD::CaloRings();
    for (auto &rs : vec_rs)
    {
      rs.clear();
      MSG_DEBUG("Retrieving hotcall ...")
      auto *hotCell = maxCell(clus, rs);
      MSG_DEBUG("Retrieving seeds ...")
      float base_eta = hotCell ? hotCell->eta() : clus->eta();
      float base_phi = hotCell ? hotCell->phi() : clus->phi();
      std::vector<SeedPosC> seeds = getSeeds(base_eta, base_phi, rs); // Obtendo o 5 centroides (C,TR,TL,BL,BR)
      for (auto *cell : clus->cells())
      {
        if (m_DoSigmaCut)
        {
          MSG_DEBUG("post_execute: cell e = " << cell->e()
                                              << " sigma = " << cell->descriptor()->sigma()
                                              << " cut = " << m_SigmaCut * cell->descriptor()->sigma());
          if (cell->e() <= m_SigmaCut * cell->descriptor()->sigma())
            continue;
        }
        std::vector<std::string> crossNames = {"Center", "Top", "Bottom", "Left", "Right"};

        for (int i = 0; i < 5; ++i)
        {

          rs.push_back(cell, seeds[i].eta, seeds[i].phi, i);
        }
      }
    }

    std::vector<float> ref_rings;
    ref_rings.reserve(m_maxRingsAccumulated);

    for (auto &rs : vec_rs)
      ref_rings.insert(ref_rings.end(), rs.rings().begin(), rs.rings().end());

    MSG_DEBUG("Setting all ring informations and attach into the EventContext.");
    rings->setRings(ref_rings);
    rings->setCaloCluster(clus);
    ringer->push_back(rings);
  }

  return StatusCode::SUCCESS;
}