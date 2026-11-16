/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/LArEMECChargeCollection.cc) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths; removed the functions of the barrettes and of the old charge collection (TransFromBarrtoWheel, _getIRlayer, _interpolateCurrentSubStep, GetCurrent), not used with EnergyCorrection = 8 on the wheels. The kept functions are verbatim. Compiled with -DNDEBUG -O2 as in the Athena release.

// LArEMECChargeCollection.cc
// Prepared by J.Toth 02-July-2003;
//*****************************************************************************
// Code for charge collection in emec                                         *
// Source: endegeo.age of Dice by A.Chekhtman and S.Klimenko in 1995.         *
//                                                                            *
//  Nov-2006 (JT) -include fieldmap for the very first and last fold as well  *
//                -include dynamic memory allocation for the fieldmaps        *
//                -field map is used for defining the signal in the Barrett   *
//                    volume                                                  *
//  31-July-2005  (J.T.):                                                     *
//     suppress signals closer to an electrodes than CHC_Esr                  *
//                                                                            *
//  01-July-2005 J.T. - fieldmap extended for outer wheel;                    *
//                   - 5 new layers 1200< r < 1500 mm are introduced          *
//  25-May-2005 (J.T.):                                                       *
//     - HV values for each power supplies are treated:                       *
//       read it from file                                                    *
//       /afs/cern.ch/atlas/offline/data/lar/emec/efield/HVEMECMap.dat;       *
//       (the values are the nominal ones from TB)                            *
//     - current computation changed:                                         *
//         - HV value from the above file is taken into account               *
//         - IonRecombination effect is taken into accont                     *
//         - drift velocity parametrized as a function of T and Efield        *
//           from:note ATLAS-LARG-99-008;                                     *
//           T is set to te average tempr. measured for ECC0,1,5 at TB        *
//         - current ~ edep*1/HV* Efield*v_drift(T,Efield);                   *
//           normalized at eta=2.25 where the gapsize is 1.3mm(=AverageGap)   *
//                                                                            *
//  20-May-2005 (J.T.):                                                       *
//             - in case of err=-999,                                         *
//               edep in EnergyCalculator is set to 0.                *
//             - change gap computation to be consistent with the fieldmap    *
//             - extrapolation of the field first,                            *
//               then put it on power of 1.3(old case is the reverse)         *
//             - change duble,int,bool..etc for G4double,G4int,G4bool etc.    *
//                                                                            *
//  20-July-2004 (J.T.): New fieldmap prepared. This takes into account the   *
//        correct thickness and folding radius of the electrodes.             *
//        Modification of the code to read either the Old or New map          *
//         was done.                                                          *
//        The desired version (New or Old) of the fieldmap should be set      *
//        to m_FieldMapVersion variable of the LArEMECEnergyCorrrection.cc      *
//        The file name which contains the map should also be set             *
//        to FieldMapFileName variable of the LArEMECEnergyCorrrection.cc     *
//                                                                            *
//  02-July-2003 (J.T.): code improved and rewritten                          *
//                                                                            *
//   -The present version uses a fieldmap which was generated using           *
//    electrode tickness of 300 mikron and curvature radius of the            *
//    electrode's folds of 3mm in both wheels.                                *
//    On other hand the WheelSolid geometry includes 275 mikron thick         *
//    electrodes with fold radius of 3mm for outer and 3.25mm for inner       *
//    wheel. The space point where the energy correction                      *
//    should be computed is defined relative to the new electrodes.           *
//    Still the old tables are used for the actual computation such a way     *
//    that the new LAr gap in the r-phi plane is mapped onto the old one.     *
//   -First and last fold are not treated, kept as they were outside          *
//    of folding region                                                       *
//   -There maybe a problem with folding angle parametrization(see comment    *
//    in the function FoldingAngle                                            *
//   -Another problem may arise, because PhiGap number computed in the        *
//    m_calculator sometimes does not match the one computed during           *
//    charge collection.                                                      *
//    (taking into account a possible 1 bin shift between them by default)    *
//     Here the result of latter is kept.                                     *
//   -The present code works independently of the parameters and functions    *
//    defined in the calculator. This is in order to keep the possibility of  *
//    cross checks for a while.                                               *
//                                                                            *
//  21-May-2003 (J.T.) : Code modified to work in                             *
//                       EnergyCalculator class                        *
//                                                                            *
//  15-Dec-2001 (J.T.) :The original code has been translated to work in      *
//                      C++ environment                                       *
//*****************************************************************************

#include <cassert>
#include <cmath>

#include "G4ThreeVector.hh"
#include "globals.hh"

#include "LArG4EC/EnergyCalculator.h"
#include "LArG4EC/HVHelper.h"
#include "LArG4EC/PortMsg.h"
#include <limits>

#include "CLHEP/Units/PhysicalConstants.h"

// #define DEBUGGetCur

//using namespace LArG4::EC;

// ***************************************************************************
void LArG4::EC::EnergyCalculator::CreateArrays(Wheel_Efield_Map &wheel, G4int n){
  // ***************************************************************************

  wheel.NumberOfRadialLayer = n;
  wheel.RadiusOfLayers         =new G4double [n];
  wheel.FoldinAngleOfLayers    =new G4double [n];
  wheel.HalfLArGapSizeOfLayers =new G4double [n];

  if(wheel.Fold0.FieldMapPrepared){

    wheel.Fold0.MinZofLayer      =new G4double [n];
    wheel.Fold0.MaxZofLayer      =new G4double [n];
    wheel.Fold0.MinYofLayer      =new G4double [n];
    wheel.Fold0.MaxYofLayer      =new G4double [n];
    wheel.Fold0.NofColofLayer    =new G4int    [n];
    wheel.Fold0.NofRowofLayer    =new G4int    [n];
    wheel.Fold0.NofPointsinLayer =new G4int    [n];
    wheel.Fold0.pLayer           =new G4int    [n];
  }

  if(wheel.Fold1.FieldMapPrepared){

    wheel.Fold1.MinZofLayer      =new G4double [n];
    wheel.Fold1.MaxZofLayer      =new G4double [n];
    wheel.Fold1.MinYofLayer      =new G4double [n];
    wheel.Fold1.MaxYofLayer      =new G4double [n];
    wheel.Fold1.NofColofLayer    =new G4int    [n];
    wheel.Fold1.NofRowofLayer    =new G4int    [n];
    wheel.Fold1.NofPointsinLayer =new G4int    [n];
    wheel.Fold1.pLayer           =new G4int    [n];
  }
}


