/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/

// EnergyCalculator.h
// Prepared 10-Apr-2002 Bill Seligman
// from code written by Jozsef Toth.
// 07-May-2003 AMS: now EnergyCalculator is not a singleton
// 02-July-2003 J.T. Charge collection added
// 20-July-2004 J.T. FieldMapVersion variable is added
// 25-May-2005 J.T. -calling sequence of GapAdj changed
//                  -new variables and function for reading and handling
//                    values of HV of power supplies
//                  - IonReco :for suppress signal because of ion recombination
//                  - DriftVelo: Walkowiak's formula for drift velocity
//  Sept-2006 J.T. - collect signal from the Barrette volume
//  Nov -2006 J.T. - fieldmap array structures changed,
//                 - lengths defined dinamically
//                 - field map for first/last fold and for Barrett volume are included
// May 2009 AMS move to namespace LArG4::EC
//              duplicated data members removed

#ifndef LArG4_EC_EnergyCalculator_H
#define LArG4_EC_EnergyCalculator_H

#include <string>
#include <stdexcept>

#include "CLHEP/Units/SystemOfUnits.h"

#include "LArG4Code/LArG4Identifier.h"
#include "LArG4Code/LArCalculatorSvcImp.h"
#include "LArG4Code/LArG4EnumDefs.h"

#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "GeoSpecialShapes/LArWheelCalculatorEnums.h"

#include "G4ThreeVector.hh"
#include "HVHelper.h"
#include "globals.hh"

class ILArCalibCalculatorSvc;
class LArG4BirksLaw;

namespace LArG4 {

  namespace EC {

    class EnergyCalculator : public LArCalculatorSvcImp
    {
    public:

      EnergyCalculator(const std::string& name, ISvcLocator *pSvcLocator);
      // Update handlers
      void CorrectionTypeHandler(Gaudi::Details::PropertyBase&);
      void SolidTypeHandler(Gaudi::Details::PropertyBase&);

      virtual StatusCode initialize() override final;
      virtual StatusCode finalize() override final;

      /////////////////////////////////////////////
      // The interface for LArVCalculator.
      virtual G4float OOTcut() const override final { return m_OOTcut; }
      virtual G4bool Process(const G4Step*, std::vector<LArHitData>&) const override final;

      // Check if the current hitTime is in-time
      virtual G4bool isInTime(G4double hitTime) const override final
      {
        return !(hitTime > m_OOTcut); //FIXME should we be checking the absolute value of hitTime here?
      }


    private:
      G4bool (EnergyCalculator::*m_Process_type) (const G4Step*, std::vector<LArHitData>&) const{};
      G4double (EnergyCalculator::*m_GetGapSize_type) (const G4ThreeVector &p) const{};
      G4double (EnergyCalculator::*m_distance_to_the_nearest_electrode_type) (const G4ThreeVector &p, G4double /*Barret_PhiStart*/) const{};

      G4bool Process_Default(const G4Step*, std::vector<LArHitData>&) const;
      G4bool Process_Barrett(const G4Step*, std::vector<LArHitData>&) const;
      G4bool FindIdentifier_Default(const G4Step *, std::vector<LArHitData>&, G4ThreeVector &, G4ThreeVector &) const;
      G4bool FindIdentifier_Barrett(const G4Step *, G4double, std::vector<LArHitData>&, G4ThreeVector &, G4ThreeVector &) const;
      G4bool FindDMIdentifier_Barrett(const G4Step* step, std::vector<LArHitData>&) const;
      G4bool GetCompartment_Barrett(G4ThreeVector,G4double,G4double,G4double,
                                    G4int &, G4int &) const;

      G4double GetHV_Value(const G4ThreeVector& p, G4double PhiStartOfPhiDiv) const;
      G4double GetGapSize_Default(const G4ThreeVector &p) const {
        return GetGapSize(p);
      }
      G4double GetGapSize_Barrett(const G4ThreeVector &p) const;
      G4int GetPhiGap_Barrett(const G4ThreeVector &p, G4double PhiStartOfPhiDiv) const;
      G4double distance_to_the_nearest_electrode_Default(const G4ThreeVector &p, G4double /*Barret_PhiStart*/) const {
        return distance_to_the_nearest_electrode(p);
      }
      G4double distance_to_the_nearest_electrode_Barrett(const G4ThreeVector &p, G4double Barret_PhiStart) const;

      ServiceHandle<ILArCalibCalculatorSvc> m_supportCalculator;

      void SetConst_OuterBarrett(void); // used only for initialization
      G4bool GetVolumeIndex(const G4Step *, G4int &, G4int &) const;
      static const G4double s_LongBarThickness;//       =   20. *mm;
      static const G4double s_ColdCorrection;//         =1.0036256;
      static const G4double s_StripWidth;//             =3.*mm/ColdCorrection;
      static const G4double s_KapGap;//                 =1.*mm/ColdCorrection;
      static const G4double s_EdgeWidth;//              =1.*mm;
      static const G4double s_DistOfEndofCuFromBack;//  =22.77*mm/ColdCorrection;
      static const G4double s_DistOfStartofCuFromBack;//=31.*mm; // frontface of the barrette
      static const G4double s_ZmaxOfSignal;// DistOfStartofCuFromBack - DistOfEndofCuFromBack + EdgeWidth;

