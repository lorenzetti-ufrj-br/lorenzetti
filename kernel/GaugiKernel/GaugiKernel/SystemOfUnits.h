/***********************************************************************************\
* (c) Copyright 1998-2019 CERN for the benefit of the LHCb and ATLAS collaborations *
* Adapted for Lorenzetti / GaugiKernel                                              *
\***********************************************************************************/
#ifndef GAUGI_SYSTEM_OF_UNITS_H
#define GAUGI_SYSTEM_OF_UNITS_H

namespace Gaugi {
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
} // namespace Gaugi

// Backward-compatibility namespace alias for Athena / Gaudi components
namespace Gaudi {
  namespace Units = Gaugi::Units;
}

#endif /* GAUGI_SYSTEM_OF_UNITS_H */
