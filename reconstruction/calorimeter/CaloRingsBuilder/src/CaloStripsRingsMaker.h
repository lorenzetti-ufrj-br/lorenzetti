#ifndef CaloStripsRingsMaker_h
#define CaloStripsRingsMaker_h

#include "CaloRingsMaker.h"

class RingSetStrips : public RingSet
{
public:
    using RingSet::RingSet;
    RingSetStrips(std::vector<CaloSampling> &samplings, unsigned nrings, float deta, float dphi, int axis);
    void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center);

private:
    int m_axis;
};

class CaloStripsRingsMaker : public CaloRingsMaker
{
public:
    CaloStripsRingsMaker(std::string name);
    virtual ~CaloStripsRingsMaker() = default;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    int m_axis;
};

#endif
