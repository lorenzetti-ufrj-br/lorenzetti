#ifndef CaloFreeRunningHitRecorderTool_h
#define CaloFreeRunningHitRecorderTool_h

#include "CaloHitBuilder/ICaloHitRecorderTool.h"
#include <string>
#include <vector>

class CaloFreeRunningHitList;

class CaloFreeRunningHitRecorderTool : public ICaloHitRecorderTool {
public:
  CaloFreeRunningHitRecorderTool( std::string name = "CaloFreeRunningHitRecorderTool" );
  virtual ~CaloFreeRunningHitRecorderTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  virtual StatusCode record( SG::EventContext &ctx, const G4Step *step,
                             const CellIdentification &cell, float energy,
                             const CellTiming &timing ) const override;

private:
  void fillTile( const CaloFreeRunningHitList *list, const G4Step *step,
                 const CellIdentification &cell, float energy, const CellTiming &timing ) const;
  void fillLAr( const CaloFreeRunningHitList *list, const G4Step *step,
                const CellIdentification &cell, float energy, const CellTiming &timing ) const;

  std::string m_listKey = "FreeRunningHits";
  bool m_binning = true;
  int  m_subdet = 0; // 0=Tile, 1=EMB, 2=EMEC, 3=HEC, 4=FCAL
  int  m_atlasBarrelEc = 1;
  int  m_atlasLArSampling = 0;
  int  m_atlasLArRegion = 0;
  int  m_atlasLArPart = 1;

  std::vector<int>   m_cellAtlasEtaIndex;
  int                m_nPhiBins = 64;
  std::vector<float> m_phiBins;
  std::vector<float> m_cellEta;

  std::vector<int>   m_cellAtlasSection;
  std::vector<int>   m_cellAtlasTower;
  std::vector<int>   m_cellAtlasSampling;
  std::vector<float> m_cellRCentre;
  std::vector<float> m_cellZCentre;
  int                m_replaceSection = 0;
  int                m_replaceTower = 0;
  int                m_replaceSampling = 0;
  float              m_replaceRCentre = 0.0f;
  float              m_replaceZCentre = 0.0f;

  int                m_fcalModule = 0;
  std::vector<int>   m_fcalCopyEtaIndex;
  std::vector<int>   m_fcalCopyPhiIndex;
  std::vector<float> m_fcalCopyEta;
  std::vector<float> m_fcalCopyPhi;
};

#endif
