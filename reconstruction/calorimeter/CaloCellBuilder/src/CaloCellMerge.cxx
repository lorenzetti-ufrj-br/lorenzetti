#include "CaloCell/CaloCellContainer.h"
#include "CaloCell/CaloDetDescriptorCollection.h"
#include "CaloCell/CaloDetDescriptorContainer.h"
#include "CaloHit/CaloHitContainer.h"
#include <unordered_set>

#include "CaloCellMerge.h"
#include "TVector3.h"
#include <cmath>
#include <cstdlib>

#include "TCanvas.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TH2Poly.h"

using namespace Gaugi;
using namespace SG;

/**
 * @class CaloCellMerge
 * @brief Merges partial calorimeter descriptor collections into unified CaloCellContainers and master CaloDetDescriptorContainer.
 * 
 * Collects descriptors from multiple calorimeter samplings (e.g. EMB1, EMB2, Tile1, etc.)
 * created by separate CaloCellMaker instances, attaches them to a master CaloDetDescriptorContainer (DataVector),
 * creates xAOD::CaloCell objects (truth and reco), sets relational ElementLinks to the master
 * descriptor container, and pushes them into the output containers.
 */
CaloCellMerge::CaloCellMerge(std::string name) : 
  IMsgService(name),
  Algorithm()
{
  declareProperty("InputCollectionKeys", m_collectionKeys = {});
  declareProperty("OutputCellsKey", m_cellsKey = "Cells");
  declareProperty("OutputTruthCellsKey", m_truthCellsKey = "TruthCells");
  declareProperty("OutputDescriptorsKey", m_descriptorsKey = "CaloDetDescriptors");
  declareProperty("FilterBySigma", m_filterBySigma = false);
  declareProperty("SigmaThreshold", m_sigmaThreshold = 2.0);
  declareProperty("InputHitsKey", m_hitsKey = "");
  declareProperty("OutputLevel", m_outputLevel = 1);
}

//!=====================================================================

