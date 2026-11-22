/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef __LArWheelCalculator_Impl_IDistanceCalculator_H__
#define __LArWheelCalculator_Impl_IDistanceCalculator_H__


#include "CLHEP/Vector/ThreeVector.h"

namespace LArWheelCalculator_Impl
{

  /// @class IDistanceCalculator
  /// Abstract interface for calculator classes that handle distance
  /// calculation to parts of the LAr endcap.
  ///
  class IDistanceCalculator
  {

    public:

      /// Virtual destructor
      virtual ~IDistanceCalculator() {};

      /// @name Geometry methods
      /// @{

      virtual double DistanceToTheNeutralFibre(const CLHEP::Hep3Vector &p,
                                               int fan_number) const = 0;

      virtual CLHEP::Hep3Vector NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &p,
                                                           int fan_number) const = 0;

      virtual double AmplitudeOfSurface(const CLHEP::Hep3Vector& p, int side,
                                        int fan_number) const = 0;

      /// @}

  };

}

#endif // __LArWheelCalculator_Impl_IDistanceCalculator_H__
