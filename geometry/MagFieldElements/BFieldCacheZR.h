/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

//
// BFieldCacheZR.h
//
// Cashe of one bin of the magnetic field map.
// Defined by ranges in z, r, and the (Bz, Br) vectors at the 4 corners of the
// "bin".
//
// Masahiro Morii, Harvard University
//
#ifndef BFIELDCACHEZR_H
#define BFIELDCACHEZR_H

#include "MagFieldElements/BFieldVectorZR.h"
#include "CxxUtils/restrict.h"
#include <cmath>

class BFieldCacheZR
{
public:
  // invalidate this cache, so that inside() will fail
  void invalidate();
  // set the z, r range that defines the bin
  void setRange(double zmin, double zmax, double rmin, double rmax);
  // set the field values at each corner (rescale for current scale factor)
  void setField(int i, const BFieldVectorZR& field, double scaleFactor = 1.0);
  // set the multiplicative factor for the field vectors
  // test if (z, r) is inside this bin
  bool inside(double z, double r) const;
  // interpolate the field and return B[3].
  // also compute field derivatives if deriv[9] is given.
  void getB(const double*  ATH_RESTRICT xyz,
            double r,
            double* ATH_RESTRICT B,
            double* ATH_RESTRICT deriv = nullptr) const;

private:
  // default unphysical boundaries, so that inside() will fail
  double m_zmin{0}, m_zmax{-1};   // bin range in z
  double m_rmin{0}, m_rmax{-1};   // bin range in r
  double m_invz{-1}, m_invr{-1};  // 1/(bin size) in z, r
  double m_field[2][4];   // (Bz,Br) at 4 corners of the bin
};
#include "MagFieldElements/BFieldCacheZR.icc"
#endif
