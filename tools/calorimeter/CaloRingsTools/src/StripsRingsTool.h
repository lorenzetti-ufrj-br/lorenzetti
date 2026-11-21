#ifndef StripsRingsTool_h
#define StripsRingsTool_h

#include "CaloRingsBaseTool.h"

/**
 * @class RingSetStrips
 * @brief RingSet projected along an axis (0 for eta, 1 for phi).
 */
class RingSetStrips : public Gaugi::RingSetBase {
public:
  RingSetStrips(const std::vector<CaloSampling> &samplings, unsigned nrings, float deta, float dphi, int axis);
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center);
  int axis() const { return m_axis; }

private:
  int m_axis{0};
};

namespace Gaugi {

/**
 * @class StripsRingsTool
 * @brief Tool to calculate strip projected rings (along eta or phi) and decorate xAOD::CaloRings.
 */
class StripsRingsTool : public CaloRingsBaseTool {
public:
  StripsRingsTool(std::string name);
  virtual ~StripsRingsTool() = default;

  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  int m_axis{0};
};

} // namespace Gaugi

using StripsRingsTool = Gaugi::StripsRingsTool;

#endif
