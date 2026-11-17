/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/

// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: CxxUtils/features.h always (Athena branch); no CLASS_DEF (no StoreGate).
#ifndef GEOSPECIALSHAPES_LARWHEELCALCULATOR_H
#define GEOSPECIALSHAPES_LARWHEELCALCULATOR_H

#include <array>
#include <vector>

// FMV and other checks
#if 1 // Lorenzetti port: the Athena branch (CxxUtils/features.h of geometry/CxxUtils)
// For athena
  #include "CxxUtils/features.h"
#else
// When run outside of Athena
  #define HAVE_VECTOR_SIZE_ATTRIBUTE 1
  #ifdef __APPLE__
    #define CXXUTILS_FEATURES_H 1
  #endif
#endif

#include "CLHEP/Vector/ThreeVector.h"
#if 0 // Lorenzetti port: no StoreGate class identifier
    #include "AthenaKernel/CLASS_DEF.h"
#endif // XAOD_STANDALONE

#if HAVE_VECTOR_SIZE_ATTRIBUTE
    #include "vec_parametrized_sincos.h"
#endif
#include "GeoSpecialShapes/LArWheelCalculatorEnums.h"

#define LARWC_SINCOS_POLY 5
#define LARWC_DTNF_NEW

struct EMECData;

//#define HARDDEBUG

// Forward declarations
namespace LArWheelCalculator_Impl {
  class IDistanceCalculator;
  class DistanceCalculatorSaggingOff;
  class DistanceCalculatorSaggingOn;

  class IFanCalculator;
  class ModuleFanCalculator;
  template <typename SaggingType> class WheelFanCalculator;
  template <typename SaggingType> class DistanceToTheNeutralFibre_OfFan;
}

/// @class LArWheelCalculator
/// This class separates some of the geometry details of the LAr
/// endcap.
/// 26-May-2009 AMS: remove all previous comments from here as obsoleted
///
class LArWheelCalculator
{

    friend class LArWheelCalculator_Impl::DistanceCalculatorSaggingOff;
    friend class LArWheelCalculator_Impl::DistanceCalculatorSaggingOn;
    friend class LArWheelCalculator_Impl::ModuleFanCalculator;
    template <typename SaggingType> friend class LArWheelCalculator_Impl::WheelFanCalculator;
    template <typename SaggingType> friend class LArWheelCalculator_Impl::DistanceToTheNeutralFibre_OfFan;

  public:

  LArWheelCalculator(const EMECData & emecData, LArG4::LArWheelCalculator_t a_wheelType, int zside = 1);
    virtual ~LArWheelCalculator();

    LArWheelCalculator (const LArWheelCalculator&) = delete;
    LArWheelCalculator& operator= (const LArWheelCalculator&) = delete;

    static const char *LArWheelCalculatorTypeString(LArG4::LArWheelCalculator_t);
    double GetFanHalfThickness(LArG4::LArWheelCalculator_t) const;

    // "Get constant" methods:
    double GetWheelThickness() const { return m_WheelThickness; }
    double GetdWRPtoFrontFace() const { return m_dWRPtoFrontFace; }
    double GetStraightStartSection() const { return m_StraightStartSection; }
    virtual LArG4::LArWheelCalculator_t type() const { return m_type; }
    // "zShift" is the z-distance (cm) that the EM endcap is shifted
    // (due to cabling, etc.)
    int GetAtlasZside() const { return m_AtlasZside; }
    double zShift() const { return m_zShift; }
    double GetFanFoldRadius() const { return m_FanFoldRadius; }
    double GetZeroFanPhi() const { return m_ZeroFanPhi; }
    int GetNumberOfWaves() const { return m_NumberOfWaves; }
    int GetNumberOfHalfWaves() const { return m_NumberOfHalfWaves; }
    int GetNumberOfFans() const { return m_NumberOfFans; }

    double GetActiveLength() const { return m_ActiveLength; }
    double GetFanStepOnPhi() const { return m_FanStepOnPhi; }
    double GetHalfWaveLength() const { return m_HalfWaveLength; }
    double GetQuarterWaveLength() const { return m_QuarterWaveLength; }
    double GetWheelRefPoint() const { return m_zWheelRefPoint; }
    double GetFanHalfThickness() const { return m_FanHalfThickness; }

    bool GetisModule() const { return m_isModule; }
    bool GetisElectrode() const { return m_isElectrode; }
    bool GetisInner() const { return m_isInner; }
    bool GetisBarrette() const { return m_isBarrette; }
    bool GetisBarretteCalib() const { return m_isBarretteCalib; }

    double GetWheelInnerRadius(double *) const;
    void GetWheelOuterRadius(double *) const;

    double GetElecFocaltoWRP() const { return m_dElecFocaltoWRP; }
    // "set constant" method:

    int GetFirstFan() const { return m_FirstFan; }
    int GetLastFan() const { return m_LastFan; }

    int GetStartGapNumber() const { return m_ZeroGapNumber; }
    void SetStartGapNumber(int n) { m_ZeroGapNumber = n; }

    /// @name geometry methods
    /// @{

