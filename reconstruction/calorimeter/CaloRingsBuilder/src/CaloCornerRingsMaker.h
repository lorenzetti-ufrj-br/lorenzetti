#ifndef CaloCornerRingsMaker_h
#define CaloCornerRingsMaker_h

#include "CaloRingsMaker.h"

class RingSetCorner : public RingSet
{
public:
    using RingSet::RingSet;

    void push_back(const xAOD::CaloCell *cell,
                   float eta_center,
                   float phi_center);
};

class CaloCornerRingsMaker : public CaloRingsMaker
{
public:
    CaloCornerRingsMaker(std::string name);
    virtual ~CaloCornerRingsMaker() = default;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    int m_cornerShift;
    std::vector<xAOD::CaloCell> getCornerSeeds(const xAOD::CaloCell *) const;
};

#endif
