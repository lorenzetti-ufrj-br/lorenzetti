#ifndef CrossRingsTool_h
#define CrossRingsTool_h

#include "CaloRingsBaseTool.h"

/**
 * @struct SeedPosC
 * @brief Seed coordinate for Cross ring topology.
 */
struct SeedPosC {
  float eta;
  float phi;
};

/**
 * @class RingSetCross
 * @brief RingSet with cross pattern (Top, Bottom, Left, Right).
 */
class RingSetCross : public Gaugi::RingSetBase {
public:
  using Gaugi::RingSetBase::RingSetBase;
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int cross_idx);
};

namespace Gaugi {

/**
 * @class CrossRingsTool
 * @brief Tool to calculate cross-shaped rings (Top, Bottom, Left, Right) and decorate xAOD::CaloRings.
 */
class CrossRingsTool : public CaloRingsBaseTool {
public:
  CrossRingsTool(std::string name);
  virtual ~CrossRingsTool() = default;

  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  int m_crossShift{3};
  std::vector<SeedPosC> getSeeds(float c_eta, float c_phi, const RingSetCross &rs) const;
};

} // namespace Gaugi

using CrossRingsTool = Gaugi::CrossRingsTool;

#endif
