/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4EC/src/HVHelper.cc) for
// --atlas-emec-charge-collection (F41 conserto 29); changes: see LArG4EC/HVHelper.h (file only, path from the caller, no DB, no
// HVHelperV00, no barrettes, no Gaudi messages). The kept functions are verbatim. Compiled with -DNDEBUG -O2 as in the Athena release.

#include "LArG4EC/HVHelper.h"
#include "LArG4EC/PortMsg.h"

#include "G4Exception.hh"

#include <iostream>
#include <cstdlib>

using namespace LArG4::EC;

const G4double HVHelper::s_EtaLimit[s_NofEtaSection + 1] = {
    1.375, 1.5, 1.6, 1.8, 2., 2.1, 2.3, 2.5, 2.8, 3.2
};


HVHelper::HVHelper(
    const LArWheelCalculator *calc,
    const G4String &version,
    const std::string &mapFile
) : m_calculator(calc)
  , m_WheelShift(calc->GetElecFocaltoWRP() + calc->GetdWRPtoFrontFace())
  , m_NofPhiSections(
        (version == "v00" || version == "v01")? 32: calc->GetNumberOfFans()
    )
  , m_EtaMin(calc->GetisInner()? 8: 1)
  , m_EtaMax(calc->GetisInner()? 9: 7)
  , m_mapFile(mapFile)
{
    ATH_MSG_DEBUG("asked for map version = " << version);
}

void HVHelper::AcquireMaps(const G4String &version, G4bool from_DB)
{
    ReadMapFromFile(version); // always have values from file as defaults
    if(from_DB){ // Lorenzetti port: the HV database is not available (EMECHVEnable = false is the Athena default)
        ATH_MSG_FATAL("HV values from the database are not available in the Lorenzetti port");
        G4Exception("LArG4::EC::HVHelper", "NoHVDB", FatalException, "AcquireMaps: no HV database");
    }
}

FILE * HVHelper::OpenFileAndCheckVersion(const G4String &version)
{
    // Lorenzetti port: the path comes from the caller (Athena: PathResolver::find_file("LArG4EC/HVEMECMap_" + version + ".dat",
    // "ATLASCALDATA"), then the local file HVEMECMap.dat)
    const G4String mapLocation = m_mapFile;

    ATH_MSG_INFO("reading maps from file: " << mapLocation);

    FILE *F = fopen(mapLocation.c_str(), "r");
    if(F == 0){
        ATH_MSG_ERROR("cannot open EMEC HV Map file " << mapLocation);
        ATH_MSG_FATAL("Cannot obtain HV maps");
        G4Exception("LArG4::EC::HVHelper", "NoHVMap", FatalException,
                    "ReadMapFromFile: cannot open file");
    }

    const size_t buf_size = 80;
    char buf[buf_size] = { 0 };
    if(fgets(buf, buf_size, F) == nullptr) buf[0] = 0;
    char *v = buf + 9;
    if(version == "v02" || version == "v99") v ++;
    v[2] = 0;
    ATH_MSG_INFO("actual HV Map Version = " << buf);
    G4int iv = atoi(v);
    G4bool version_ok = false;
    if(version == "v00" && iv == 0)  version_ok = true;
    if(version == "v01" && iv == 1)  version_ok = true;
    if(version == "v02" && iv == 2)  version_ok = true;
    if(version == "v99" && iv == 99) version_ok = true; // this is a test file
    if(!version_ok){
        ATH_MSG_FATAL("field map version in the file (" << iv
                      << ") is different from expected ("
                      << version << ")");
        G4Exception("LArG4::EC::HVHelper", "MapVersionMismatch",
                    FatalException,
                    "ReadMapFromFile: map version mismatch");
    }
    return F;
}