// ***************************************************************************
void LArG4::EC::EnergyCalculator::IniGeomforFieldMaps(void){
  // ***************************************************************************
  ATH_MSG_INFO("***IniGeomforFieldMaps() called for FieldMapVersion = "
               << m_FieldMapVersion);

  if(m_FieldMapVersion == "v00" || m_FieldMapVersion == "v01" ||
     m_FieldMapVersion == "v02"){

    m_ChCollInner.Fold1.FieldMapPrepared=true;
    m_ChCollOuter.Fold1.FieldMapPrepared=true;

    m_ChCollInner.Fold0.FieldMapPrepared=false;
    m_ChCollOuter.Fold0.FieldMapPrepared=false;

    if(m_FieldMapVersion == "v00") {

      G4int nlayer=6; // number of radial layers
      ATH_MSG_INFO(" ***IniGeomforFieldMaps calls CreateArrays");
      CreateArrays(m_ChCollInner,nlayer);
      CreateArrays(m_ChCollOuter,nlayer);

      m_ChCollInner.RadiusOfLayers[0]=300.;//[mm]
      m_ChCollInner.RadiusOfLayers[1]=400.;
      m_ChCollInner.RadiusOfLayers[2]=500.;
      m_ChCollInner.RadiusOfLayers[3]=600.;
      m_ChCollInner.RadiusOfLayers[4]=700.;
      m_ChCollInner.RadiusOfLayers[5]=800.;

      m_ChCollOuter.RadiusOfLayers[0]= 600.; //[mm]
      m_ChCollOuter.RadiusOfLayers[1]= 900.;
      m_ChCollOuter.RadiusOfLayers[2]=1200.;
      m_ChCollOuter.RadiusOfLayers[3]=1500.;
      m_ChCollOuter.RadiusOfLayers[4]=1800.;
      m_ChCollOuter.RadiusOfLayers[5]=2100.;

      m_ChCollInner.FoldinAngleOfLayers[0]= 112.7;//[degree]
      m_ChCollInner.FoldinAngleOfLayers[1]=  92.2;
      m_ChCollInner.FoldinAngleOfLayers[2]=  78.7;
      m_ChCollInner.FoldinAngleOfLayers[3]=  68.8;
      m_ChCollInner.FoldinAngleOfLayers[4]=  61.3;
      m_ChCollInner.FoldinAngleOfLayers[5]=  55.2;

      m_ChCollInner.HalfLArGapSizeOfLayers[0]= 1.44; //[mm]
      m_ChCollInner.HalfLArGapSizeOfLayers[1]= 1.94;
      m_ChCollInner.HalfLArGapSizeOfLayers[2]= 2.29;
      m_ChCollInner.HalfLArGapSizeOfLayers[3]= 2.56;
      m_ChCollInner.HalfLArGapSizeOfLayers[4]= 2.78;
      m_ChCollInner.HalfLArGapSizeOfLayers[5]= 2.96;

      m_ChCollOuter.FoldinAngleOfLayers[0]=129.;//[degree]
      m_ChCollOuter.FoldinAngleOfLayers[1]=101.4;
      m_ChCollOuter.FoldinAngleOfLayers[2]= 84.8;
      m_ChCollOuter.FoldinAngleOfLayers[3]= 73.2;
      m_ChCollOuter.FoldinAngleOfLayers[4]= 64.5;
      m_ChCollOuter.FoldinAngleOfLayers[5]= 57.7;

      m_ChCollOuter.HalfLArGapSizeOfLayers[0]=0.87; //[mm]
      m_ChCollOuter.HalfLArGapSizeOfLayers[1]=1.5;
      m_ChCollOuter.HalfLArGapSizeOfLayers[2]=1.96;
      m_ChCollOuter.HalfLArGapSizeOfLayers[3]=2.31;
      m_ChCollOuter.HalfLArGapSizeOfLayers[4]=2.58;
      m_ChCollOuter.HalfLArGapSizeOfLayers[5]=2.79;
    }

    if(m_FieldMapVersion == "v01") {

      G4int nlayer=6;
      CreateArrays(m_ChCollInner,nlayer);
      CreateArrays(m_ChCollOuter,nlayer);

      m_ChCollInner.RadiusOfLayers[0]=300.;//[mm]
      m_ChCollInner.RadiusOfLayers[1]=400.;
      m_ChCollInner.RadiusOfLayers[2]=500.;
      m_ChCollInner.RadiusOfLayers[3]=600.;
      m_ChCollInner.RadiusOfLayers[4]=700.;
      m_ChCollInner.RadiusOfLayers[5]=800.;

      m_ChCollOuter.RadiusOfLayers[0]= 600.; //[mm]
      m_ChCollOuter.RadiusOfLayers[1]= 900.;
      m_ChCollOuter.RadiusOfLayers[2]=1200.;
      m_ChCollOuter.RadiusOfLayers[3]=1500.;
      m_ChCollOuter.RadiusOfLayers[4]=1800.;
      m_ChCollOuter.RadiusOfLayers[5]=2100.;

      m_ChCollInner.FoldinAngleOfLayers[0]= 112.742024;  //[degree]
      m_ChCollInner.FoldinAngleOfLayers[1]=  92.2379512;
      m_ChCollInner.FoldinAngleOfLayers[2]=  78.6993545;
      m_ChCollInner.FoldinAngleOfLayers[3]=  68.8423119;
      m_ChCollInner.FoldinAngleOfLayers[4]=  61.2714745;
      m_ChCollInner.FoldinAngleOfLayers[5]=  55.2462062;

      m_ChCollInner.HalfLArGapSizeOfLayers[0]= 1.47806735;  //[mm]
      m_ChCollInner.HalfLArGapSizeOfLayers[1]= 1.95080191;
      m_ChCollInner.HalfLArGapSizeOfLayers[2]= 2.30318731;
      m_ChCollInner.HalfLArGapSizeOfLayers[3]= 2.57486515;
      m_ChCollInner.HalfLArGapSizeOfLayers[4]= 2.79014569;
      m_ChCollInner.HalfLArGapSizeOfLayers[5]= 2.96463479;

      m_ChCollOuter.FoldinAngleOfLayers[0]= 129.00197;  //[degree]
      m_ChCollOuter.FoldinAngleOfLayers[1]= 101.408128;
      m_ChCollOuter.FoldinAngleOfLayers[2]=  84.7966382;
      m_ChCollOuter.FoldinAngleOfLayers[3]=  73.1643989;
      m_ChCollOuter.FoldinAngleOfLayers[4]=  64.4458572;
      m_ChCollOuter.FoldinAngleOfLayers[5]=  57.6301588;

      m_ChCollOuter.HalfLArGapSizeOfLayers[0]= 0.877808149;  //[mm]
      m_ChCollOuter.HalfLArGapSizeOfLayers[1]= 1.5116158;
      m_ChCollOuter.HalfLArGapSizeOfLayers[2]= 1.97238634;
      m_ChCollOuter.HalfLArGapSizeOfLayers[3]= 2.31937997;
      m_ChCollOuter.HalfLArGapSizeOfLayers[4]= 2.58864056;
      m_ChCollOuter.HalfLArGapSizeOfLayers[5]= 2.80290925;
    }

    if(m_FieldMapVersion == "v02") {

      G4int nilayer=6;  // number of layers for inner/outer wheel
      G4int nolayer=11;
      CreateArrays(m_ChCollInner,nilayer);
      CreateArrays(m_ChCollOuter,nolayer);

      m_ChCollInner.RadiusOfLayers[0]=300.;//[mm]
      m_ChCollInner.RadiusOfLayers[1]=400.;
      m_ChCollInner.RadiusOfLayers[2]=500.;
      m_ChCollInner.RadiusOfLayers[3]=600.;
      m_ChCollInner.RadiusOfLayers[4]=700.;
      m_ChCollInner.RadiusOfLayers[5]=800.;

      m_ChCollOuter.RadiusOfLayers[0] = 600.; //[mm]
      m_ChCollOuter.RadiusOfLayers[1] = 900.;
      m_ChCollOuter.RadiusOfLayers[2] =1200.;
      m_ChCollOuter.RadiusOfLayers[3] =1250.;
      m_ChCollOuter.RadiusOfLayers[4] =1300.;
      m_ChCollOuter.RadiusOfLayers[5] =1350.;
      m_ChCollOuter.RadiusOfLayers[6] =1400.;
      m_ChCollOuter.RadiusOfLayers[7] =1450.;
      m_ChCollOuter.RadiusOfLayers[8] =1500.;
      m_ChCollOuter.RadiusOfLayers[9] =1800.;
      m_ChCollOuter.RadiusOfLayers[10]=2100.;

      m_ChCollInner.FoldinAngleOfLayers[0]= 112.742024;  //[degree]
      m_ChCollInner.FoldinAngleOfLayers[1]=  92.2379512;
      m_ChCollInner.FoldinAngleOfLayers[2]=  78.6993545;
      m_ChCollInner.FoldinAngleOfLayers[3]=  68.8423119;
      m_ChCollInner.FoldinAngleOfLayers[4]=  61.2714745;
      m_ChCollInner.FoldinAngleOfLayers[5]=  55.2462062;

      m_ChCollInner.HalfLArGapSizeOfLayers[0]= 1.47806735;  //[mm]
      m_ChCollInner.HalfLArGapSizeOfLayers[1]= 1.95080191;
      m_ChCollInner.HalfLArGapSizeOfLayers[2]= 2.30318731;
      m_ChCollInner.HalfLArGapSizeOfLayers[3]= 2.57486515;
      m_ChCollInner.HalfLArGapSizeOfLayers[4]= 2.79014569;
      m_ChCollInner.HalfLArGapSizeOfLayers[5]= 2.96463479;

      m_ChCollOuter.FoldinAngleOfLayers[0]= 129.00197;  //[degree]
      m_ChCollOuter.FoldinAngleOfLayers[1]= 101.408128;
      m_ChCollOuter.FoldinAngleOfLayers[2]=  84.7966382;
      m_ChCollOuter.FoldinAngleOfLayers[3]=  82.5893317;
      m_ChCollOuter.FoldinAngleOfLayers[4]=  80.5022136;
      m_ChCollOuter.FoldinAngleOfLayers[5]=  78.524804;
      m_ChCollOuter.FoldinAngleOfLayers[6]=  76.6479315;
      m_ChCollOuter.FoldinAngleOfLayers[7]=  74.8635164;
      m_ChCollOuter.FoldinAngleOfLayers[8]=  73.1643989;
      m_ChCollOuter.FoldinAngleOfLayers[9]=  64.4458572;
      m_ChCollOuter.FoldinAngleOfLayers[10]= 57.6301588;

      m_ChCollOuter.HalfLArGapSizeOfLayers[0]= 0.877808149;  //[mm]
      m_ChCollOuter.HalfLArGapSizeOfLayers[1]= 1.5116158;
      m_ChCollOuter.HalfLArGapSizeOfLayers[2]= 1.97238634;
      m_ChCollOuter.HalfLArGapSizeOfLayers[3]= 2.03692756;
      m_ChCollOuter.HalfLArGapSizeOfLayers[4]= 2.09855584;
      m_ChCollOuter.HalfLArGapSizeOfLayers[5]= 2.15745335;
      m_ChCollOuter.HalfLArGapSizeOfLayers[6]= 2.21378826;
      m_ChCollOuter.HalfLArGapSizeOfLayers[7]= 2.26771591;
      m_ChCollOuter.HalfLArGapSizeOfLayers[8]= 2.31937997;
      m_ChCollOuter.HalfLArGapSizeOfLayers[9]= 2.58864056;
      m_ChCollOuter.HalfLArGapSizeOfLayers[10]=2.80290925;
    }
  }
  else if(m_FieldMapVersion == "v03"){

    m_ChCollInner.Fold1.FieldMapPrepared=true;
    m_ChCollOuter.Fold1.FieldMapPrepared=true;

    m_ChCollInner.Fold0.FieldMapPrepared=true;
    m_ChCollOuter.Fold0.FieldMapPrepared=true;

    G4int nilayer=6; //number of radial layers; should be the same for
    G4int nolayer=16;// all fold type
    CreateArrays(m_ChCollInner,nilayer);
    CreateArrays(m_ChCollOuter,nolayer);

    for(G4int i=0;i<nilayer;++i){
      m_ChCollInner.RadiusOfLayers[i]=300.+i*100.;
    }
    m_ChCollInner.FoldinAngleOfLayers[0]= 112.7420;  //[degree]
    m_ChCollInner.FoldinAngleOfLayers[1]=  92.238;
    m_ChCollInner.FoldinAngleOfLayers[2]=  78.6994;
    m_ChCollInner.FoldinAngleOfLayers[3]=  68.8423;
    m_ChCollInner.FoldinAngleOfLayers[4]=  61.2715;
    m_ChCollInner.FoldinAngleOfLayers[5]=  55.2462;

    m_ChCollInner.HalfLArGapSizeOfLayers[0]= 1.5326;  //[mm]
    m_ChCollInner.HalfLArGapSizeOfLayers[1]= 2.0053;
    m_ChCollInner.HalfLArGapSizeOfLayers[2]= 2.3577;
    m_ChCollInner.HalfLArGapSizeOfLayers[3]= 2.6294;
    m_ChCollInner.HalfLArGapSizeOfLayers[4]= 2.8446;
    m_ChCollInner.HalfLArGapSizeOfLayers[5]= 3.0191;

    for(G4int i=0;i<nolayer;++i){
      m_ChCollOuter.RadiusOfLayers[i]=600.+i*100.;
    }

    m_ChCollOuter.FoldinAngleOfLayers[0]= 129.002;  //[degree]
    m_ChCollOuter.FoldinAngleOfLayers[1]= 117.7235;
    m_ChCollOuter.FoldinAngleOfLayers[2]= 108.8045;
    m_ChCollOuter.FoldinAngleOfLayers[3]= 101.4081;
    m_ChCollOuter.FoldinAngleOfLayers[4]=  95.1012;
    m_ChCollOuter.FoldinAngleOfLayers[5]=  89.6220;
    m_ChCollOuter.FoldinAngleOfLayers[6]=  84.7966;
    m_ChCollOuter.FoldinAngleOfLayers[7]=  80.5022;
    m_ChCollOuter.FoldinAngleOfLayers[8]=  76.6479;
    m_ChCollOuter.FoldinAngleOfLayers[9]=  73.1644;
    m_ChCollOuter.FoldinAngleOfLayers[10]= 69.9972;
    m_ChCollOuter.FoldinAngleOfLayers[11]= 67.1028;
    m_ChCollOuter.FoldinAngleOfLayers[12]= 64.4459;
    m_ChCollOuter.FoldinAngleOfLayers[13]= 61.9970;
    m_ChCollOuter.FoldinAngleOfLayers[14]= 59.7320;
    m_ChCollOuter.FoldinAngleOfLayers[15]= 57.6302;

    m_ChCollOuter.HalfLArGapSizeOfLayers[0]= 0.9367;  //[mm]
    m_ChCollOuter.HalfLArGapSizeOfLayers[1]= 1.1723;
    m_ChCollOuter.HalfLArGapSizeOfLayers[2]= 1.3824;
    m_ChCollOuter.HalfLArGapSizeOfLayers[3]= 1.5705;
    m_ChCollOuter.HalfLArGapSizeOfLayers[4]= 1.7398;
    m_ChCollOuter.HalfLArGapSizeOfLayers[5]= 1.8927;
    m_ChCollOuter.HalfLArGapSizeOfLayers[6]= 2.0313;
    m_ChCollOuter.HalfLArGapSizeOfLayers[7]= 2.1575;
    m_ChCollOuter.HalfLArGapSizeOfLayers[8]= 2.2727;
    m_ChCollOuter.HalfLArGapSizeOfLayers[9]= 2.3783;
    m_ChCollOuter.HalfLArGapSizeOfLayers[10]=2.4754;
    m_ChCollOuter.HalfLArGapSizeOfLayers[11]=2.5648;
    m_ChCollOuter.HalfLArGapSizeOfLayers[12]=2.6476;
    m_ChCollOuter.HalfLArGapSizeOfLayers[13]=2.7242;
    m_ChCollOuter.HalfLArGapSizeOfLayers[14]=2.7955;
    m_ChCollOuter.HalfLArGapSizeOfLayers[15]=2.8618;

  }
  else{
    ATH_MSG_FATAL("IniGeomforFieldMaps -  FieldMapVersion = '"
                  << m_FieldMapVersion << "' not found!");
  }

  m_ChCollInner.GridShift=0.050;
  m_ChCollOuter.GridShift=0.0667;
}

