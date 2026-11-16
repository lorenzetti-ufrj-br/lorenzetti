/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.

#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorSaggingOff.h"
#include "GeoSpecialShapes/LArWheelCalculator.h"

#include<cassert>

//#define LWC_PARAM_ANGLE

#ifdef LWC_PARAM_ANGLE
#include <CxxUtils/sincos.h>
#endif

#include<signal.h>


namespace LArWheelCalculator_Impl
{

  DistanceCalculatorSaggingOff::DistanceCalculatorSaggingOff(LArWheelCalculator* c)
    : m_lwc(c)
  {
    m_EndQuarterWave = lwc()->m_ActiveLength - lwc()->m_QuarterWaveLength;
  }

#ifndef LARWC_DTNF_NEW
  double DistanceCalculatorSaggingOff::DistanceToTheNeutralFibre(const CLHEP::Hep3Vector& P, int /*fan_number*/) const
#else
  double DistanceCalculatorSaggingOff::DistanceToTheNeutralFibre_ref(const CLHEP::Hep3Vector& P, int /*fan_number*/) const
#endif
  {
    assert(P.y() > 0.);
    double distance = 0.;
    double z = P.z() - lwc()->m_StraightStartSection;
    double x = P.x();

#ifdef LWC_PARAM_ANGLE //old variant
    const double alpha = lwc()->parameterized_slant_angle(P.y());
    //double cos_a, sin_a;
    //::sincos(alpha, &sin_a, &cos_a);
    CxxUtils::sincos scalpha(alpha);
    const double cos_a = scalpha.cs, sin_a = scalpha.sn;
#else // parameterized sine
    double cos_a, sin_a;
    lwc()->m_vsincos_par.eval(P.y(), sin_a, cos_a);
#endif
    // determination of the nearest quarter-wave number
    int nqwave = (z < 0.) ? 0 : int(z / lwc()->m_QuarterWaveLength);
    //if(z < 0.) nqwave = 0;
    //else nqwave = int(z / lwc()->m_QuarterWaveLength);

    bool begin_qw = false;
    if((nqwave % 2) != 0){
      nqwave ++;
      begin_qw = true;
    }

    nqwave /= 2;

    // now nqwave is not the number of quarter-wave but the number of half-wave
    // half-waves with last and zero numbers are not really half-waves but start
    // and finish quarter-waves
    // It means that half-wave number 1 begins after starting quarter-wave
    if(nqwave != 0 && nqwave != lwc()->m_NumberOfHalfWaves){ // regular half-waves
      z -= nqwave * lwc()->m_HalfWaveLength;
      // there are some symmetries, so use them
      if((nqwave % 2) == 0) x = -x;
      if(begin_qw){
        z = -z;
        x = -x;
      }
      // certain situation: rising slope of wave, z is positive
      // rotate to prime-coordinate system (see description)
      const double z_prime = z * cos_a + x * sin_a;
      const double x_prime = x * cos_a - z * sin_a;
      const double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
      if(z_prime > straight_part){// fold region
        const double dz = straight_part - z_prime;
        const double dx = x_prime + lwc()->m_FanFoldRadius;
        distance = sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
      } else if(z_prime > -straight_part){
        distance = x_prime; // straight part of the quarter-wave
      } else {// fold region
        const double dz = straight_part + z_prime;
        const double dx = x_prime - lwc()->m_FanFoldRadius;
        distance = lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
      }
      // set correct sign for result
      if(!begin_qw) distance = -distance;
      if((nqwave % 2) == 0) distance = -distance;

    } else { // start and finish quarter-waves
      if(nqwave == 0)	{ // start quarter-wave
        x = - x;
      } else { // finish quarter-wave
        z = lwc()->m_ActiveLength - z;
      }

      const double tan_beta = sin_a/(1.0 + cos_a); //tan(alpha * 0.5);
      const double local_straight_section = lwc()->m_FanFoldRadius * tan_beta;
      if( z < - local_straight_section &&
          ( x < lwc()->m_FanFoldRadius ||
            x < - lwc()->m_StraightStartSection * z / local_straight_section / tan_beta ) )
      {
        distance = - x;
      }
      else {
        const double z_prime = z * cos_a + x * sin_a;
        const double x_prime = x * cos_a - z * sin_a;
        if (z_prime < local_straight_section) { // start fold region
          const double dz = local_straight_section - z_prime;
          const double dx = x_prime - lwc()->m_FanFoldRadius;
          distance = sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
        } else {
          const double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
          if (z_prime <= straight_part) { // straight part of quarter-wave
            distance = - x_prime;
          } else { // regular fold region of the quarter-wave
            const double dz = straight_part - z_prime;
            const double dx = x_prime + lwc()->m_FanFoldRadius;
            distance = lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
          }
        }
      }
      // set correct sign
      if (nqwave == 0) distance = -distance;
    }
#ifdef HARDDEBUG
    double dd = DistanceToTheNeutralFibre_ref(P);
    if(fabs(dd - distance) > 0.000001){
      //static int cnt = 0;
      std::cout << "DTNF MISMATCH " << this << " " << P << " "
                << dd << " vs " << distance << std::endl;
      //cnt ++;
      //if(cnt > 100) exit(0);
    }
#endif
    return distance;
  }

