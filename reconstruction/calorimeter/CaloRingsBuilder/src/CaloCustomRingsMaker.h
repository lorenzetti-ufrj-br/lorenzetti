#ifndef CALOCUSTOMRINGSMAKER_H
#define CALOCUSTOMRINGSMAKER_H

#include "CaloRingsMaker.h"
#include <vector>
#include <utility>

// ---------------------------------------------------------------------------
// RingSetCustom
// ---------------------------------------------------------------------------
class RingSetCustom : public RingSet
{
public:
    RingSetCustom(std::vector<CaloSampling> samplings,
                  int nRings,
                  float deta,
                  float dphi,
                  int nShifts)
        : RingSet(samplings, nRings, deta, dphi),
          m_nShifts(nShifts)
    {
    }

    void push_back(const xAOD::CaloCell *cell,
                   float eta_center,
                   float phi_center,
                   int shift_idx);

private:
    int m_nShifts;
};

// ---------------------------------------------------------------------------
// CaloCustomRingsMaker
// ---------------------------------------------------------------------------
class CaloCustomRingsMaker : public CaloRingsMaker
{
public:
    CaloCustomRingsMaker(std::string name);

    // Retorna seeds deslocados. Cada par (m_ringsShiftEta[i], m_ringsShiftPhi[i])
    // é multiplicado por (rs.deta(), rs.dphi()) para obter o deslocamento real.
    std::vector<std::pair<float, float>> getSeeds(float c_eta,
                                                  float c_phi,
                                                  const RingSetCustom &rs) const;

    StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    // Dois vetores paralelos — GaugiKernel só suporta vector<float>
    // Ex.: ShiftEta={0,1,-1}  ShiftPhi={0,1,4}  → seeds (0,0),(1,1),(-1,4)
    std::vector<float> m_ringsShiftEta;
    std::vector<float> m_ringsShiftPhi;
};

#endif // CALOCUSTOMRINGSMAKER_H