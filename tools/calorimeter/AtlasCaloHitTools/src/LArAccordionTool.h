#ifndef LArAccordionTool_h
#define LArAccordionTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>

class LArAccordionTool : public ICaloCellIdentifierTool {
public:
  LArAccordionTool( std::string name = "LArAccordionTool" );
  virtual ~LArAccordionTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  int embSampSeg( double x, double y, double z, int &iregion, int &isampling, int &ieta ) const;
  int embFindCell( double x, double y, double z ) const;
  int psbGapCell( double x, double y, double z ) const;
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

  int m_embMode = 0;
  int m_embSampling = 0;
  int m_embRegion = 0;
  float m_embZShift = 0.0f;
  float m_psbR0 = 0.0f;
  bool m_embSampSeg = false;

  int m_atlasBarrelEc = 0;
  int m_atlasLArSampling = 0;
  int m_atlasLArRegion = 0;
  std::vector<int> m_cellAtlasEtaIndex;
  float m_phiShift = 0.0f;
};

#endif
