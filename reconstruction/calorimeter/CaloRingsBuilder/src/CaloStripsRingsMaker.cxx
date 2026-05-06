#include "CaloStripsRingsMaker.h"
#include "G4Kernel/CaloPhiRange.h"

CaloStripsRingsMaker::CaloStripsRingsMaker(std::string name)
    : CaloRingsMaker(name), m_axis(0)
{
  declareProperty("Axis", m_axis);
}

RingSetStrips::RingSetStrips(std::vector<CaloSampling> &samplings, unsigned nrings, float deta, float dphi, int axis)
    : RingSet(samplings, nrings, deta, dphi),
      m_axis(axis)
{
}

void RingSetStrips::push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center)
{
  if (isValid(cell))
  {
    int nStrips = (int)m_rings.size();
    int midPoint = nStrips / 2;

    float dphi = CaloPhiRange::diff(phi_center, cell->phi());
    bool phiPositive = dphi > 0;

    double delta = 0.0;
    if (m_axis)
    {
      delta = dphi / m_dphi;
    }
    else
    {
      delta = (eta_center - cell->eta()) / m_deta;
    }

    int index = copysign(static_cast<int>(std::floor(delta + .5)), delta);
    unsigned int stripIdx(0);

    if (!phiPositive)
    {
      stripIdx = midPoint - (index * 2);
      if (stripIdx > 100000)
      {
        stripIdx = 0;
      }
    }
    else
    {
      stripIdx = midPoint - (index * 2 + 1);
      if (stripIdx > 100000)
      {
        stripIdx = 0;
      }
    }

    if (stripIdx < nStrips)
    {
      m_rings[stripIdx] += cell->e() / std::cosh(std::abs(eta_center));
    }
  }
}

//!=====================================================================

StatusCode CaloStripsRingsMaker::post_execute(SG::EventContext &ctx) const
{
  SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
  ringer.record(std::unique_ptr<xAOD::CaloRingsContainer>(new xAOD::CaloRingsContainer()));

  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);

  // Strips RingSet
  std::vector<RingSetStrips> vec_rs;

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

    vec_rs.push_back(RingSetStrips(samplings, m_nRings[rs], m_detaRings[rs], m_dphiRings[rs], m_axis));
  }

  for (auto *clus : **clusters.ptr())
  {
    MSG_INFO("Creating the Stripsetric CaloRings for this cluster...");

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