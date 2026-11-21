#ifndef CustomRingsTool_h
#define CustomRingsTool_h

#include "CaloRingsBaseTool.h"
#include <utility>
#include <vector>

/**
 * @class RingSetCustom
 * @brief RingSet with arbitrary custom seed coordinate shifts.
 */
class RingSetCustom : public Gaugi::RingSetBase {
public:
  RingSetCustom(const std::vector<CaloSampling> &samplings, int nRings, float deta, float dphi, int nShifts);
  void push_back(const xAOD::CaloCell *cell, float eta_center, float phi_center, int shift_idx);
  int nShifts() const { return m_nShifts; }

private:
  int m_nShifts{1};
};

namespace Gaugi {

/**
 * @class CustomRingsTool
 * @brief Tool to calculate custom shifted rings and decorate xAOD::CaloRings.
 */
class CustomRingsTool : public CaloRingsBaseTool {
public:
  CustomRingsTool(std::string name);
  virtual ~CustomRingsTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  std::vector<float> m_ringsShiftEta;
  std::vector<float> m_ringsShiftPhi;
  std::vector<std::pair<float, float>> getSeeds(float c_eta, float c_phi, const RingSetCustom &rs) const;
};

} // namespace Gaugi

using CustomRingsTool = Gaugi::CustomRingsTool;

#endif
