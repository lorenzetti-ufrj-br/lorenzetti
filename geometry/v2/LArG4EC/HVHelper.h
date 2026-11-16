/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/HVHelper.h) for
// --atlas-emec-charge-collection (F41 conserto 29); changes: no AthMessaging (messages through LArG4EC/PortMsg.h); the map is read
// only from the file (EMECHVEnable = false, the Athena default: no GetMapFromDB); the file path is given by the caller instead of
// PathResolver (LArG4EC/HVEMECMap_<version>.dat of ATLASCALDATA); only the helper of the map versions 02 and above (HVHelperV02,
// what CreateHelper returns for the default "v02"); no barrette voltage (GetVoltageBarrett).

#ifndef LARG4_EC_HVHELPER_H
#define LARG4_EC_HVHELPER_H

#include <stdio.h>
#include <stdexcept>
#include <string>
#include <memory>

#include "GeoSpecialShapes/LArWheelCalculator.h"

#include "G4ThreeVector.hh"
#include "globals.hh"

namespace LArG4 { namespace EC {

class HVHelper
{
  protected:
    static constexpr G4int s_NofAtlasSide     = 2;
    static constexpr G4int s_NofEtaSection    = 9;
    static constexpr G4int s_NofElectrodeSide = 2;
    static constexpr G4int s_NofElectrodesOut = 768;

    static const G4double s_EtaLimit[s_NofEtaSection + 1];

    G4double m_Values[s_NofAtlasSide][s_NofEtaSection][s_NofElectrodeSide][s_NofElectrodesOut];

    const LArWheelCalculator *m_calculator;
    const LArWheelCalculator *lwc(void) const { return m_calculator; }

    const G4double m_WheelShift;
    const G4int m_NofPhiSections;

    const G4int m_EtaMin, m_EtaMax;

    const std::string m_mapFile; // Lorenzetti port: the file that PathResolver finds in Athena

    HVHelper(
        const LArWheelCalculator *calc,
        const G4String &version,
        const std::string &mapFile
    );
    void AcquireMaps(const G4String &version, G4bool from_DB);
    virtual void ReadMapFromFile(const G4String &version) = 0;
    FILE * OpenFileAndCheckVersion(const G4String &version);

    G4int GetEtaSection(const G4ThreeVector &p) const;

    virtual G4int GetPhiSection(
        G4int, G4int, G4int, G4int
    ) const = 0;

  public:
    G4double GetVoltage(const G4ThreeVector& p) const;

    virtual G4double GetVoltage(const G4ThreeVector&, G4int, G4int) const;
    virtual G4double GetVoltage(
        const G4ThreeVector&, const std::pair<G4int, G4int> &
    ) const;

    static std::unique_ptr<const HVHelper> CreateHelper(
        const LArWheelCalculator *calc,
        const G4String &version,
        G4bool fromDB,
        const std::string &mapFile
    );

    virtual ~HVHelper() {}
};

class HVHelperV02 : public HVHelper // This serves map versions 02 and above
{
  private:
    void ReadMapFromFile(const G4String &version) override final;

    virtual G4int GetPhiSection(
        G4int, G4int, G4int, G4int
    ) const override final;

  public:
    HVHelperV02(
        const LArWheelCalculator *calc,
        const G4String &version,
        G4bool fromDB,
        const std::string &mapFile
    ) : HVHelper(calc, version, mapFile) { AcquireMaps(version, fromDB); }
};

}} // namespaces

#endif // LARG4_EC_HVHELPER_H
