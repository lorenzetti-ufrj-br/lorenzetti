#include "PulsePerturberTool.h"
#include "CaloCell/CaloDetDescriptor.h"
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/EventInfoConverter.h"
#include "Randomize.hh"
#include "TRandom.h"
#include <algorithm>

using namespace Gaugi;

PulsePerturberTool::PulsePerturberTool(std::string name)
    : IMsgService(name), Tool(), m_rng(0) {
  declareProperty("DeadModules", m_deadModules = {});
  declareProperty("Cells", m_cells = {});
  declareProperty("NoiseMean", m_noiseMean = 0);
  declareProperty("NoiseStd", m_noiseStd = 0);
  declareProperty("NoiseStdFactor", m_noiseStdFactor = {});
  declareProperty("EventNumberRange", m_eventNumberRange = {});
  declareProperty("InputEventKey", m_inputEventKey = "EventInfo");
  declareProperty("OutputLevel", m_outputLevel = 1);
}

PulsePerturberTool::~PulsePerturberTool() { ; }

StatusCode PulsePerturberTool::initialize() {
  setMsgLevel((MSG::Level)m_outputLevel);
  MSG_INFO("artificial anomalies will be applied to some cell signals");
  return StatusCode::SUCCESS;
}

StatusCode PulsePerturberTool::finalize() { return StatusCode::SUCCESS; }

StatusCode PulsePerturberTool::execute(SG::EventContext &ctx,
                                       Gaugi::EDM *edm) const {
  auto *cell = static_cast<xAOD::CaloDetDescriptor *>(edm);
  auto pulse_sum = cell->pulse();
  auto pulse_size = pulse_sum.size();

  SG::ReadHandle<xAOD::EventInfoContainer> event(m_inputEventKey, ctx);
  if (!event.isValid()) {
    MSG_FATAL("It's not possible to read the xAOD::EventInfoContainer from "
              "this Context");
  }
  auto const_evt = (**event.ptr()).front();
  auto eventNumber = const_evt->eventNumber();

  for (std::size_t block = 0; block < m_eventNumberRange.size(); ++block) {

    if ((eventNumber >= m_eventNumberRange[block][0]) &&
        (eventNumber <= m_eventNumberRange[block][1])) {
      unsigned long int id =
          m_deadModules[block]
              ? static_cast<unsigned long int>(cell->hash() / 1e7)
              : cell->hash();
      bool found = std::find(m_cells[block].begin(), m_cells[block].end(),
                             id) != m_cells[block].end();
      if (found) {

        if (m_deadModules[block]) {
          MSG_INFO("perturbed event: " << eventNumber);
          MSG_INFO("simulating dead cell, setting pulse to zero");
          pulse_sum.assign(pulse_size, 0.0);
          cell->edep(0, 0.0);
          cell->setE(0.0);
          MSG_INFO("pulse sum after noise: " << pulse_sum);
          MSG_INFO("cell energy after noise: " << cell->e());

        } else {
          MSG_INFO("perturbed event: " << eventNumber);
          MSG_INFO("events concerned by noise: " << m_eventNumberRange[block]);
          MSG_INFO("increasing noise for cell with hash id: " << cell->hash());
          AddGaussianNoise(pulse_sum, m_noiseMean,
                           m_noiseStdFactor[block] * m_noiseStd);
          MSG_INFO("pulse sum after noise: " << pulse_sum);
          MSG_INFO("cell energy after noise: " << cell->e());
        }

        cell->setAnomalous(true);
        cell->setPulse(pulse_sum);
        break;

      }
    }
  }

  return StatusCode::SUCCESS;
}

void PulsePerturberTool::AddGaussianNoise(std::vector<float> &pulse,
                                          float noiseMean, float noiseStd) const {
  for (auto &value : pulse)
    value += m_rng.Gaus(noiseMean, noiseStd);
}
