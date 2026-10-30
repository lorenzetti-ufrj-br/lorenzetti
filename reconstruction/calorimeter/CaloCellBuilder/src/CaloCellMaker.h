#ifndef CaloCellMaker_h
#define CaloCellMaker_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include <vector>
#include <string>

/**
 * @class CaloCellMaker
 * @brief Algorithm to build calorimeter cells from hits.
 *
 * This algorithm is responsible for converting simulated hits (energy deposits)
 * into calorimeter cells. It defines the readout geometry and applies the
 * digitization steps (pulse shaping, noise, etc) by scheduling sub-tools.
 */
class CaloCellMaker : public Gaugi::Algorithm {
public:
  /** Constructor **/
  CaloCellMaker(std::string name);

  /** Destructor **/
  virtual ~CaloCellMaker() = default;

  /*! Initialize the algorithm **/
  virtual StatusCode initialize() override;

  /*! Book histograms into the current StoreGate **/
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;

  /*! Execute during Geant4 step action (no-op for cell maker) **/
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;

  /*! Execute in ComponentAccumulator **/
  virtual StatusCode execute(SG::EventContext &ctx, int /*evt*/) const override;

  /*! Execute before step action **/
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;

  /*! Execute after step action (digitization loop) **/
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;

  /*! Fill histograms **/
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;

  /*! Finalize the algorithm **/
  virtual StatusCode finalize() override;

  /**
   * @brief Add a tool to the execution list.
   * @param tool Pointer to the Tool to be added.
   */
  void addTool(Gaugi::Tool *tool) {
    m_toolHandles.push_back(tool);
  }

  /**
   * @brief Set the pulse generator tool.
   * @param tool Pointer to the PulseGenerator tool.
   */
  void setPulseGenerator(Gaugi::Tool *tool) {
    m_pulseGenerator = tool;
  }

private:
  int find(const std::vector<float> &vec, float value) const;
  unsigned long int hash(unsigned bin) const;

  /*! Output collection key */
  std::string m_collectionKey;
  /*! Input hits key */
  std::string m_hitsKey;
  /*! Base histogram path */
  std::string m_histPath;
  /*! Sampling id for this reconstruction */
  int m_sampling;
  /*! Segment index for this sample calorimeter */
  int m_segment;
  /*! Detector id for this sampling*/
  int m_detector;
  /*! The start bunch crossing id for energy estimation */
  int m_bcid_start;
  /*! The end bunch crossing id for energy estimation */
  int m_bcid_end;
  /*! The number of samples per bunch crossing */
  int m_bc_nsamples;
  /*! The time space (in ns) between two bunch crossings */
  float m_bc_duration;

  std::vector<float> m_etaBins;
  std::vector<float> m_phiBins;
  float m_zMin;
  float m_zMax;
  float m_z;

  bool m_detailedHistograms;

  unsigned int m_nEtaBins;
  unsigned int m_nPhiBins;

  /*! Pulse generator */
  Gaugi::Tool *m_pulseGenerator;
  /*! The tool list that will be executed into the post execute step */
  std::vector<Gaugi::Tool *> m_toolHandles;
};

#endif
