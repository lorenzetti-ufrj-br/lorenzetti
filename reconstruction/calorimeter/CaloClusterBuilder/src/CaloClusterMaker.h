#ifndef CaloClusterMaker_h
#define CaloClusterMaker_h

#include "CaloCell/enumeration.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/Tool.h"
#include "CaloCell/CaloCellContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "EventInfo/SeedContainer.h"
#include <string>
#include <vector>

/**
 * @class CaloClusterMaker
 * @brief Reconstruction algorithm to perform Seeded-Clustering.
 * 
 * Uses a seed-based approach to group calorimeter cells into clusters.
 * It identifies the highest energy cell (seed) and aggregates surrounding cells
 * within a defined window, delegating shower shape and moments calculations to pluggable tools.
 */
class CaloClusterMaker : public Gaugi::Algorithm {
public:
  /** Constructor **/
  CaloClusterMaker(std::string name);
  
  /** Destructor **/
  virtual ~CaloClusterMaker();
  
  /*! Initialize the algorithm **/
  virtual StatusCode initialize() override;

  /*! Book histograms into the current StoreGate **/
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  
  /*! Execute in step action (no-op for cluster maker) **/
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  
  /*! Execute in ComponentAccumulator **/
  virtual StatusCode execute(SG::EventContext &ctx, int /*evt*/) const override;
  
  /*! Execute before step action **/
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;

  /*! Execute after step action / event clustering loop **/
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  
  /*! Fill histograms in the end **/
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  
  /*! Finalize the algorithm **/
  virtual StatusCode finalize() override;

  /** Add tool to cluster processing **/
  void addTool(Gaugi::Tool *tool) {
    m_tools.push_back(tool);
  }

  void push_back(Gaugi::Tool *tool) {
    m_tools.push_back(tool);
  }

  const std::vector<Gaugi::Tool*>& tools() const {
    return m_tools;
  }

private:
  void fillCluster(SG::EventContext &ctx, xAOD::CaloCluster *clus, const std::string &key) const;
  float dR(float eta1, float phi1, float eta2, float phi2) const;

  // Input keys
  std::string m_cellsKey; 
  std::string m_seedKey;

  // Output keys
  std::string m_clusterKey;

  float m_etaWindow;
  float m_phiWindow;
  std::string m_histPath;

  // Tools executed on each reconstructed cluster
  std::vector<Gaugi::Tool*> m_tools;

  float m_minCenterEnergy;
};

#endif
