// F41 conserto 29: Athena 23.0.14 harness to validate the port of the EMEC charge collection.
// Takes the four EMEC calculators (LArG4::EC::EnergyCalculator, services configured as in the simulation, LArG4ECConfig.py)
// and, in initialize, evaluates every step of the input file with the functions of Athena itself (libAtlasGeant4.so), writing
// everything in hexadecimal. The private members are reached with "#define private public" (same layout).

// headers other than those of the EnergyCalculator first, without the define
#include <array>
#include <vector>
#include <string>
#include <memory>
#include <map>
#include <set>
#include <list>
#include <deque>
#include <sstream>
#include <iostream>
#include <fstream>
#include <functional>
#include <mutex>
#include <atomic>
#include <unordered_map>
#include <stdexcept>
#include <cstdio>
#include "AthenaBaseComps/AthAlgorithm.h"
#include "GaudiKernel/ServiceHandle.h"
#include "AthenaBaseComps/AthMessaging.h"
#include "AthenaBaseComps/AthService.h"
#include "AthenaKernel/Units.h"
#include "AthenaKernel/CLASS_DEF.h"
#include "CxxUtils/features.h"
#include "CxxUtils/vec.h"
#include "CxxUtils/restrict.h"
#include "CLHEP/Vector/ThreeVector.h"
#include "CLHEP/Units/SystemOfUnits.h"
#include "G4ThreeVector.hh"
#include "G4String.hh"
#include "G4Step.hh"
#include "globals.hh"
#include "LArG4Code/LArG4Identifier.h"
#include "LArG4Code/LArG4EnumDefs.h"
#include "LArG4Code/LArCalculatorSvcImp.h"
#include "LArG4Code/ILArCalibCalculatorSvc.h"
#include "LArG4Code/LArG4BirksLaw.h"
#include "GeoSpecialShapes/LArWheelCalculatorEnums.h"

#define private public
#define protected public
#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "HVHelper.h"
#include "EnergyCalculator.h"
#undef private
#undef protected

#include "../../../../evaluate_common.icc"

class EmecHarnessAlg : public AthAlgorithm {
public:
  EmecHarnessAlg(const std::string& name, ISvcLocator* svc) : AthAlgorithm(name, svc) {}
  StatusCode initialize() override {
    const char* names[4] = {"EMECPosInnerWheelCalculator", "EMECPosOuterWheelCalculator",
                            "EMECNegInnerWheelCalculator", "EMECNegOuterWheelCalculator"};
    std::vector<const LArG4::EC::EnergyCalculator*> ecs;
    for (int i = 0; i < 4; ++i) {
      ServiceHandle<ILArCalculatorSvc> h(names[i], this->name());
      ATH_CHECK(h.retrieve());
      const auto* ec = dynamic_cast<const LArG4::EC::EnergyCalculator*>(&*h);
      if (!ec) { ATH_MSG_FATAL("not an EnergyCalculator: " << names[i]); return StatusCode::FAILURE; }
      ecs.push_back(ec);
    }
    FILE* out = std::fopen(m_out.value().c_str(), "w");
    for (int i = 0; i < 4; ++i) c29::dumpInit(out, names[i], ecs[i]);
    FILE* in = std::fopen(m_in.value().c_str(), "r");
    if (!in || !out) { ATH_MSG_FATAL("cannot open input/output"); return StatusCode::FAILURE; }
    int calc; double a[7]; long idx = 0;
    while (std::fscanf(in, "%d %lf %lf %lf %lf %lf %lf %lf", &calc, a, a+1, a+2, a+3, a+4, a+5, a+6) == 8) {
      const G4ThreeVector p1(a[0], a[1], a[2]), p2(a[3], a[4], a[5]);
      c29::evalStep(out, idx++, ecs[calc], p1, p2, a[6]);
    }
    std::fclose(in); std::fclose(out);
    ATH_MSG_INFO("evaluated " << idx << " steps");
    return StatusCode::SUCCESS;
  }
  StatusCode execute() override { return StatusCode::SUCCESS; }
private:
  Gaudi::Property<std::string> m_in{this, "InputFile", "steps.txt"};
  Gaudi::Property<std::string> m_out{this, "OutputFile", "athena.txt"};
};

DECLARE_COMPONENT(EmecHarnessAlg)
