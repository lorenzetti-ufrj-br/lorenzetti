#include "ShowerShapeTool.h"
#include "CaloCluster/CaloCluster.h"
#include "G4Kernel/CaloPhiRange.h"
#include <cmath>
#include <algorithm>

using namespace std;
using namespace SG;

ShowerShapeTool::ShowerShapeTool(std::string name) :
  IMsgService(name),
  Tool(),
  m_outputLevel(1)
{
  declareProperty("OutputLevel", m_outputLevel = 1);
}

StatusCode ShowerShapeTool::initialize() {
  setMsgLevel((MSG::Level)m_outputLevel);
  return StatusCode::SUCCESS;
}

StatusCode ShowerShapeTool::finalize() {
  return StatusCode::SUCCESS;
}

StatusCode ShowerShapeTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const {
  MSG_DEBUG("Calculate shower shapes for this cluster.");

  auto *clus = static_cast<xAOD::CaloCluster*>(edm);
  if (!clus) {
    return StatusCode::FAILURE;
  }

  // Eratio for strip em layer (EM1, all cells must be EMB1 or EMEC1 sampling)
  auto em1Cells = clus->cells();
  em1Cells.erase(std::remove_if(em1Cells.begin(), em1Cells.end(),
                 [](const xAOD::CaloCell* c){
                   if (!c || !c->descriptor()) return true;
                   return (
                     (c->descriptor()->sampling() != CaloSampling::EMB1) &&
                     (c->descriptor()->sampling() != CaloSampling::EMEC1));
                 }),
                 em1Cells.end());

  std::sort(em1Cells.begin(), em1Cells.end(),
            [](const xAOD::CaloCell* c1, const xAOD::CaloCell* c2){
              if (!c1 || !c2) return false;
              return c1->e() > c2->e();
            });

  float emaxs1  = (em1Cells.size() >= 4) ? (em1Cells[0]->e() + em1Cells[1]->e()) : 0.0f;
  float e2tsts1 = (em1Cells.size() >= 4) ? (em1Cells[2]->e() + em1Cells[3]->e()) : 0.0f;

  float eratio = (emaxs1 + e2tsts1) ? ((emaxs1 - e2tsts1) / (emaxs1 + e2tsts1)) : 0.0f;

  float e277  = sumEnergyEM(clus, 2, 7, 7);
  float e233  = sumEnergyEM(clus, 2, 3, 3);
  float e237  = sumEnergyEM(clus, 2, 3, 7);

  float reta  = (e277 > 0.0f) ? (e237 / e277) : 0.0f;
  float rphi  = (e237 > 0.0f) ? (e233 / e237) : 0.0f;

  float e0    = sumEnergyEM(clus, 0);
  float e1    = sumEnergyEM(clus, 1);
  float e2    = sumEnergyEM(clus, 2);
  float e3    = sumEnergyEM(clus, 3);
  float ehad1 = sumEnergyHAD(clus, 0);
  float ehad2 = sumEnergyHAD(clus, 1);
  float ehad3 = sumEnergyHAD(clus, 2);

  float weta2 = calculateWeta2(clus, 3, 5);

  float etot = e0 + e1 + e2 + e3 + ehad1 + ehad2 + ehad3;
  float emtot = e0 + e1 + e2 + e3;

  float f0 = (emtot > 0.0f) ? (e0 / emtot) : 0.0f;
  float f1 = (emtot > 0.0f) ? (e1 / emtot) : 0.0f;
  float f2 = (emtot > 0.0f) ? (e2 / emtot) : 0.0f;
  float f3 = (emtot > 0.0f) ? (e3 / emtot) : 0.0f;

  float rhad  = (emtot > 0.0f) ? ((ehad1 + ehad2 + ehad3) / emtot) : 0.0f;
  float rhad1 = (emtot > 0.0f) ? (ehad1 / emtot) : 0.0f;

  clus->setE0(e0);
  clus->setE1(e1);
  clus->setE2(e2);
  clus->setE3(e3);
  clus->setEhad1(ehad1);
  clus->setEhad2(ehad2);
  clus->setEhad3(ehad3);
  clus->setEtot(etot);
  clus->setE277(e277);
  clus->setE237(e237);
  clus->setE233(e233);
  clus->setReta(reta);
  clus->setRphi(rphi);
  clus->setWeta2(weta2);
  clus->setEratio(eratio);
  clus->setEmaxs1(emaxs1);
  clus->setE2tsts1(e2tsts1);
  clus->setF0(f0);
  clus->setF1(f1);
  clus->setF2(f2);
  clus->setF3(f3);
  clus->setRhad(rhad);
  clus->setRhad1(rhad1);
  clus->setEt(clus->eta() != 0.0 ? (e0 + e1 + e2 + e3) / cosh(std::abs(clus->eta())) : 0.0);
  clus->setE(e0 + e1 + e2 + e3);

  return StatusCode::SUCCESS;
}

