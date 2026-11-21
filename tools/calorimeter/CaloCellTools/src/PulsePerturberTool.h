#ifndef PulsePerturberTool_h
#define PulsePerturberTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include "GaugiKernel/StatusCode.h"
#include "TRandom3.h"
#include <vector>
#include <string>

/**
 * @class PulsePerturberTool
 * @brief Tool to inject anomalies and defects into the calorimeter simulation.
 *
 * This tool can simulate dead modules or add extra noise to specific cells
 * to mimic realistic detector conditions.
 */
class PulsePerturberTool : public Gaugi::Tool {

public:
  /** Constructor **/
  PulsePerturberTool(std::string name);
  virtual ~PulsePerturberTool();

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  /**
   * @brief Apply anomalies to the current cell.
   * @param ctx Event context.
   * @param edm Pointer to the CaloDetDescriptor (cell).
   */
  virtual StatusCode execute(SG::EventContext &ctx,
                             Gaugi::EDM *edm) const override;

private:
  void AddGaussianNoise(std::vector<float> &pulse, float noiseMean,
                        float noiseStddev) const;

  float m_noiseMean;
  float m_noiseStd;
  std::vector<bool> m_deadModules;
  std::vector<std::vector<int>> m_cells;
  std::vector<std::vector<int>> m_eventNumberRange;
  std::vector<float> m_noiseStdFactor;

  std::string m_inputEventKey;
  int m_outputLevel;
  mutable TRandom3 m_rng;
};

using PulsePerturber = PulsePerturberTool;
using PulsePertuberTool = PulsePerturberTool;
using PulsePertuber = PulsePerturberTool;

#endif
