#ifndef LArEmecCompartmentTool_h
#define LArEmecCompartmentTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>

class LArEmecCompartmentTool : public ICaloCellIdentifierTool {
public:
  LArEmecCompartmentTool( std::string name = "LArEmecCompartmentTool" );
  virtual ~LArEmecCompartmentTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  int emecFindCell( double x, double y, double z, int &etaBin, int &phiBin ) const;
  unsigned long int hash( unsigned bin ) const;

private:
  int m_sampling = 0;
  int m_segment = 0;
  int m_detector = 0;
  float m_zMin = 0.0f;
  float m_zMax = 0.0f;
  float m_rMin = 0.0f;
  float m_rMax = 0.0f;
  bool m_activeEnergyOnly = false;
  float m_bc_duration = 25.0f;
  int m_bcid_start = -7;
  int m_bcid_end = 7;

  std::vector<float> m_phiBins;
  unsigned int m_nPhiBins = 0;

  std::vector<float> m_cellEta;
  std::vector<float> m_cellDeltaEta;

  int m_emecCompartment = 0;
  float m_emecEtaScale = 0.0f;
  float m_emecEtaOffset = 0.0f;
  int m_emecMaxEta = 0;
  float m_emecFocalShift = 0.0f;
  std::vector<int> m_emecZSep12;
  std::vector<int> m_emecZSep23;
  std::vector<int> m_emecZInner;
  std::vector<float> m_emecWheelRMin;
  std::vector<float> m_emecWheelRMax;
  std::vector<float> m_emecWheelZMin;
  std::vector<float> m_emecWheelZMax;

  int m_atlasBarrelEc = 0;
  int m_atlasLArSampling = 0;
  int m_atlasLArRegion = 0;
  std::vector<int> m_cellAtlasEtaIndex;
  float m_phiShift = 0.0f;
};

#endif