StatusCode CaloCellMerge::initialize() {
  CHECK_INIT();
  setMsgLevel((MSG::Level)m_outputLevel);
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::finalize() {
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::bookHistograms(SG::EventContext &/*ctx*/) const {
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::pre_execute(EventContext &/*ctx*/) const {
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::execute(EventContext &/*ctx*/, const G4Step * /*step*/) const {
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::execute(EventContext &ctx, int /*evt*/) const {
  return post_execute(ctx);
}

//!=====================================================================

/**
 * @brief Core merge logic.
 * 
 * Iterates through all input collection keys, retrieves each `CaloDetDescriptorCollection`,
 * appends descriptors into the master `CaloDetDescriptorContainer` (DataVector), creates new
 * `xAOD::CaloCell` objects (for both truth and reconstruction), attaches the
 * `ElementLink<CaloDetDescriptor>` referencing the master descriptor container key and index, and stores them.
 */
StatusCode CaloCellMerge::post_execute(EventContext &ctx) const {
  MSG_DEBUG("Starting collection merge algorithm...");

  MSG_DEBUG("Creating master descriptors container with key " << m_descriptorsKey);
  SG::WriteHandle<xAOD::CaloDetDescriptorContainer> descContainer(m_descriptorsKey, ctx);
  descContainer.record(std::unique_ptr<xAOD::CaloDetDescriptorContainer>(new xAOD::CaloDetDescriptorContainer()));

  MSG_DEBUG("Creating reco cells container with key " << m_cellsKey);
  SG::WriteHandle<xAOD::CaloCellContainer> recoContainer(m_cellsKey, ctx);
  recoContainer.record(std::unique_ptr<xAOD::CaloCellContainer>(new xAOD::CaloCellContainer()));
  
  MSG_DEBUG("Creating truth cells container with key " << m_truthCellsKey);
  SG::WriteHandle<xAOD::CaloCellContainer> truthContainer(m_truthCellsKey, ctx);
  truthContainer.record(std::unique_ptr<xAOD::CaloCellContainer>(new xAOD::CaloCellContainer()));

  for (const auto &key : m_collectionKeys) {
    MSG_DEBUG("Reading all cells from collection with key " << key);
    SG::ReadHandle<xAOD::CaloDetDescriptorCollection> collection(key, ctx);
    
    if (!collection.isValid()) {
      MSG_WARNING("It's not possible to read xAOD::CaloDetDescriptorCollection with key: " << key);
      continue;
    }

    MSG_DEBUG("Creating new cells and attaching descriptors to master container"); 
    for (const auto &pair : **collection.ptr()) {
      const xAOD::CaloDetDescriptor *const_descriptor = pair.second;
      if (!const_descriptor) {
        continue;
      }

      float reco_e = const_descriptor->e();
      float truth_e = const_descriptor->edep();

      bool pass_reco = false;
      bool pass_truth = false;

      if (m_filterBySigma) {
        float sigma = const_descriptor->sigma();
        float threshold = (sigma > 0.0f) ? (m_sigmaThreshold * sigma) : 0.0f;
        pass_reco = (reco_e > threshold);
        pass_truth = (truth_e > threshold);
      } else {
        pass_reco = true;
        pass_truth = true;
      }

      if (!pass_reco && !pass_truth) {
        continue;
      }

      // Clone descriptor into a new instance owned by master descContainer (DataVector)
      auto descriptor = new xAOD::CaloDetDescriptor(*const_descriptor);
      uint32_t desc_index = static_cast<uint32_t>(descContainer->size());
      descContainer->push_back(descriptor);
     
      // 1. Create the truth cell (deposited energy from simulation)
      if (pass_truth) {
        auto truth_cell = new xAOD::CaloCell();
        truth_cell->setEta(const_descriptor->eta());
        truth_cell->setPhi(const_descriptor->phi());
        truth_cell->setDeltaEta(const_descriptor->deltaEta());
        truth_cell->setDeltaPhi(const_descriptor->deltaPhi());
        truth_cell->setE(truth_e);
        truth_cell->setEt(truth_cell->e() / std::cosh(truth_cell->eta()));
        truth_cell->setTau(-1.0);
        
        // Set the descriptor ElementLink with master descriptor container key and index
        truth_cell->setDescriptor(m_descriptorsKey, desc_index, descriptor);
        truthContainer->push_back(truth_cell);
      }

      // 2. Create the reconstructed cell (estimated energy from Optimal Filter)
      if (pass_reco) {
        auto cell = new xAOD::CaloCell();
        cell->setEta(const_descriptor->eta());
        cell->setPhi(const_descriptor->phi());
        cell->setDeltaEta(const_descriptor->deltaEta());
        cell->setDeltaPhi(const_descriptor->deltaPhi());
        cell->setE(reco_e);
        cell->setEt(cell->e() / std::cosh(cell->eta()));
        cell->setTau(const_descriptor->tau());

        // Set the descriptor ElementLink with master descriptor container key and index
        cell->setDescriptor(m_descriptorsKey, desc_index, descriptor);
        recoContainer->push_back(cell);
      }
    } // Loop over all descriptors in collection
  } // Loop over all collection keys

  // Hits with energy that no cell received (a hit and a cell are matched only by the hash): before, dropped in silence
  if (!m_hitsKey.empty()) {
    SG::ReadHandle<xAOD::CaloHitContainer> hits(m_hitsKey, ctx);
    if (hits.isValid()) {
      std::unordered_set<unsigned long int> cellHashes;
      for (const auto &key : m_collectionKeys) {
        SG::ReadHandle<xAOD::CaloDetDescriptorCollection> collection(key, ctx);
        if (!collection.isValid()) continue;
        for (const auto &pair : **collection.ptr()) cellHashes.insert(pair.second->hash());
      }
      unsigned nLost = 0; float eLost = 0;
      for (const auto &hit : **hits.ptr()) {
        float e = 0;
        for (int bcid = hit->bcid_start(); bcid <= hit->bcid_end(); ++bcid) e += hit->edep(bcid);
        if (e <= 0) continue;
        if (!cellHashes.count(hit->hash())) { ++nLost; eLost += e; }
      }
      if (nLost > 0) {
        MSG_WARNING(nLost << " hits with energy (" << eLost << " MeV in all) have no cell in the digitization and were dropped: "
                    "use the same geometry options as in the simulation");
      }
    }
  }

  MSG_DEBUG("Merged cells into containers: " << recoContainer->size() << " reco cells, " 
            << truthContainer->size() << " truth cells, "
            << descContainer->size() << " master descriptors.");
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloCellMerge::fillHistograms(EventContext & /*ctx*/) const {
  return StatusCode::SUCCESS;
}
