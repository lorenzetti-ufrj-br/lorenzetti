/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

//
// BFieldVector.h
// Magnetic field value stored in the map.
// We allow short (usual case)  double (special case)
//
// Masahiro Morii, Harvard University
//
// Athena MT RD Schaffer , C Anastopoulos
//
#ifndef BFIELDVECTOR_H
#define BFIELDVECTOR_H

#include <array>
#include <cstdlib>

template<class T>
class BFieldVector
{
public:
  static_assert(
    (std::is_same<T, short>::value || std::is_same<T, double>::value),
    "Type for the BField Vector must be one of short or double");

  // Default
  BFieldVector() = default;
  BFieldVector(const BFieldVector&) = default;
  BFieldVector(BFieldVector&&) = default;
  BFieldVector& operator=(const BFieldVector&) = default;
  BFieldVector& operator=(BFieldVector&&) = default;
  ~BFieldVector() = default;

  BFieldVector(T Bz, T Br, T Bphi)
    : m_B{ Bz, Br, Bphi }
  {}
  // setter
  void set(T Bz, T Br, T Bphi) { m_B = { Bz, Br, Bphi }; }

  // accessors
  T z() const { return m_B[0]; }
  T r() const { return m_B[1]; }
  T phi() const { return m_B[2]; }
  // array-like accessor
  T operator[](size_t i) const { return m_B[i]; }

private:
  std::array<T, 3> m_B;
};

#endif
