#include "CaloAsymRingsMaker.h"
#include "G4Kernel/CaloPhiRange.h"

// Construtor repassando o nome para a classe base
CaloAsymRingsMaker::CaloAsymRingsMaker(std::string name)
    : CaloRingsMaker(name)
{
}

// Implementação da lógica de preenchimento assimétrico
void RingSetAsym::push_back(const xAOD::CaloCell *cell,
                            float eta_center,
                            float phi_center)
{
  if (isValid(cell))
  {
    float deta = eta_center - cell->eta();
    bool etaPositive = deta > 0;
    deta = std::abs(deta) / m_deta;

    float dphi = CaloPhiRange::diff(phi_center, cell->phi());
    bool phiPositive = dphi > 0;
    dphi = std::abs(dphi) / m_dphi;

    float deltaGreater = std::max(deta, dphi);

    int ringNumber = static_cast<unsigned int>(std::round(deltaGreater));

    if (ringNumber > 0)
    {
      if (etaPositive && phiPositive) // Q1
      {
        ringNumber = (ringNumber * 4) - 3;
      }
      else if (etaPositive && !phiPositive) // Q2
      {
        ringNumber = (ringNumber * 4) - 1;
      }
      else if (!etaPositive && !phiPositive) // Q3
      {
        ringNumber = (ringNumber * 4);
      }
      else // Q4
      {
        ringNumber = (ringNumber * 4) - 2;
      }
    }

    if (ringNumber < (int)m_rings.size())
    {
      m_rings[ringNumber] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

//!=====================================================================

StatusCode CaloAsymRingsMaker::post_execute(SG::EventContext &ctx) const
{
  SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
  ringer.record(std::unique_ptr<xAOD::CaloRingsContainer>(new xAOD::CaloRingsContainer()));

  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);

  // Asym RingSet
  std::vector<RingSetAsym> vec_rs;

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

    vec_rs.push_back(RingSetAsym(samplings, m_nRings[rs], m_detaRings[rs], m_dphiRings[rs]));
  }

  for (auto *clus : **clusters.ptr())
  {
    MSG_INFO("Creating the Asymetric CaloRings for this cluster...");

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
      auto *hotCell = maxCell(clus, rs);

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
        if (hotCell)
        {
          rs.push_back(cell, hotCell->eta(), hotCell->phi());
        }
        else
        {
          rs.push_back(cell, clus->eta(), clus->phi());
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