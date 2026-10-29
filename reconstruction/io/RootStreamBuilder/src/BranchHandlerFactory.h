#ifndef BranchHandlerFactory_h
#define BranchHandlerFactory_h

#include "GenericBranchHandler.h"
#include "CaloCellBranchHandler.h"

// EDM Includes
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/EventInfoConverter.h"

#include "TruthParticle/TruthParticleContainer.h"
#include "TruthParticle/TruthParticleConverter.h"

#include "EventInfo/SeedContainer.h"
#include "EventInfo/SeedConverter.h"

#include "CaloHit/CaloHitContainer.h"
#include "CaloHit/CaloHitConverter.h"

#include "CaloCell/CaloDetDescriptorContainer.h"
#include "CaloCell/CaloDetDescriptorConverter.h"

#include "CaloCell/CaloCellContainer.h"
#include "CaloCell/CaloCellConverter.h"

#include "CaloCluster/CaloClusterContainer.h"
#include "CaloCluster/CaloClusterConverter.h"

#include "CaloRings/CaloRingsContainer.h"
#include "CaloRings/CaloRingsConverter.h"

#include "Egamma/ElectronContainer.h"
#include "Egamma/ElectronConverter.h"

#include <memory>
#include <string>
#include <algorithm>

namespace Gaugi {

  /**
   * @class BranchHandlerFactory
   * @brief Factory creating typed IBranchHandler instances from type names and keys.
   */
  class BranchHandlerFactory {
  public:
    static std::unique_ptr<IBranchHandler> createHandler(
        const std::string &rawTypeName,
        const std::string &key,
        bool filterBySigma = false,
        float sigmaThreshold = 2.0f,
        const std::string &descriptorsKey = "CaloDetDescriptors")
    {
      std::string typeName = rawTypeName;
      // Strip namespace if present
      if (typeName.find("xAOD::") == 0) {
        typeName = typeName.substr(6);
      }

      if (typeName == "CaloHitContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::CaloHitContainer,
                                                     xAOD::CaloHit_t,
                                                     xAOD::CaloHitConverter>>("CaloHitContainer", key);
      }
      else if (typeName == "EventInfoContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::EventInfoContainer,
                                                     xAOD::EventInfo_t,
                                                     xAOD::EventInfoConverter>>("EventInfoContainer", key);
      }
      else if (typeName == "TruthParticleContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::TruthParticleContainer,
                                                     xAOD::TruthParticle_t,
                                                     xAOD::TruthParticleConverter>>("TruthParticleContainer", key);
      }
      else if (typeName == "SeedContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::SeedContainer,
                                                     xAOD::Seed_t,
                                                     xAOD::SeedConverter>>("SeedContainer", key);
      }
      else if (typeName == "CaloDetDescriptorContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::CaloDetDescriptorContainer,
                                                     xAOD::CaloDetDescriptor_t,
                                                     xAOD::CaloDetDescriptorConverter>>("CaloDetDescriptorContainer", key);
      }
      else if (typeName == "CaloCellContainer") {
        return std::make_unique<CaloCellBranchHandler>(
            key, filterBySigma, sigmaThreshold, descriptorsKey);
      }
      else if (typeName == "CaloClusterContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::CaloClusterContainer,
                                                     xAOD::CaloCluster_t,
                                                     xAOD::CaloClusterConverter>>("CaloClusterContainer", key);
      }
      else if (typeName == "CaloRingsContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::CaloRingsContainer,
                                                     xAOD::CaloRings_t,
                                                     xAOD::CaloRingsConverter>>("CaloRingsContainer", key);
      }
      else if (typeName == "ElectronContainer") {
        return std::make_unique<GenericBranchHandler<xAOD::ElectronContainer,
                                                     xAOD::Electron_t,
                                                     xAOD::ElectronConverter>>("ElectronContainer", key);
      }

      return nullptr;
    }
  };

} // namespace Gaugi

#endif
