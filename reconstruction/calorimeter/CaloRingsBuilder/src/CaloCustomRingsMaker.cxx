#include "CaloCustomRingsMaker.h"
#include "G4Kernel/CaloPhiRange.h"
#include <memory>

// ---------------------------------------------------------------------------
// RingSetCustom::push_back
// ---------------------------------------------------------------------------
void RingSetCustom::push_back(const xAOD::CaloCell *cell,
                              float eta_center,
                              float phi_center,
                              int shift_idx)
{
    if (!isValid(cell))
        return;

    const int total_rings = static_cast<int>(m_rings.size());
    const int rings_per_seed = total_rings / m_nShifts;
    const int offset = shift_idx * rings_per_seed;

    const float deta = std::abs(eta_center - cell->eta()) / m_deta;
    const float dphi = std::abs(CaloPhiRange::diff(phi_center, cell->phi())) / m_dphi;
    const float deltaGreater = std::max(deta, dphi);

    const int i = static_cast<int>(std::round(deltaGreater)) + offset;

    if (i < total_rings)
        m_rings[i] += cell->e() / std::cosh(std::abs(eta_center));
}

// ---------------------------------------------------------------------------
// CaloCustomRingsMaker
// ---------------------------------------------------------------------------
CaloCustomRingsMaker::CaloCustomRingsMaker(std::string name)
    : CaloRingsMaker(name),
      m_ringsShiftEta({0.f}),
      m_ringsShiftPhi({0.f})
{
    // GaugiKernel suporta vector<float> — usamos dois vetores paralelos
    declareProperty("RingsShiftEta", m_ringsShiftEta);
    declareProperty("RingsShiftPhi", m_ringsShiftPhi);
}

std::vector<std::pair<float, float>> CaloCustomRingsMaker::getSeeds(
    float c_eta, float c_phi, const RingSetCustom &rs) const
{
    std::vector<std::pair<float, float>> seeds;
    seeds.reserve(m_ringsShiftEta.size());

    for (size_t i = 0; i < m_ringsShiftEta.size(); ++i)
    {
        const float seed_eta = c_eta + m_ringsShiftEta[i] * rs.deta();
        const float seed_phi = c_phi + m_ringsShiftPhi[i] * rs.dphi();

        MSG_DEBUG("Shift (" << m_ringsShiftEta[i] << ", " << m_ringsShiftPhi[i] << ")"
                            << " → seed (" << seed_eta << ", " << seed_phi << ")");

        seeds.emplace_back(seed_eta, seed_phi);
    }

    return seeds;
}

StatusCode CaloCustomRingsMaker::post_execute(SG::EventContext &ctx) const
{
    if (m_ringsShiftEta.size() != m_ringsShiftPhi.size())
    {
        MSG_ERROR("RingsShiftEta e RingsShiftPhi devem ter o mesmo tamanho! ("
                  << m_ringsShiftEta.size() << " vs " << m_ringsShiftPhi.size() << ")");
        return StatusCode::FAILURE;
    }

    if (m_ringsShiftEta.empty())
    {
        MSG_ERROR("RingsShiftEta está vazio. Informe ao menos um par.");
        return StatusCode::FAILURE;
    }

    const int nShifts = static_cast<int>(m_ringsShiftEta.size());

    SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
    ringer.record(std::make_unique<xAOD::CaloRingsContainer>());

    SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);

    std::vector<RingSetCustom> vec_rs;
    vec_rs.reserve(m_nRings.size());

    for (int rs = 0; rs < static_cast<int>(m_nRings.size()); ++rs)
    {
        std::vector<CaloSampling> samplings;
        for (auto samp : m_layerRings[rs])
            samplings.push_back(static_cast<CaloSampling>(samp));

        vec_rs.emplace_back(samplings,
                            m_nRings[rs] * nShifts,
                            m_detaRings[rs],
                            m_dphiRings[rs],
                            nShifts);
    }

    for (auto *clus : **clusters.ptr())
    {
        MSG_INFO("Creating Custom CaloRings for this cluster...");

        if (std::abs(clus->eta()) < m_etaRange[0] ||
            std::abs(clus->eta()) >= m_etaRange[1])
        {
            MSG_DEBUG("Skipping cluster out of eta range: " << clus->eta());
            continue;
        }

        auto *rings = new xAOD::CaloRings();

        for (auto &rs : vec_rs)
        {
            rs.clear();

            auto *hotCell = maxCell(clus, rs);
            float base_eta = hotCell ? hotCell->eta() : clus->eta();
            float base_phi = hotCell ? hotCell->phi() : clus->phi();

            auto seeds = getSeeds(base_eta, base_phi, rs);

            for (auto *cell : clus->cells())
            {
                if (m_DoSigmaCut &&
                    cell->e() <= m_SigmaCut * cell->descriptor()->sigma())
                    continue;

                for (int i = 0; i < nShifts; ++i)
                    rs.push_back(cell, seeds[i].first, seeds[i].second, i);
            }
        }

        std::vector<float> ref_rings;
        ref_rings.reserve(m_maxRingsAccumulated);
        for (auto &rs : vec_rs)
            ref_rings.insert(ref_rings.end(), rs.rings().begin(), rs.rings().end());

        rings->setRings(ref_rings);
        rings->setCaloCluster(clus);
        ringer->push_back(rings);
    }

    return StatusCode::SUCCESS;
}