// ***********************************************************
void LArG4::EC::EnergyCalculator::LoadFieldMaps(const G4String fname){
  // ***********************************************************

  G4int foldtypemx=0;
  char fieldmapversion[10] = { 0 };

  ATH_MSG_INFO("GetFieldMaps from file = " << fname);

  FILE *lun = fopen(fname, "r");

  if(lun == 0){
    ATH_MSG_FATAL("GetFieldMaps - file '" << fname << "' not found!");
    throw std::runtime_error("LArEMECChargeCollection: File not found!");
  }

  if(m_FieldMapVersion != "v00"){
    if (fscanf(lun, "%9s", fieldmapversion) < 1) {
      ATH_MSG_ERROR("GetFieldMaps Error reading field map");
    }
    ATH_MSG_INFO("This file contains fieldmap of version '" << fieldmapversion << "'");
  }

  // Check which fold should have a map

  if     (m_ChCollInner.Fold1.FieldMapPrepared &&
          m_ChCollOuter.Fold1.FieldMapPrepared &&
          m_ChCollInner.Fold0.FieldMapPrepared &&
          m_ChCollOuter.Fold0.FieldMapPrepared)     foldtypemx=2;
  else if(m_ChCollInner.Fold1.FieldMapPrepared &&
          m_ChCollOuter.Fold1.FieldMapPrepared &&
          !m_ChCollInner.Fold0.FieldMapPrepared &&
          !m_ChCollOuter.Fold0.FieldMapPrepared)     foldtypemx=1;
  else{

    ATH_MSG_FATAL(" ***GetFieldMaps file format is incompatible");
  }

  // occupy store for the FieldMaps

  for(G4int foldtype  = 0; foldtype  < foldtypemx; ++ foldtype) {
    for(G4int wheeltype = 0; wheeltype < 2; ++ wheeltype) {
      Wheel_Efield_Map *ChCollWheelType = (wheeltype == 0) ? &m_ChCollInner : &m_ChCollOuter;

      Fold_Efield_Map *ChCollFoldType = ( foldtype == 0 ) ? &(ChCollWheelType->Fold1) : &(ChCollWheelType->Fold0);

      const G4int nlayer = ChCollWheelType->NumberOfRadialLayer; // should be the same for Fold0 and Fold1

      for(G4int i=0; i<nlayer; ++i) {
        if (fscanf(lun, "%lg%lg%lg%lg", &ChCollFoldType->MinZofLayer[i],
                   &ChCollFoldType->MaxZofLayer[i],
                   &ChCollFoldType->MinYofLayer[i],
                   &ChCollFoldType->MaxYofLayer[i]) < 4
            ) {
          ATH_MSG_ERROR("GetFieldMaps Error reading field map");
        }
        if (fscanf(lun, "%i%i", &ChCollFoldType->NofColofLayer[i], &ChCollFoldType->NofRowofLayer[i]) < 2
            ) {
          ATH_MSG_ERROR("GetFieldMaps Error reading field map");
        }

        ChCollFoldType->NofColofLayer[i] ++;
        ChCollFoldType->NofRowofLayer[i] ++;
        const G4int npoints = ChCollFoldType->NofColofLayer[i]*ChCollFoldType->NofRowofLayer[i];
        if(npoints>0 && npoints < std::numeric_limits<int>::max()) {
          ChCollFoldType->NofPointsinLayer[i]=npoints;
          if (i==0) {
            ChCollFoldType->pLayer[i]=0;
          } else {
            ChCollFoldType->pLayer[i]=ChCollFoldType->pLayer[i-1]+ 3*ChCollFoldType->NofPointsinLayer[i-1];
          }

          for(G4int j=0;j<npoints;++j){
            G4double zdummy,ydummy,wdummy;
            if (fscanf(lun, "%lg%lg%lg", &zdummy,&ydummy,&wdummy) < 3) {
              ATH_MSG_ERROR("GetFieldMaps Error reading field map");
            }
          } // end for points
        }
        ATH_MSG_INFO(" foldtype="<<foldtype<< " wheeltype="<<wheeltype
                     <<" ilayer = " << i << " zmin, max = "
                     << ChCollFoldType->MinZofLayer[i] << " "
                     << ChCollFoldType->MaxZofLayer[i] << " "
                     << " ymin, max = "
                     << ChCollFoldType->MinYofLayer[i] << " "
                     << ChCollFoldType->MaxYofLayer[i] << " "
                     << " ncol = " << ChCollFoldType->NofColofLayer[i]
                     << " nrow = " << ChCollFoldType->NofRowofLayer[i]
                     << " npoints = " << npoints);
      } // end for layers

      const G4int length=ChCollFoldType->pLayer[nlayer-1]+3*ChCollFoldType->NofPointsinLayer[nlayer-1];
      ChCollFoldType->FieldMap = new G4double [length];

      if(ChCollFoldType->FieldMap == 0 ) {

        ATH_MSG_FATAL(" ***GetFieldMaps: FATAL  FieldMap array cannot be created");
      }

    }  // end for wheels
  }   //end for foldtypes

  rewind(lun);
  if(m_FieldMapVersion != "v00") {
    if (fscanf(lun, "%9s", fieldmapversion) < 1) {
      ATH_MSG_ERROR( "GetFieldMaps Error reading field map");
    }
  }

  // now fill the coordinates and efield in the FieldMaps

  for(G4int foldtype  = 0; foldtype  < foldtypemx; ++ foldtype) {
    for(G4int wheeltype = 0; wheeltype < 2; ++ wheeltype){
      Wheel_Efield_Map *ChCollWheelType = (wheeltype == 0) ? &m_ChCollInner : &m_ChCollOuter;

      Fold_Efield_Map *ChCollFoldType = ( foldtype == 0 ) ? &(ChCollWheelType->Fold1) : &(ChCollWheelType->Fold0);

      const G4int nlayer = ChCollWheelType->NumberOfRadialLayer; // should be the same for Fold0 and Fold1
      for(G4int i=0; i<nlayer; ++i){
        G4double dummy1,dummy2,dummy3,dummy4;
        G4int    dummy5,dummy6;
        if (fscanf(lun, "%lg%lg%lg%lg", &dummy1, &dummy2, &dummy3, &dummy4) < 4) {
          ATH_MSG_ERROR("GetFieldMaps Error reading field map");
        }
        if (fscanf(lun, "%i%i",         &dummy5, &dummy6) < 2) {
          ATH_MSG_ERROR("GetFieldMaps Error reading field map");
        }

        const G4int npoints = ChCollFoldType->NofPointsinLayer[i];
        if(npoints>0){
          for(G4int j = 0; j < npoints; ++ j){
            if (fscanf(lun, "%lg%lg%lg", &ChCollFoldType->FieldMap[Index(ChCollFoldType,i,0,j)],
                       &ChCollFoldType->FieldMap[Index(ChCollFoldType,i,1,j)],
                       &ChCollFoldType->FieldMap[Index(ChCollFoldType,i,2,j)]) < 3) {
              ATH_MSG_ERROR("GetFieldMaps Error reading field map");
            }


          } // end of loop(j) on points
        }
      }    // end of loop(i) on layers
    }           // end of loop on wheeltype
  }    // end of loop for foldtypes
  fclose(lun);
}

