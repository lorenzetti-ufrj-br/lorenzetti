/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

/*
 * BFieldMeshZR.h
 *
 * A 2-dim z-r mesh inside the solenoid field map
 *
 * Masahiro Morii, Harvard University
 *
 * AthenaMT : RD Schaffer , Christos Anastopoulos
 */
#ifndef BFIELDMESHZR_H
#define BFIELDMESHZR_H

#include "MagFieldElements/BFieldCacheZR.h"
#include "MagFieldElements/BFieldVectorZR.h"
#include <array>
#include <cmath>
#include <vector>

class BFieldMeshZR
{
public:
  // constructor
  BFieldMeshZR(double zmin, double zmax, double rmin, double rmax);
  // allocate space to vectors
  void reserve(int nz, int nr);
  // add elements to vectors
  void appendMesh(int i, double mesh);
  void appendField(const BFieldVectorZR& field);
  // build LUT
  void buildLUT();
  // test if a point is inside this zone
  bool inside(double z, double r) const;
  // find the bin
  inline void getCache(double z,
                       double r,
                       BFieldCacheZR& cache,
                       double scaleFactor = 1.0) const;
  // accessors
  double min(size_t i) const;
  double max(size_t i) const;
  double zmin() const;
  double zmax() const;
  double rmin() const;
  double rmax() const;
  unsigned nmesh(size_t i) const;
  double mesh(size_t i, size_t j) const;
  unsigned nfield() const;
  const BFieldVectorZR& field(size_t i) const;
  int memSize() const;

private:
  std::array<double, 2> m_min;
  std::array<double, 2> m_max;
  std::array<std::vector<double>, 2> m_mesh;
  std::vector<BFieldVectorZR> m_field;
  // look-up table and related variables
  std::array<std::vector<int>, 2> m_LUT;
  std::array<double, 2> m_invUnit; // inverse unit size in the LUT
  int m_zoff{0};
};

#include "MagFieldElements/BFieldMeshZR.icc"
#endif
