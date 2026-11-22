/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef __LArWheelCalculator_Impl_DistanceCalculatorFactory_H__
#define __LArWheelCalculator_Impl_DistanceCalculatorFactory_H__

// DistanceCalculator factory
// calculator creation depends on sagging mode

#include <string>
#include "IDistanceCalculator.h"
class LArWheelCalculator;
namespace LArWheelCalculator_Impl
{
  /// @todo Why is this a class???
  class DistanceCalculatorFactory
  {
    public:
      static IDistanceCalculator* Create(const std::string & sagging_opt,
                                         LArWheelCalculator* lwc);
  };

}

#endif // __LArWheelCalculator_Impl_DistanceCalculatorFactory_H__
