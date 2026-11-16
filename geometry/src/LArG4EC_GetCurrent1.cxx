/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/GetCurrent1.cc) for --atlas-emec-charge-collection (F41 conserto 29); changes: include paths. Compiled with -DNDEBUG -O2 as in the Athena release.

#include <cassert>

#include "G4ThreeVector.hh"
#include "globals.hh"

#include "LArG4EC/EnergyCalculator.h"
#include "LArG4EC/HVHelper.h"

#include "CLHEP/Units/SystemOfUnits.h"

static inline int signof(double a){ return (a == 0.) ? 0: (a < 0 ? -1: 1); }

//using namespace LArG4::EC;

G4int LArG4::EC::EnergyCalculator::_getIRlayerA(G4double fold_angle_deg) const {
  //search for radial layers the substep is in between;
  /*	G4int irlayer = 0;
        const G4int &n_layers = ChCollWheelType->NumberOfRadialLayer;
        G4double R = Pe.r();
        for(G4int j = 1; j < n_layers; ++ j){
        if(R < ChCollWheelType->RadiusOfLayers[j]){
        irlayer = j - 1;
        break;
        }
        }*/
  // AMS
  G4int irlayer = 0;
  const G4int n_layers = ChCollWheelType()->NumberOfRadialLayer;

  for(G4int j = 1; j < n_layers; ++ j) {
    if(fold_angle_deg > ChCollWheelType()->FoldinAngleOfLayers[j]) {
      irlayer = j - 1;
      break;
    }
  }
  assert(irlayer >= 0 && irlayer < n_layers - 1);
  return irlayer;
}

G4double  LArG4::EC::EnergyCalculator::_interpolateCurrentSubStep1(G4double rforalpha, const G4double vmap[],
                                                                   const G4ThreeVector & Pe, int side_dte, int Pe_fan,
                                                                   const G4ThreeVector & Pa, int side_dta, int Pa_fan,
                                                                   const FoldArea & fa, G4int & gaperr ) const {

  const G4double fold_angle = M_PI - 2. * lwc()->parameterized_slant_angle(rforalpha); //<<<JT
  const G4double fold_angle_deg=fold_angle/M_PI*180.;  //<<<JT
  const G4int irlayer = _getIRlayerA(fold_angle_deg);

  if(!fa.ChCollFoldType->FieldMapPrepared // fieldmap is not available for this fold
     || (   vmap[2] < fa.ChCollFoldType->MinZofLayer[irlayer] // or out of z range of both maps
            && vmap[2] < fa.ChCollFoldType->MinZofLayer[irlayer + 1])
     ){
    // interpolation not needed
    return 1.0;
  }

  // interpolation needed
  // compute radial interpolation parameter
  G4double dr = -(ChCollWheelType()->FoldinAngleOfLayers[irlayer] - fold_angle_deg)
    / (ChCollWheelType()->FoldinAngleOfLayers[irlayer + 1] - ChCollWheelType()->FoldinAngleOfLayers[irlayer]);

  if(dr < 0.) dr = 0.;
  if(dr > 1.) dr = 1.;

  const G4double a_e = elc()->AmplitudeOfSurface(Pe, side_dte, Pe_fan);
  const G4double a_a = lwc()->AmplitudeOfSurface(Pa, side_dta, Pa_fan);

  const G4double x_e = fabs(Pe.x() - a_e);
  const G4double x_a = fabs(Pa.x() - a_a);

  //check geom. err condition if point is outside of LAr gap
  if(gaperr > -100 && (x_e < 0. || x_a < 0.)) gaperr -= 100;


  const G4double z1 = Pe.z() - lwc()->GetStraightStartSection();
  G4int nhwave = G4int(z1 / lwc()->GetHalfWaveLength());
  if(nhwave < 0) nhwave = 0;
  if(nhwave >= lwc()->GetNumberOfHalfWaves()) nhwave = lwc()->GetNumberOfHalfWaves() - 1;
  //if((nhwave % 2) == 1) side = -side;
  const int side = ((nhwave % 2) == 1) ? -side_dte : side_dte ;

  // get relative y coordinate
  G4double yratio = ((side > 0)? x_e: x_a) / (x_e + x_a);

  if(yratio <= 0.) yratio = 0.00001;      // pull the point into the gap if it wouldn't be there;
  else if(yratio >= 1.) yratio = 0.99999; // this may happen bec.G4 does not grantee that the full
  // step-line is within the same volume

  // get corresponding y coordinates on the radial layers
  // where the weight is to be taken from;
  G4double shift = lwc()->GetStraightStartSection();
  if(fa.PointFoldMapArea != 0) shift += WaveLength();

  WheelGeometry wg;
  SetHalfWave(shift + vmap[2], wg);

  G4double Ylimits[4];
  SetYlimitsofPhigapinFieldMap(irlayer, wg, Ylimits);    //on the lower layer
  G4double pos_low = 0.;
  if(side < 0) pos_low = Ylimits[0] * (1. - yratio) + Ylimits[1] * yratio;
  else if(side > 0) pos_low = Ylimits[2] * (1. - yratio) + Ylimits[3] * yratio;

  SetYlimitsofPhigapinFieldMap(irlayer + 1, wg, Ylimits);  //on the upper layer
  G4double pos_up = 0.;
  if(side < 0) pos_up = Ylimits[0] * (1. - yratio) + Ylimits[1] * yratio;
  else if(side > 0) pos_up = Ylimits[2] * (1. - yratio) + Ylimits[3] * yratio;

  // get weights from the maps of lower and upper layer
  const G4double w_low = GetWeightfromFieldMap(irlayer, vmap[2], pos_low, fa);
  const G4double w_up = GetWeightfromFieldMap(irlayer + 1, vmap[2], pos_up, fa);

  // get the interpolated normalized Efield alias cur
  return w_low * (1. - dr) + w_up * dr;
  // end of interpolation
}