// **********************************************************
void LArG4::EC::EnergyCalculator::PrepareFieldMap(Wheel_Efield_Map* ChCollWheelType) {
  // **********************************************************
  //Selects points which are in the range  -0<z<QuarterWaveLength;
  //Set weights to 1 for points in LAr if they were not defined
  //previously;
  //Map array is too long(not optimal) because:
  //  -the array length is fixed,
  //while the layers are described by different number of points
  //(this maybe solved by introducing some type of dynamic
  //memory handling);
  //  -z,y values are not needed at all.
  //The points in the map are strictly ordered, therefore their
  //coordinates can be computed from the point-address and
  // minz,maxz,miny,maxy parameters.

  //G4int nredef,nlayer,ncol,ipnt,ipold/*,i,j,foldtype,foldtypemx*/;
  G4double minz/*,y,z,w,wx*/;
  //G4int npoints;
  G4double maxz=0.;

  ATH_MSG_INFO("PrepareFieldMap for solidtype = "
               << LArWheelCalculator::LArWheelCalculatorTypeString(lwc()->type()));

  const G4int nlayer = ChCollWheelType->NumberOfRadialLayer; // should be the same for Fold0 and Fold1
  //foldtypemx=1;
  //if ( ChCollWheelType->Fold1.FieldMapPrepared && ChCollWheelType->Fold0.FieldMapPrepared) {
  //	foldtypemx=2;
  //}

  const G4int foldtypemx = (ChCollWheelType->Fold1.FieldMapPrepared && ChCollWheelType->Fold0.FieldMapPrepared) ? 2 : 1;

  for(G4int foldtype = 0; foldtype  < foldtypemx; ++ foldtype) {

    //if(foldtype  == 0 ) ChCollFoldType  = &(ChCollWheelType->Fold1); //normal fold
    //if(foldtype  == 1 ) ChCollFoldType  = &(ChCollWheelType->Fold0); //very first fold
    Fold_Efield_Map *ChCollFoldType = ( foldtype == 0 ) ? &(ChCollWheelType->Fold1) : &(ChCollWheelType->Fold0);

    for(G4int i=0; i<nlayer; ++i) {
      if(foldtype == 0) {  //normal fold
        minz = ChCollFoldType->MinZofLayer[i];
        maxz = lwc()->GetQuarterWaveLength();
        ChCollFoldType->NofColofLayer[i] = G4int( (maxz-minz)/s_GridSize+1.1 );
        ChCollFoldType->MaxZofLayer[i] = lwc()->GetQuarterWaveLength();
      }

      G4int ipnt=-1;  // new counter for numbering the selected points
      const G4int npoints=ChCollFoldType->NofPointsinLayer[i];
      //if(npoints>0) {
      for(G4int j=0;j<npoints;++j){
        const G4double z=ChCollFoldType->FieldMap[Index(ChCollFoldType,i,0,j)];
        const G4double y=ChCollFoldType->FieldMap[Index(ChCollFoldType,i,1,j)];
        const G4double w=ChCollFoldType->FieldMap[Index(ChCollFoldType,i,2,j)];
        G4double wx=w;

        const G4int ipold=ipnt;

        if(foldtype == 1 ) {  // very first fold
          ++ipnt;
          if( wx < 0.00001 )  wx=0.;
        } else {  // normal folds
          if(z<maxz) {  // only grid points within quarterwavelength is to be included
            ++ipnt;
            if( w<0.00001 ) {  // check weight in the file
              if(m_FieldMapVersion != "v00") {
                wx=0.; // new map
              } else {                               // old map
                WheelGeometry wg;
                SetHalfWave(lwc()->GetStraightStartSection()+WaveLength()+z, wg);
                //PointFoldMapArea=1; // looks like this assignment does not affect on something
                G4double Ylimits[4];
                SetYlimitsofPhigapinFieldMap(i, wg, Ylimits);
                if ((y>=Ylimits[0] && y<=Ylimits[1]) ||
                    (y>=Ylimits[2] && y<=Ylimits[3])) {  //point in LAr
                  wx=1.;     // Dice computes the Ylimits at (z+GridShift) value,
                }
              }// endif for old map
            } //endif for  w<0
          }// endif for z<maxz
        }//end for normal fold


        if(ipold != ipnt){

          ChCollFoldType->FieldMap[Index(ChCollFoldType,i,0,ipnt)]=z;
          ChCollFoldType->FieldMap[Index(ChCollFoldType,i,1,ipnt)]=y;
          ChCollFoldType->FieldMap[Index(ChCollFoldType,i,2,ipnt)]=wx;
        }

      }  // end j loop for points
      //}
      if(ipnt+1 != ChCollFoldType->NofColofLayer[i]*ChCollFoldType->NofRowofLayer[i] ){
        ATH_MSG_FATAL(" ERROR: ipnt+1="<<ipnt+1<<" npoints="<<
                      ChCollFoldType->NofColofLayer[i]*ChCollFoldType->NofRowofLayer[i]);
      }
    } //end i loop for layers
  } //end for foldtype
} //end of function

