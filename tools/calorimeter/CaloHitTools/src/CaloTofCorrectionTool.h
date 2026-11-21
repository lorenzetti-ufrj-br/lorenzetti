#ifndef CaloTofCorrectionTool_h
#define CaloTofCorrectionTool_h

#include "CaloHitBuilder/ICaloTimeCorrectionTool.h"

class CaloTofCorrectionTool : public ICaloTimeCorrectionTool {
public:
  CaloTofCorrectionTool( std::string name = "CaloTofCorrectionTool" );
  virtual ~CaloTofCorrectionTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual CellTiming computeTime( const G4Step *step, const CellIdentification &cell ) const override;

private:
  bool m_applyTof = true;
};

#endif
