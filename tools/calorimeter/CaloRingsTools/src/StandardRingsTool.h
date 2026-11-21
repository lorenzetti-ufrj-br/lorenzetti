#ifndef StandardRingsTool_h
#define StandardRingsTool_h

#include "CaloRingsBaseTool.h"

/**
 * @class RingSet
 * @brief Helper class to manage a set of concentric rings for a specific calorimeter layer.
 */
class RingSet : public Gaugi::RingSetBase {
public:
  using Gaugi::RingSetBase::RingSetBase;
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center);
};

namespace Gaugi {

/**
 * @class StandardRingsTool
 * @brief Tool to calculate concentric calorimeter rings and decorate xAOD::CaloRings.
 */
class StandardRingsTool : public CaloRingsBaseTool {
public:
  StandardRingsTool(std::string name);
  virtual ~StandardRingsTool() = default;

  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;
};

} // namespace Gaugi

using StandardRingsTool = Gaugi::StandardRingsTool;

#endif