// **********************************************************
G4double LArG4::EC::EnergyCalculator::GetWeightfromFieldMap(
                                                            G4int ilayer, G4double z, G4double y, const FoldArea & fa) const {
  // **********************************************************
  //return interpolated weight from the fieldmap;
  // inp: ilayer= layernumber;
  //      z,y     = z and y coord. of the point where the weight
  //                is to be computed;
  //                they are defined in the coord system of the Map;
  //  interpolated weight =1 by default;

  G4int /*i,*/icol,irow,ip11,ip12,ip21,ip22;
  G4double weight/*,eps*/;
  G4double w11,w12,w21,w22,z11/*,z12,z21,z22*/,y11/*,y12,y21,y22*/,wdown,wup,
    w,dz,dy,dzx,dyx;

  w11=1.; w12=1.; w21=1.; w22=1.; z11=0.; y11=0.; // to avoid compiler warning

  weight=1.;
  const G4double eps=0.0005;
  const G4int i=ilayer;

  //check whether the point is in the area of validity of the table
  if(z<fa.ChCollFoldType->MinZofLayer[i]-eps || z>fa.ChCollFoldType->MaxZofLayer[i]+eps ||
     y<fa.ChCollFoldType->MinYofLayer[i]-eps || y>fa.ChCollFoldType->MaxYofLayer[i]+eps ){
    return weight;
  }

  //Search for the 4 points in the grid surrounding P(z,y).
  //Index of points in the FieldMap:
  //   (21)----(22)
  //     | P    |
  //   (11)----(12)
  //If some of them is outside of LAr their weight=0 by default.
  //Weights set to zero by hand for those surrounding points which
  //have no correspondant grid point in the table.
  //Such situation will happen for example at the z border,
  //because the z coordinate of the last
  //column is less then QuarteWaveLength by 50 and 67 mikron for
  //inner and outer wheel respectively;
  //Only gridpoints of nonzero weight are taken into account
  //for interpolation.
  //The case of all 4 weights are zero should not happen. If still,
  // interpolated weight =1 is returned.


  icol=int((z-fa.ChCollFoldType->MinZofLayer[i])/s_GridSize)+1; //column number of left corners

  if(icol>fa.ChCollFoldType->NofColofLayer[i]) icol=fa.ChCollFoldType->NofColofLayer[i];

  irow=int((y-fa.ChCollFoldType->MinYofLayer[i])/s_GridSize)+1; //row number of lower corners
  if(irow>fa.ChCollFoldType->NofRowofLayer[i]) irow=fa.ChCollFoldType->NofRowofLayer[i];

  assert(icol>0 && irow>0);

  ip11=(icol-1)*fa.ChCollFoldType->NofRowofLayer[i]+irow-1; //index of points in the FieldMap
  ip21=ip11+1;                                           //   (21)----(22)
  ip12= icol   *fa.ChCollFoldType->NofRowofLayer[i]+irow-1; //   (11)----(12)
  ip22=ip12+1;

  G4int i2ip11=Index(fa.ChCollFoldType,i,2,ip11);
  G4int i2ip12=Index(fa.ChCollFoldType,i,2,ip12);
  G4int i2ip21=Index(fa.ChCollFoldType,i,2,ip21);
  G4int i2ip22=Index(fa.ChCollFoldType,i,2,ip22);
  G4int i0ip11=Index(fa.ChCollFoldType,i,0,ip11);
  //G4int i0ip12=Index(fa.ChCollFoldType,i,0,ip12);
  //G4int i0ip21=Index(fa.ChCollFoldType,i,0,ip21);
  //G4int i0ip22=Index(fa.ChCollFoldType,i,0,ip22);
  G4int i1ip11=Index(fa.ChCollFoldType,i,1,ip11);
  //G4int i1ip12=Index(fa.ChCollFoldType,i,1,ip12);
  //G4int i1ip21=Index(fa.ChCollFoldType,i,1,ip21);
  //G4int i1ip22=Index(fa.ChCollFoldType,i,1,ip22);


  if(icol<fa.ChCollFoldType->NofColofLayer[i] && irow<fa.ChCollFoldType->NofRowofLayer[i]){
    w11=fa.ChCollFoldType->FieldMap[i2ip11]; //[i][2][ip11];
    w12=fa.ChCollFoldType->FieldMap[i2ip12]; //[i][2][ip12];
    w21=fa.ChCollFoldType->FieldMap[i2ip21]; //[i][2][ip21];
    w22=fa.ChCollFoldType->FieldMap[i2ip22]; //[i][2][ip22];
    z11=fa.ChCollFoldType->FieldMap[i0ip11]; //[i][0][ip11];
    //z12=fa.ChCollFoldType->FieldMap[i0ip12]; //[i][0][ip12];
    //z21=fa.ChCollFoldType->FieldMap[i0ip21]; //[i][0][ip21];
    //z22=fa.ChCollFoldType->FieldMap[i0ip22]; //[i][0][ip22];
    y11=fa.ChCollFoldType->FieldMap[i1ip11]; //[i][1][ip11];
    //y12=fa.ChCollFoldType->FieldMap[i1ip12]; //[i][1][ip12];
    //y21=fa.ChCollFoldType->FieldMap[i1ip21]; //[i][1][ip21];
    //y22=fa.ChCollFoldType->FieldMap[i1ip22]; //[i][1][ip22];
  }
  else if(icol==fa.ChCollFoldType->NofColofLayer[i] && irow<fa.ChCollFoldType->NofRowofLayer[i]){
    w11=fa.ChCollFoldType->FieldMap[i2ip11]; //[i][2][ip11];
    w12=0.;
    w21=fa.ChCollFoldType->FieldMap[i2ip21]; //[i][2][ip21];
    w22=0.;
    z11=fa.ChCollFoldType->FieldMap[i0ip11]; //[i][0][ip11];
    //z12=z11+GridSize;
    //z21=fa.ChCollFoldType->FieldMap[i0ip21]; //[i][0][ip21];
    //z22=z11+GridSize;
    y11=fa.ChCollFoldType->FieldMap[i1ip11]; //[i][1][ip11];
    //y12=y11;
    //y21=fa.ChCollFoldType->FieldMap[i1ip21]; //[i][1][ip21];
    //y22=y11+GridSize;
  }
  else if(icol<fa.ChCollFoldType->NofColofLayer[i] && irow==fa.ChCollFoldType->NofRowofLayer[i]){
    w11=fa.ChCollFoldType->FieldMap[i2ip11]; //[i][2][ip11];
    w12=fa.ChCollFoldType->FieldMap[i2ip12]; //[i][2][ip12];
    w21=0.;
    w22=0.;
    z11=fa.ChCollFoldType->FieldMap[i0ip11]; //[i][0][ip11];
    //z12=fa.ChCollFoldType->FieldMap[i0ip12]; //[i][0][ip12];
    //z21=z11;
    //z22=z11+GridSize;
    y11=fa.ChCollFoldType->FieldMap[i1ip11]; //[i][1][ip11];
    //y12=fa.ChCollFoldType->FieldMap[i1ip12]; //[i][1][ip12];
    //y21=y11+GridSize;
    //y22=y11+GridSize;
  }
  else if(icol==fa.ChCollFoldType->NofColofLayer[i] && irow==fa.ChCollFoldType->NofRowofLayer[i]){
    w11=fa.ChCollFoldType->FieldMap[i2ip11]; //[i][2][ip11];
    w12=0.;
    w21=0.;
    w22=0.;
    z11=fa.ChCollFoldType->FieldMap[i0ip11]; //[i][0][ip11];
    //z12=z11+GridSize;
    //z21=z11;
    //z22=z11+GridSize;
    y11=fa.ChCollFoldType->FieldMap[i1ip11]; //[i][1][ip11];
    //y12=y11;
    //y21=y11+s_GridSize;
    //y22=y11+s_GridSize;
  }

  dz=(z-z11)/s_GridSize;
  dy=(y-y11)/s_GridSize;

  if(dz<0.) dz=0.;
  if(dz>1.) dz=1.;
  if(dy<0.) dy=0.;
  if(dy>1.) dy=1.;

  dzx=dz;
  if(w11<0.000001) dzx=1.;
  if(w12<0.000001) dzx=0.;
  wdown=w11*(1.-dzx)+w12*dzx;  //interpol. along lower line
  dzx=dz;
  if(w21<0.000001) dzx=1.;
  if(w22<0.000001) dzx=0.;
  wup=w21*(1.-dzx)+w22*dzx;  //interpol. along upper line

  dyx=dy;
  if(wdown<0.000001) dyx=1.;
  if(wup  <0.000001) dyx=0.;
  w=wdown*(1.-dyx)+wup*dyx;   //interpol along column
  if(w>0.000001) weight=w;

  return weight;
}

