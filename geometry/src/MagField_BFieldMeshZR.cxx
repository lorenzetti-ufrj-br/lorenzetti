/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

//
// BFieldMeshZR.cxx
//
// A 2-dim z-r mesh inside the solenoid field map
//
// Masahiro Morii, Harvard University
//
#include "MagFieldElements/BFieldMeshZR.h"

//
// Construct the look-up table to accelerate bin-finding.
//
void
BFieldMeshZR::buildLUT()
{
  for (int j = 0; j < 2; j++) { // z, r
    // determine the unit size, q, to be used in the LUTs
    double width = m_mesh[j].back() - m_mesh[j].front();
    double q(width);
    for (unsigned i = 0; i < m_mesh[j].size() - 1; i++) {
      q = std::min(q, m_mesh[j][i + 1] - m_mesh[j][i]);
    }
    // find the number of units in the LUT
    int n = int(width / q) + 1;
    q = width / (n + 0.5);
    m_invUnit[j] = 1.0 / q; // new unit size
    n++;
    int m = 0; // mesh number
    m_LUT[j].reserve(n);
    for (int i = 0; i < n; i++) { // LUT index
      if (i * q + m_mesh[j].front() > m_mesh[j][m + 1]) {
        m++;
      }
      m_LUT[j].push_back(m);
    }
  }
  m_zoff = m_mesh[1].size(); // index offset for incrementing z by 1
}

int
BFieldMeshZR::memSize() const
{
  int size = 0;
  size += sizeof(double) * 6;
  size += sizeof(int) * 1;
  for (int i = 0; i < 2; i++) {
    size += sizeof(double) * m_mesh[i].capacity();
    size += sizeof(int) * m_LUT[i].capacity();
  }
  size += sizeof(BFieldVectorZR) * m_field.capacity();
  return size;
}
