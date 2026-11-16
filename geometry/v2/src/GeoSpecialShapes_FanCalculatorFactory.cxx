/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.


#include "GeoSpecialShapes/LArWheelCalculator_Impl/FanCalculatorFactory.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/ModuleFanCalculator.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/WheelFanCalculator.h"

namespace LArWheelCalculator_Impl
{

  IFanCalculator* FanCalculatorFactory::Create(bool isSaggingOn, bool isModule,
                                               LArWheelCalculator* lwc)

  {
    if (isModule) {
      return new ModuleFanCalculator(lwc);
    }
    if (isSaggingOn) {
      return new WheelFanCalculator<SaggingOn_t>(lwc);
    } else {
      return new WheelFanCalculator<SaggingOff_t>(lwc);
    }
  }

}