// ***********************************************************
void LArG4::EC::EnergyCalculator::SetFoldArea(G4double zinwheel, FoldArea & fa) const {
  // ***********************************************************
  if(zinwheel > lwc()->GetStraightStartSection()+lwc()->GetQuarterWaveLength()*0.5 &&
     zinwheel < lwc()->GetWheelThickness()-lwc()->GetStraightStartSection()-lwc()->GetQuarterWaveLength()*0.5){
    fa.PointFoldMapArea=1;
    fa.ChCollFoldType=&(ChCollWheelType()->Fold1);
  }
  else{
    fa.PointFoldMapArea=0;
    fa.ChCollFoldType=&(ChCollWheelType()->Fold0);
  }
}
// ***********************************************************
void LArG4::EC::EnergyCalculator::SetHalfWave(G4double zinwheel, WheelGeometry & wg) const {
  // ***********************************************************

  const G4double z = zinwheel - lwc()->GetStraightStartSection();
  wg.HalfWaveNumber = int((z+lwc()->GetQuarterWaveLength())/lwc()->GetHalfWaveLength());
  wg.ZinHalfWave=z - wg.HalfWaveNumber*lwc()->GetHalfWaveLength();
  wg.SignofZinHalfWave = (wg.ZinHalfWave < 0.) ? -1 : +1;
  wg.SignofSlopeofHalfWave = (wg.HalfWaveNumber % 2 == 0) ? +1 : -1;

}

