#ifndef AsymRingsTool_h
#define AsymRingsTool_h

#include "CaloRingsBaseTool.h"

/**
 * @class RingSetAsym
 * @brief RingSet with 4 distinct quadrants (Q1..Q4) for asymmetric ring profiles.
 */
class RingSetAsym : public Gaugi::RingSetBase {
public:
  using Gaugi::RingSetBase::RingSetBase;
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center);
};

namespace Gaugi {

/**
 * @class AsymRingsTool
 * @brief Tool to calculate 4-quadrant asymmetric rings and decorate xAOD::CaloRings.
 */
class AsymRingsTool : public CaloRingsBaseTool {
public:
  AsymRingsTool(std::string name);
  virtual ~AsymRingsTool() = default;

  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;
};

} // namespace Gaugi

using AsymRingsTool = Gaugi::AsymRingsTool;

#endif
