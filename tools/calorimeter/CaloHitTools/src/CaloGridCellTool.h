#ifndef CaloGridCellTool_h
#define CaloGridCellTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>

class CaloGridCellTool : public ICaloCellIdentifierTool {
public:
  CaloGridCellTool( std::string name = "CaloGridCellTool" );
  virtual ~CaloGridCellTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  int find( const std::vector<float> &vec, float value ) const;
  int findPhi( float phi ) const;
  unsigned long int hash( unsigned bin ) const;

private:
  std::vector<float> m_etaBins;
  std::vector<float> m_phiBins;
  unsigned int m_nEtaBins = 0;
  unsigned int m_nPhiBins = 0;
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
};

#endif
