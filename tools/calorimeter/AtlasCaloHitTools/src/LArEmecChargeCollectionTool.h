#ifndef LArEmecChargeCollectionTool_h
#define LArEmecChargeCollectionTool_h

#include "CaloHitBuilder/ICaloEnergyModifierTool.h"
#include "CLHEP/Vector/ThreeVector.h"
#include <string>
#include <memory>

namespace LArG4 { namespace EC { class EnergyCalculator; } }

class LArEmecChargeCollectionTool : public ICaloEnergyModifierTool {
public:
  LArEmecChargeCollectionTool( std::string name = "LArEmecChargeCollectionTool" );
  virtual ~LArEmecChargeCollectionTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  virtual float modifyEnergy( const G4Step *step, CellIdentification &cell, float currentEnergy ) const override;

  bool emecChargeEnergy( const G4Step *step, double &energy ) const;
  double emecLArPhiShift( const CLHEP::Hep3Vector &p ) const;
  void emecDiscardCount( bool inner, double energyBefore, bool discarded ) const;

private:
  bool m_emecChargeCollection = true;
  std::string m_emecChargeTables = "";
  std::string m_emecChargeFieldMap = "";
  std::string m_emecChargeHVMap = "";
  int m_emecCompartment = 0;
  float m_emecFocalShift = 0.0f;
  float m_zMin = 0.0f;
  float m_zMax = 0.0f;

  const LArG4::EC::EnergyCalculator *m_emecCalculator = nullptr;
};

#endif
