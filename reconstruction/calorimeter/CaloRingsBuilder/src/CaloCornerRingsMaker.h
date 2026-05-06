#ifndef CaloCornerRingsMaker_h
#define CaloCornerRingsMaker_h

#include "CaloRingsMaker.h"

struct SeedPos
{
    float eta;
    float phi;
};

class RingSetCorner : public RingSet
{
public:
    using RingSet::RingSet;

    void push_back(const xAOD::CaloCell *cell, float eta, float phi, int i);
};

class CaloCornerRingsMaker : public CaloRingsMaker
{
public:
    CaloCornerRingsMaker(std::string name);
    virtual ~CaloCornerRingsMaker() = default;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;

private:
    int m_cornerShift;
    std::vector<SeedPos> getSeeds(float c_eta, float c_phi, const RingSetCorner &rs) const;
};

#endif