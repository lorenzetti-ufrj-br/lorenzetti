#ifndef ICaloEnergyModifierTool_h
#define ICaloEnergyModifierTool_h

#include "GaugiKernel/Tool.h"
#include "CaloHitBuilder/CaloHitTypes.h"

class G4Step;

class ICaloEnergyModifierTool : public Gaugi::Tool {
public:
  ICaloEnergyModifierTool( std::string name = "ICaloEnergyModifierTool" ) : IMsgService(name), Tool() {}
  virtual ~ICaloEnergyModifierTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }
  virtual StatusCode execute( SG::EventContext &, Gaugi::EDM * ) const override { return StatusCode::SUCCESS; }

  virtual float modifyEnergy( const G4Step *step, CellIdentification &cell, float currentEnergy ) const = 0;
};

#endif
