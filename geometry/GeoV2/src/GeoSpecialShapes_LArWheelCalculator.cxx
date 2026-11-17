/*
  Copyright (C) 2002-2019 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: messages to PortableMsgStream instead of the Gaudi message service; include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.

// LArWheelCalculator 19-Apr-2001 Bill Seligman
// 26-May-2009 AMS: remove all previous comments from here as obsoleted

#include <cmath>
#include <climits>
#include <cassert>
#if 0 // Lorenzetti port: no Gaudi message service, the messages go to PortableMsgStream
#include "GaudiKernel/Bootstrap.h"
#include "GaudiKernel/ISvcLocator.h"
#include "GaudiKernel/MsgStream.h"
#else
#include "PortableMsgStream/PortableMsgStream.h"
#endif

#include "GeoSpecialShapes/LArWheelCalculator.h"
#include "GeoSpecialShapes/EMECData.h"

#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorFactory.h"
#include "GeoSpecialShapes/LArWheelCalculator_Impl/FanCalculatorFactory.h"


#include "GeoSpecialShapes/GeoModelKernelUnits.h" // Lorenzetti port: same units, without GeoModel

using namespace GeoModelKernelUnits;


// these numbers are taken from DB in constructor,
// hardcoded values here are just for reference
/*
  double LArWheelCalculator::zWheelRefPoint       = 3689.5*mm;  //=endg_z0
  double LArWheelCalculator::dMechFocaltoWRP      = 3691. *mm;  //=endg_z1
  double LArWheelCalculator::dElecFocaltoWRP      = 3689. *mm;  //=endg_dcf
  double LArWheelCalculator::rOuterCutoff                 = 2034. *mm;  //=endg_rlimit
  double LArWheelCalculator::HalfGapBetweenWheels = 0.15*cm;  // In DB EMECGEOMETRY.DCRACK
  float LArWheelCalculator::m_zShift = 4. *cm; // endg_zshift
  double LArWheelCalculator::eta_hi  = 3.2; // from EmecWheelParameters
  double LArWheelCalculator::eta_mid = 2.5;
  double LArWheelCalculator::eta_low = 1.375;
*/

// these values are taken from "EMECParams" DB
/*
  bool LArWheelCalculator::SaggingOn = false;
  bool LArWheelCalculator::phiRotation = false;
*/

// these were internal constants, now everything in DB
//const double LArWheelCalculator::s_dWRPtoFrontFace = 11.*mm;
//const double LArWheelCalculator::s_WheelThickness = 514.*mm;
// 2x2mm are to be substracted from value of wheel thickness
// - for straight 2-mm domains at start and finish of absorber
//const double LArWheelCalculator::s_StraightStartSection = 2.*mm;
//const double LArWheelCalculator::s_HalfWheelThickness = s_WheelThickness * 0.5;
//const double LArWheelCalculator::s_WheelThickness_wo_2sss = s_WheelThickness - 2.*s_StraightStartSection;

static const double default_slant_parametrization[2][5] = {
  { -50.069, 0.50073, -0.10127E-02, 0.10390E-05, -0.42176E-09 }, // inner
  { -34.254, 0.15528, -0.11670E-03, 0.45018E-07, -0.68473E-11 }  //outer
};

const char *LArWheelCalculator::LArWheelCalculatorTypeString(LArG4::LArWheelCalculator_t type)
{
  switch(type){
     case LArG4::InnerAbsorberWheel:           return("InnerAbsorberWheel");
     case LArG4::OuterAbsorberWheel:           return("OuterAbsorberWheel");
     case LArG4::InnerElectrodWheel:           return("InnerElectrodWheel");
     case LArG4::OuterElectrodWheel:           return("OuterElectrodWheel");
     case LArG4::InnerAbsorberModule:          return("InnerAbsorberModule");
     case LArG4::OuterAbsorberModule:          return("OuterAbsorberModule");
     case LArG4::InnerElectrodModule:          return("InnerElectrodModule");
     case LArG4::OuterElectrodModule:          return("OuterElectrodModule");
     case LArG4::BackOuterBarretteWheel:       return("BackOuterBarretteWheel");
     case LArG4::BackInnerBarretteWheel:       return("BackInnerBarretteWheel");
     case LArG4::BackOuterBarretteModule:      return("BackOuterBarretteModule");
     case LArG4::BackInnerBarretteModule:      return("BackInnerBarretteModule");
     case LArG4::BackOuterBarretteWheelCalib:  return("BackOuterBarretteWheelCalib");
     case LArG4::BackInnerBarretteWheelCalib:  return("BackInnerBarretteWheelCalib");
     case LArG4::BackOuterBarretteModuleCalib: return("BackOuterBarretteModuleCalib");
     case LArG4::BackInnerBarretteModuleCalib: return("BackInnerBarretteModuleCalib");
     case LArG4::InnerGlueWheel:               return("InnerGlueWheel");
     case LArG4::InnerLeadWheel:               return("InnerLeadWheel");
     case LArG4::OuterGlueWheel:               return("OuterGlueWheel");
     case LArG4::OuterLeadWheel:               return("OuterLeadWheel");
  }
  return("unknown");
}

