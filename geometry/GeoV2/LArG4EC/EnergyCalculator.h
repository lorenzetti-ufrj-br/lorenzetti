/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/EnergyCalculator.h) for
// --atlas-emec-charge-collection (F41 conserto 29). Only the part of LArG4::EC::EnergyCalculator that the EM end-cap wheels use with
// EnergyCorrection = 8 (EMEC_ECOR_CHCL1, the default of the class) is kept: the charge collection (CalculateChargeCollection1,
// GetCurrent1 and its helpers, the field maps), GetGapSize and the HV helper used by Birks' law in Process_Default, and the Birks law
// object. Removed: the Gaudi service (initialize() becomes the constructor, with the default values of the properties), the
// identifiers (FindIdentifier_*), the barrettes, the other energy corrections and the calibration calculators. The kept declarations,
// data members and inline functions are those of Athena, in the same order.

#ifndef LArG4_EC_EnergyCalculator_H
#define LArG4_EC_EnergyCalculator_H

#include <string>
#include <stdexcept>
#include <memory>

#include "CLHEP/Units/SystemOfUnits.h"

#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "GeoSpecialShapes/LArWheelCalculatorEnums.h"
#include "GeoSpecialShapes/EMECData.h"

#include "G4ThreeVector.hh"
#include "LArG4EC/HVHelper.h"
#include "LArG4EC/LArG4BirksLaw.h"
#include "globals.hh"

namespace LArG4 {

  namespace EC {

    class EnergyCalculator
    {
    public:

      /// Lorenzetti port: the constructor does what EnergyCalculator::initialize() does for a wheel with
      /// EnergyCorrection = 8, EMECHVEnable = false, EMECGapPower = 1.4, EMECEsr = 0.2 mm, EMECHVMap = "v02",
      /// EMECChMap = "v03", BirksLaw = true and Birksk = 0.05832 (the defaults of the Athena properties).
      /// fieldMapFile and hvMapFile are the files that PathResolver finds in Athena (LArG4EC/ec.fieldzv03 and
      /// LArG4EC/HVEMECMap_v02.dat of ATLASCALDATA).
      EnergyCalculator(const EMECData &emecData, LArG4::LArWheelCalculator_t solidtype, int zside,
                       const std::string &fieldMapFile, const std::string &hvMapFile);
      ~EnergyCalculator();

      EnergyCalculator (const EnergyCalculator&) = delete;
      EnergyCalculator& operator= (const EnergyCalculator&) = delete;

      // Lorenzetti port: public entry points for the hit maker (the same functions as in Athena)
      G4double ChargeCollection(G4double a_energy, const G4ThreeVector &p1, const G4ThreeVector &p2) const {
        return CalculateChargeCollection1(a_energy, p1, p2, 0.654321);
      }
      G4double GapSize(const G4ThreeVector &p) const { return GetGapSize(p); }
      G4double Voltage(const G4ThreeVector &p) const { return m_HVHelper->GetVoltage(p); }
      G4double Birks(G4double E, G4double wholeStepLengthCm, G4double efield) const { return (*m_birksLaw)(E, wholeStepLengthCm, efield); }
      const LArWheelCalculator * calculator() const { return lwc(); }
      const LArWheelCalculator * electrodeCalculator() const { return elc(); }

