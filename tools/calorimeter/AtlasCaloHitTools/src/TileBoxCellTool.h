#ifndef TileBoxCellTool_h
#define TileBoxCellTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>

class TileBoxCellTool : public ICaloCellIdentifierTool {
public:
  TileBoxCellTool( std::string name = "TileBoxCellTool" );
  virtual ~TileBoxCellTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  int findCell( float radius, float z ) const;
  int find( const std::vector<float> &vec, float value ) const;
  int findPhi( float phi ) const;
  unsigned long int hash( unsigned bin ) const;
  int tileNPmt( int cell, int phiBin ) const;

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
  int m_tileDualReadout = 0;

  std::vector<float> m_phiBins;
  unsigned int m_nPhiBins = 0;

  std::vector<float> m_cellEta;
  std::vector<float> m_cellDeltaEta;
  std::vector<float> m_cellBoxRMin;
  std::vector<float> m_cellBoxRMax;
  std::vector<float> m_cellBoxZMin;
  std::vector<float> m_cellBoxZMax;
  std::vector<int>   m_cellBoxIndex;

  std::vector<int>   m_cellNPmt;
  std::vector<int>   m_specialModule;
  std::vector<int>   m_specialNPmt;

  int m_replaceSection = 0;
  int m_replaceTower = 0;
  int m_replaceSampling = 0;
  float m_replaceRCentre = 0.0f;
  float m_replaceZCentre = 0.0f;
  std::string m_replaceCollectionKey = "";
  int m_replaceHashBase = 0;

  std::vector<int>   m_cellAtlasSection;
  std::vector<int>   m_cellAtlasTower;
  std::vector<int>   m_cellAtlasSampling;
  std::vector<float> m_cellRCentre;
  std::vector<float> m_cellZCentre;
};

#endif
