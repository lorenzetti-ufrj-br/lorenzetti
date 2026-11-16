/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4Code/LArG4Code/LArG4BirksLaw.h) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef LArG4BirksLaw_h_
#define LArG4BirksLaw_h_

class LArG4BirksLaw {

 public:

  // Constructor.  Set the density of liquid argon and the Birk's law
  // constant K:

  LArG4BirksLaw(double density, double k):
    m_LArDensity(density), m_BirksLawK(k) {}

  // Get the K factor
  double k() const { return m_BirksLawK;}
  
  // Get the LAr Density
  double LArDensity() const { return m_LArDensity;} 

  //
  // Function call operator
  //
  double operator () (double dEMeV, double dXCm, double EFieldKVPerCm)  const;
  

 private:
  
  // Density:  g/cm^3
  double m_LArDensity;  

  // Birk's K  kV/cm g/(cm^2 MeV)
  double m_BirksLawK;

};

#endif
