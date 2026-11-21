#include "MomentsTool.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloCell/CaloCell.h"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"

#include <cmath>
#include <vector>

using namespace std;
using namespace SG;

MomentsTool::MomentsTool(std::string name) :
  IMsgService(name),
  Tool(),
  m_outputLevel(1)
{
  declareProperty("OutputLevel", m_outputLevel = 1);
}

StatusCode MomentsTool::initialize() {
  setMsgLevel((MSG::Level)m_outputLevel);
  return StatusCode::SUCCESS;
}

StatusCode MomentsTool::finalize() {
  return StatusCode::SUCCESS;
}

StatusCode MomentsTool::execute(SG::EventContext &/*ctx*/, Gaugi::EDM *edm) const {
  auto *clus = static_cast<xAOD::CaloCluster*>(edm);
  if (!clus) {
    return StatusCode::FAILURE;
  }

  if (!clus->isForward()) {
    return StatusCode::SUCCESS;
  }

  std::vector<TVector3> axis = calculateShowerAxis(clus);
  float secondR = calculateSecondR(clus, axis);
  float lambdaCenter = calculateLambdaCenter(clus, axis);
  float secondLambda = calculateSecondLambda(clus, axis);
  float fracMax = calculateFracMax(clus, axis);
  float lateralMom = calculateLateralMom(clus, axis);
  float longitudinalMom = calculateLongitudinalMom(clus, axis);

  clus->setSecondR(secondR);
  clus->setLambdaCenter(lambdaCenter);
  clus->setSecondLambda(secondLambda);
  clus->setFracMax(fracMax);
  clus->setLateralMom(lateralMom);
  clus->setLongitudinalMom(longitudinalMom);

  return StatusCode::SUCCESS;
}

std::vector<TVector3> MomentsTool::calculateShowerAxis(xAOD::CaloCluster *clus) const {
  float xc = 0;
  float yc = 0;
  float zc = 0;
  float w = 0;
  float emax1 = 0;
  float emax2 = 0;
  double angle = 0;
  float totalE = 0;
  float m_maxAxisAngle = 20 * 3.14159265358979323846 / 180.0;

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float eta = cell->eta();
    float phi = cell->phi();
    float energy = cell->e();

    if (energy > emax2) {
      emax2 = energy;
    }
    if (energy > emax1) {
      emax2 = emax1;
      emax1 = energy;
    }

    float thetaCell = 2 * std::atan(std::exp(-eta));
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    xc += energy * xCell;
    yc += energy * yCell;
    zc += energy * zCell;
    totalE += energy;
  }

  if (totalE <= 0.0f) {
    TVector3 zero(0, 0, 0);
    return {zero, zero, zero, zero};
  }

  TVector3 emec1_cell(0, 0, 0);
  TVector3 showerAxis(xc / totalE, yc / totalE, zc / totalE);
  TVector3 showerCenter(xc / totalE, yc / totalE, zc / totalE);
  showerAxis.SetMag(1.0);
  TMatrixD C(3, 3);

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float energy = cell->e();
    float eta = cell->eta();
    float phi = cell->phi();
    float thetaCell = 2 * std::atan(std::exp(-eta));
    const double e2 = energy * energy;
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    C(0, 0) += e2 * (xCell - xc) * (xCell - xc);
    C(1, 0) += e2 * (xCell - xc) * (yCell - yc);
    C(2, 0) += e2 * (xCell - xc) * (zCell - zc);
    C(1, 1) += e2 * (yCell - yc) * (yCell - yc);
    C(2, 1) += e2 * (yCell - yc) * (zCell - zc);
    C(2, 2) += e2 * (zCell - zc) * (zCell - zc);
    w += e2;

    if (cell->descriptor()->sampling() == CaloSampling::EMEC1) {
      emec1_cell.SetZ(zCell);
    }
  }

  if (w > 0.0) {
    C(0, 0) /= w;
    C(1, 0) /= w;
    C(2, 0) /= w;
    C(1, 1) /= w;
    C(2, 1) /= w;
    C(2, 2) /= w;
    auto S = TMatrixDEigen(C).GetEigenValues();
    auto U = TMatrixDEigen(C).GetEigenVectors();
    float epsilon = 1.E-6;
    if (std::abs(S(0, 0)) >= epsilon && std::abs(S(1, 1)) >= epsilon && std::abs(S(2, 2)) >= epsilon) {
      TVector3 prAxis(showerAxis);
      int iEigen = -1;
      for (int i = 0; i < 3; i++) {
        TVector3 tmpAxis(U(i, 0), U(i, 1), U(i, 2));
        double tmpAngle = tmpAxis.Angle(showerAxis);
        if (tmpAngle > 90 * deg) {
          tmpAngle = 180 * deg - tmpAngle;
          tmpAxis = -tmpAxis;
        }
        if (iEigen == -1 || tmpAngle < angle) {
          iEigen = i;
          angle = tmpAngle;
          prAxis = tmpAxis;
        }
        if (angle < m_maxAxisAngle) {
          showerAxis = prAxis;
        }
      }
    }
  }

  TVector3 energies(totalE, emax1, emax2);
  return {showerAxis, showerCenter, energies, emec1_cell};
}

