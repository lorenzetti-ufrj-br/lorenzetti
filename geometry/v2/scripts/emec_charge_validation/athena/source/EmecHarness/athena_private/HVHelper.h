/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/

#ifndef LARG4_EC_HVHELPER_H
#define LARG4_EC_HVHELPER_H

#include <stdio.h>
#include <stdexcept>

#include "AthenaBaseComps/AthMessaging.h"
#include "AthenaKernel/Units.h"

#include "GeoSpecialShapes/LArWheelCalculator.h"

#include "G4ThreeVector.hh"
#include "globals.hh"

#include <memory>

namespace LArG4 { namespace EC {

class HVHelper : public AthMessaging
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

    HVHelper(
        const LArWheelCalculator *calc,
        const G4String &version
    );
    void AcquireMaps(const G4String &version, G4bool from_DB);
    void GetMapFromDB(void);
    virtual void ReadMapFromFile(const G4String &version) = 0;
    FILE * OpenFileAndCheckVersion(const G4String &version);

    G4int GetEtaSection(const G4ThreeVector &p) const;

    virtual G4int GetPhiSection(
        G4int, G4int, G4int, G4int
    ) const = 0;

  public:
    G4double GetVoltageBarrett(
        G4double phi, G4int compartment, G4int eta_bin
    ) const;

    G4double GetVoltage(const G4ThreeVector& p) const;

    virtual G4double GetVoltage(const G4ThreeVector&, G4int, G4int) const;
    virtual G4double GetVoltage(
        const G4ThreeVector&, const std::pair<G4int, G4int> &
    ) const;

    static std::unique_ptr<const HVHelper> CreateHelper(
        const LArWheelCalculator *calc,
        const G4String &version,
        G4bool fromDB
    );

    virtual ~HVHelper() {}
};

class HVHelperV00 : public HVHelper // This serves map versions 00 and 01
{
  private:
    G4int m_StartPhi[s_NofAtlasSide * s_NofEtaSection * s_NofElectrodeSide];
    G4int StartPhi(G4int side, G4int eta, G4int ele) const
    {
        return m_StartPhi[(side*s_NofEtaSection + eta)*s_NofElectrodeSide + ele];
    }

    void SetStartPhi(G4int value, G4int side, G4int eta, G4int ele)
    {
        m_StartPhi[(side*s_NofEtaSection + eta)*s_NofElectrodeSide + ele] = value;
    }

    const G4int m_NumberOfElectrodesInPhiSection;

    void ReadMapFromFile(const G4String &version) override final;

    virtual G4int GetPhiSection(
        G4int, G4int, G4int, G4int
    ) const override final;

  public:
    HVHelperV00(
        const LArWheelCalculator *calc,
        const G4String &version,
        G4bool fromDB
    ) : HVHelper(calc, version)
      , m_NumberOfElectrodesInPhiSection(lwc()->GetNumberOfFans() / m_NofPhiSections)
    {
        AcquireMaps(version, fromDB);
    }
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
        G4bool fromDB
    ) : HVHelper(calc, version) { AcquireMaps(version, fromDB); }
};

}} // namespaces

#endif // LARG4_EC_HVHELPER_H
