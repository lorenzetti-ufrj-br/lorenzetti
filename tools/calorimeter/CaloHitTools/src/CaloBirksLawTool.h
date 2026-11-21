#ifndef CaloBirksLawTool_h
#define CaloBirksLawTool_h

#include "CaloHitBuilder/ICaloEnergyModifierTool.h"

class CaloBirksLawTool : public ICaloEnergyModifierTool {
public:
  CaloBirksLawTool( std::string name = "CaloBirksLawTool" );
  virtual ~CaloBirksLawTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual float modifyEnergy( const G4Step *step, CellIdentification &cell, float currentEnergy ) const override;

private:
  double m_birksLArK = 0.05832;
};

#endif
