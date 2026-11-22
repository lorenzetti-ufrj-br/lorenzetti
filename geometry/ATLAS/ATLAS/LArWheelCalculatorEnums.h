/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

#ifndef GEOSPECIALSHAPES_LARWHEELCALCULATORENUMS_H
#define GEOSPECIALSHAPES_LARWHEELCALCULATORENUMS_H

namespace LArG4 {

  enum LArWheelCalculator_t {
    InnerAbsorberWheel,  OuterAbsorberWheel,
    InnerElectrodWheel,  OuterElectrodWheel,
    InnerAbsorberModule, OuterAbsorberModule,
    InnerElectrodModule, OuterElectrodModule,
    BackInnerBarretteWheel,       BackOuterBarretteWheel,
    BackInnerBarretteWheelCalib,  BackOuterBarretteWheelCalib,
    BackInnerBarretteModule,      BackOuterBarretteModule,
    BackInnerBarretteModuleCalib, BackOuterBarretteModuleCalib,
    InnerGlueWheel, OuterGlueWheel,
    InnerLeadWheel, OuterLeadWheel
  };

  struct ROOT6_NamespaceAutoloadHook_WheelCalc{};
}
#endif
