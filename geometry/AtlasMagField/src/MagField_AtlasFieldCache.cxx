/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

//
// AtlasFieldCache.cxx
//
// Local cache for magnetic field (based on MagFieldServices/AtlasFieldSvcTLS.h)
//
// R.D.Schaffer -at- cern.ch
//
#include "MagFieldElements/AtlasFieldCache.h"

#include <cmath>
#include <iostream>

namespace {
/* In Gaudi Units
 * Units.tesla
 * = Units.volt * Units.second / Units.meter2 = 1e-3
 * So 1kT  is 1
 * Unit.gauss = 1e-4 * Units.tesla
 * the number below is  0.1 * 1e-3 * 1e-4 = 1e-8
 * So 0.1 Gauss in Units of kT (which is what we return)
 */
constexpr double defaultB = 0.1 * Gaudi::Units::gauss;
}

#if defined(__GNUC__)
// We compile this package with optimization, even in debug builds; otherwise,
// the heavy use of Eigen makes it too slow.  However, from here we may call
// to out-of-line Eigen code that is linked from other DSOs; in that case,
// it would not be optimized.  Avoid this by forcing all Eigen code
// to be inlined here if possible.
[[gnu::flatten]]
#endif
void
MagField::AtlasFieldCache::getField(const double* ATH_RESTRICT xyz,
                                    double* ATH_RESTRICT bxyz,
                                    double* ATH_RESTRICT deriv)
{
  // Allow for the case of no map for testing
  if (m_fieldMap == nullptr) {
    // return default
    bxyz[0] = bxyz[1] = bxyz[2] = defaultB;
    // return zero gradient if requested
    if (deriv) {
      for (int i = 0; i < 9; i++) {
        deriv[i] = 0.;
      }
    }
    return;
  }

  const double x = xyz[0];
  const double y = xyz[1];
  const double z = xyz[2];
  const double r = std::sqrt(x * x + y * y);
  const double phi = std::atan2(y, x);

  // Check that the cached z,r, phi cell is valid
  // and if we are still inside it
  if (!m_cache3d.inside(z, r, phi)) {
    // if not we need to find and cache a new cell
    if (!fillFieldCache(z, r, phi)) {
      // caching failed
      // outside the valid map volume
      // return default
      bxyz[0] = bxyz[1] = bxyz[2] = defaultB;
      // return zero gradient if requested
      if (deriv) {
        for (int i = 0; i < 9; i++) {
          deriv[i] = 0.;
        }
      }
      return;
    }
  }

  // do interpolation (cache3d has correct scale factor)
  m_cache3d.getB(xyz, r, phi, bxyz, deriv);

  if (!m_cond) {
    return;
  }
  // add biot savart component - must add in scale factor to avoid changing
  // conductor SF since the conductor is part of the static magnetic field model
  const size_t condSize = m_cond->size();
  for (size_t i = 0; i < condSize; i++) {
    (*m_cond)[i].addBiotSavart(m_scaleToUse, xyz, bxyz, deriv);
  }
}

void
MagField::AtlasFieldCache::getFieldZR(const double* ATH_RESTRICT xyz,
                                      double* ATH_RESTRICT bxyz,
                                      double* ATH_RESTRICT deriv)
{

  // Allow for the case of no map for testing
  if (m_fieldMap == nullptr) {
    // return default
    bxyz[0] = bxyz[1] = bxyz[2] = defaultB;
    // return zero gradient if requested
    if (deriv) {
      for (int i = 0; i < 9; i++) {
        deriv[i] = 0.;
      }
    }
    return;
  }

  const double x = xyz[0];
  const double y = xyz[1];
  const double z = xyz[2];
  const double r = std::sqrt(x * x + y * y);

  // Check that the cached z,r, cell is valid
  // and if we are still inside it
  if (!m_cacheZR.inside(z, r)) {
    // cached cell is invalid -> refresh cached cell
    if (!fillFieldCacheZR(z, r)) {
      // No cell found -> outside the valid z-r map volume
      // fallback to calling
      // the full version of getField()
      getField(xyz, bxyz, deriv);
      return;
    }
  }
  // do interpolation
  m_cacheZR.getB(xyz, r, bxyz, deriv);
}