  // IMPROVED PERFORMANCE
#ifdef LARWC_DTNF_NEW
  double DistanceCalculatorSaggingOff::DistanceToTheNeutralFibre(const CLHEP::Hep3Vector& P, int /*fan_number*/) const
#else
  double DistanceCalculatorSaggingOff::DistanceToTheNeutralFibre_ref(const CLHEP::Hep3Vector& P, int /*fan_number*/) const
#endif
  {
    double z = P.z() - lwc()->m_StraightStartSection;
    double x = P.x();

#ifdef LWC_PARAM_ANGLE //old variant
    const double alpha = lwc()->parameterized_slant_angle(P.y());
    CxxUtils::sincos scalpha(alpha);
    double cos_a = scalpha.cs, sin_a = scalpha.sn;
#else // parameterized sine
    double cos_a, sin_a;
    lwc()->m_vsincos_par.eval(P.y(), sin_a, cos_a);
#endif

    bool sqw = false;
    if(z > lwc()->m_QuarterWaveLength){
      if(z < m_EndQuarterWave){ // regular half-waves
        unsigned int nhwave = (unsigned int)(z / lwc()->m_HalfWaveLength + 0.5);
        z -= lwc()->m_HalfWaveLength * nhwave;
        const double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
        nhwave &= 1U;
        if(nhwave == 0) sin_a = - sin_a;
        double z_prime = z * cos_a + x * sin_a;
        const double x_prime = z * sin_a - x * cos_a;
        if(z_prime > straight_part){ // up fold region
          const double dz = z_prime - straight_part;
          if(nhwave == 0){
            const double dx = x_prime + lwc()->m_FanFoldRadius;
            return sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
          } else {
            const double dx = x_prime - lwc()->m_FanFoldRadius;
            return lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
          }
        }
        z_prime += straight_part;
        if(z_prime > 0){
          return x_prime; // straight part of the quarter-wave
        } else { // low fold region
          const double &dz = z_prime;
          if(nhwave == 0){
            const double dx = x_prime - lwc()->m_FanFoldRadius;
            return lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
          } else {
            const double dx = x_prime + lwc()->m_FanFoldRadius;
            return sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
          }
        }
      } else { // ending quarter-wave
        z = lwc()->m_ActiveLength - z;
      }
    } else { // starting quarter-wave
      x = - x;
      sqw = true;
    }

    // start and finish quarter-waves
    const double tan_beta = sin_a/(1.0 + cos_a); //tan(alpha * 0.5);
    const double local_straight_section = lwc()->m_FanFoldRadius * tan_beta;
    if(z < - local_straight_section &&
       ( x < lwc()->m_FanFoldRadius ||
         x < - lwc()->m_StraightStartSection * z / local_straight_section / tan_beta ))
    {
      return sqw? x: (-x);
    }
    else {
      const double z_prime = z * cos_a + x * sin_a;
      const double x_prime = x * cos_a - z * sin_a;
      if (z_prime < local_straight_section) { // start fold region
        const double dz = local_straight_section - z_prime;
        const double dx = x_prime - lwc()->m_FanFoldRadius;
        if(sqw) return lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
        else    return sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
      } else {
        const double straight_part =
          (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
        if (z_prime <= straight_part) { // straight part of quarter-wave
          return sqw? x_prime: (-x_prime);
        } else { // regular fold region of the quarter-wave
          const double dz = straight_part - z_prime;
          const double dx = x_prime + lwc()->m_FanFoldRadius;
          if(sqw) return sqrt(dz*dz + dx*dx) - lwc()->m_FanFoldRadius;
          else    return lwc()->m_FanFoldRadius - sqrt(dz*dz + dx*dx);
        }
      }
    }
    // ???
    std::abort();
  }

  CLHEP::Hep3Vector DistanceCalculatorSaggingOff::NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &P, int /*fan_number*/) const
  {
    CLHEP::Hep3Vector result;
    double z = P.z() - lwc()->m_StraightStartSection;
    double x = P.x();
    double y = P.y();

#ifdef LWC_PARAM_ANGLE //old variant
    const double alpha = lwc()->parameterized_slant_angle(P.y());
    CxxUtils::sincos scalpha(alpha);
    const double cos_a = scalpha.cs, sin_a = scalpha.sn;
#else // parameterized sine
    double cos_a, sin_a;
    lwc()->m_vsincos_par.eval(P.y(), sin_a, cos_a);
#endif

    int nqwave;
    if(z < 0.) nqwave = 0;
    else nqwave = int(z / lwc()->m_QuarterWaveLength);
    bool begin_qw = false;
    if((nqwave % 2) != 0){
      nqwave ++;
      begin_qw = true;
    }
    nqwave /= 2;
    if(nqwave != 0 && nqwave != lwc()->m_NumberOfHalfWaves){
      z -= nqwave * lwc()->m_HalfWaveLength;
      if((nqwave % 2) == 0) x = -x;
      if(begin_qw){
        z = -z;
        x = -x;
      }
      const double z_prime = z * cos_a + x * sin_a;
      const double x_prime = x * cos_a - z * sin_a;
      const double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
      const double dz = straight_part - z_prime;
      if (dz > 0) result.set(0., y, z_prime);
      else {
        double a = atan(fabs(dz / (x_prime + lwc()->m_FanFoldRadius)));
        result.set(lwc()->m_FanFoldRadius * (cos(a) - 1), y, straight_part + lwc()->m_FanFoldRadius * sin(a));
      }
      result.rotateY(asin(sin_a));
      if(begin_qw){
        result.setX(-result.x());
        result.setZ(-result.z());
      }
      if((nqwave % 2) == 0) result.setX(-result.x());
      result.setZ(result.z() + nqwave * lwc()->m_HalfWaveLength);
    } else {
      if(nqwave == 0) x = -x;
      else z = lwc()->m_ActiveLength - z;
      const double tan_beta = sin_a/(1.0+cos_a); //tan(alpha * 0.5);
      const double local_straight_section = lwc()->m_FanFoldRadius * tan_beta;
      if(z < - local_straight_section &&
         ( x < lwc()->m_FanFoldRadius ||
           x < - lwc()->m_StraightStartSection * z / local_straight_section / tan_beta))
      {
        result.set(0., y, z);
      }
      else {
        const double z_prime = z * cos_a + x * sin_a;
        const double x_prime = x * cos_a - z * sin_a;
        if(z_prime < local_straight_section) {
          double a = fabs(atan((local_straight_section - z_prime) / (x_prime - lwc()->m_FanFoldRadius)));

          result.set(lwc()->m_FanFoldRadius * (1 - cos(a)), y, local_straight_section - lwc()->m_FanFoldRadius * sin(a));
        } else {
          double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
          if(z_prime <= straight_part) {
            result.set(0., y, z_prime);
          } else {
            double a = fabs(atan((straight_part - z_prime) /  (x_prime + lwc()->m_FanFoldRadius)) );
            result.set(lwc()->m_FanFoldRadius * (cos(a) - 1), y, straight_part + lwc()->m_FanFoldRadius * sin(a));
          }
        }
        result.rotateY(asin(sin_a));
      }
      if(nqwave != 0){
        result.setZ(lwc()->m_ActiveLength - result.z());
      } else {
        result.setX(-result.x());
      }
    }
    result.setZ(result.z() + lwc()->m_StraightStartSection);
    return result;
  }

