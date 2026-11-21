#ifndef EgammaMonitoringMaker_h
#define EgammaMonitoringMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "GaugiKernel/DataHandle.h"

#include <memory>
#include <string>
#include <map>

class TFile;
class TH1F;
class TH2F;

namespace Gaugi {

/**
 * @class EgammaMonitoringMaker
 * @brief Expert monitoring algorithm for calorimeter and e/gamma physics objects.
 *
 * Runs at the end of the reconstruction pipeline (AOD step) and produces a
 * dedicated ROOT file (default: expert_monitoring.root) containing data quality
 * validation distributions (kinematics, shower shapes, cluster moments, PID, and rings).
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

  const std::string& outputFile() const { return m_outputFile; }
  const std::string& directory() const { return m_histDir; }

private:
  void bookAll() const;
  TDirectory* getOrCreateDir(const std::string &subDir) const;
  void book1D(const std::string &subDir, const std::string &name, const std::string &title,
              int nbins, float xmin, float xmax) const;
  void book2D(const std::string &subDir, const std::string &name, const std::string &title,
              int nbinsX, float xmin, float xmax, int nbinsY, float ymin, float ymax) const;
  void fill1D(const std::string &key, float value, float weight = 1.0) const;
  void fill2D(const std::string &key, float xval, float yval, float weight = 1.0) const;

  std::string m_outputFile;
  std::string m_histDir;
  std::string m_eventInfoKey;
  std::string m_clusterKey;
  std::string m_electronKey;
  std::string m_ringsKey;
  int m_outputLevel;

  mutable std::unique_ptr<TFile> m_file;
  mutable bool m_isBooked;
  mutable std::map<std::string, TH1F*> m_hists1D;
  mutable std::map<std::string, TH2F*> m_hists2D;
};

} // namespace Gaugi

using EgammaMonitoringMaker = Gaugi::EgammaMonitoringMaker;

#endif
