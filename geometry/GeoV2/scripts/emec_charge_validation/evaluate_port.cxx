// F41 conserto 29: the test of the Athena harness (EmecHarnessAlg) with the port in the fork (geometry/LArG4EC, geometry/GeoSpecialShapes).
// Usage: evaluate_port <EmecTables.csv> <ec.fieldzv03> <HVEMECMap_v02.dat> <steps.txt> <output.txt> [athena.txt: diagnostic]
#include <array>
#include <vector>
#include <string>
#include <memory>
#include <map>
#include <iostream>
#include <sstream>
#include <fstream>
#include <stdexcept>
#include <cstdio>
#include "CLHEP/Vector/ThreeVector.h"
#include "CLHEP/Units/SystemOfUnits.h"
#include "G4ThreeVector.hh"
#include "G4String.hh"
#include "globals.hh"
#include "CxxUtils/features.h"
#include "CxxUtils/vec.h"
#include "LArG4EC/EMECDataCSV.h"
#define private public
#define protected public
#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "LArG4EC/HVHelper.h"
#include "LArG4EC/EnergyCalculator.h"
#undef private
#undef protected
#include "evaluate_common.icc"

int main(int argc, char** argv) {
  if (argc != 6 && argc != 7) { std::cerr << "usage: evaluate_port tables fieldmap hvmap steps output [athena]\n"; return 1; }
  const EMECData data = readEMECDataCSV(argv[1]);
  const char* names[4] = {"EMECPosInnerWheelCalculator", "EMECPosOuterWheelCalculator",
                          "EMECNegInnerWheelCalculator", "EMECNegOuterWheelCalculator"};
  // the order of creation of Athena (LArG4ECConfig.py: PosInner, PosOuter, NegInner, NegOuter)
  std::vector<std::unique_ptr<LArG4::EC::EnergyCalculator>> ecs;
  const LArG4::LArWheelCalculator_t types[4] = {LArG4::InnerAbsorberWheel, LArG4::OuterAbsorberWheel,
                                                LArG4::InnerAbsorberWheel, LArG4::OuterAbsorberWheel};
  const int sides[4] = {1, 1, -1, -1};
  for (int i = 0; i < 4; ++i)
    ecs.emplace_back(new LArG4::EC::EnergyCalculator(data, types[i], sides[i], argv[2], argv[3]));
  // diagnostic (optional 6th argument, the output of the Athena harness): replaces the coefficients of the sin/cos polynomial of each
  // calculator by those computed by Athena, to see the differences left outside the fit. Not part of the port.
  if (argc == 7) {
    std::ifstream ref(argv[6]); std::string line; int i = 0;
    while (i < 4 && std::getline(ref, line)) {
      if (line.rfind("INIT", 0) != 0) continue;
      std::istringstream ss(line); std::vector<std::string> t; std::string w; while (ss >> w) t.push_back(w);
      // fields: INIT name nfans N nwaves N zside N + 13 numbers; then 12 (sin, cos) of the wheel and 12 of the electrode
      for (int pass = 0; pass < 2; ++pass) {
        LArWheelCalculator* c = pass == 0 ? ecs[i]->m_lwc : ecs[i]->m_electrode_calculator;
        for (int k = 0; k < 6; ++k) {
          c->m_sin_parametrization[k] = std::strtod(t[21 + pass * 12 + 2 * k].c_str(), nullptr);
          c->m_cos_parametrization[k] = std::strtod(t[22 + pass * 12 + 2 * k].c_str(), nullptr);
        }
        auto& sp = c->m_sin_parametrization; auto& cp = c->m_cos_parametrization; auto& v = c->m_vsincos_par;
        v.param_0[0] = sp[4]; v.param_0[1] = sp[5]; v.param_0[2] = cp[4]; v.param_0[3] = cp[5];
        v.param_1[0] = sp[2]; v.param_1[1] = sp[3]; v.param_1[2] = cp[2]; v.param_1[3] = cp[3];
        v.param_2[0] = sp[0]; v.param_2[1] = sp[1]; v.param_2[2] = cp[0]; v.param_2[3] = cp[1];
      }
      ++i;
    }
  }
  FILE* out = std::fopen(argv[5], "w");
  for (int i = 0; i < 4; ++i) c29::dumpInit(out, names[i], ecs[i].get());
  FILE* in = std::fopen(argv[4], "r");
  if (!in || !out) { std::cerr << "cannot open input/output\n"; return 1; }
  int calc; double a[7]; long idx = 0;
  while (std::fscanf(in, "%d %lf %lf %lf %lf %lf %lf %lf", &calc, a, a+1, a+2, a+3, a+4, a+5, a+6) == 8) {
    const G4ThreeVector p1(a[0], a[1], a[2]), p2(a[3], a[4], a[5]);
    c29::evalStep(out, idx++, ecs[calc].get(), p1, p2, a[6]);
  }
  std::fclose(in); std::fclose(out);
  std::cerr << "evaluated " << idx << " steps\n";
  return 0;
}