// ***********************************************************
void LArG4::EC::EnergyCalculator::TransformWheeltoFieldMap(
                                                           const G4double PointinWheel[], G4double PointinFieldMap[],
                                                           const WheelGeometry & wg, const FoldArea & fa
                                                           ) const {
  // ***********************************************************
  // fieldmap is defined for
  //  --  'normal' folds  :
  //      in the coord syst. of a halfwave of pos.slope
  //      in the range of 0<z<QuarterWaveLength;
  //  --  0th and last fold in the range -13mm < z < QuarterWaveLength/2.
  // SetHalfWave() and GetPhiGap() should be called previously;

  PointinFieldMap[0]=PointinWheel[0]*  wg.CosPhiGap  + PointinWheel[1]*wg.SinPhiGap;
  PointinFieldMap[1]=PointinWheel[0]*(-wg.SinPhiGap) + PointinWheel[1]*wg.CosPhiGap;

  if(fa.PointFoldMapArea == 0){
    if(wg.HalfWaveNumber == 0 )             /*0th fold*/
      PointinFieldMap[2]= wg.ZinHalfWave;
    else{                                /*last fold*/
      PointinFieldMap[1]=-PointinFieldMap[1];
      PointinFieldMap[2]= -wg.ZinHalfWave;
    }
  } else{    // normal folds
    PointinFieldMap[1]=wg.SignofZinHalfWave*wg.SignofSlopeofHalfWave
      *PointinFieldMap[1];
    PointinFieldMap[2]=fabs(wg.ZinHalfWave);
  }
}

// *********************************************************************
void LArG4::EC::EnergyCalculator::SetYlimitsofPhigapinFieldMap(G4int ilayer, const WheelGeometry & wg, G4double Ylimits[4]) const {
  // *********************************************************************
  // compute limits of LAr gap along y axis in the system of Halfwaves
  //  using the geometry defined at the time when fieldmap was created;
  //
  // SetHalfWave, GetPhiGap, TransformWheeltoFieldMap should be called previously

  const G4double alpha = ChCollWheelType()->FoldinAngleOfLayers[ilayer] / CLHEP::rad * CLHEP::deg;
  //s=sin(alpha/2.);
  const G4double halfgap = ChCollWheelType()->RadiusOfLayers[ilayer]*CLHEP::pi/lwc()->GetNumberOfFans(); //half of y distance

  Ylimits[3]=YofSurface(alpha,lwc()->GetFanFoldRadius(),-FanAbsThickness(), wg)+halfgap;
  Ylimits[2]=YofSurface(alpha,lwc()->GetFanFoldRadius(),+FanEleThickness(), wg);
  Ylimits[1]=YofSurface(alpha,lwc()->GetFanFoldRadius(),-FanEleThickness(), wg);
  Ylimits[0]=YofSurface(alpha,lwc()->GetFanFoldRadius(),+FanAbsThickness(), wg)-halfgap;
}

// ******************************************************************
void LArG4::EC::EnergyCalculator::SetYlimitsofPhigapinWheel(
                                                            G4double rforpoint, G4double rforalpha, const WheelGeometry & wg, G4double Ylimits[4]) const {
  // ******************************************************************
  // compute limits of LAr gap in the system of Halfwaves using the
  // present geometry of the wheels;
  // valid in 0<z<QuaterWavelength for normal fold;
  // and   in -13mm<z<QuaterWavelength/2. for the 0th fold
  // SetHalfWave GetPhiGap and
  // TransformWheeltoFieldMap should be called previously

  const G4double alpha = FoldingAngle(rforalpha);
  //s=sin(alpha*0.5);
  const G4double halfgap = rforpoint*CLHEP::pi/lwc()->GetNumberOfFans(); //half of y distance between 2 abs.

  Ylimits[3]=YofSurface(alpha,lwc()->GetFanFoldRadius(),-FanAbsThickness(), wg)+halfgap;
  Ylimits[2]=YofSurface(alpha,lwc()->GetFanFoldRadius(),+FanEleThickness(), wg);
  Ylimits[1]=YofSurface(alpha,lwc()->GetFanFoldRadius(),-FanEleThickness(), wg);
  Ylimits[0]=YofSurface(alpha,lwc()->GetFanFoldRadius(),+FanAbsThickness(), wg)-halfgap;
}