LArWheelCalculator::~LArWheelCalculator() {
  delete m_distanceCalcImpl;
  m_distanceCalcImpl = 0;
  delete m_fanCalcImpl;
  m_fanCalcImpl = 0;
}

LArWheelCalculator::LArWheelCalculator(const EMECData & emecData, LArG4::LArWheelCalculator_t a_wheelType, int zside) :
  m_type(a_wheelType),
  m_AtlasZside(zside),
  m_distanceCalcImpl(0),
  m_fanCalcImpl(0)
{

#if 0 // Lorenzetti port: no Gaudi message service, the messages go to PortableMsgStream
  // Get pointer to the message service
  ISvcLocator* svcLocator = Gaudi::svcLocator();
  IMessageSvc* msgSvc;
  StatusCode status = svcLocator->service("MessageSvc", msgSvc);
  if(status.isFailure()){
    throw std::runtime_error("LArWheelCalculator constructor: cannot initialze message service");
  }
  MsgStream msg(msgSvc, "LArWheelCalculator");
#else
  PortableMsgStream msg("LArWheelCalculator");
#endif
  msg << MSG::VERBOSE << "LArWheelCalculator constructor at " << this
      << " (type " << LArWheelCalculatorTypeString(m_type)
      << "):" << endmsg;


  msg << MSG::VERBOSE << "LArWheelCalculator constructor at " << this
      << " (type " << LArWheelCalculatorTypeString(m_type)
      << "):" << endmsg;

#ifdef LARWC_DTNF_NEW
  msg << MSG::VERBOSE << "compiled with new DTNF" << endmsg;
#endif

  // Access source of detector parameters.
  msg << MSG::VERBOSE
      << "initializing data members from DB..." << endmsg;

  m_zWheelRefPoint       =emecData.emecgeometry[0].Z0*cm;
  m_dMechFocaltoWRP      =emecData.emecgeometry[0].Z1*cm;
  m_dElecFocaltoWRP      =emecData.emecgeometry[0].DCF*cm;
  m_HalfGapBetweenWheels =emecData.emecgeometry[0].DCRACK*cm;
  m_rOuterCutoff         =emecData.emecgeometry[0].RLIMIT*cm;
  m_zShift               =emecData.emecgeometry[0].ZSHIFT*cm;
  
  
  m_eta_hi  =emecData.emecwheelparameters[0].ETAINT;  
  m_eta_mid =emecData.emecwheelparameters[0].ETAEXT;  
  m_eta_low =emecData.emecwheelparameters[1].ETAEXT;  



  m_leadThicknessInner=emecData.emecfan[0].LEADTHICKNESSINNER*mm; 
  m_leadThicknessOuter=emecData.emecfan[0].LEADTHICKNESSOUTER*mm;
  m_steelThickness=emecData.emecfan[0].STEELTHICKNESS*mm;
  m_glueThickness=emecData.emecfan[0].GLUETHICKNESS*mm;
  m_electrodeTotalThickness=emecData.emecfan[0].ELECTRODETOTALTHICKNESS*mm;
  m_coldContraction=emecData.coldcontraction[0].ABSORBERCONTRACTION;
  m_electrodeInvContraction=emecData.coldcontraction[0].ELECTRODEINVCONTRACTION;


    
  m_ActiveLength         =emecData.emecmagicnumbers[0].ACTIVELENGTH*mm;
  m_StraightStartSection =emecData.emecmagicnumbers[0].STRAIGHTSTARTSECTION*mm;
  m_dWRPtoFrontFace      =emecData.emecmagicnumbers[0].REFTOACTIVE*mm;


  m_WheelThickness = m_ActiveLength + 2.*m_StraightStartSection;
  m_HalfWheelThickness = m_WheelThickness * 0.5;

  std::string pr_opt_value=emecData.emecparams[0].PHIROTATION;
  std::string sagging_opt_value=emecData.emecparams[0].SAGGING;

  m_phiRotation =  pr_opt_value == "g3"? true: false;

  m_zWheelFrontFace = m_dMechFocaltoWRP + m_dWRPtoFrontFace;
  m_zWheelBackFace = m_zWheelFrontFace + m_WheelThickness;

  msg << MSG::DEBUG << "... got these values:" << endmsg 
      << "m_zWheelRefPoint       : " << m_zWheelRefPoint / cm << " [cm]" << endmsg 
      << "m_dMechFocaltoWRP      : " << m_dMechFocaltoWRP / cm << " [cm]" << endmsg 
      << "m_dElecFocaltoWRP      : " << m_dElecFocaltoWRP / cm << " [cm]" << endmsg 
      << "m_HalfGapBetweenWheels : " << m_HalfGapBetweenWheels / cm << " [cm]" << endmsg
      << "m_rOuterCutoff         : " << m_rOuterCutoff / cm << " [cm]" << endmsg
      << "m_zWheelFrontFace      : " << m_zWheelFrontFace / cm << " [cm]" << endmsg
      << "m_zWheelBackFace       : " << m_zWheelBackFace / cm << " [cm]" << endmsg
      << "m_zShift               : " << m_zShift / cm << " [cm]" << endmsg
      << "Phi rotation           : " << (m_phiRotation? "true": "false") << "" << endmsg
      << "eta wheels limits      : " << m_eta_low << ", " << m_eta_mid << ", " << m_eta_hi
      << endmsg;
  msg << MSG::VERBOSE << "hardcoded constants: " << endmsg 
      << "m_WheelThickness       : " << m_WheelThickness / cm << " [cm]" << endmsg 
      << "m_dWRPtoFrontFace      : " << m_dWRPtoFrontFace / cm << " [cm]"
      << endmsg;


  // Constructor initializes the geometry.

  m_isBarrette      = false;
  m_isBarretteCalib = false;
  m_isModule        = false;
  m_isElectrode     = false;
  m_isInner         = false;
  m_FirstFan        = 0;
  m_LastFan         = 0;

  switch(m_type){
    case LArG4::BackInnerBarretteWheelCalib:
      m_isBarretteCalib = true;
      /* FALLTHROUGH */
    case LArG4::BackInnerBarretteWheel:
      m_isBarrette = true;
      m_type = LArG4::InnerAbsorberWheel;
      /* FALLTHROUGH */
    case LArG4::InnerAbsorberWheel:
    case LArG4::InnerGlueWheel:
    case LArG4::InnerLeadWheel:
      inner_wheel_init(emecData);
      m_ZeroFanPhi = m_FanStepOnPhi * 0.5;
      if(m_phiRotation) m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      break;
    case LArG4::BackOuterBarretteWheelCalib:
      m_isBarretteCalib = true;
      /* FALLTHROUGH */
    case LArG4::BackOuterBarretteWheel:
      m_isBarrette = true;
      m_type = LArG4::OuterAbsorberWheel;
      /* FALLTHROUGH */
    case LArG4::OuterAbsorberWheel:
    case LArG4::OuterGlueWheel:
    case LArG4::OuterLeadWheel:
      outer_wheel_init(emecData);
      m_ZeroFanPhi = m_FanStepOnPhi * 0.5;
      if(m_phiRotation) m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      break;
    case LArG4::InnerElectrodWheel:
      inner_wheel_init(emecData);
      m_ZeroFanPhi = 0;
      if(m_phiRotation) m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      m_isElectrode = true;
      break;
    case LArG4::OuterElectrodWheel:
      outer_wheel_init(emecData);
      m_ZeroFanPhi = 0;
      if(m_phiRotation) m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      m_isElectrode = true;
      break;
    case LArG4::BackInnerBarretteModuleCalib:
      m_isBarretteCalib = true;
      /* FALLTHROUGH */
    case LArG4::BackInnerBarretteModule:
      m_isBarrette = true;
      m_type = LArG4::InnerAbsorberModule;
      /* FALLTHROUGH */
    case LArG4::InnerAbsorberModule:
      inner_wheel_init(emecData);
      module_init();
      m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      // later for all? m_ZeroFanPhi_ForDetNeaFan = m_ZeroFanPhi - m_FanStepOnPhi * 0.5;
      break;
    case LArG4::BackOuterBarretteModuleCalib:
      m_isBarretteCalib = true;
      /* FALLTHROUGH */
    case LArG4::BackOuterBarretteModule:
      m_isBarrette = true;
      m_type = LArG4::OuterAbsorberModule;
      /* FALLTHROUGH */
    case LArG4::OuterAbsorberModule:
      outer_wheel_init(emecData);
      module_init();
      m_ZeroFanPhi += m_FanStepOnPhi * 0.5;
      // later for all? m_ZeroFanPhi_ForDetNeaFan = m_ZeroFanPhi - m_FanStepOnPhi * 0.5;
      break;
    case LArG4::InnerElectrodModule:
      inner_wheel_init(emecData);
      module_init();
      m_FirstFan ++;
      m_isElectrode = true;
      break;
    case LArG4::OuterElectrodModule:
      outer_wheel_init(emecData);
      module_init();
      m_FirstFan ++;
      m_isElectrode = true;
      break;
    default:
      throw std::runtime_error("LArWheelCalculator constructor:unknown LArWheelCalculator_t");
  }
  m_ZeroFanPhi_ForDetNeaFan = m_ZeroFanPhi - m_FanStepOnPhi * 0.5;
  m_NumberOfHalfWaves = m_NumberOfWaves * 2;
  m_HalfWaveLength = m_ActiveLength / m_NumberOfHalfWaves;
  m_QuarterWaveLength = m_HalfWaveLength * 0.5;
  //m_HalfNumberOfFans = m_NumberOfFans / 2;
  m_FanHalfThickness = GetFanHalfThickness(m_type);

  // Init sagging
  // value read above
  // std::string sagging_opt_value = (*DB_EMECParams)[0]->getString("SAGGING");

  msg << MSG::VERBOSE << "SAGGING value = " << sagging_opt_value << endmsg;

  // the same condition is in DistanceCalculatorFactory::Create
  m_SaggingOn = (sagging_opt_value != "" && sagging_opt_value != "off")? true: false;

  m_distanceCalcImpl = LArWheelCalculator_Impl::DistanceCalculatorFactory::Create(
										  sagging_opt_value, this);
  if (m_SaggingOn) {
    msg << MSG::VERBOSE << "Creating DistanceCalculatorSaggingOn = "  << this
        << ',' << m_distanceCalcImpl << endmsg;
  } else {
    msg << MSG::VERBOSE << "Creating DistanceCalculatorSaggingOff = " << this
        << ',' << m_distanceCalcImpl << endmsg;
  }

  m_fanCalcImpl = LArWheelCalculator_Impl::FanCalculatorFactory::Create(
      m_SaggingOn, m_isModule, this);

  //--------------------------
  // At this place there was the loading of sagging parameters
  // Transfered to DistanceCalculatorSaggingOn
  //--------------------------

  // Get option: Slant params.
  msg << MSG::VERBOSE << "Loading SlantAngle parameters ...";
  std::string slant_params;

  if (m_isInner) {
    slant_params=emecData.emecparams[0].INNERSLANTPARAM;
  } else {
    slant_params=emecData.emecparams[0].OUTERSLANTPARAM;
  }

  msg << (m_isInner?" InnerWheel ":" OuterWheel ") << slant_params << endmsg;

  if(slant_params != "" && slant_params != "default"){
    double a, b, c, d, e;
    if(sscanf(slant_params.c_str(), "%80le %80le %80le %80le %80le", &a, &b, &c, &d, &e) != 5){
      msg << MSG::ERROR
          << "LArWheelCalculator: ERROR: wrong value(s) "
          << "for EMEC slant angle parameters: "
          << slant_params << ", "
          << "defaults are used" << endmsg;
    } else {
      m_slant_parametrization[0] = a;
      m_slant_parametrization[1] = b;
      m_slant_parametrization[2] = c;
      m_slant_parametrization[3] = d;
      m_slant_parametrization[4] = e;
      m_slant_use_default = false;
    }
  } // else already initialized in inner/outer_wheel_init()

  fill_sincos_parameterization(); // initialize sin&cos parameterization

  msg << MSG::VERBOSE << "All params initialized. Print some internal variables" << endmsg;

  msg << MSG::VERBOSE << "Data members:" << endmsg 
      << "m_AtlasZside              = " << m_AtlasZside << "" << endmsg
      << "m_NumberOfFans            = " << m_NumberOfFans << "" << endmsg
      << "m_ZeroFanPhi              = " << m_ZeroFanPhi << "" << endmsg
      << "m_ZeroFanPhi_ForDetNeaFan = " << m_ZeroFanPhi_ForDetNeaFan << "" << endmsg
      << "m_FanStepOnPhi            = " << m_FanStepOnPhi << "" << endmsg
      << "m_FanHalfThickness        = " << m_FanHalfThickness << "" << endmsg
      //<< "Sagging parameters        : " << m_sagging_parameter[0][0] << " " << m_sagging_parameter[0][1] << "" << endmsg
      //<< "Sagging parameters        : " << m_sagging_parameter[1][0] << " " << m_sagging_parameter[1][1] << "" << endmsg
      << "slant_params              = " << slant_params << "" << endmsg
      << "Sagging option            = " << sagging_opt_value << "" << endmsg
      << "SaggingOn                 = " << (m_SaggingOn? "true": "false") << "" << endmsg
      << "Slant parameters          : ";
  for(int i = 0; i < 5; i ++) msg << " " << m_slant_parametrization[i];
  msg << endmsg;

  if(m_isModule){
    msg << MSG::VERBOSE
        << "module_init: FirstFan = " << m_FirstFan
        << ", LastFan = " << m_LastFan
        << ", ZeroFanPhi = " << m_ZeroFanPhi
        << endmsg;
  }

  //m_fan_number = -1000;

  // Is the following code fragment obsoleted? DM 2015-03-13
  /* to compare various methods of slant angle computation:
     if(isInner) return;
     FILE *O = fopen("slant_stat.table1.txt", "w");
     if(O == 0) abort();
     struct timeval t1, t2;
     struct timezone tz;
     std::vector<double> alpha;
     gettimeofday(&t1, &tz);
     for(double r = 600.; r < 2100.; r += .01){
     alpha.push_back(parameterized_slant_angle(r));
     }
     gettimeofday(&t2, &tz);

     fprintf(O, "%d.%06d %d.%06d" << endmsg, t1.tv_sec, t1.tv_usec, t2.tv_sec, t2.tv_usec);
     int i = 0;
     for(double r = 600.; r < 2100.; r += .01, i ++){
     fprintf(O, "%f %f\n", r, alpha[i]);
     }

     fclose(O);
     exit(0);
  */
}

