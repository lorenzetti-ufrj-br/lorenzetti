#ifndef CaloCellMerge_h
#define CaloCellMerge_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include "CaloCell/CaloCell.h"
#include "CaloCell/CaloDetDescriptor.h"
#include "CaloCell/CaloDetDescriptorContainer.h"
#include <vector>
#include <string>

/**
 * @class CaloCellMerge
 * @brief Algorithm to merge multiple sampling CaloDetDescriptor collections into global CaloCellContainers and master CaloDetDescriptorContainer.
 * 
 * Collects descriptors and cells from different calorimeter samplings (created by separate
 * CaloCellMaker instances) and merges them into a unified CaloDetDescriptorContainer (DataVector),
 * a global reconstructed CaloCellContainer, and a truth CaloCellContainer, binding relational
 * ElementLinks from cells to the master descriptor container.
 */
class CaloCellMerge : public Gaugi::Algorithm {
public:
  /** Constructor **/
  CaloCellMerge(std::string name);

  /** Destructor **/
  virtual ~CaloCellMerge() = default;
  
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

  /*! Execute after step action / digitization **/ 
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;

  /*! Fill histograms **/
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;

  /*! Finalize the algorithm **/ 
  virtual StatusCode finalize() override;

private:
  /*! Input collection keys to merge */
  std::vector<std::string> m_collectionKeys;

  /*! Output CaloCellContainer key for reconstructed cells */
  std::string m_cellsKey;

  /*! Output CaloCellContainer key for truth cells */
  std::string m_truthCellsKey;

  /*! Output master CaloDetDescriptorContainer key */
  std::string m_descriptorsKey;

  /*! Filter cells with energy <= m_sigmaThreshold * sigma */
  bool m_filterBySigma;

  /*! Multiplier threshold for noise sigma cut (reco energy > m_sigmaThreshold * sigma) */
  float m_sigmaThreshold;

  /*! hits of the event (empty: no check): the hits with energy and no cell are counted and reported */
  std::string m_hitsKey;
};

#endif