// ***********************************************************
void LArG4::EC::EnergyCalculator::GetPhiGap(const G4double SpacePoint[], WheelGeometry & wg) const {
  // ***********************************************************
  // inp: x,y of SpacePoint defined in the Wheel's system
  // outp: gap number(=1,2,..NumberOfFans);
  //       first gap is at phi=0 +- FanStepOnPhi/2
  //     : HalfGapNumber, number of half LAr gaps,
  //          indexed from 1 to 2*NumberOfFans
  //          1st and 2nd halfgaps are in the 1st gap
  // SetHalfWave(z) should be called previously

  const G4double x=SpacePoint[0];
  const G4double y=SpacePoint[1];
  const G4double r2=x*x+y*y;
  G4double r = sqrt(r2);

  //  G4double phiofSpacePoint = atan2(y,x);   //-pi<phi<+pi;
  //  if(phiofSpacePoint<0.) phiofSpacePoint=CLHEP::twopi+phiofSpacePoint;
  const G4double phiofSpacePoint = _normalizeAngle2Pi( atan2(y,x) );
  assert(phiofSpacePoint>0. && phiofSpacePoint<CLHEP::twopi);

  //compute the crossingpoint of the circle of radius r on the x-y plane
  // with the surface of the neutral fibre of the fan 1.
  // fan 1 positioned at phi=0. One iteration gives precise result.
  // It was checked by solving exact equations.

  G4double y0=YofNeutralFibre(FoldingAngle(r),lwc()->GetFanFoldRadius(), wg);
  r = sqrt(r2-y0*y0); // this is an approximation, based on 2 conditons:
  // surface tangent in the transvrsal plane is almost
  // pointing to the beamline,
  // (rold-rnew)/rold << 1.
  y0=YofNeutralFibre(FoldingAngle(r),lwc()->GetFanFoldRadius(), wg);
  //phiCross=atan(y0/r);  //-pi<phi<+pi; // asin is used in Dice - it is a bug
  //phiCross=phiCross-lwc()->GetFanStepOnPhi()/2.;
  //if(phiCross<0.) phiCross=CLHEP::twopi+phiCross;
  const G4double phiCross = _normalizeAngle2Pi( atan2(y0, r) - lwc()->GetFanStepOnPhi()/2. );
  //position of the crossing point
  //on the neutral fibre of the left absorber of the first gap
  const G4double dphi = _normalizeAngle2Pi( phiofSpacePoint - phiCross );
  //if(dphi<0.) dphi=CLHEP::twopi+dphi; //distance in phi from the SpacePoint to the
  //point on the left absorber's neu.fibre
  //at the same radius
  assert (dphi>=0. && dphi<=CLHEP::twopi);

  const G4int phigap=int(dphi/lwc()->GetFanStepOnPhi())+1;
  assert(phigap>=1 && phigap<=lwc()->GetNumberOfFans());

  const G4int phihalfgap=int(2.*dphi/lwc()->GetFanStepOnPhi())+1;
  assert(phihalfgap>=1 && phihalfgap<=2*lwc()->GetNumberOfFans());

  wg.PhiGapNumber=phigap;
  wg.PhiHalfGapNumber=phihalfgap;
  const G4double phi=(phigap-1)*lwc()->GetFanStepOnPhi();
  wg.CosPhiGap=cos(phi);
  wg.SinPhiGap=sin(phi);
}
// ***********************************************************************************
G4double LArG4::EC::EnergyCalculator::YofSurface(G4double alpha,G4double rho,G4double thickness, const WheelGeometry & wg) const {
  // ***********************************************************************************
  // compute y coord of of the fan surface
  //
  // coord system of halfwave is used
  //  y axis: parallel to y axis of ATLAS
  //  z axis: parallel to z axis of Atlas
  //          z is limited by: -wavelength/4 < z < +wavelength/4
  //  origin of the system is fixed  at the node of the halfwave
  //  inp:
  //    halfwave parameters: should be set previously by SetHalfWave();
  //    m_ZinHalfWave :z coord of a point where YofSurf is to be computed
  //    alpha :folding angle[rad]
  //    rho   : curvature radius of the fold
  //    thickness: >0 --> compute y of the  upper surface
  //               =0 --> compute y of the neutral fibre
  //               <0 --> compute y of the lower surface


  const G4double alp=alpha/2.;
  const G4double s=sin(alp);    //sin(alpha/2.)
  const G4double c=cos(alp);    //cos(alpha/2.)
  const G4double t=s/c;         //tan(alpha/2);
  const G4double tb=(1.-s)/c;   //tan(beta); beta=0.5*(90-alpha/2);
  const G4double th=thickness/2.;

  if(wg.HalfWaveNumber==0){                  //0.th 'halfwave'

    const G4double zminoffirstfold   = -rho*tb;
    const G4double zmaxoffirstfold   = -rho*tb+(rho-th)*tb*(1.+s);
    const G4double zminofsecondfold  =  lwc()->GetQuarterWaveLength()-(rho+th)*c;

    if(wg.ZinHalfWave<=zminoffirstfold)  return th;
    if(wg.ZinHalfWave<=zmaxoffirstfold)  return rho-sqrt( pow((rho-th),2)-pow((wg.ZinHalfWave+rho*tb),2) );
    if(wg.ZinHalfWave<=zminofsecondfold) return wg.ZinHalfWave/t+th/s;
    return (lwc()->GetQuarterWaveLength()*c-rho)/s + sqrt( pow((rho+th),2)-pow((wg.ZinHalfWave-lwc()->GetQuarterWaveLength()),2));

  } // end of first fold

  else if(wg.HalfWaveNumber==lwc()->GetNumberOfHalfWaves()){ //last 'halfwave'

    const G4double zmaxoflastfold=rho*tb;
    const G4double zminoflastfold=rho*tb-(rho+th)*tb*(1.+s);
    const G4double zmaxofpreviousfold=-lwc()->GetQuarterWaveLength()+(rho-th)*c;

    if(wg.ZinHalfWave>=zmaxoflastfold)     return th;
    if(wg.ZinHalfWave>=zminoflastfold)     return -rho+sqrt( pow((rho+th),2)-pow((wg.ZinHalfWave-rho*tb),2) );
    if(wg.ZinHalfWave>=zmaxofpreviousfold) return wg.ZinHalfWave/t+th/s;
    return -(lwc()->GetQuarterWaveLength()*c-rho)/s-sqrt( pow((rho-th),2)-pow((wg.ZinHalfWave+lwc()->GetQuarterWaveLength()),2) );

  } // end of last fold

  else if(wg.HalfWaveNumber>0 && wg.HalfWaveNumber<lwc()->GetNumberOfHalfWaves()) {

    const G4double sn=wg.SignofZinHalfWave*wg.SignofSlopeofHalfWave;
    const G4double z2= -lwc()->GetQuarterWaveLength()+(rho-wg.SignofSlopeofHalfWave*th)*c;
    const G4double z3=  lwc()->GetQuarterWaveLength()-(rho+wg.SignofSlopeofHalfWave*th)*c;

    if(wg.ZinHalfWave<=z2 || z3<=wg.ZinHalfWave) {
      return sn*(lwc()->GetQuarterWaveLength()*c-rho)/s+
        sn*sqrt( pow((rho+sn*th),2)-pow((wg.ZinHalfWave-wg.SignofZinHalfWave*lwc()->GetQuarterWaveLength()),2) );
    }

    if(z2<=wg.ZinHalfWave && wg.ZinHalfWave<=z3) {
      return wg.SignofSlopeofHalfWave*wg.ZinHalfWave/t+th/s;
    }

    return 0.;
  }
  return 0.;
}

// **********************************************************
G4double LArG4::EC::EnergyCalculator::FoldingAngle(G4double radius) const {
  // **********************************************************
  // inp:  radius in [mm]
  // outp:  angle in [radian]
  //
  // WARNING !! This formula does not reproduce the folding angle at
  //    radius=800mm for the inner wheel. Therefore LAr halfgapsize
  //    (folding angle) predicted is bigger by 100mikron (1.6degree).
  //    This may give an unpredictable effect making the interpolation
  //    at charge collection, because one of the tables is defined at
  //    this radius. Fitting parameters should be improved!!
  //    The imprecision for outer wheel at smallest/highest radius
  //    is present as well, however it is smaller by a factor of 2.
  //    In case of 'medium' radia the fitted parameters are ok.

  return CLHEP::pi - 2. * lwc()->parameterized_slant_angle(radius);
}
// ***************************************************************
G4double  LArG4::EC::EnergyCalculator::HalfLArGapSizeOld(G4double radius) const {
  // ***************************************************************
  const G4double alpha=FoldingAngle(radius);
  const G4double s=sin(alpha *0.5);
  const G4double halfgap=CLHEP::pi*radius/lwc()->GetNumberOfFans()*s-( FanAbsThickness() + FanEleThicknessOld() )*0.5;
  return halfgap;
}
// ***************************************************************
G4double  LArG4::EC::EnergyCalculator::HalfLArGapSize(G4double rforpoint,G4double rforalpha) const {
  // ***************************************************************
  const G4double alpha=FoldingAngle(rforalpha);
  const G4double s=sin(alpha/2.);
  const G4double halfgap=CLHEP::pi*rforpoint/lwc()->GetNumberOfFans()*s-( FanAbsThickness() + FanEleThickness() )/2.;
  return halfgap;
}
