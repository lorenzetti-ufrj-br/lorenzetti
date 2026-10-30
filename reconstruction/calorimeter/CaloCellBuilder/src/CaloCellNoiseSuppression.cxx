#include "CaloCellNoiseSuppression.h"
#include "CaloCell/CaloCellContainer.h"
#include "CaloCell/CaloCell.h"
#include "CaloCell/CaloDetDescriptor.h"
#include "GaugiKernel/DataHandle.h"
#include <memory>

using namespace Gaugi;

CaloCellNoiseSuppression::CaloCellNoiseSuppression(std::string name)
  : IMsgService(name),
    Algorithm(),
    m_inputCellsKey("Cells_original"),
    m_outputCellsKey("Cells"),
    m_sigmaThreshold(2.0f),
    m_outputLevel(1)
{
  declareProperty("InputCellsKey",   m_inputCellsKey);
  declareProperty("OutputCellsKey",  m_outputCellsKey);
  declareProperty("SigmaThreshold",  m_sigmaThreshold);
  declareProperty("OutputLevel",     m_outputLevel);
}

StatusCode CaloCellNoiseSuppression::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);
  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::finalize()
{
  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::bookHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::pre_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::execute(SG::EventContext &ctx, int /*evt*/) const
{
  return post_execute(ctx);
}

StatusCode CaloCellNoiseSuppression::post_execute(SG::EventContext &ctx) const
{
  SG::ReadHandle<xAOD::CaloCellContainer> inCells(m_inputCellsKey, ctx);
  if (!inCells.isValid()) {
    MSG_ERROR("Cannot read input CaloCellContainer with key '" << m_inputCellsKey << "'");
    return StatusCode::FAILURE;
  }

  SG::WriteHandle<xAOD::CaloCellContainer> outCells(m_outputCellsKey, ctx);
  outCells.record(std::make_unique<xAOD::CaloCellContainer>());

  uint32_t passed = 0;
  for (const auto cell : *inCells) {
    if (!cell) continue;

    const auto *desc = cell->descriptor();
    float sigma = desc ? desc->sigma() : 0.0f;
    float threshold = (sigma > 0.0f) ? (m_sigmaThreshold * sigma) : 0.0f;

    if (cell->e() > threshold) {
      auto new_cell = new xAOD::CaloCell(*cell);
      outCells->push_back(new_cell);
      passed++;
    }
  }

  MSG_DEBUG("CaloCellNoiseSuppression: input cells = " << inCells->size() << ", passed (" 
            << m_sigmaThreshold << "*sigma) = " << passed << " recorded into '" << m_outputCellsKey << "'");

  return StatusCode::SUCCESS;
}

StatusCode CaloCellNoiseSuppression::fillHistograms(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}