/* converts module gap number into wheel gap number */
int LArWheelCalculator::PhiGapNumberForWheel(int i) const
{
  return m_fanCalcImpl->PhiGapNumberForWheel(i);
}

void LArWheelCalculator::inner_wheel_init(const EMECData & emecData)
{
  for(int i = 0; i < 5; ++ i) {
    m_slant_parametrization[i] = default_slant_parametrization[0][i];
  }
  m_slant_use_default = true;

  m_NumberOfFans=emecData.emecwheelparameters[0].NABS;
  m_NumberOfWaves=emecData.emecwheelparameters[0].NACC;

  m_FanFoldRadius = 3.25*mm;
  m_ZeroGapNumber = 64; // internal constant, should not be taken from DB
  m_FanStepOnPhi = 2*M_PI / m_NumberOfFans;
  m_isInner = true;
}

void LArWheelCalculator::outer_wheel_init(const EMECData & emecData)
{
  for(int i = 0; i < 5; ++ i) {
    m_slant_parametrization[i] = default_slant_parametrization[1][i];
  }
  m_slant_use_default = true;

  m_NumberOfFans=emecData.emecwheelparameters[1].NABS;
  m_NumberOfWaves=emecData.emecwheelparameters[1].NACC;


  m_FanFoldRadius = 3.0*mm;
  m_ZeroGapNumber = 192; // internal constant, should not be taken from DB
  m_FanStepOnPhi = 2*M_PI / m_NumberOfFans;
  m_isInner = false;
}

