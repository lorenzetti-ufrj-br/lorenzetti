/*
  Copyright (C) 2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).


//---------------------------------------------------------------
//                           
// Data structures which determine properties (such as geometry)
// of the EMEC detector in ATLAS.  May be filled by the database
//
//----------------------------------------------------------------

#ifndef EMEC_DATA_H
#define EMEC_DATA_H
#include <string> 
#include <vector> 


struct EMECGEOMETRY {
  double  EFIELD ;
  double  MLGAP ;
  double  SABL ;
  double  SBAR ;
  double  SBRN ;
  double  SCRB ;
  double  Z1 ;
  double  Z0 ;
  double  DCF ;
  double  RLIMIT ;
  double  EPS ;
  double  RHOIN ;
  double  RCKP ;
  double  ETOT ;
  double  EKAP ;
  double  ECU ;
  double  EPREP ;
  double  EINOX ;
  int     NLAYER;
  double  RMIN ;
  double  RMAX ;
  double  DZENDE ;
  double  ZORIG ;
  double  DCRACK ;
  double  DZPLA ;
  double  DZDSE ;
  double  DZDSM ;
  double  DZDSI ;
  int     NUREG ;
  double  DETA_0 ;
  double  DETA_1 ;
  double  DETA_2 ;
  double  DETA_3 ;
  double  DETA_4 ;
  double  DETA_5 ;
  double  DETA_6 ;
  double  DETA_7 ;
  double  DETA_8 ;
  double  DETA_9 ;
  double  DETA_10 ;
  double  DPHI_0 ;
  double  DPHI_1 ;
  double  DPHI_2 ;
  double  DPHI_3 ;
  double  DPHI_4 ;
  double  DPHI_5 ;
  double  DPHI_6 ;
  double  DPHI_7 ;
  double  DPHI_8 ;
  double  DPHI_9 ;
  double  DPHI_10 ;
  double  ETASTR_0 ;
  double  ETASTR_1 ;
  double  ETASTR_2 ;
  double  ETASTR_3 ;
  double  ETASTR_4 ;
  double  ETASTR_5 ;
  double  ETASTR_6 ;
  double  EMHIT ;
  double  EMDIGI ;
  double  GAP0 ;
  double  ZSHIFT ;
  
};

struct EMECPARAMS {
  std::string  PHIROTATION;
  std::string  SAGGING;
  std::string  INNERSLANTPARAM;
  std::string  OUTERSLANTPARAM;
};


struct EMECWHEELPARAMETERS {
  int IWHEEL;
  int NABS;
  int NACC;
  double ETAINT;
  double ETAEXT;
  int  NWSAMP;
};


struct EMECMAGICNUMBERS {
  double STRAIGHTSTARTSECTION;
  double FOCALTOREF ;
  double REFTOACTIVE ;
  double ACTIVELENGTH ;
  double REFTOPRESAMPLER;
  double PRESAMPLERLENGTH;

};

struct COLDCONTRACTION {
  double ABSORBERCONTRACTION;
  double G10RINGCONTRACTION;
  double MOTHERBOARDCONTRACTION;
  double CABLECONTRACTION;
  double COLDWINDOWCONTRACTION;
  double ELECTRODEINVCONTRACTION;
};

struct EMECFAN {
  double LEADTHICKNESSINNER;
  double LEADTHICKNESSOUTER; 
  double STEELTHICKNESS;
  double GLUETHICKNESS;
  double ELECTRODETOTALTHICKNESS; 
};


struct EMECData {
  std::vector<EMECGEOMETRY>        emecgeometry;
  std::vector<EMECPARAMS>          emecparams;
  std::vector<EMECWHEELPARAMETERS> emecwheelparameters;
  std::vector<EMECMAGICNUMBERS>    emecmagicnumbers;
  std::vector<COLDCONTRACTION>     coldcontraction;
  std::vector<EMECFAN>             emecfan;
};

#endif

