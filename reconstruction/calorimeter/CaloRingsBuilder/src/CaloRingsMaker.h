#ifndef CaloRingsMaker_h
#define CaloRingsMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/Tool.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/DataHandle.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"

#include <string>
#include <vector>

/**
 * @class CaloRingsMaker
 * @brief Orchestrator algorithm managing the creation of xAOD::CaloRingsContainer
 *        and delegating ring decoration to specialized Gaugi::Tool instances.
 */
class CaloRingsMaker : public Gaugi::Algorithm {
public:
  CaloRingsMaker(std::string name);
  virtual ~CaloRingsMaker() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

  void addTool(Gaugi::Tool *tool) { m_tools.push_back(tool); }
  void push_back(Gaugi::Tool *tool) { m_tools.push_back(tool); }
  void setRingsTool(Gaugi::Tool *tool) { m_tools.clear(); m_tools.push_back(tool); }
  Gaugi::Tool* tool() const { return m_tools.empty() ? nullptr : m_tools[0]; }
  const std::vector<Gaugi::Tool*>& tools() const { return m_tools; }

private:
  std::string m_clusterKey;
  std::string m_ringerKey;
  std::string m_histPath;
  std::vector<float> m_etaRange;
  int m_outputLevel;
  std::vector<Gaugi::Tool*> m_tools;
};

#endif
