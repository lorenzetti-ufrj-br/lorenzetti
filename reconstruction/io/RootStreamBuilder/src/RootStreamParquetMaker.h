#ifndef RootStreamParquetMaker_h
#define RootStreamParquetMaker_h

#include "GaugiKernel/Algorithm.h"
#include <string>
#include <vector>
#include <memory>

/**
 * @class RootStreamParquetMaker
 * @brief Algorithm to dump analysis-level variables into an Apache Parquet file.
 *
 * Reads reconstructed objects (Clusters, Rings, Electrons) and truth info
 * and writes them into a columnar Parquet file using Apache Arrow.
 */
class RootStreamParquetMaker : public Gaugi::Algorithm
{
public:
  /** Constructor **/
  RootStreamParquetMaker(std::string name);

  virtual ~RootStreamParquetMaker();

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

private:
  struct Impl;
  std::unique_ptr<Impl> m_impl;

  std::string m_outputFile;
  std::string m_seedsKey;
  std::string m_eventKey;
  std::string m_truthKey;
  std::string m_clusterKey;
  std::string m_electronKey;
  std::string m_ringerL0Key;
  std::string m_truthClusterKey;
  std::string m_truthElectronKey;

  std::vector<std::string> m_ringerKeys;
  std::vector<std::string> m_truthRingerKeys;

  int m_outputLevel;
};

#endif