double LArWheelCalculator::GetFanHalfThickness(LArG4::LArWheelCalculator_t t) const
{

  switch(t){
    case LArG4::BackInnerBarretteWheelCalib:
    case LArG4::BackInnerBarretteModuleCalib:
    case LArG4::BackInnerBarretteWheel:
    case LArG4::BackInnerBarretteModule:
    case LArG4::InnerAbsorberWheel:
    case LArG4::InnerAbsorberModule:
       return (m_leadThicknessInner / 2 + m_steelThickness + m_glueThickness)*m_coldContraction; // new values, 02.11.06 J.T. with contraction in cold
      // lead / 2 + steel + glue
    case LArG4::InnerGlueWheel:
      return (m_leadThicknessInner / 2 + m_glueThickness)*m_coldContraction;
    case LArG4::InnerLeadWheel:
      return m_leadThicknessInner / 2 * m_coldContraction;

    case LArG4::BackOuterBarretteWheelCalib:
    case LArG4::BackOuterBarretteModuleCalib:
    case LArG4::BackOuterBarretteWheel:
    case LArG4::BackOuterBarretteModule:
    case LArG4::OuterAbsorberWheel:
    case LArG4::OuterAbsorberModule:
       return (m_leadThicknessOuter / 2 + m_steelThickness + m_glueThickness)*m_coldContraction;  // new values, 02.11.06 J.T.
    case LArG4::OuterGlueWheel:
      return (m_leadThicknessOuter / 2 + m_glueThickness)*m_coldContraction;
    case LArG4::OuterLeadWheel:
      return m_leadThicknessOuter / 2 * m_coldContraction;

    case LArG4::InnerElectrodWheel:
    case LArG4::OuterElectrodWheel:
    case LArG4::InnerElectrodModule:
    case LArG4::OuterElectrodModule:
      return m_electrodeTotalThickness/m_electrodeInvContraction * 0.5;  //new values, 02.11.06 J.T
  }
  throw std::runtime_error("LArWheelCalculator::GetFanHalfThickness: wrong wheel type");
}

