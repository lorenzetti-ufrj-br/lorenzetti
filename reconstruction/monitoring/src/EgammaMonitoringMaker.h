#ifndef EgammaMonitoringMaker_h
#define EgammaMonitoringMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/StoreGate.h"

#include <memory>
#include <string>
#include <vector>

class TH1F;
class TH2F;

namespace Gaugi {

/**
 * @class EgammaMonitoringMaker
 * @brief Expert monitoring algorithm for calorimeter and e/gamma physics objects.
 *
 * Runs at the end of the reconstruction pipeline (AOD step) and produces data quality
 * validation distributions (kinematics, shower shapes, cluster moments, PID, and rings)
 * assembled and recorded directly through SG::StoreGate and SG::EventContext.
 */
class EgammaMonitoringMaker : public Algorithm {
public:
  EgammaMonitoringMaker(std::string name);
  virtual ~EgammaMonitoringMaker();

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

  const std::string& directory() const { return m_histDir; }
  const std::vector<std::string>& ringsKeys() const { return m_ringsKeys; }

private:
  TH1F* book1D(SG::StoreGate *store, const std::string &subDir, const std::string &name,
               const std::string &title, int nbins, float xmin, float xmax) const;
  TH2F* book2D(SG::StoreGate *store, const std::string &subDir, const std::string &name,
               const std::string &title, int nbinsX, float xmin, float xmax,
               int nbinsY, float ymin, float ymax) const;
  void fill1D(SG::StoreGate *store, const std::string &subDir, const std::string &name,
              float value, float weight = 1.0f) const;
  void fill2D(SG::StoreGate *store, const std::string &subDir, const std::string &name,
              float xval, float yval, float weight = 1.0f) const;

  std::string m_histDir;
  std::string m_eventInfoKey;
  std::string m_clusterKey;
  std::string m_electronKey;
  std::string m_ringsKey;
  std::vector<std::string> m_ringsKeys;
  int m_outputLevel;
};

} // namespace Gaugi

using EgammaMonitoringMaker = Gaugi::EgammaMonitoringMaker;

#endif
