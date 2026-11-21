#ifndef CornerRingsTool_h
#define CornerRingsTool_h

#include "CaloRingsBaseTool.h"

/**
 * @struct SeedPos
 * @brief Seed coordinate for Corner ring topology.
 */
struct SeedPos {
  float eta;
  float phi;
};

/**
 * @class RingSetCorner
 * @brief RingSet with 4 diagonal corner centroids (TopRight, TopLeft, BottomLeft, BottomRight).
 */
class RingSetCorner : public Gaugi::RingSetBase {
public:
  using Gaugi::RingSetBase::RingSetBase;
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int corner_idx);
};

namespace Gaugi {

/**
 * @class CornerRingsTool
 * @brief Tool to calculate corner-shaped rings (TopRight, TopLeft, BottomLeft, BottomRight) and decorate xAOD::CaloRings.
 */
class CornerRingsTool : public CaloRingsBaseTool {
public:
  CornerRingsTool(std::string name);
  virtual ~CornerRingsTool() = default;

  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  int m_cornerShift{3};
  std::vector<SeedPos> getSeeds(float c_eta, float c_phi, const RingSetCorner &rs) const;
};

} // namespace Gaugi

using CornerRingsTool = Gaugi::CornerRingsTool;

#endif