void LArWheelCalculator::module_init()
{
  m_isModule = true;
  m_LastFan = m_NumberOfFans / 8;
  m_FirstFan = 0;
  m_ZeroFanPhi = - m_LastFan / 2 * m_FanStepOnPhi;
}

/*
  array of r is filled with:
  for inner wheel - 2 elements { r_front, r_back }
  for outer wheel - 3 elements { r_front, r_middle, r_back }
  return value - delta_z of middle point in case of outer wheel
*/
double LArWheelCalculator::GetWheelInnerRadius(double *r) const
{
  double zMid = 0.;
  if(m_isInner){
    double tanThetaInner = 2. * exp(-m_eta_hi ) / (1. - exp(-2.*m_eta_hi ));
    r[0] = m_zWheelFrontFace * tanThetaInner;
    r[1] = m_zWheelBackFace  * tanThetaInner;
  } else {
    double tanThetaMid   = 2. * exp(-m_eta_mid) / (1. - exp(-2.*m_eta_mid));
    double inv_tanThetaOuter = (1. - exp(-2.*m_eta_low)) / (2. * exp(-m_eta_low));
    // Note that there is a 3mm gap between the outer surface of the
    // inner wheel and the inner surface of the outer wheel.
    r[0] = m_zWheelFrontFace * tanThetaMid + m_HalfGapBetweenWheels;
    r[1] = m_rOuterCutoff * inv_tanThetaOuter * tanThetaMid + m_HalfGapBetweenWheels;
    r[2] = m_zWheelBackFace  * tanThetaMid + m_HalfGapBetweenWheels;
    zMid = m_rOuterCutoff * inv_tanThetaOuter - m_zWheelFrontFace;
  }
  return zMid;
}

/*
  array of r is filled with:
  for inner wheel - 2 elements { r_front, r_back }
  for outer wheel - 3 elements { r_front, r_middle, r_back }
*/
void LArWheelCalculator::GetWheelOuterRadius(double *r) const
{
  if(m_isInner){
    double tanThetaMid   = 2. * exp(-m_eta_mid) / (1. - exp(-2.*m_eta_mid));
    // Note that there is a 3mm gap between the outer surface of the
    // inner wheel and the inner surface of the outer wheel.
    r[0] = m_zWheelFrontFace * tanThetaMid - m_HalfGapBetweenWheels;
    r[1] = m_zWheelBackFace  * tanThetaMid - m_HalfGapBetweenWheels;
  } else {
    double tanThetaOuter = 2. * exp(-m_eta_low) / (1. - exp(-2.*m_eta_low));
    r[0] = m_zWheelFrontFace * tanThetaOuter;
    r[1] = m_rOuterCutoff;
    r[2] = m_rOuterCutoff;
  }
}