float ShowerShapeTool::sumEnergyEM(xAOD::CaloCluster *clus, int sampling, unsigned eta_ncell, unsigned phi_ncell) const {
  float energy = 0.0;
  if (!clus) return energy;
  for (const auto& cell : clus->cells()) {
    if (!cell) continue;
    const xAOD::CaloDetDescriptor* det = cell->descriptor();
    if (!det) continue;
    if (det->detector() != Detector::TTEM) continue;
    if (sampling == 0 && (det->sampling() != CaloSampling::PSB && det->sampling() != CaloSampling::PSE)) continue;
    if (sampling == 1 && (det->sampling() != CaloSampling::EMB1 && det->sampling() != CaloSampling::EMEC1)) continue;
    if (sampling == 2 && (det->sampling() != CaloSampling::EMB2 && det->sampling() != CaloSampling::EMEC2)) continue;
    if (sampling == 3 && (det->sampling() != CaloSampling::EMB3 && det->sampling() != CaloSampling::EMEC3)) continue;
    float deltaEta = std::abs(clus->eta() - cell->eta());
    float deltaPhi = std::abs(CaloPhiRange::fix(clus->phi() - cell->phi()));
    if (deltaEta < eta_ncell * (cell->deltaEta() / 2) && deltaPhi < phi_ncell * (cell->deltaPhi() / 2)) {
      energy += cell->e();
    }
  }
  return energy;
}

float ShowerShapeTool::sumEnergyHAD(xAOD::CaloCluster *clus, int sampling, unsigned eta_ncell, unsigned phi_ncell) const {
  float energy = 0.0;
  if (!clus) return energy;
  for (const auto& cell : clus->cells()) {
    if (!cell) continue;
    const xAOD::CaloDetDescriptor* det = cell->descriptor();
    if (!det) continue;
    if (det->detector() == Detector::TTEM) continue;
    if (sampling == 0 && (det->sampling() != CaloSampling::HEC1 && det->sampling() != CaloSampling::TileCal1 && det->sampling() != CaloSampling::TileExt1)) continue;
    if (sampling == 1 && (det->sampling() != CaloSampling::HEC2 && det->sampling() != CaloSampling::TileCal2 && det->sampling() != CaloSampling::TileExt2)) continue;
    if (sampling == 2 && (det->sampling() != CaloSampling::HEC3 && det->sampling() != CaloSampling::TileCal3 && det->sampling() != CaloSampling::TileExt3)) continue;
    float deltaEta = std::abs(clus->eta() - cell->eta());
    float deltaPhi = std::abs(CaloPhiRange::fix(clus->phi() - cell->phi()));
    if (deltaEta < eta_ncell * (cell->deltaEta() / 2) && deltaPhi < phi_ncell * (cell->deltaPhi() / 2)) {
      energy += cell->e();
    }
  }
  return energy;
}

float ShowerShapeTool::calculateWeta2(xAOD::CaloCluster *clus, unsigned eta_ncell, unsigned phi_ncell) const {
  if (!clus) return 0.0;
  float En2 = 0.0;
  float En = 0.0;
  float E = 0.0;
  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    const xAOD::CaloDetDescriptor* det = cell->descriptor();
    if (!det) continue;
    if (det->sampling() != CaloSampling::EMB2 && det->sampling() != CaloSampling::EMEC2) continue;
    float deltaEta = std::abs(clus->eta() - cell->eta());
    float deltaPhi = std::abs(CaloPhiRange::diff(clus->phi(), cell->phi()));
    if (deltaEta < eta_ncell * (cell->deltaEta() / 2) && deltaPhi < phi_ncell * (cell->deltaPhi() / 2)) {
      En2 += cell->e() * std::pow(cell->eta(), 2);
      En += cell->e() * cell->eta();
      E += cell->e();
    }
  }
  if (E <= 0.0) return 0.0;
  float var = (En2 / E) - std::pow((En / E), 2);
  return var > 0.0 ? std::sqrt(var) : 0.0;
}
