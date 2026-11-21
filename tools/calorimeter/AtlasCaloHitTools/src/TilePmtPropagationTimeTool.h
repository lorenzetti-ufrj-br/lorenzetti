#ifndef TilePmtPropagationTimeTool_h
#define TilePmtPropagationTimeTool_h

#include "CaloHitBuilder/ICaloTimeCorrectionTool.h"
#include <vector>

class TilePmtPropagationTimeTool : public ICaloTimeCorrectionTool {
public:
  TilePmtPropagationTimeTool( std::string name = "TilePmtPropagationTimeTool" );
  virtual ~TilePmtPropagationTimeTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual CellTiming computeTime( const G4Step *step, const CellIdentification &cell ) const override;

  void tileTime( const G4Step *step, int cell, int phiBin, int npmt, double &tglobal, double &t, double &dtUp, double &dtDown ) const;

private:
  std::vector<float> m_phiBins;
  std::vector<float> m_cellRCentre;
  std::vector<float> m_cellZCentre;
  float m_replaceRCentre = 0.0f;
  float m_replaceZCentre = 0.0f;
};

#endif
