#ifndef CaloHitMerge_h
#define CaloHitMerge_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include "CaloHit/CaloHit.h"
#include <vector>
#include <string>

/**
 * @class CaloHitMerge
 * @brief Algorithm to merge individual calorimeter sampling hit collections into a master container.
 * 
 * Aggregates separate xAOD::CaloHitCollection maps from different detector regions/samplings
 * into a single unified xAOD::CaloHitContainer (DataVector).
 * Optionally filters out empty hits (energy <= minEnergy) to optimize memory and disk usage.
 */
class CaloHitMerge : public Gaugi::Algorithm {
public:
  /** Constructor **/
  CaloHitMerge(std::string name);

  /** Destructor **/
  virtual ~CaloHitMerge() = default;
  
  /*! Initialize the algorithm **/
  virtual StatusCode initialize() override;

  /*! Book histograms into the current StoreGate **/
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;

  /*! Execute during Geant4 step action (no-op for merge) **/
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;

  /*! Execute in ComponentAccumulator event loop **/
  virtual StatusCode execute(SG::EventContext &ctx, int /*evt*/) const override;

  /*! Execute before step action **/
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;

  /*! Execute after step action / event simulation **/ 
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;

  /*! Fill histograms **/
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;

  /*! Finalize the algorithm **/ 
  virtual StatusCode finalize() override;

private:
  /*! Input collection keys to merge */
  std::vector<std::string> m_collectionKeys;

  /*! Output master CaloHitContainer key */
  std::string m_hitsKey;

  /*! Filter out empty hits with edep <= m_minEnergy */
  bool m_filterEmptyHits;

  /*! Minimum energy threshold for hit retention when filtering is active (in MeV) */
  float m_minEnergy;

  /*! Filter hits within Region of Interest (RoI) around truth particles */
  bool m_onlyRoI;

  /*! RoI window size in eta */
  float m_etaWindow;

  /*! RoI window size in phi */
  float m_phiWindow;

  /*! Input truth particle container key */
  std::string m_truthKey;

  /*! Specific cell hashes to always keep even if outside RoI */
  std::vector<int> m_cellHashes;
};

#endif
