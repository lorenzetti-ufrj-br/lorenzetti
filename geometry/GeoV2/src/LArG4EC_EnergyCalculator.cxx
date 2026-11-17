/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/EnergyCalculator.cc) for
// --atlas-emec-charge-collection (F41 conserto 29); changes: see LArG4EC/EnergyCalculator.h. The constructor runs, in the same order,
// the steps of EnergyCalculator::initialize() that a wheel calculator with EnergyCorrection = 8 executes (the EMEC tables come in
// EMECData instead of the geometry database service; the field map and HV map paths come from the caller instead of PathResolver).
// The constants, CalculateChargeCollection1, distance_to_the_nearest_electrode and GetGapSize are verbatim. Compiled with
// -DNDEBUG -O2 as in the Athena release.

#include <cmath>
#include <cassert>
#include <string>

#include "G4ThreeVector.hh"
#include "G4Exception.hh"
#include "globals.hh"

#include "LArG4EC/EnergyCalculator.h"
#include "LArG4EC/PortMsg.h"

using namespace LArG4::EC;

// ****************************************************************************
const G4double            EnergyCalculator::s_GridSize        =0.1; //[mm]
const G4double            EnergyCalculator::s_AverageGap      = 1.3*CLHEP::mm;
const G4double EnergyCalculator::s_LArTemperature_ECC0=88.15; //K
const G4double EnergyCalculator::s_LArTemperature_ECC1=88.37;
const G4double EnergyCalculator::s_LArTemperature_ECC5=87.97;
const G4double EnergyCalculator::s_LArTemperature_av  =88.16;
const G4double EnergyCalculator::s_AverageHV=1250.;//[V]
const G4double EnergyCalculator::s_AverageEfield=0.01*s_AverageHV/s_AverageGap;//[kv/cm]
const G4double EnergyCalculator::s_AverageCurrent=1./s_AverageGap*IonReco(s_AverageEfield)
                                                                        *DriftVelo(s_LArTemperature_av,s_AverageEfield);
// ****************************************************************************

EnergyCalculator::EnergyCalculator(const EMECData &emecData, LArG4::LArWheelCalculator_t solidtype, int zside,
                                   const std::string &fieldMapFile, const std::string &hvMapFile)
  : m_GApower(1.4)              // declareProperty("EMECGapPower",m_GApower=1.4)
  , m_HVMapVersion("v02")       // declareProperty("EMECHVMap",m_HVMapVersion="v02")
  , m_DB_HV(false)              // declareProperty("EMECHVEnable",m_DB_HV=false)
  , m_CHC_Esr(0.2*CLHEP::mm)    // declareProperty("EMECEsr",m_CHC_Esr=0.2*CLHEP::mm)
  , m_solidtype(solidtype)
  , m_zside(zside)
  , m_birksLaw(nullptr)
  , m_lwc(nullptr)
  , m_suffix("v03")             // declareProperty("EMECChMap", m_suffix="v03")
{
  // EnergyCorrection = 8 (m_corrProp(8), m_correction_type(EMEC_ECOR_CHCL1)): the only correction of this port

  m_lwc = new LArWheelCalculator(emecData, m_solidtype, m_zside);
  if(lwc()->GetisElectrode() || lwc()->GetisBarrette() || lwc()->GetisModule())
    {
      ATH_MSG_FATAL("energy caclculator must be of 'absorber' wheel type in the Lorenzetti port");
      G4Exception("EnergyCalculator", "IncorrectSolidType", FatalException, "Lorenzetti port: absorber wheels only");
    }

  // LArCalculatorSvcImp: m_BirksLaw(true), m_Birksk(0.05832)
  {
      const double Birks_LAr_density = 1.396;
      m_birksLaw = new LArG4BirksLaw(Birks_LAr_density,0.05832);
  }

  m_ElectrodeFanHalfThickness = lwc()->GetFanHalfThickness(LArG4::InnerElectrodWheel);
  m_FanEleThickness = ElectrodeFanHalfThickness() * 2.;
  m_FanEleThicknessOld = 0.300*CLHEP::mm;
  m_FanEleFoldRadiusOld = 3.*CLHEP::mm;
  m_FanAbsThickness = lwc()->GetFanHalfThickness() * 2.;
  m_WaveLength = lwc()->GetActiveLength() / lwc()->GetNumberOfWaves();

  m_HVHelper = HVHelper::CreateHelper(lwc(), m_HVMapVersion, m_DB_HV, hvMapFile);

  // if charge collection is required
  {
      // get fieldmap from file
      m_ChCollInner.FieldMapPrepared=false;
      m_ChCollOuter.FieldMapPrepared=false;
      m_FieldMapVersion = m_suffix.empty() ? "v00" : m_suffix;

      ATH_MSG_DEBUG("EnergyCalculator: field map version = " << m_FieldMapVersion);

      IniGeomforFieldMaps();

      // Lorenzetti port: the path comes from the caller (Athena: PathResolver::find_file("LArG4EC/ec.fieldz" + m_suffix,
      // "ATLASCALDATA"))
      LoadFieldMaps(fieldMapFile.c_str());

      // prepare the fieldmaps for further calculation

      if(m_FieldMapVersion != "v00"){
        m_FanEleThicknessOld  = FanEleThickness();
        m_FanEleFoldRadiusOld = lwc()->GetFanFoldRadius();
      }

      m_ChCollWheelType = lwc()->GetisInner() ? &m_ChCollInner : &m_ChCollOuter;

      if(ChCollWheelType()->FieldMapPrepared == false){
        PrepareFieldMap(m_ChCollWheelType);
        m_ChCollWheelType->FieldMapPrepared = true;
      }
  }  // end if charge collection is required

  // Aug 2007 AMS, lost Aug 2008, restored May 2009
  m_electrode_calculator = 0;
  {
    LArG4::LArWheelCalculator_t t = LArG4::OuterElectrodWheel;
    if(lwc()->GetisInner()) t = LArG4::InnerElectrodWheel;

    m_electrode_calculator = new LArWheelCalculator(emecData, t, lwc()->GetAtlasZside());
  }
}

