/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

/**
 *
 * @class BFieldZone.h
 *
 * @brief
 * A "zone" inside the field map
 * Expands BFieldMesh<short>
 * adding an id
 * and a vector of current conductors.
 *
 * @author Masahiro Morii, Harvard University
 *
 * @author RD Schaffer , Christos Anastopoulos (Athena MT)
 */

#ifndef BFIELDZONE_H
#define BFIELDZONE_H

#include "CxxUtils/restrict.h"
#include "MagFieldElements/BFieldCond.h"
#include "MagFieldElements/BFieldMesh.h"
#include <vector>

class BFieldZone : public BFieldMesh<short>
{
public:
  // constructor
  BFieldZone(int id,
             double zmin,
             double zmax,
             double rmin,
             double rmax,
             double phimin,
             double phimax,
             double scale);
  /** @brief add elements to the current conductors vector*/
  void appendCond(const BFieldCond& cond);
  /** @brief compute Biot-Savart magnetic field and add to B[3]*/
  void addBiotSavart(const double* ATH_RESTRICT xyz,
                     double* ATH_RESTRICT B,
                     double* ATH_RESTRICT deriv = nullptr) const;
  // accessors
  int id() const;
  unsigned ncond() const;
  const BFieldCond& cond(int i) const;
  const std::vector<BFieldCond>* condVector() const;
  int memSize() const;
  // adjust the min/max edges to a new value
  void adjustMin(int i, double x);
  void adjustMax(int i, double x);

private:
  int m_id;                       // zone ID number
  std::vector<BFieldCond> m_cond; // list of current conductors
};

#include "BFieldZone.icc"

#endif
