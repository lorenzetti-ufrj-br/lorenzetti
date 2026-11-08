/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

/**
 * BFieldCache.h
 *
 * Cache of one bin of the magnetic field map.
 * Defined by ranges in z, r, phi, and the B vectors at the 8 corners of the
 * "bin".
 *
 * Masahiro Morii, Harvard University
 *
 * AthenaMT : RD Schaffer , Christos Anastopoulos
 */

#ifndef BFIELDCACHE_H
#define BFIELDCACHE_H

#include "CxxUtils/restrict.h"
#include "CxxUtils/vec.h"
#include "MagFieldElements/BFieldVector.h"

class BFieldCache
{
public:
  // default constructor sets unphysical boundaries, so that inside() will fail
  BFieldCache() = default;
  // make this cache invalid, so that inside() will fail
  void invalidate();

  // set the z, r, phi range that defines the bin
  void setRange(double zmin,
                double zmax,
                double rmin,
                double rmax,
                double phimin,
                double phimax);

  // set the 3x8 field array.
  void setField(const CxxUtils::vec<double, 8>& field1,
                const CxxUtils::vec<double, 8>& field2,
                const CxxUtils::vec<double, 8>& field3);

  // set the multiplicative factor for the field vectors
  void setBscale(double bscale);
  float bscale() const;

  // test if (z, r, phi) is inside this bin
  bool inside(double z, double r, double phi) const;
  // interpolate the field and return B[3].
  // also compute field derivatives if deriv[9] is given.
  void getB(const double* ATH_RESTRICT xyz,
            double r,
            double phi,
            double* ATH_RESTRICT B,
            double* ATH_RESTRICT deriv = nullptr) const;

private:
  // bin range in z
  double m_zmin = 0.0;
  double m_zmax = 0.0;
  // bin range in r
  double m_rmin = 0.0;
  double m_rmax = 0.0;
  // bin range in phi
  double m_phimin = 0.0;
  double m_phimax = -1.0;
  // 1/(bin size) in z, r, phi
  double m_invz;
  double m_invr;
  double m_invphi;
  double m_scale;                   // unit of m_field in kT
  alignas(16) double m_field[3][8]; // (Bz,Br,Bphi) at 8 corners of the bin
};

#include "MagFieldElements/BFieldCache.icc"
#endif
