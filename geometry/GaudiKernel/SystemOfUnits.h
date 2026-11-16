/***********************************************************************************\
* (c) Copyright 1998-2019 CERN for the benefit of the LHCb and ATLAS collaborations *
*                                                                                   *
* This software is distributed under the terms of the Apache version 2 licence,     *
* copied verbatim in the file "LICENSE".                                            *
*                                                                                   *
* In applying this licence, CERN does not waive the privileges and immunities       *
* granted to it by virtue of its status as an Intergovernmental Organization        *
* or submit itself to any jurisdiction.                                             *
\***********************************************************************************/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: shim of the Gaudi header GaudiKernel/SystemOfUnits.h (Gaudi of AthenaExternals 23.0.14), reduced to the chain of definitions behind Gaudi::Units::gauss (the only unit used by MagFieldElements), copied with the same expressions so the constants are bit-identical; tesla and kilogauss kept for convenience.
// -*- C++ -*-
// ----------------------------------------------------------------------
// HEP coherent system of Units
//
// This file has been provided to CLHEP by Geant4 (simulation toolkit for HEP).
// ----------------------------------------------------------------------

#ifndef GAUDI_SYSTEM_OF_UNITS_H
#define GAUDI_SYSTEM_OF_UNITS_H

namespace Gaudi {
  namespace Units {

    //
    // Length [L]
    //
    constexpr double millimeter = 1.;
    constexpr double meter      = 1000. * millimeter;
    constexpr double meter2     = meter * meter;

    //
    // Time [T]
    //
    constexpr double nanosecond = 1.;
    constexpr double second     = 1.e+9 * nanosecond;

    //
    // Electric charge [Q]
    //
    constexpr double eplus = 1.; // positron charge

    //
    // Energy [E]
    //
    constexpr double megaelectronvolt = 1.;

    //
    // Electric potential [E/Q]
    //
    constexpr double megavolt = megaelectronvolt / eplus;
    constexpr double volt     = 1.e-6 * megavolt;

    //
    // Magnetic Field [T/L^2]
    //
    constexpr double tesla = volt * second / meter2; // tesla =0.001*megavolt*ns/mm2

    constexpr double gauss     = 1.e-4 * tesla;
    constexpr double kilogauss = 1.e-1 * tesla;

  } // namespace Units
} // namespace Gaudi

#endif /* GAUDI_SYSTEM_OF_UNITS_H */
