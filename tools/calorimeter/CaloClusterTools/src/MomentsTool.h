#ifndef MomentsTool_h
#define MomentsTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include "CaloCluster/CaloCluster.h"

#include <cmath>
#include <vector>
#include <string>
#include <TVector3.h>
#include <TMatrixD.h>
#include <TMatrixDEigen.h>

/**
 * @class MomentsTool
 * @brief Tool to calculate 3D cluster spatial moments and shower axis.
 * 
 * Computes shower axis using PCA eigen-analysis and spatial moments:
 * secondR, lambdaCenter, secondLambda, fracMax, lateralMom, longitudinalMom.
 */
class MomentsTool : public Gaugi::Tool {
public:
  MomentsTool(std::string name);
  virtual ~MomentsTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;
  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  std::vector<TVector3> calculateShowerAxis(xAOD::CaloCluster *clus) const;
  float calculateSecondR(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;
  float calculateSecondLambda(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;
  float calculateLambdaCenter(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;
  float calculateFracMax(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;
  float calculateLateralMom(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;
  float calculateLongitudinalMom(xAOD::CaloCluster *clus, const std::vector<TVector3> &axis) const;

  int m_outputLevel;
};

using MomentsTools = MomentsTool;

#endif
