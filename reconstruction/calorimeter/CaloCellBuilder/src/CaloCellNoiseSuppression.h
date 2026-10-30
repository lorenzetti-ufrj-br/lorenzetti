#ifndef CaloCellNoiseSuppression_h
#define CaloCellNoiseSuppression_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include <string>

/**
 * @class CaloCellNoiseSuppression
 * @brief Algorithm to filter calorimeter cells based on noise sigma threshold.
 * 
 * In ATLAS Run 4 / HL-LHC workflows, cells can be filtered online or offline based
 * on a configurable noise cut: E > threshold * sigma, where sigma is retrieved
 * from the cell's CaloDetDescriptor.
 */
class CaloCellNoiseSuppression : public Gaugi::Algorithm {
public:
  CaloCellNoiseSuppression(std::string name);
  virtual ~CaloCellNoiseSuppression() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;

private:
  std::string m_inputCellsKey;
  std::string m_outputCellsKey;
  float m_sigmaThreshold;
  int m_outputLevel;
};

// Aliases for alternate spelling and backward compatibility
using CaloCellNoiseSupression = CaloCellNoiseSuppression;
using CaloCellFilter = CaloCellNoiseSuppression;

#endif