float MomentsTool::calculateLambdaCenter(xAOD::CaloCluster * /*clus*/, const std::vector<TVector3> &axis) const {
  if (axis.size() < 4) return 0.0f;
  float LambdaCenter = 0;
  float factor = 0;
  auto showerAxis = axis.at(0);
  auto z_showerAxis = axis.at(0).Z();
  auto showerCenter = axis.at(1);
  auto z_showerCenter = axis.at(1).Z();
  auto z_emec1 = axis.at(3).Z();

  if (std::abs(z_showerAxis) < 1e-9) return 0.0f;

  if (z_showerCenter > 0) {
    factor = (z_showerCenter - z_emec1) / z_showerAxis;
  } else {
    factor = (z_showerCenter + z_emec1) / z_showerAxis;
  }
  LambdaCenter = (factor * showerAxis).Mag();
  return LambdaCenter;
}

float MomentsTool::calculateSecondLambda(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const {
  if (axis.size() < 3) return 0.0f;
  float secondLambda = 0;
  auto showerAxis = axis.at(0);
  auto showerCenter = axis.at(1);
  auto totalE = axis.at(2).X();

  if (totalE <= 0.0f) return 0.0f;

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float eta = cell->eta();
    float phi = cell->phi();
    float energy = cell->e();
    float thetaCell = 2 * std::atan(std::exp(-eta));
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    TVector3 currentCell(xCell, yCell, zCell);
    float r = ((currentCell - showerCenter).Dot(showerAxis));
    secondLambda += energy * r * r;
  }
  return secondLambda / totalE;
}

float MomentsTool::calculateSecondR(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const {
  if (axis.size() < 3) return 0.0f;
  float secondR = 0;
  auto showerAxis = axis.at(0);
  auto showerCenter = axis.at(1);
  auto totalE = axis.at(2).X();

  if (totalE <= 0.0f) return 0.0f;

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float eta = cell->eta();
    float phi = cell->phi();
    float energy = cell->e();
    float thetaCell = 2 * std::atan(std::exp(-eta));
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    TVector3 currentCell(xCell, yCell, zCell);
    float r = ((currentCell - showerCenter).Cross(showerAxis)).Mag();
    secondR += energy * r * r;
  }
  return secondR / totalE;
}

float MomentsTool::calculateFracMax(xAOD::CaloCluster * /*clus*/, const std::vector<TVector3> &axis) const {
  if (axis.size() < 3) return 0.0f;
  auto totalE = axis.at(2).X();
  auto emax1 = axis.at(2).Y();
  return (totalE > 0.0f) ? (emax1 / totalE) : 0.0f;
}

float MomentsTool::calculateLateralMom(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const {
  if (axis.size() < 3) return 0.0f;
  float lateralMom = 0;
  float r_2 = 0;
  float r_max = 0;
  auto showerAxis = axis.at(0);
  auto showerCenter = axis.at(1);
  auto totalE = axis.at(2).X();
  auto emax1 = axis.at(2).Y();
  auto emax2 = axis.at(2).Z();

  if (totalE <= 0.0f) return 0.0f;

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float eta = cell->eta();
    float phi = cell->phi();
    float energy = cell->e();
    float thetaCell = 2 * std::atan(std::exp(-eta));
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    TVector3 currentCell(xCell, yCell, zCell);
    if (energy != emax1 && energy != emax2) {
      float r = ((currentCell - showerCenter).Cross(showerAxis)).Mag();
      r_2 += energy * std::pow(r, 2) / totalE;
    } else {
      r_max += energy * std::pow(40.0f, 2) / totalE;
    }
  }
  lateralMom = (r_2 + r_max > 0.0f) ? (r_2 / (r_2 + r_max)) : 0.0f;
  return lateralMom;
}

float MomentsTool::calculateLongitudinalMom(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const {
  if (axis.size() < 3) return 0.0f;
  float longitudinalMom = 0;
  float l_2 = 0;
  float l_max = 0;
  auto showerAxis = axis.at(0);
  auto showerCenter = axis.at(1);
  auto totalE = axis.at(2).X();
  auto emax1 = axis.at(2).Y();
  auto emax2 = axis.at(2).Z();

  if (totalE <= 0.0f) return 0.0f;

  for (auto& cell : clus->cells()) {
    if (!cell) continue;
    float eta = cell->eta();
    float phi = cell->phi();
    float energy = cell->e();
    float thetaCell = 2 * std::atan(std::exp(-eta));
    float zCell = cell->descriptor()->z();
    float rCell = zCell / std::cos(thetaCell);
    float xCell = rCell * std::sin(thetaCell) * std::cos(phi);
    float yCell = rCell * std::sin(thetaCell) * std::sin(phi);
    TVector3 currentCell(xCell, yCell, zCell);
    if (energy != emax1 && energy != emax2) {
      float l = ((currentCell - showerCenter).Dot(showerAxis));
      l_2 += energy * std::pow(l, 2) / totalE;
    } else {
      l_max += energy * std::pow(100.0f, 2) / totalE;
    }
  }
  longitudinalMom = (l_2 + l_max > 0.0f) ? (l_2 / (l_2 + l_max)) : 0.0f;
  return longitudinalMom;
}