    private:
      G4double CalculateChargeCollection1(G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;

      G4double m_GApower;  // used as const after init
      inline G4double GApower() const { return m_GApower; };

      // **************************************************************************
      //Declaration of variables,functions  for charge collection
      //J.T
      // **************************************************************************


      //variables specific for wheel geometry
      struct WheelGeometry {
        G4int PhiGapNumber, PhiHalfGapNumber;
        G4int HalfWaveNumber, SignofZinHalfWave, SignofSlopeofHalfWave;
        G4double SinPhiGap, CosPhiGap, ZinHalfWave;
        G4double HalfEleThickness;
        WheelGeometry() :
          PhiGapNumber(0),
          PhiHalfGapNumber(0),
          HalfWaveNumber(0),
          SignofZinHalfWave(0),
          SignofSlopeofHalfWave(0),
          SinPhiGap(0),
          CosPhiGap(0),
          ZinHalfWave(0),
          HalfEleThickness(0)
        {}
      };


      G4double m_ElectrodeFanHalfThickness = 0.0;   // used as const after init
      G4double m_FanEleThicknessOld = 0.0;          // used as const after init
      G4double m_FanEleFoldRadiusOld = 0.0;         // used as const after init
      G4double m_FanAbsThickness = 0.0;             // used as const after init
      G4double m_FanEleThickness = 0.0;             // used as const after init
      G4double m_WaveLength = 0.0;                  // used as const after init

      inline G4double ElectrodeFanHalfThickness() const { return m_ElectrodeFanHalfThickness; };
      inline G4double FanEleThicknessOld() const { return m_FanEleThicknessOld; };
      inline G4double FanEleFoldRadiusOld() const { return m_FanEleFoldRadiusOld; };
      inline G4double FanAbsThickness() const { return m_FanAbsThickness; };
      inline G4double FanEleThickness() const { return m_FanEleThickness; };
      inline G4double WaveLength() const { return m_WaveLength; };

      //variables specific for Efield calculation

      G4String m_FieldMapVersion; // used as const after init

      static const G4double s_GridSize;
      static const G4double s_AverageGap;
      static const G4double s_inv_AverageGap;

      struct Fold_Efield_Map{
        G4bool    FieldMapPrepared;
        G4double*  FieldMap;           // [NumberOfRadialLayers][ZYWeight][MaxNofPoints];
        G4double* MinZofLayer;        //these are limits of the
        G4double* MaxZofLayer;        //area where  the FieldMap can
        G4double* MinYofLayer;        //be used for interpolation
        G4double* MaxYofLayer;
        G4int*    NofColofLayer;      // a column is parallel to y
        G4int*    NofRowofLayer;      // a row is  parallel to z
        G4int*    NofPointsinLayer;
        G4int*    pLayer;
      };

      struct Wheel_Efield_Map {G4bool          FieldMapPrepared;
        G4int           NumberOfRadialLayer;
        G4double*       RadiusOfLayers;
        G4double*       FoldinAngleOfLayers;
        G4double*       HalfLArGapSizeOfLayers;
        Fold_Efield_Map* Fold;
        Fold_Efield_Map Fold0;
        Fold_Efield_Map Fold1;
        G4double  GridShift;
      };

      Wheel_Efield_Map m_ChCollInner,m_ChCollOuter; // used as const after init
      Wheel_Efield_Map* m_ChCollWheelType = nullptr;             // used as const after init

      inline const Wheel_Efield_Map* ChCollWheelType() const { return m_ChCollWheelType; };

      struct FoldArea {
        const Fold_Efield_Map*  ChCollFoldType;
        G4int PointFoldMapArea;
        FoldArea() :
          ChCollFoldType(0),
          PointFoldMapArea(0)
        {}
      };

      void CreateArrays(Wheel_Efield_Map &, G4int);
      inline G4int Index(const Fold_Efield_Map* foldmap, G4int i, G4int j, G4int k ) const {
        return foldmap->pLayer[i]+j*foldmap->NofPointsinLayer[i]+k;
      };
      void SetFoldArea(G4double, FoldArea & ) const;

      std::string m_HVMapVersion; // used only for initialization
      G4bool m_DB_HV;

      static const G4double s_AverageHV;
      static const G4double s_AverageEfield;
      static const G4double s_AverageCurrent;

      static const G4double s_LArTemperature_ECC0;//={88.15}; //K
      static const G4double s_LArTemperature_ECC1;//={88.37};
      static const G4double s_LArTemperature_ECC5;//={87.97};
      static const G4double s_LArTemperature_av ;// ={88.16};

      //Efield in [kv/cm], driftvelo in [mm/microsec], Temperature in [K]

      inline static G4double IonReco(const G4double Efield) {
        if(Efield<=0.000001){return 0.;}
        if(Efield>2.)       {return (1./(1.  +0.36/Efield));}
        return (1./(1.04+0.28/Efield));
      }

      inline static G4double DriftVelo(const G4double T, const G4double Efield) {
        if( Efield <= 0.000001) {return 0.;}
        return ( (-0.01481*(T-90.371)+1.)*
                 ( 0.141*Efield*log(1.+12.4/Efield)+
                   1.627*pow(Efield,0.317) )
                 -0.0075*(T-90.371)
                 );
      }

      // functions specific for geometry

      void     SetHalfWave(G4double, WheelGeometry &) const;
      void     GetPhiGap(const G4double *, WheelGeometry &) const;
      void     SetYlimitsofPhigapinWheel(G4double, G4double, const WheelGeometry & wg, G4double * Ylimits) const;
      G4double YofSurface(G4double,G4double,G4double,const WheelGeometry &) const;
      inline   G4double YofNeutralFibre(G4double alpha,G4double rho, const WheelGeometry & wg) const {
        return YofSurface(alpha,rho,0., wg);
      }
      G4double FoldingAngle(G4double) const;
      G4double HalfLArGapSize(G4double, G4double) const;

      //  functions specific for charge coll.

      void     IniGeomforFieldMaps(void);      // called only at init phase
      void     LoadFieldMaps(const G4String);  // called only at init phase
      void     PrepareFieldMap(Wheel_Efield_Map* ChCollWheelType);  // called only at init phase
      void     TransformWheeltoFieldMap(const G4double *,G4double *, const WheelGeometry & wg, const FoldArea & fa) const;
      void     SetYlimitsofPhigapinFieldMap(G4int, const WheelGeometry & wg, G4double * Ylimits) const;
      G4double GetWeightfromFieldMap(G4int,G4double,G4double, const FoldArea & fa) const;
      G4double HalfLArGapSizeOld(G4double) const;

      G4double m_CHC_Esr;  // used as const after init
      inline G4double CHC_Esr() const { return m_CHC_Esr; };

    private:
      G4double GetGapSize(const G4ThreeVector &p) const;

      //  public:
      G4double distance_to_the_nearest_electrode(const G4ThreeVector &p) const;

      LArG4::LArWheelCalculator_t m_solidtype;
      int m_zside;
      LArG4BirksLaw *m_birksLaw;
      LArWheelCalculator *m_lwc;
      const LArWheelCalculator * lwc() const { return m_lwc; }

      std::string m_suffix;

      // Aug 2007 AMS, lost Aug 2008, restored May 2009
      LArWheelCalculator *m_electrode_calculator = nullptr;
      const LArWheelCalculator * elc() const { return m_electrode_calculator; }

      G4double GetCurrent1(const G4ThreeVector &, const G4ThreeVector &, G4double) const;

      G4int _getIRlayerA(G4double rforalpha) const;

      G4double _interpolateCurrentSubStep1(G4double rforalpha, const G4double vmap[],
                                           const G4ThreeVector & Pe, int side_dte, int Pe_fan,
                                           const G4ThreeVector & Pa, int side_dta, int Pa_fan,
                                           const FoldArea & fa, G4int & gaperr ) const;

      static inline G4double _normalizeAngle2Pi(G4double a) {
        return ( a<0.) ?
          a + CLHEP::twopi
          :
          (a >= CLHEP::twopi ? a - CLHEP::twopi: a);
      }

  private:
    std::unique_ptr<const HVHelper> m_HVHelper;

    };
  } // namespace EC
} // namespace LArG4

#endif // LArG4_EC_EnergyCalculator_H