  // IMPROVED VERSION
  CLHEP::Hep3Vector DistanceCalculatorSaggingOff::NearestPointOnNeutralFibre_ref(const CLHEP::Hep3Vector &P, int /*fan_number*/) const
  {
    CLHEP::Hep3Vector result;
    double z = P.z() - lwc()->m_StraightStartSection;
    double x = P.x();
    double y = P.y();

#ifdef LWC_PARAM_ANGLE //old variant
    const double alpha = lwc()->parameterized_slant_angle(P.y());
    CxxUtils::sincos scalpha(alpha);
    double cos_a = scalpha.cs, sin_a = scalpha.sn;
#else // parameterized sine
    double cos_a, sin_a;
    lwc()->m_vsincos_par.eval(P.y(), sin_a, cos_a);
#endif

    bool sqw = false;
    if(z > lwc()->m_QuarterWaveLength){
      if(z < m_EndQuarterWave){ // regular half-waves
        unsigned int nhwave = (unsigned int)(z / lwc()->m_HalfWaveLength + 0.5);
        const double zshift = lwc()->m_HalfWaveLength * nhwave;
        z -= zshift;
        const double straight_part =
          (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
        nhwave &= 1U;
        if(nhwave == 0) sin_a = - sin_a;
        const double z_prime = z * cos_a + x * sin_a;
        if(z_prime > straight_part){ // up fold
          const double x_prime = x * cos_a - z * sin_a;
          const double dz = straight_part - z_prime;
          double a1 = atan(fabs(dz / (x_prime + lwc()->m_FanFoldRadius)));
          const double x1 = lwc()->m_FanFoldRadius * (cos(a1) - 1.);
          const double z1 = straight_part + lwc()->m_FanFoldRadius * sin(a1);
          result.set(x1*cos_a - z1*sin_a, y, z1*cos_a + z1*sin_a);
          return result;
        } else if(z_prime > -straight_part){ // straight part
          result.set(-z_prime * sin_a, y, z_prime*cos_a + zshift);
          return result;
        } else { // low fold
          const double x_prime = x * cos_a - z * sin_a;
          const double dz = straight_part + z_prime;
          double a1 = atan(fabs(dz / (x_prime + lwc()->m_FanFoldRadius)));
          const double x1 = lwc()->m_FanFoldRadius * (cos(a1) - 1.);
          const double z1 = straight_part + lwc()->m_FanFoldRadius * sin(a1);
          result.set(x1*cos_a - z1*sin_a, y, z1*cos_a + z1*sin_a);
          return result;
        }
      } else { // ending quarter-wave
        z = lwc()->m_ActiveLength - z;
      }
    } else { // starting quarter-wave
      x = - x;
      sqw = true;
    }

    // start and finish quarter-waves
    const double tan_beta = sin_a / (1.0 + cos_a);
    const double local_straight_section = lwc()->m_FanFoldRadius * tan_beta;
    if(z < - local_straight_section &&
       (x < lwc()->m_FanFoldRadius ||
        x < - lwc()->m_StraightStartSection * z / local_straight_section / tan_beta))
    {
      result.set(0., y, z);
    }
    else {
      const double z_prime = z * cos_a + x * sin_a;
      const double x_prime = x * cos_a - z * sin_a;
      if(z_prime < local_straight_section) {
        double a = fabs(atan((local_straight_section - z_prime) / (x_prime - lwc()->m_FanFoldRadius)));
        result.set(lwc()->m_FanFoldRadius * (1 - cos(a)), y, local_straight_section - lwc()->m_FanFoldRadius * sin(a));
      } else {
        double straight_part = (lwc()->m_QuarterWaveLength - lwc()->m_FanFoldRadius * sin_a) / cos_a;
        if(z_prime <= straight_part) {
          result.set(0., y, z_prime);
        } else {
          double a = fabs(atan((straight_part - z_prime) /  (x_prime + lwc()->m_FanFoldRadius)) );
          result.set(lwc()->m_FanFoldRadius * (cos(a) - 1), y, straight_part + lwc()->m_FanFoldRadius * sin(a));
        }
      }
      result.rotateY(asin(sin_a));
    }
    if(sqw) result.setX(-result.x());
    else result.setZ(lwc()->m_ActiveLength - result.z());
    result.setZ(result.z() + lwc()->m_StraightStartSection);
    return result;
  }

  /*
  input is in local fan's coordinate system
  side: < 0 - lower phi
        > 0 - greater phi
        = 0 - neutral fibre
  */
  double DistanceCalculatorSaggingOff::AmplitudeOfSurface(const CLHEP::Hep3Vector& P, int side, int /*fan_number*/) const
  {
    double result = 0.;
    double rho = lwc()->m_FanFoldRadius;
    double z = P.z() - lwc()->m_StraightStartSection;

#ifdef LWC_PARAM_ANGLE //old variant
    const double alpha = lwc()->parameterized_slant_angle(P.y());
    //double cos_a, sin_a;
    //::sincos(alpha, &sin_a, &cos_a);
    CxxUtils::sincos scalpha(alpha);
    const double cos_a = scalpha.cs, sin_a = scalpha.sn;
    // parameterized sine
#else
    double cos_a, sin_a;
    lwc()->m_vsincos_par.eval(P.y(), sin_a, cos_a);
#endif

    // determination of the nearest quarter-wave number
    int nqwave;
    if(z < 0.) nqwave = 0;
    else nqwave = int(z / lwc()->m_QuarterWaveLength);
    bool begin_qw = false;
    if((nqwave % 2) != 0){
      nqwave ++;
      begin_qw = true;
    }
    nqwave /= 2;
    // now nqwave is not the number of quarter-wave but the number of half-wave
    // half-waves with last and zero numbers are not really half-waves but start
    // and finish quarter-waves
    // It means that half-wave number 1 begins after starting quarter-wave
    if(nqwave != 0 && nqwave != lwc()->m_NumberOfHalfWaves){ // regular half-waves
      z -= nqwave * lwc()->m_HalfWaveLength;
      if(begin_qw) z = -z;
      double dz = lwc()->m_QuarterWaveLength - z;

      int local_side = 1;
      if((nqwave % 2) == 0){
        if(begin_qw) local_side = -1;
      } else {
        if(!begin_qw) local_side = -1;
      }

      rho += lwc()->m_FanHalfThickness * local_side * side;

      if(dz >= rho * sin_a){
        result = z * sin_a / cos_a; // straight part of the quarter-wave
      } else { // fold region
        result = (lwc()->m_QuarterWaveLength * sin_a - rho) / cos_a
          + sqrt(rho * rho - dz * dz);
      }
      result *= -local_side;
      if(side < 0) result += lwc()->m_FanHalfThickness / cos_a;
      else if(side > 0) result -= lwc()->m_FanHalfThickness / cos_a;

    } else { // start and finish quarter-waves
      int local_side = 1;
      if(nqwave == 0) { // start quarter-wave
        local_side = -1;
      } else { // finish quarter-wave
        z = lwc()->m_ActiveLength - z;
      }

      const double rho1i = lwc()->m_FanFoldRadius;
      const double tan_beta = sin_a/(1.0+cos_a); //tan(alpha * 0.5);
      const double min_local_fold_region = rho1i * tan_beta;

      if(z <= - min_local_fold_region){
        result = - side * lwc()->m_FanHalfThickness;
      } else {
        const double rho1 = rho1i + lwc()->m_FanHalfThickness * side * local_side;

        const double max_local_fold_region = rho1 * sin_a - min_local_fold_region;
        //const double max_local_fold_region = rho1 * tan_beta * (1. + cos_a) - min_local_fold_region;
        if(z < max_local_fold_region){ // start fold region
          z += min_local_fold_region;
          result = rho1 - sqrt(rho1 * rho1 - z * z);
          if(nqwave == 0) result = -result;
          if(side < 0) result += lwc()->m_FanHalfThickness;
          else if(side > 0) result -= lwc()->m_FanHalfThickness;
        } else {
          rho -= lwc()->m_FanHalfThickness * local_side * side;
          const double dz = lwc()->m_QuarterWaveLength - z;
          if(dz >= rho * sin_a){
            result = z * sin_a / cos_a; // straight part of the quarter-wave
          } else { // regular fold region
            result = (lwc()->m_QuarterWaveLength * sin_a - rho) / cos_a
                     + sqrt(rho * rho - dz * dz);
          }
          if(nqwave == 0) result = -result;
          if(side < 0) result += lwc()->m_FanHalfThickness / cos_a;
          else if(side > 0) result -= lwc()->m_FanHalfThickness / cos_a;
        }
      }
    }
    return result;
  }

}
