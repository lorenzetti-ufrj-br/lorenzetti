/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

#include "MagFieldElements/BFieldCacheZR.h"
#include <cmath>

void
BFieldCacheZR::getB(const double* ATH_RESTRICT xyz,
                    double r,
                    double* ATH_RESTRICT B,
                    double* ATH_RESTRICT deriv) const
{
  const double x = xyz[0];
  const double y = xyz[1];
  const double z = xyz[2];
  // fractional position inside this bin
  const double fz = (z - m_zmin) * m_invz;
  const double gz = 1.0 - fz;
  const double fr = (r - m_rmin) * m_invr;
  const double gr = 1.0 - fr;
  // interpolate field values in z, r
  double Bzr[2];
  for (int i = 0; i < 2; ++i) { // z, r components
    const double* field = m_field[i];
    Bzr[i] = gz * (gr * field[0] + fr * field[1]) +
             fz * (gr * field[2] + fr * field[3]);
  }
  // convert (Bz,Br) to (Bx,By,Bz)
  double invr;
  if (r > 0.0) {
    invr = 1.0 / r;
  } else {
    invr = 0.0;
  }
  const double c(x * invr);
  const double s(y * invr);
  B[0] = Bzr[1] * c;
  B[1] = Bzr[1] * s;
  B[2] = Bzr[0];

  // compute field derivatives if requested
  if (deriv) {
    std::array<double, 2> dBdz{};
    std::array<double, 2> dBdr{};
    for (int j = 0; j < 2; ++j) { // Bz, Br components
      const double* field = m_field[j];
      dBdz[j] =
        m_invz * (gr * (field[2] - field[0]) + fr * (field[3] - field[1]));
      dBdr[j] =
        m_invr * (gz * (field[1] - field[0]) + fz * (field[3] - field[2]));
    }
    // convert to cartesian coordinates
    const double cc = c * c;
    const double cs = c * s;
    const double ss = s * s;
    const double sinvr = s * invr;
    const double cinvr = c * invr;
    deriv[0] = cc * dBdr[1] + sinvr * B[1];
    deriv[1] = cs * dBdr[1] - cinvr * B[1];
    deriv[2] = c * dBdz[1];
    deriv[3] = cs * dBdr[1] - sinvr * B[0];
    deriv[4] = ss * dBdr[1] + cinvr * B[0];
    deriv[5] = s * dBdz[1];
    deriv[6] = c * dBdr[0];
    deriv[7] = s * dBdr[0];
    deriv[8] = dBdz[0];
  }
}

