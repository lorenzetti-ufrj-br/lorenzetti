#ifndef CALOCUSTOMRINGSMAKER_H
#define CALOCUSTOMRINGSMAKER_H

#include "CaloRingsMaker.h"
#include <vector>
#include <utility>

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

class CaloCustomRingsMaker : public CaloRingsMaker
{
public:
    CaloCustomRingsMaker(std::string name);
    std::vector<std::pair<float, float>> getSeeds(float c_eta,
                                                  float c_phi,
                                                  const RingSetCustom &rs) const;

    StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    std::vector<float> m_ringsShiftEta;
    std::vector<float> m_ringsShiftPhi;
};

#endif
