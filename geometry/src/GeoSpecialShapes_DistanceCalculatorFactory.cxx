/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.


#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorFactory.h"

#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorSaggingOff.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorSaggingOn.h"

namespace LArWheelCalculator_Impl
{

  IDistanceCalculator* DistanceCalculatorFactory::Create(const std::string & sagging_opt,
                                                         LArWheelCalculator* lwc)

  {
    // the same condition is in LArWheelCalculator constructor
    bool SaggingOn = (sagging_opt != "" && sagging_opt != "off")? true: false;

    if (SaggingOn) {
      return new DistanceCalculatorSaggingOn(sagging_opt, lwc);
    } else {
      return new DistanceCalculatorSaggingOff(lwc);
    }
  }

}
