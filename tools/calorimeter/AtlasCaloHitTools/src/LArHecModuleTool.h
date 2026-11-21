#ifndef LArHecModuleTool_h
#define LArHecModuleTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>

class LArHecModuleTool : public ICaloCellIdentifierTool {
public:
  LArHecModuleTool( std::string name = "LArHecModuleTool" );
  virtual ~LArHecModuleTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  int findCell( float radius, float z ) const;
  float cellRadius( float radius, float phi ) const;
  int find( const std::vector<float> &vec, float value ) const;
  int findPhi( float phi ) const;
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
  std::vector<float> m_cellBoxRMin;
  std::vector<float> m_cellBoxRMax;
  std::vector<float> m_cellBoxZMin;
  std::vector<float> m_cellBoxZMax;
  std::vector<int>   m_cellBoxIndex;
  int m_cellRadiusModules = 32;

  int m_atlasBarrelEc = 0;
  int m_atlasLArSampling = 0;
  int m_atlasLArRegion = 0;
  std::vector<int> m_cellAtlasEtaIndex;
  float m_phiShift = 0.0f;
};

#endif
