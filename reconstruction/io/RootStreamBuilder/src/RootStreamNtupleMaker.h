#ifndef RootStreamNtupleMaker_h
#define RootStreamNtupleMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/BranchSpec.h"
#include "EventInfo/EventInfo.h"
#include "TruthParticle/TruthParticle.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloRings/CaloRings.h"
#include "Egamma/Electron.h"
#include "TTree.h"
#include <string>
#include <vector>
#include <map>

/**
 * @class RootStreamNtupleMaker
 * @brief Algorithm to dump analysis-level variables into a flat Ntuple (TTree).
 *
 * Reads reconstructed objects (Electrons, Clusters, Rings) and truth info
 * and writes them into a flat TTree structure using EDM converters.
 */
class RootStreamNtupleMaker : public Gaugi::Algorithm
{
public:
  /** Constructor **/
  RootStreamNtupleMaker(std::string name);

  virtual ~RootStreamNtupleMaker();

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

private:
  std::string m_seedsKey;
  std::string m_eventKey;
  std::string m_truthKey;
  std::string m_clusterKey;
  std::string m_electronKey;
  std::string m_ringerL0Key;
  std::string m_truthClusterKey;
  std::string m_truthElectronKey;
  std::string m_outputNtupleName;

  std::vector<std::string> m_ringerKeys;
  std::vector<std::string> m_truthRingerKeys;

  std::map<std::string, std::string> m_schema;

  int m_outputLevel;
};

#endif