void HVHelperV02::ReadMapFromFile(const G4String &version)
{
    if(version != "v02" && version != "v99"){
        ATH_MSG_ERROR("wrong HV helper version");
        return;
    }
    FILE *F = OpenFileAndCheckVersion(version);

    const size_t buf_size = 200;
    char buffer[buf_size];

// TODO: regularize printout when it will be necessary
    for(G4int i = 0; i < s_NofAtlasSide; ++ i){
        for(G4int j = 0; j < 3; ++ j){ // read header lines
            if(fgets(buffer, buf_size, F) == nullptr) break;
        }
        for(G4int j = 0; j < s_NofElectrodesOut; ++ j){
            G4int electrodenumber = 0;
            if(fscanf(F, "%i", &electrodenumber) < 1){
                ATH_MSG_ERROR("ReadMapFromFile: Error reading map file");
            }
            for(G4int k = 0; k < s_NofEtaSection; ++ k){
                for(G4int l = 0; l < s_NofElectrodeSide; ++ l){
                    if(fscanf(F, "%lg", &m_Values[i][k][l][j]) < 1){
                        ATH_MSG_ERROR("ReadMapFromFile: Error reading map file");
                    }
                }
            }
        }
        if(fgets(buffer, buf_size, F) == nullptr) buffer[0] = 0; // read leftover end of line
    }

    fclose(F);
}

G4double HVHelper::GetVoltage(const G4ThreeVector& p) const
{
  // pickup HV value from the data of power supplies;
  // everything positioned in the Wheel's coord.system;
  // if it is not the same as the Atlas's one, adjustment is needed
  // either in this code or in the data file

    const std::pair<G4int, G4int> gap = lwc()->GetPhiGapAndSide(p);
    return GetVoltage(p, gap);
}

G4double HVHelper::GetVoltage(
    const G4ThreeVector& p, G4int phigap, G4int phihalfgap
) const
{
    const auto atlas_side = (lwc()->GetAtlasZside() > 0) ? 0 : 1;

    const auto eta_section = GetEtaSection(p);

    /*(right side of e large phi)*/ /*left side of electrode(small phi)*/
    const G4int electrode_side = (phihalfgap%2 == 0 ) ?   1   :   0  ;

    const G4int phi_section = GetPhiSection(
        phigap - 1, atlas_side, eta_section, electrode_side
    );

    return m_Values[atlas_side][eta_section][electrode_side][phi_section];
}

G4int HVHelperV02::GetPhiSection(
    G4int gap, G4int, G4int, G4int
) const
{
    G4int phi_section = gap;
// TODO: check if this check is necessary
// doesn't have it for barrettes
    if(phi_section < 0) phi_section += lwc()->GetNumberOfFans();
    return phi_section;
}

G4double HVHelper::GetVoltage(
    const G4ThreeVector& p, const std::pair<G4int, G4int> &gap
) const
{
    const auto atlas_side = (lwc()->GetAtlasZside() > 0) ? 0 : 1;

    const auto eta_section = GetEtaSection(p);

    /*(right side of e large phi)*/   /*left side of electrode(small phi)*/
    const G4int electrode_side = gap.second > 0? 1: 0;

    const auto phi_section = GetPhiSection(
        lwc()->PhiGapNumberForWheel(gap.first),
        atlas_side, eta_section, electrode_side
    );

    return m_Values[atlas_side][eta_section][electrode_side][phi_section];
}

G4int HVHelper::GetEtaSection(const G4ThreeVector &p) const
{
    const G4ThreeVector p1(p.x(), p.y(), p.z() + m_WheelShift);
    const G4double eta = p1.pseudoRapidity();

    G4int eta_section = -1;
    for(G4int i = m_EtaMin; i <= m_EtaMax; ++ i){
        if(eta <= s_EtaLimit[i]){
            eta_section = i - 1;
            break;
        }
    }

    if(eta_section < 0) throw std::runtime_error("Index out of range");

    return eta_section;
}

std::unique_ptr<const HVHelper> HVHelper::CreateHelper(
    const LArWheelCalculator *calc,
    const G4String &version,
    G4bool fromDB,
    const std::string &mapFile
) {
    if(version == "v00" || version == "v01"){
        // Lorenzetti port: HVHelperV00 is not ported (the Athena default is "v02")
        ATH_MSG_FATAL("HV map version " << version << " is not available in the Lorenzetti port");
        G4Exception("LArG4::EC::HVHelper", "NoHVHelperV00", FatalException, "CreateHelper: version v00/v01 not ported");
        return nullptr;
    } else {
        return std::make_unique<HVHelperV02>(calc, version, fromDB, mapFile);
    }
}
