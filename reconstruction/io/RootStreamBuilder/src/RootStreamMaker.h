#ifndef RootStreamMaker_h
#define RootStreamMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "IBranchHandler.h"
#include "TFile.h"
#include "TTree.h"
#include <string>
#include <vector>
#include <memory>

/**
 * @class RootStreamMaker
 * @brief Generic, item-list driven ROOT stream maker for all Lorenzetti data tiers.
 * 
 * Configured with an ItemList (e.g., ["CaloClusterContainer#CaloClusters", "ElectronContainer#Electrons"]),
 * dynamically initializes branches and streams containers into a persistent ROOT TTree.
 */
class RootStreamMaker : public Gaugi::Algorithm {
public:
  RootStreamMaker(std::string name);
  virtual ~RootStreamMaker();

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

private:
  std::vector<std::unique_ptr<Gaugi::IBranchHandler>> createHandlers() const;

  std::string m_ntupleName;
  std::string m_outputFile;
  std::vector<std::string> m_itemList;
  int m_outputLevel;
  bool m_onlyRoI;
  float m_etaWindow;
  float m_phiWindow;
  std::string m_truthKey;
  std::vector<int> m_cellHashes;
};

#endif
