/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.

#include "GeoSpecialShapes/LArWheelCalculator_Impl/ModuleFanCalculator.h"

#include "GeoSpecialShapes/LArWheelCalculator.h"



#ifdef HARDDEBUG
#undef HARDDEBUG
#endif

namespace LArWheelCalculator_Impl
{

  ModuleFanCalculator::ModuleFanCalculator(LArWheelCalculator* lwc)
    : m_lwc(lwc)
  {
  }

  double ModuleFanCalculator::DistanceToTheNearestFan(CLHEP::Hep3Vector &p, int & out_fan_number) const
  {
    static const double halfpi=M_PI/2.0;
    int fan_number = int((p.phi() - halfpi - lwc()->m_ZeroFanPhi_ForDetNeaFan) / lwc()->m_FanStepOnPhi);
    double angle = lwc()->m_FanStepOnPhi * fan_number + lwc()->m_ZeroFanPhi_ForDetNeaFan;
#ifdef HARDDEBUG
    printf("DistanceToTheNearestFan: initial FN %4d\n", fan_number);
#endif
    p.rotateZ(-angle);
    // determine search direction
    double d0 = lwc()->DistanceToTheNeutralFibre(p, lwc()->adjust_fan_number(fan_number));
    double d1 = d0;
    int delta = 1;
    if(d0 < 0.) delta = -1; // search direction has been determined
    angle = - lwc()->m_FanStepOnPhi * delta;
    do { // search:
      p.rotateZ(angle);
      fan_number += delta;
      d1 = lwc()->DistanceToTheNeutralFibre(p, lwc()->adjust_fan_number(fan_number));
    } while(d0 * d1 > 0.);
    // if signs of d1 and d0 are different, the point is between current pair
    if(delta > 0) fan_number --;

    int adj_fan_number = fan_number;
    if(adj_fan_number < lwc()->m_FirstFan) {
      p.rotateZ((adj_fan_number - lwc()->m_FirstFan) * lwc()->m_FanStepOnPhi);
      adj_fan_number = lwc()->m_FirstFan;
    } else if(adj_fan_number >= lwc()->m_LastFan) {
      p.rotateZ((adj_fan_number - lwc()->m_LastFan + 1) * lwc()->m_FanStepOnPhi);
      adj_fan_number = lwc()->m_LastFan - 1;
    }

    p.rotateZ(-0.5 * angle);
    out_fan_number = adj_fan_number;
    return lwc()->DistanceToTheNeutralFibre(p, adj_fan_number);
  }

  int ModuleFanCalculator::PhiGapNumberForWheel(int i) const {
    i += lwc()->m_ZeroGapNumber;
    i -= lwc()->m_LastFan / 2;
    if(i < 0) i += lwc()->m_NumberOfFans;
    if(i >= lwc()->m_NumberOfFans) i -= lwc()->m_NumberOfFans;
    return i;
  }

  std::pair<int, int> ModuleFanCalculator::GetPhiGapAndSide(const CLHEP::Hep3Vector &p) const
  {
    // Note: this object was changed from static to local for thread-safety.
    // If this is found to be too costly we can re-evaluate.
    CLHEP::Hep3Vector p1 = p;
    static const double halfpi=M_PI/2.0;
    int fan_number = int((p.phi() - halfpi - lwc()->m_ZeroFanPhi) / lwc()->m_FanStepOnPhi);

    double angle = lwc()->m_FanStepOnPhi * fan_number + lwc()->m_ZeroFanPhi;
    p1.rotateZ(-angle);

    double d0 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
    double d1 = d0;

    int delta = 1;
    if(d0 < 0.) delta = -1;
    angle = - lwc()->m_FanStepOnPhi * delta;
    do {
      p1.rotateZ(angle);
      fan_number += delta;
      d1 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
    } while(d0 * d1 > 0.);
    if(delta > 0) fan_number --;
    if(!lwc()->m_isElectrode) fan_number ++;

    int adj_fan_number = fan_number;
    if(adj_fan_number < lwc()->m_FirstFan) adj_fan_number = lwc()->m_FirstFan - 1;
    else if(adj_fan_number > lwc()->m_LastFan) adj_fan_number = lwc()->m_LastFan;

    p1.rotateZ(-0.5 * angle);
    double dd = lwc()->DistanceToTheNeutralFibre(p1, adj_fan_number);
    int side = dd < 0.? -1: 1;
#ifdef HARDDEBUG
    printf("GetPhiGapAndSide: MFN %4d\n", adj_fan_number);
#endif
    return std::pair<int, int>(adj_fan_number, side);
  }

}
