#ifndef PulsePerturber_h
#define PulsePerturber_h

#include "GaugiKernel/AlgTool.h"
#include "GaugiKernel/EDM.h"
#include "GaugiKernel/StatusCode.h"
#include "TRandom3.h"

/**
 * @class PulsePerturber
 * @brief Tool to inject anomalies and defects into the calorimeter simulation.
 *
 * This tool can simulate dead modules or add extra noise to specific cells
 * to mimic realistic detector conditions.
 */
class PulsePerturber : public Gaugi::AlgTool {

public:
  /** Constructor **/
  PulsePerturber(std::string name);
  virtual ~PulsePerturber();

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
  /*! Output level message */
  int m_outputLevel;
  /*! Random generator */
  mutable TRandom3 m_rng;
};

#endif
