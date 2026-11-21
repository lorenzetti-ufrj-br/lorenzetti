#ifndef ShowerShapeTool_h
#define ShowerShapeTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/EDM.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloCell/CaloCell.h"

#include <cmath>
#include <string>

/**
 * @class ShowerShapeTool
 * @brief Tool to calculate classic calorimeter layer shower shape variables.
 * 
 * Computes longitudinal and lateral development of the shower in EM and HAD samplings
 * (such as Reta, Rphi, weta2, f0-f3, Rhad, Eratio, etc.) and sets them on the CaloCluster.
 */
class ShowerShapeTool : public Gaugi::Tool {
public:
  ShowerShapeTool(std::string name);
  virtual ~ShowerShapeTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;
  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override;

private:
  float calculateWeta2(xAOD::CaloCluster *clus, unsigned eta_ncell = 3, unsigned phi_ncell = 5) const;
  float sumEnergyEM(xAOD::CaloCluster *clus, int sampling, unsigned eta_ncell = 1000, unsigned phi_ncell = 1000) const;
  float sumEnergyHAD(xAOD::CaloCluster *clus, int sampling, unsigned eta_ncell = 1000, unsigned phi_ncell = 1000) const;

  int m_outputLevel;
};

#endif
