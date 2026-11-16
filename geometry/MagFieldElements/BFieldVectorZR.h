/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).

//
// BFieldVectorZR.h
//
// Magnetic field value (Bz,Br) stored in 2d map.
//
// Masahiro Morii, Harvard University
//
// Athena MT RD Schaffer , C Anastopoulos
//
#ifndef BFIELDVECTORZR_H
#define BFIELDVECTORZR_H
#include <array>
#include <cstdlib>
class BFieldVectorZR
{
public:
  // default
  BFieldVectorZR() = default;
  BFieldVectorZR(const BFieldVectorZR&) = default;
  BFieldVectorZR(BFieldVectorZR&&) = default;
  BFieldVectorZR& operator=(const BFieldVectorZR&) = default;
  BFieldVectorZR& operator=(BFieldVectorZR&&) = default;
  ~BFieldVectorZR() = default;

  //constructor
  BFieldVectorZR(double Bz, double Br)
    : m_B{ Bz, Br }
  {}
  // setter
  void set(double Bz, double Br) { m_B = { Bz, Br }; }
  // accessors
  double z() const { return m_B[0]; }
  double r() const { return m_B[1]; }
  // array-like accessor
  double operator[](size_t i) const { return m_B[i]; }

private:
  std::array<double, 2> m_B;
};

#endif
