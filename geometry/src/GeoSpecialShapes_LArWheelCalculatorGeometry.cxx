/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.

#include "CxxUtils/sincos.h"
//#include <cmath>
#include <climits>
#include <cassert>
#include <iostream>

#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/IDistanceCalculator.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/IFanCalculator.h"
#include "GeoSpecialShapes/GeoModelKernelUnits.h" // Lorenzetti port: same units, without GeoModel
#ifdef HARDDEBUG
#include<stdio.h>
#endif

using namespace GeoModelKernelUnits;

void LArWheelCalculator::parameterized_sin(const double r, double &sin_a, double &cos_a) const
{
  const double r2 = r*r;
  const double r3 = r2*r;
  const double r4 = r2*r2;
#if LARWC_SINCOS_POLY > 4
  const double r5 = r4*r;
#endif
  sin_a = m_sin_parametrization[0]
        + m_sin_parametrization[1]*r
        + m_sin_parametrization[2]*r2
        + m_sin_parametrization[3]*r3
        + m_sin_parametrization[4]*r4
#if LARWC_SINCOS_POLY > 4
        + m_sin_parametrization[5]*r5
#endif
  ;
  cos_a = sqrt(1. - sin_a*sin_a);
}

void LArWheelCalculator::parameterized_sincos(const double r, double &sin_a, double &cos_a) const
{
  const double r2 = r*r;
  const double r3 = r2*r;
  const double r4 = r2*r2;
#if LARWC_SINCOS_POLY > 4
  const double r5 = r4*r;
#endif
  sin_a = m_sin_parametrization[0]
        + m_sin_parametrization[1]*r
        + m_sin_parametrization[2]*r2
        + m_sin_parametrization[3]*r3
        + m_sin_parametrization[4]*r4
#if LARWC_SINCOS_POLY > 4
        + m_sin_parametrization[5]*r5
#endif
  ;
  cos_a = m_cos_parametrization[0]
        + m_cos_parametrization[1]*r
        + m_cos_parametrization[2]*r2
        + m_cos_parametrization[3]*r3
        + m_cos_parametrization[4]*r4
#if LARWC_SINCOS_POLY > 4
        + m_cos_parametrization[5]*r5
#endif
  ;
}

// calculates wave slant angle using parametrization for current wheel
// for given distance from calorimeter axis
double LArWheelCalculator::parameterized_slant_angle(double r) const
{
  const double r2 = r*r;
  const double r3 = r2*r;
  const double r4 = r2*r2;
  const double result = m_slant_parametrization[0] +
                        r*m_slant_parametrization[1] +
                        r2*m_slant_parametrization[2] +
                        r3*m_slant_parametrization[3] +
                        r4*m_slant_parametrization[4];
  return result*deg;
}

// Determines the nearest to the input point fan.
// Relays on the fact that each two fans have a fan of a different type between
// them.
// Returns distance to the nearest fan. Vector p is set to nearest fan coord.
// system.
// m_fan_number is set to nearest fan number
double LArWheelCalculator::DistanceToTheNearestFan(CLHEP::Hep3Vector &p, int & out_fan_number) const
{
  return m_fanCalcImpl->DistanceToTheNearestFan(p, out_fan_number);
}

// Relays on the fact that each two fans have a fan of a different type between
// them.
// Affects m_fan_number.
std::pair<int, int> LArWheelCalculator::GetPhiGapAndSide(const CLHEP::Hep3Vector &p) const
{
  return m_fanCalcImpl->GetPhiGapAndSide(p);
}

// Represents aproximate, probably underestimate, distance to the
// neutral fibre of the vertical fan. Sign of return value means
// side of the fan; negative - lower phi.
//
// Uses m_fan_number to compute sagging.
double LArWheelCalculator::DistanceToTheNeutralFibre(const CLHEP::Hep3Vector& P, int fan_number) const
{
  return m_distanceCalcImpl->DistanceToTheNeutralFibre(P, fan_number);
}

CLHEP::Hep3Vector LArWheelCalculator::NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &P, int fan_number) const
{
  return m_distanceCalcImpl->NearestPointOnNeutralFibre(P, fan_number);
}

std::vector<double> LArWheelCalculator::NearestPointOnNeutralFibre_asVector(const CLHEP::Hep3Vector &p, int fan_number) const
{
  CLHEP::Hep3Vector np = NearestPointOnNeutralFibre(p, fan_number);
  return std::vector<double> { np.x(), np.y(), np.z() };
}

/*
input is in local fan's coordinate system
side: < 0 - lower phi
      > 0 - greater phi
      = 0 - neutral fibre
*/
double LArWheelCalculator::AmplitudeOfSurface(const CLHEP::Hep3Vector& P, int side, int fan_number) const
{
  return m_distanceCalcImpl->AmplitudeOfSurface(P, side, fan_number);
}