    /// Determines the nearest to the input point fan.
    /// Rotates point p to the localFan coordinates and returns the
    /// fan number to out_fan_number parameter.
    double DistanceToTheNearestFan(CLHEP::Hep3Vector &p, int & out_fan_number) const;

    /// Calculates aproximate, probably underestimate, distance to the
    /// neutral fibre of the vertical fan. Sign of return value means
    /// side of the fan; negative - lower phi.
    double DistanceToTheNeutralFibre(const CLHEP::Hep3Vector &p, int fan_number) const;

    CLHEP::Hep3Vector NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &p,
                                                 int fan_number) const;
    std::vector<double> NearestPointOnNeutralFibre_asVector(const CLHEP::Hep3Vector &p,
                                                            int fan_number) const;
    int GetPhiGap(const CLHEP::Hep3Vector &p) const { return GetPhiGapAndSide(p).first; }
    int PhiGapNumberForWheel(int) const;
    std::pair<int, int> GetPhiGapAndSide(const CLHEP::Hep3Vector &p) const;
    double AmplitudeOfSurface(const CLHEP::Hep3Vector& P, int side, int fan_number) const;

    /// @}

  private:
    LArG4::LArWheelCalculator_t m_type;

    int m_AtlasZside;
    bool m_SaggingOn; // !
    bool m_phiRotation;
    bool m_slant_use_default;
    std::array<double,5> m_slant_parametrization; // pol4
    std::array<double,LARWC_SINCOS_POLY+1> m_sin_parametrization;
    std::array<double,LARWC_SINCOS_POLY+1> m_cos_parametrization;
    std::vector<std::vector<double> > m_sagging_parameter; // !

    double m_ActiveLength;
    double m_StraightStartSection;
    double m_dWRPtoFrontFace;
    double m_HalfGapBetweenWheels;
    double m_zWheelRefPoint;
    double m_dMechFocaltoWRP;
    double m_dElecFocaltoWRP;
    double m_rOuterCutoff;
    double m_eta_hi, m_eta_mid, m_eta_low;
    double m_zShift;

    double m_WheelThickness;
    double m_HalfWheelThickness;
    double m_zWheelFrontFace, m_zWheelBackFace;

    double m_QuarterWaveLength;
    double m_HalfWaveLength;
    double m_FanFoldRadius;
    double m_ZeroFanPhi;
    double m_ZeroFanPhi_ForDetNeaFan;
    double m_FanStepOnPhi;
    int m_NumberOfWaves;
    int m_NumberOfHalfWaves;
    int m_NumberOfFans;
    //int m_HalfNumberOfFans; removed because unused. DM 2015-07-30
    double m_FanHalfThickness;
    int m_ZeroGapNumber;
    int m_FirstFan;
    int m_LastFan;

    bool m_isModule;
    bool m_isElectrode;
    bool m_isInner;
    bool m_isBarrette;
    bool m_isBarretteCalib;


    double m_leadThicknessInner;
    double m_leadThicknessOuter;
    double m_steelThickness;
    double m_glueThickness;
    double m_electrodeTotalThickness;
    double m_coldContraction;
    double m_electrodeInvContraction;


    // int m_fan_number; // break thread-safety -> removed DM 2015-07-30

    void outer_wheel_init(const EMECData &);
    void inner_wheel_init(const EMECData &);
    void module_init();

  public:

    /*void set_m_fan_number(const int &fan_number)
    {
      m_fan_number = fan_number;
      if(m_fan_number < 0) m_fan_number += m_NumberOfFans;
      m_fan_number += m_ZeroGapNumber;
      if(m_fan_number >= m_NumberOfFans) m_fan_number -= m_NumberOfFans;
    }*/
    int adjust_fan_number(int fan_number) const {
      int res_fan_number = fan_number;
      if(res_fan_number < 0) res_fan_number += m_NumberOfFans;
      res_fan_number += m_ZeroGapNumber;
      if(res_fan_number >= m_NumberOfFans) res_fan_number -= m_NumberOfFans;
      return res_fan_number;
    }

    /// Calculates wave slant angle using parametrization for current wheel
    /// for given distance from calorimeter axis
    double parameterized_slant_angle(double) const;

  private:

    void parameterized_sincos(const double, double &, double &) const;
    void parameterized_sin(const double, double &, double &) const;

  private:

    LArWheelCalculator_Impl::IDistanceCalculator *m_distanceCalcImpl;
    LArWheelCalculator_Impl::IFanCalculator *m_fanCalcImpl;
    void fill_sincos_parameterization();
#if HAVE_VECTOR_SIZE_ATTRIBUTE
    vsincos_par m_vsincos_par{};
#endif

};

#if 0 // Lorenzetti port: no StoreGate class identifier
    //using the macro below we can assign an identifier (and a version)
    //This is required and checked at compile time when you try to record/retrieve
    CLASS_DEF(LArWheelCalculator , 900345678 , 1)
#endif // XAOD_STANDALONE

#endif // GEOSPECIALSHAPES_LARWHEELCALCULATOR_H
