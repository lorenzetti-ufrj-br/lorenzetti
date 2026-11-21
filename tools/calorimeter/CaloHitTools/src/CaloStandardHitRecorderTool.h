#ifndef CaloStandardHitRecorderTool_h
#define CaloStandardHitRecorderTool_h

#include "CaloHitBuilder/ICaloHitRecorderTool.h"

class CaloStandardHitRecorderTool : public ICaloHitRecorderTool {
public:
  CaloStandardHitRecorderTool( std::string name = "CaloStandardHitRecorderTool" );
  virtual ~CaloStandardHitRecorderTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode record( SG::EventContext &ctx, const G4Step *step,
                             const CellIdentification &cell, float energy,
                             const CellTiming &timing ) const override;

private:
  std::string m_collectionKey = "CaloHitCollection";
  float m_noiseStd = 0.0f;
};

#endif