EnergyCalculator::~EnergyCalculator()
{
  // EnergyCalculator::finalize(); the field map arrays are not freed, as in Athena
  delete m_birksLaw;
  m_birksLaw = nullptr;
  delete m_lwc;
  m_lwc = nullptr;
  delete m_electrode_calculator;
  m_electrode_calculator = nullptr;
}

G4double EnergyCalculator::CalculateChargeCollection1(
                                                      G4double a_energy,
                                                      const G4ThreeVector &p1,
                                                      const G4ThreeVector &p2,
                                                      G4double /*Barret_PhiStart*/) const
{
  if(!lwc()->GetisBarrette()){   // should be wheel
    G4double current1 = GetCurrent1(p1, p2, a_energy);
    return current1;
  }
  return a_energy;
}

/* gives the distance to the nearest electrode's surface */
// ****************************************************************************
G4double EnergyCalculator::distance_to_the_nearest_electrode(const G4ThreeVector &p) const
// ****************************************************************************
{
  G4ThreeVector p1( p );
  int fan_number = G4int((p.phi() - M_PI_2 - lwc()->GetZeroFanPhi()) / lwc()->GetFanStepOnPhi());
  G4double angle = lwc()->GetFanStepOnPhi() * fan_number + lwc()->GetZeroFanPhi();
  p1.rotateZ(-angle);
  G4double d0 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
  G4double d1;
  d1 = d0;
  G4int delta = 1;
  if(d0 < 0.) delta = -1;
  angle = - lwc()->GetFanStepOnPhi() * delta;
  do{
    p1.rotateZ(angle);
    fan_number += delta;
    d1 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
  } while(d0 * d1 > 0.);
  p1.rotateZ(-angle / 2);
  if(delta > 0) fan_number --;
  G4double d3 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
  return(fabs(d3) - ElectrodeFanHalfThickness());
}

// No account for edge effects in this function in case of module,
// because Process() will return "false" in this case.
// Affects m_fan_number.
// returns size of gap between absorber's and electrode's surfaces

// ****************************************************************************
double EnergyCalculator::GetGapSize(const G4ThreeVector& p) const
// ****************************************************************************
{
  G4ThreeVector p1 ( p );
  int fan_number = G4int((p.phi() - M_PI_2 - lwc()->GetZeroFanPhi()) / lwc()->GetFanStepOnPhi());
  G4double angle = lwc()->GetFanStepOnPhi() * fan_number + lwc()->GetZeroFanPhi();
  p1.rotateZ(-angle);
  const G4double d0 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));

  const G4int delta = (d0 < 0.)? -1 : 1;
  G4double d1(d0), d2;

  angle = - lwc()->GetFanStepOnPhi() * delta;
  do {
    d2 = d1;
    p1.rotateZ(angle);
    fan_number += delta;
    d1 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
  } while(d0 * d1 > 0.);
  p1.rotateZ(-angle / 2);
  if(delta > 0) fan_number --;
  const G4double d3 = lwc()->DistanceToTheNeutralFibre(p1, lwc()->adjust_fan_number(fan_number));
  if(d3 * d2 < 0.){
    return(fabs(d2)
           - lwc()->GetFanHalfThickness() + fabs(d3) - ElectrodeFanHalfThickness());
  } else {
    return(fabs(d1)
           - lwc()->GetFanHalfThickness() + fabs(d3) - ElectrodeFanHalfThickness());
  }
}
