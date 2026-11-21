#ifndef CaloRingsBaseTool_h
#define CaloRingsBaseTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloRings/CaloRings.h"
#include "CaloCell/CaloCell.h"
#include "CaloCell/enumeration.h"
#include <vector>
#include <string>
#include <cstddef>
#include <algorithm>

namespace Gaugi {

/**
 * @class RingSetBase
 * @brief Common base class for ring accumulator sets used across CaloRings tools.
 */
class RingSetBase {
public:
  RingSetBase(const std::vector<CaloSampling> &samplings, unsigned nrings, float deta, float dphi)
      : m_rings(nrings, 0.0f),
        m_deta(deta),
        m_dphi(dphi),
        m_samplings(samplings) {}
  RingSetBase() = default;
  virtual ~RingSetBase() = default;

  const std::vector<float> &rings() const { return m_rings; }
  size_t size() const { return m_rings.size(); }
  bool isValid(const xAOD::CaloCell *cell) const {
    if (!cell || !cell->descriptor()) return false;
    for (auto samp : m_samplings) {
      if (cell->descriptor()->sampling() == samp) return true;
    }
    return false;
  }
  void clear() { std::fill(m_rings.begin(), m_rings.end(), 0.0f); }

  float deta() const { return m_deta; }
  float dphi() const { return m_dphi; }
  const std::vector<CaloSampling> &samplings() const { return m_samplings; }

protected:
  std::vector<float> m_rings;
  float m_deta{0.0f};
  float m_dphi{0.0f};
  std::vector<CaloSampling> m_samplings;
};

/**
 * @class CaloRingsBaseTool
 * @brief Base class for calorimeter ring calculation and CaloRings decoration tools.
 */
class CaloRingsBaseTool : public Tool {
public:
  CaloRingsBaseTool(std::string name);
  virtual ~CaloRingsBaseTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  /*! Canonical Gaugi::Tool signature: receives CaloRings to decorate */
  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override = 0;

  int maxRingsAccumulated() const { return m_maxRingsAccumulated; }

protected:
  const xAOD::CaloCell* maxCell(const xAOD::CaloCluster *clus, const RingSetBase &rs) const;
  bool passSigmaCut(const xAOD::CaloCell *cell) const;

  std::vector<float> m_detaRings;
  std::vector<float> m_dphiRings;
  std::vector<int> m_nRings;
  std::vector<std::vector<int>> m_layerRings;
  bool m_doSigmaCut;
  float m_sigmaCut;
  mutable int m_maxRingsAccumulated;
  int m_outputLevel;
};

} // namespace Gaugi

using RingSetBase = Gaugi::RingSetBase;
using CaloRingsBaseTool = Gaugi::CaloRingsBaseTool;

#endif