G4double  LArG4::EC::EnergyCalculator::GetCurrent1(const G4ThreeVector &P1, const G4ThreeVector &P2, G4double edep) const
{
  G4int gaperr = 0;

  const std::pair<G4int, G4int> gap2 = lwc()->GetPhiGapAndSide(P2);
  const std::pair<G4int, G4int> gap1 = lwc()->GetPhiGapAndSide(P1);
  //	gap1.first = PhiGapNumberForWheel(gap1.first);
  //	gap2.first = PhiGapNumberForWheel(gap2.first);

  if(gap1 != gap2) gaperr = -1;

  WheelGeometry wg;
  FoldArea fa;
  //JT.>>>
  SetFoldArea(P1.z(), fa);                 // set fold type
  SetHalfWave(P1.z(), wg);                 // set halfwave parameters for substep
  G4double p1[3];
  p1[0] = P1.x();
  p1[1] = P1.y();
  p1[2] = P1.z();

  GetPhiGap(p1, wg);  //set rotation angle from the wheel to the efield Map system; once for each G4 step

  const G4double step = (P2 - P1).mag();
  const G4int nofstep = G4int(step / s_GridSize) + 1;  // step is divided to substeps
  G4double current = 0.;                          //current to be returned
  const G4double step_current = edep / nofstep / s_AverageCurrent; // base current for each step

  const G4double inv_nofstep = 1. / static_cast<double>(nofstep);
  for(G4int i = 0; i < nofstep; ++ i){
    G4double ds = (i + 0.5) * inv_nofstep;
    G4ThreeVector Pe = P1 * (1. - ds) + P2 * ds;
    G4ThreeVector Pa = Pe;

    SetFoldArea(Pe.z(), fa);                 // set fold type
    SetHalfWave(Pe.z(), wg);                 // set halfwave parameters for substep
    G4double vstep[3], vmap[3];
    vstep[0] = Pe.x();
    vstep[1] = Pe.y();
    vstep[2] = Pe.z();
    TransformWheeltoFieldMap(vstep, vmap, wg, fa);  //get corresponding point in Map

    //JT.>>>
    const G4double rvstep2=vstep[0]*vstep[0]+vstep[1]*vstep[1] ;
    const G4double rforalpha=sqrt( rvstep2-vmap[1]*vmap[1] );
    const G4double gap=HalfLArGapSize(rforalpha,rforalpha);// LAr gap at the straight section on the fieldmap
    const G4double yshift_on_map  =    rforalpha*M_PI/lwc()->GetNumberOfFans()-(FanAbsThickness() + FanEleThickness() )/2.;
    const G4double yshift_on_wheel=sqrt(rvstep2)*M_PI/lwc()->GetNumberOfFans()-(FanAbsThickness() + FanEleThickness() )/2.;
    const G4double cylgapcorr=yshift_on_wheel/yshift_on_map; // scale difference between plane and cylindrical surface
    //<<<JT

    const G4double HV_value = m_HVHelper->GetVoltage(Pe, gap1);

    int Pe_fan = 0;
    const G4double dte = elc()->DistanceToTheNearestFan(Pe, Pe_fan);
    //G4int side = signof(dte);
    int Pa_fan = 0;
    const G4double dta = lwc()->DistanceToTheNearestFan(Pa, Pa_fan);

    const G4double suppression_range = ElectrodeFanHalfThickness() + CHC_Esr();
    if(fabs(dte) < suppression_range){
      continue; //skip point if too close to the electrode
    }

    const G4double agap = fabs(dte) - ElectrodeFanHalfThickness()
      + fabs(dta) - lwc()->GetFanHalfThickness();   //correction to electrode suppression not to
    G4double suppression = agap / ( agap - CHC_Esr() ); // change av. signal in the gap
    if(suppression < 0.) suppression = 1.;

    const G4double cur = _interpolateCurrentSubStep1( rforalpha, vmap, Pe, signof(dte), Pe_fan, Pa, signof(dta), Pa_fan, fa, gaperr );
    //(25-05-2005) new current calculation: edep*1/U*IonReco*E*v_drift
    //   normalized so that signal=edep in the straight section of the same gap
    //                             as above;
    //       where: HV=1250V,E=9.615 [kv/cm] ,T=88.16 K,
    //       vdrift=4.62 [mm/mikrosec],  Ionreco=96.4%
    // ==> s_AverageCurrent=3.425/[mikrosec];

    //		G4double gap = HalfLArGapSize(Pe.r(), Pe.r());       // gapsize in the straight section
    // AMS: why "straight section"? I would better use agap...
    // JT: because the fieldmap table is normalized to the efield in the straight section

    // JT>>const G4double &gap = agap;

    const G4double efield = cur * (HV_value * CLHEP::volt) / (gap * CLHEP::mm) / (CLHEP::kilovolt / CLHEP::cm) /cylgapcorr;
    const G4double substep_current =  step_current * cur / gap * IonReco(efield) *
      DriftVelo(s_LArTemperature_av, efield) * suppression / cylgapcorr;

    //		if(birksLaw){
    //			current += (*birksLaw)(substep_current, step/nofstep/cm, efield);
    //		} else {
    current += substep_current;
    //		}
  } // end of loop for substeps
  if(current < 0.){
    gaperr -= 1000;
    current = 0.;
  }

#ifdef DEBUG_CHCL
  if(gaperr != 0){
    s_CHCEbad = s_CHCEbad + edep;
    if(s_CHCIprint < s_CHCMaxPrint){
      ++ s_CHCIprint;
      ATH_MSG_WARNING("GetCurrent has strange step, gaperr="
                      << gaperr << " correction still computed"
                      << " bad edep ratio=" << s_CHCEbad/s_CHCEtotal
                      << endmsg;
                      )
      }
  }
#endif

    return current;
  }

  /*
    G4double  LArG4::EC::EnergyCalculator::transform_z_to_fieldmap(const G4ThreeVector &p)
    {
    // fieldmap is defined for
    //  --  'normal' folds  :
    //      in the coord syst. of a halfwave of pos.slope
    //      in the range of 0<z<QuarterWaveLength;
    //  --  0th and last fold in the range -13mm < z < QuarterWaveLength/2.
    // SetHalfWave() and GetPhiGap() should be called previously;

    G4double result = 0.;

    if(s_PointFoldMapArea == 0){
    if(HalfWaveNumber == 0) result = ZinHalfWave; // 0th fold
    else result = -ZinHalfWave; // last fold
    } else {    // normal folds
    result = fabs(ZinHalfWave);
    }
    return result;
    }

  */
