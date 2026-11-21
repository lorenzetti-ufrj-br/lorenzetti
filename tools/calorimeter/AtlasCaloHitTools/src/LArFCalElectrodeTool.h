#ifndef LArFCalElectrodeTool_h
#define LArFCalElectrodeTool_h

#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include <vector>
#include <string>
#include <map>

class LArFCalElectrodeTool : public ICaloCellIdentifierTool {
public:
  LArFCalElectrodeTool( std::string name = "LArFCalElectrodeTool" );
  virtual ~LArFCalElectrodeTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const override;
  virtual CellIdentification identify( const G4Step *step ) const override;

  bool isShowerSpot( const G4Step *step ) const;
  bool fcalTileID( double x, double y, int &eta, int &phi ) const;
  unsigned long int hash( unsigned bin ) const;

private:
  int m_fcalModule = 0;
  int m_fcalSide = 1;
  std::string m_fcalGapVolume = "";
  std::vector<int>   m_fcalCopyEtaIndex;
  std::vector<int>   m_fcalCopyPhiIndex;
  std::vector<float> m_fcalCopyEta;
  std::vector<float> m_fcalCopyPhi;
  std::vector<float> m_fcalCopyDeltaEta;
  std::vector<float> m_fcalCopyDeltaPhi;

  std::vector<int>   m_fcalCopyI;
  std::vector<int>   m_fcalCopyJ;
  std::vector<float> m_fcalCopyX;
  std::vector<float> m_fcalCopyY;

  bool m_activeEnergyOnly = false;
  float m_bc_duration = 25.0f;
  int m_bcid_start = -7;
  int m_bcid_end = 7;
  int m_sampling = 0;
  int m_detector = 0;
  int m_segment = 0;
  double m_zMin = 0.0;
  double m_zMax = 0.0;

  std::map<std::pair<int,int>, std::pair<float,float>> m_fcalTileCentre;
  std::map<std::pair<int,int>, std::pair<float,float>> m_fcalTileWidth;
  std::map<unsigned int, std::pair<int,int>> m_fcalTubeMap;
  unsigned int m_fcalFirstTube = 0;
  double m_fcalFirstTubeX = 0.0;
  double m_fcalFirstTubeY = 0.0;
};

#endif
