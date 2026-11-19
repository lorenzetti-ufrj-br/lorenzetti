#ifndef CaloHitMaker_h
#define CaloHitMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/Tool.h"
#include "CaloHit/CaloHit.h"
#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include "CaloHitBuilder/ICaloEnergyModifierTool.h"
#include "CaloHitBuilder/ICaloTimeCorrectionTool.h"
#include "CaloHitBuilder/ICaloHitRecorderTool.h"
#include "CaloHitBuilder/CaloHitTypes.h"
#include <string>
#include <vector>

/**
 * @class CaloHitMaker
 * @brief Pure, generic orchestrator algorithm to build calorimeter hits during simulation.
 *
 * Delegates cell identification, energy modification, time correction, and hit recording
 * entirely to pluggable Gaugi::Tool components.
 */
class CaloHitMaker : public Gaugi::Algorithm {
public:
  CaloHitMaker( std::string name = "CaloHitMaker" );
  virtual ~CaloHitMaker() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
  virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
  virtual StatusCode execute( SG::EventContext &ctx, const G4Step *step ) const override;
  virtual StatusCode execute( SG::EventContext &ctx, int evt ) const override;
  virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
  virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
  virtual StatusCode finalize() override;

private:
  bool passFilter( const G4Step *step ) const;

  std::string m_collectionKey = "Hits";
  float m_noiseStd = 0.0f;
  bool  m_detailedHistograms = false;
  std::string m_histPath = "Expert";
  bool  m_activeEnergyOnly = false;
  float m_rMin = 0.0f;
  float m_rMax = 0.0f;
  float m_zMin = 0.0f;
  float m_zMax = 0.0f;

  Gaugi::Tool*               m_cellIdentifier = nullptr;
  std::vector<Gaugi::Tool*>  m_energyModifiers;
  Gaugi::Tool*               m_timeCorrection = nullptr;
  std::vector<Gaugi::Tool*>  m_hitRecorders;
};

#endif