      static const G4double s_S3_Etalim[21];
      static const G4double s_Rmeas_outer[50];
      static const G4double s_Zmeas_outer[2];
      G4double m_RefzDist; // = dElecFocaltoWRP+dWRPtoFrontFace+WheelThickness+  // used as const after
      // +dWRPtoFrontFace+ LongBarThickness                 // initialization
      // -DistOfEndofCuFromBack

      G4double m_S3_Rlim[21]; // used as const after init
      G4double m_rlim[50];    // used as const after init
      G4double m_zlim[4];     // used as const after init

      UnsignedIntegerProperty m_corrProp;
      EnergyCorrection_t m_correction_type;

      G4double (EnergyCalculator::*m_ecorr_method) (G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const{};
      G4double dummy_correction_method(G4double e, const G4ThreeVector&, const G4ThreeVector&,
                                       G4double /*Barret_PhiStart*/) const {
        return e;
      }
      G4double GapAdjustment_old(G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
      G4double GapAdjustment    (G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
      G4double GapAdjustment_E  (G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
      G4double GapAdjustment_s  (G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
      G4double GapAdjustment__sE (G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
      G4double CalculateChargeCollection(G4double, const G4ThreeVector&, const G4ThreeVector&, G4double /*Barret_PhiStart*/) const;
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

      G4double m_zsep12[44]; // used as const after initialization
      G4double m_ziw[7];     // used as const after initialization
      G4double m_zsep23[22]; // used as const after initialization


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
      G4double GetCurrent(G4double *,G4double *,G4double, G4double Barret_PhiStart) const;
      void     TransformWheeltoFieldMap(const G4double *,G4double *, const WheelGeometry & wg, const FoldArea & fa) const;
      void     SetYlimitsofPhigapinFieldMap(G4int, const WheelGeometry & wg, G4double * Ylimits) const;
      void     TransFromBarrtoWheel(const G4double*, G4double PhiStartOfPhiDiv, G4double*) const;
      G4double GetWeightfromFieldMap(G4int,G4double,G4double, const FoldArea & fa) const;
      G4double HalfLArGapSizeOld(G4double) const;

      G4double m_CHC_Esr;  // used as const after init
      inline G4double CHC_Esr() const { return m_CHC_Esr; };

#ifdef DEBUG_CHCL // non thread-safe debug of charge collection
      static const G4int    s_CHCMaxPrint=00; // exists only if debug activated
      static       G4int    s_CHCIprint;      // exists only if debug activated
      static       G4double s_CHCEbad;        // exists only if debug activated
      static       G4double s_CHCEtotal;      // exists only if debug activated
      static       G4double s_CHCStotal;      // exists only if debug activated
#endif

    private:
      /* to be developed...
         std::pair<double, double>DxToFans(Hep3Vector &p);
         double XDistanceToTheNeutralFibre(const Hep3Vector& P) const;
      */
      G4double GetGapSize(const G4ThreeVector &p) const;

      //  public:
      G4double distance_to_the_nearest_electrode(const G4ThreeVector &p) const;

      UnsignedIntegerProperty m_solidtypeProp;
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

      EnergyCalculator (const EnergyCalculator&);
      EnergyCalculator& operator= (const EnergyCalculator&);

      G4int _getIRlayer(G4double rforalpha) const;
      G4int _getIRlayerA(G4double rforalpha) const;

      G4double _interpolateCurrentSubStep(G4double rforalpha, G4int gapup, const G4double vmap[],
                                          G4double tol, const FoldArea & fa, G4int & gaperr ) const;


      G4double _interpolateCurrentSubStep1(G4double rforalpha, const G4double vmap[],
                                           const G4ThreeVector & Pe, int side_dte, int Pe_fan,
                                           const G4ThreeVector & Pa, int side_dta, int Pa_fan,
                                           const FoldArea & fa, G4int & gaperr ) const;

      G4double _AdjustedPhiOfPoint_Barrett(const G4ThreeVector& p, G4double PhiStartOfPhiDiv) const;

      static inline G4double _normalizeAngle2Pi(G4double a) {
        return ( a<0.) ?
          a + CLHEP::twopi
          :
          (a >= CLHEP::twopi ? a - CLHEP::twopi: a);
      }

      G4double getPhiStartOfPhiDiv(const G4Step* step) const;

  private:
    std::unique_ptr<const HVHelper> m_HVHelper;
    const static G4double s_GA_SubstepSize;
    G4double DistanceToEtaLine(const G4ThreeVector &p, G4double eta) const;

    struct geometry_t {
        G4int    zSide;      // +- 3 for inner wheel, +- 2 for outer wheel, z determines sign
        G4int    sampling;
        G4int    region;
        G4double etaScale;   // 1/deta
        G4double etaOffset;  // set so that the range of etaBin starts at zero for each compartment
        G4int    maxEta;     // the maximum value of etaBin in this compartment
        G4int    gapsPerBin; // number of phi gaps (in LArWheelSolid) for each cell bin.
        G4int    maxPhi;     // the maximum value of phiBin in this compartment
    };
    static const geometry_t s_geometry[];

    G4bool GetBarrettePCE(
        const G4ThreeVector& p, G4double PhiStartOfPhiDiv,
        G4double &phi, G4int &compartment, G4int &eta_bin
    ) const;

    };
  } // namespace EC
} // namespace LArG4

#endif // LArG4_EC_EnergyCalculator_H
