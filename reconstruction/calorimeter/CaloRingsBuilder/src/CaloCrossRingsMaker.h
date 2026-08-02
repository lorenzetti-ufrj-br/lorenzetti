#ifndef CaloCrossRingsMaker_h
#define CaloCrossRingsMaker_h

#include "CaloRingsMaker.h"

struct SeedPosC
{
    float eta;
    float phi;
};

class RingSetCross : public RingSet
{
public:
    using RingSet::RingSet;

    void push_back(const xAOD::CaloCell *cell, float eta, float phi, int i);
};

class CaloCrossRingsMaker : public CaloRingsMaker
{
public:
    CaloCrossRingsMaker(std::string name);
    virtual ~CaloCrossRingsMaker() = default;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    int m_crossShift;
    std::vector<SeedPosC> getSeeds(float c_eta, float c_phi, const RingSetCross &rs) const;
};

#endif