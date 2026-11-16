/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef __LArWheelCalculator_Impl_FanCalculatorFactory_H__
#define __LArWheelCalculator_Impl_FanCalculatorFactory_H__


#include "IFanCalculator.h"

class LArWheelCalculator;

namespace LArWheelCalculator_Impl
{

  /// @class FanCalculatorFactory
  /// @brief A factory for FanCalculators
  ///
  /// Calculator creation depends on sagging mode and wheel/module calo.
  ///
  class FanCalculatorFactory
  {
    public:
      static IFanCalculator* Create(bool isSaggingOn, bool isModule,
                                    LArWheelCalculator* lwc);
  };

}

#endif // __LArWheelCalculator_Impl_FanCalculatorFactory_H__
