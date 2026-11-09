/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef __LArWheelCalculator_Impl_DistanceCalculatorSaggingOff_H__
#define __LArWheelCalculator_Impl_DistanceCalculatorSaggingOff_H__


#include "IDistanceCalculator.h"

class LArWheelCalculator;

namespace LArWheelCalculator_Impl
{

  /// @class DistanceCalculatorSaggingOff
  /// @brief Implements details of distance calculation to parts of the
  /// LAr endcap without sagging corrections.
  ///
  class DistanceCalculatorSaggingOff : public IDistanceCalculator
  {

    public:

      /// Constructor
      DistanceCalculatorSaggingOff(LArWheelCalculator* lwc);

      /// @name Geometry methods
      /// @{
      virtual double DistanceToTheNeutralFibre(const CLHEP::Hep3Vector &p, int fan_number) const;
      virtual double DistanceToTheNeutralFibre_ref(const CLHEP::Hep3Vector &p, int fan_number) const;
      virtual CLHEP::Hep3Vector NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &p, int fan_number) const;
      virtual CLHEP::Hep3Vector NearestPointOnNeutralFibre_ref(const CLHEP::Hep3Vector &p, int fan_number) const;
      virtual double AmplitudeOfSurface(const CLHEP::Hep3Vector& P, int side, int fan_number) const;
      /// @}

      /// Return the calculator:
      inline const LArWheelCalculator *lwc() const { return m_lwc; };

    private:

      LArWheelCalculator* m_lwc;
      double m_EndQuarterWave;

  };

}

#endif // __LArWheelCalculator_Impl_IDistanceCalculatorOff_H__
