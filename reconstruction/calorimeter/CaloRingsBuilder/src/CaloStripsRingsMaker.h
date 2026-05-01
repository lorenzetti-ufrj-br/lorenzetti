#ifndef CaloAsymRingsMaker_h
#define CaloAsymRingsMaker_h

#include "CaloRingsMaker.h"

class RingSetAsym : public RingSet
{
public:
    using RingSet::RingSet;

    void push_back(const xAOD::CaloCell *cell,
                   float eta_center,
                   float phi_center);
};

class CaloAsymRingsMaker : public CaloRingsMaker
{
public:
    CaloAsymRingsMaker(std::string name);
    virtual ~CaloAsymRingsMaker() = default;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;
};

#endif
