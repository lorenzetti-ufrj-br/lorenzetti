#ifndef TileDualReadoutSplitTool_h
#define TileDualReadoutSplitTool_h

#include "CaloHitBuilder/ICaloEnergyModifierTool.h"
#include <vector>

class TileDualReadoutSplitTool : public ICaloEnergyModifierTool {
public:
  TileDualReadoutSplitTool( std::string name = "TileDualReadoutSplitTool" );
  virtual ~TileDualReadoutSplitTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual float modifyEnergy( const G4Step *step, CellIdentification &cell, float currentEnergy ) const override;

  void tilePmtWeights( float phiLocal, float z, float &w0, float &w1, bool replaced ) const;

private:
  int m_tileDualReadout = 1;
  int m_sampling = 0;
  std::vector<float> m_phiBins;
  int m_uShapePart = -1;
  int m_uShapeLayer = -1;
};

#endif
