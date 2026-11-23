#include "ATLAS/DetectorConstruction_v2.h"
#include "ATLAS/json.hpp"

#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4Tubs.hh"
#include "G4Polycone.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4GlobalMagFieldMessenger.hh"
#include "G4AutoDelete.hh"
#include "G4GeometryManager.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4SolidStore.hh"
#include "G4ProductionCuts.hh"
#include "G4RegionStore.hh"
#include "G4UniformMagField.hh"
#include "G4FieldManager.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"

#include <fstream>
#include <iostream>

namespace ATLAS {

G4ThreadLocal G4GlobalMagFieldMessenger* DetectorConstruction_v2::m_magFieldMessenger = nullptr;

DetectorConstruction_v2::DetectorConstruction_v2(std::string name)
    : IMsgService(name),
      G4VUserDetectorConstruction(),
      m_checkOverlaps(true),
      m_absorberPV(nullptr),
      m_gapPV(nullptr),
      m_solenoidLV(nullptr)
{
    declareProperty("UseMagneticField", m_useMagneticField = false);
    declareProperty("UseSolenoidField", m_useSolenoidField = true);
    declareProperty("CutOnPhi", m_cutOnPhi = false);
    declareProperty("OutputLevel", m_outputLevel = 0);
    declareProperty("GeometryFile", m_geometryFile = "");
}

DetectorConstruction_v2::~DetectorConstruction_v2()
{
}

bool DetectorConstruction_v2::LoadGeometryFile(const std::string& filepath)
{
    std::ifstream f(filepath);
    if (!f.is_open()) {
        MSG_ERROR("Cannot open geometry file: " << filepath);
        return false;
    }
    try {
        nlohmann::json j;
        f >> j;
        if (!j.contains("volumes") || !j["volumes"].is_array()) {
            MSG_ERROR("Geometry file has no valid 'volumes' array: " << filepath);
            return false;
        }
        m_volumes.clear();
        for (const auto& vol : j["volumes"]) {
            Volume v;
            v.name = vol.value("name", "");
            std::string platesStr = vol.value("plates", "Horizontal");
            if (platesStr == "Vertical") {
                v.plates = 1;
            } else if (platesStr == "Polycone") {
                v.plates = 2;
            } else {
                v.plates = 0;
            }

            if (vol.contains("materials")) {
                v.absorberMaterial = vol["materials"].value("absorber", "");
                v.gapMaterial = vol["materials"].value("gap", "");
            } else {
                v.absorberMaterial = "";
                v.gapMaterial = "";
            }

            v.inSolenoidField = vol.value("in_solenoid_field", false);

            if (vol.contains("geometry")) {
                const auto& geom = vol["geometry"];
                v.nofLayers = geom.value("nof_layers", 1);
                v.absoThickness = geom.value("absorber_thickness", 1.0);
                v.gapThickness = geom.value("gap_thickness", 1.0);
                v.rMin = geom.value("rmin", 0.0);
                v.rMax = geom.value("rmax", 0.0);
                v.zSize = geom.value("z_size", 0.0);
                if (geom.contains("center") && geom["center"].is_array() && geom["center"].size() >= 3) {
                    v.x = geom["center"][0].get<double>();
                    v.y = geom["center"][1].get<double>();
                    v.z = geom["center"][2].get<double>();
                } else {
                    v.x = v.y = v.z = 0.0;
                }
            } else {
                v.nofLayers = 1;
                v.absoThickness = v.gapThickness = 1.0;
                v.rMin = v.rMax = v.zSize = 0.0;
                v.x = v.y = v.z = 0.0;
            }

            if (v.plates == 2 && vol.contains("polycone")) {
                const auto& pcon = vol["polycone"];
                if (pcon.contains("z") && pcon["z"].is_array()) {
                    for (const auto& val : pcon["z"]) v.polyconePlanes.z.push_back(val.get<double>() * mm);
                }
                if (pcon.contains("rmin") && pcon["rmin"].is_array()) {
                    for (const auto& val : pcon["rmin"]) v.polyconePlanes.rmin.push_back(val.get<double>() * mm);
                }
                if (pcon.contains("rmax") && pcon["rmax"].is_array()) {
                    for (const auto& val : pcon["rmax"]) v.polyconePlanes.rmax.push_back(val.get<double>() * mm);
                }
            }

            if (vol.contains("cuts")) {
                const auto& cuts = vol["cuts"];
                v.electronCut = cuts.value("electron", 1.0);
                v.positronCut = cuts.value("positron", 1.0);
                v.gammaCut = cuts.value("gamma", 1.0);
                v.photonCut = cuts.value("proton", 1.0);
            } else {
                v.electronCut = v.positronCut = v.gammaCut = v.photonCut = 1.0;
            }
            m_volumes.push_back(v);
        }
        MSG_INFO("Successfully loaded " << m_volumes.size() << " volumes from " << filepath);
        return true;
    } catch (const std::exception& e) {
        MSG_ERROR("Error parsing geometry file " << filepath << ": " << e.what());
        return false;
    }
}

G4VPhysicalVolume* DetectorConstruction_v2::Construct()
{
    if (m_volumes.empty()) {
        if (!m_geometryFile.empty()) {
            MSG_INFO("Loading ATLAS geometry directly from file: " << m_geometryFile);
            if (!LoadGeometryFile(m_geometryFile)) {
                MSG_FATAL("Failed to load geometry file: " << m_geometryFile);
            }
        } else {
            MSG_FATAL("No geometry file specified for ATLAS DetectorConstruction_v2 and no volumes loaded!");
        }
    }

    DefineMaterials();
    return DefineVolumes();
}

void DetectorConstruction_v2::DefineMaterials()
{
    auto* nistManager = G4NistManager::Instance();
    nistManager->FindOrBuildMaterial("G4_Pb");
    nistManager->FindOrBuildMaterial("G4_Cu");
    nistManager->FindOrBuildMaterial("G4_Fe");
    nistManager->FindOrBuildMaterial("G4_Al");
    nistManager->FindOrBuildMaterial("G4_Si");
    nistManager->FindOrBuildMaterial("G4_W");
    nistManager->FindOrBuildMaterial("G4_AIR");

    G4double a, z, density;
    if (!G4Material::GetMaterial("liquidArgon", false)) {
        new G4Material("liquidArgon", z = 18., a = 39.95 * g / mole, density = 1.390 * g / cm3);
    }
    if (!G4Material::GetMaterial("Scintillator", false)) {
        auto* sc = nistManager->FindOrBuildMaterial("G4_PLASTIC_SC_VINYLTOLUENE");
        if (sc) {
            new G4Material("Scintillator", sc->GetDensity(), sc);
        } else {
            new G4Material("Scintillator", z = 6., a = 12.01 * g / mole, density = 1.032 * g / cm3);
        }
    }
    if (!G4Material::GetMaterial("Vacuum", false)) {
        new G4Material("Vacuum", z = 1., a = 1.01 * g / mole, density = universe_mean_density,
                       kStateGas, 2.73 * kelvin, 3.e-18 * pascal);
    }
}

G4VPhysicalVolume* DetectorConstruction_v2::DefineVolumes()
{
    auto* defaultMaterial = G4Material::GetMaterial("Vacuum");

    auto* worldS = new G4Tubs("World", 0, 6 * m, 10 * m, 0 * deg,
                              (!m_cutOnPhi) ? (360 * deg) : (235 * deg));
    auto* worldLV = new G4LogicalVolume(worldS, defaultMaterial, "World");
    auto* worldPV = new G4PVPlacement(0, G4ThreeVector(), worldLV, "World", 0, false, 0, m_checkOverlaps);

    // Solenoid volume envelope if UseSolenoidField is active (R < 1.228 m, |z| < 2.9 m to represent the warm bore field)
    if (m_useSolenoidField) {
        auto* solS = new G4Tubs("SolenoidEnvelope", 0, 1.228 * m, 2.9 * m, 0 * deg,
                                (!m_cutOnPhi) ? (360 * deg) : (235 * deg));
        m_solenoidLV = new G4LogicalVolume(solS, defaultMaterial, "SolenoidEnvelope");
        new G4PVPlacement(0, G4ThreeVector(), m_solenoidLV, "SolenoidEnvelope", worldLV, false, 0, m_checkOverlaps);
    }

    for (const auto& vol : m_volumes) {
        auto* region = GetRegion(vol.name);
        G4Material* absorberMat = G4Material::GetMaterial(vol.absorberMaterial);
        G4Material* gapMat = G4Material::GetMaterial(vol.gapMaterial);

        G4LogicalVolume* motherLV = (vol.inSolenoidField && m_solenoidLV) ? m_solenoidLV : worldLV;

        if (vol.plates == 0) {
            CreateHorizontalPlates(motherLV, vol, defaultMaterial, absorberMat, gapMat, region);
        } else if (vol.plates == 1) {
            CreateVerticalPlates(motherLV, vol, defaultMaterial, absorberMat, gapMat, region);
        } else if (vol.plates == 2) {
            CreatePolycone(motherLV, vol, absorberMat, region);
        }
    }

    return worldPV;
}

void DetectorConstruction_v2::CreateHorizontalPlates(G4LogicalVolume* worldLV,
                                                     const Volume& vol,
                                                     G4Material* defaultMaterial,
                                                     G4Material* absorberMaterial,
                                                     G4Material* gapMaterial,
                                                     G4Region* region)
{
    G4double calorRmin = vol.rMin * mm;
    G4double calorZ = vol.zSize * mm;
    G4double absoThickness = vol.absoThickness * mm;
    G4double gapThickness = vol.gapThickness * mm;
    G4double layerThickness = absoThickness + gapThickness;
    G4double calorRmax = (vol.nofLayers > 0 && layerThickness > 1e-5)
                             ? (calorRmin + vol.nofLayers * layerThickness)
                             : (vol.rMax * mm);
    G4ThreeVector center_pos(vol.x * mm, vol.y * mm, vol.z * mm);

    G4double dPhi = (!m_cutOnPhi) ? (360 * deg) : (235 * deg);

    auto* calorS = new G4Tubs(vol.name, calorRmin, calorRmax, calorZ / 2.0, 0 * deg, dPhi);
    auto* calorLV = new G4LogicalVolume(calorS, defaultMaterial, vol.name);
    new G4PVPlacement(0, center_pos, calorLV, vol.name, worldLV, false, 0, m_checkOverlaps);
    region->AddRootLogicalVolume(calorLV);

    for (int i = 0; i < vol.nofLayers; ++i) {
        G4double rmin_layer = calorRmin + i * layerThickness;
        G4double rmax_layer = calorRmin + (i + 1) * layerThickness;

        auto* layerS = new G4Tubs(vol.name + "_Layer", rmin_layer, rmax_layer, calorZ / 2.0, 0 * deg, dPhi);
        auto* layerLV = new G4LogicalVolume(layerS, defaultMaterial, vol.name + "_Layer");
        new G4PVPlacement(0, G4ThreeVector(), layerLV, vol.name + "_Layer", calorLV, false, i, m_checkOverlaps);

        if (absoThickness > 1e-5) {
            auto* absoS = new G4Tubs(vol.name + "_Abso", rmin_layer, rmin_layer + absoThickness, calorZ / 2.0, 0 * deg, dPhi);
            auto* absoLV = new G4LogicalVolume(absoS, absorberMaterial, vol.name + "_Abso");
            m_absorberPV = new G4PVPlacement(0, G4ThreeVector(), absoLV, vol.name + "_Abso", layerLV, false, i, m_checkOverlaps);
        }

        if (gapThickness > 1e-5) {
            auto* gapS = new G4Tubs(vol.name + "_Gap", rmin_layer + absoThickness, rmax_layer, calorZ / 2.0, 0 * deg, dPhi);
            auto* gapLV = new G4LogicalVolume(gapS, gapMaterial, vol.name + "_Gap");
            m_gapPV = new G4PVPlacement(0, G4ThreeVector(), gapLV, vol.name + "_Gap", layerLV, false, i, m_checkOverlaps);
        }
    }
}

void DetectorConstruction_v2::CreateVerticalPlates(G4LogicalVolume* worldLV,
                                                   const Volume& vol,
                                                   G4Material* defaultMaterial,
                                                   G4Material* absorberMaterial,
                                                   G4Material* gapMaterial,
                                                   G4Region* region)
{
    G4double calorRmin = vol.rMin * mm;
    G4double calorRmax = vol.rMax * mm;
    G4double calorZ = vol.zSize * mm;
    G4double absoThickness = vol.absoThickness * mm;
    G4double gapThickness = vol.gapThickness * mm;
    G4ThreeVector center_pos(vol.x * mm, vol.y * mm, vol.z * mm);

    G4double dPhi = (!m_cutOnPhi) ? (360 * deg) : (235 * deg);

    auto* calorS = new G4Tubs(vol.name, calorRmin, calorRmax, calorZ / 2.0, 0 * deg, dPhi);
    auto* calorLV = new G4LogicalVolume(calorS, defaultMaterial, vol.name);
    new G4PVPlacement(0, center_pos, calorLV, vol.name, worldLV, false, 0, m_checkOverlaps);
    region->AddRootLogicalVolume(calorLV);

    G4double layerThickness = absoThickness + gapThickness;
    for (int i = 0; i < vol.nofLayers; ++i) {
        G4double z_center_layer = -calorZ / 2.0 + (i + 0.5) * layerThickness;
        if (z_center_layer + layerThickness / 2.0 > calorZ / 2.0) break;

        auto* layerS = new G4Tubs(vol.name + "_Layer", calorRmin, calorRmax, layerThickness / 2.0, 0 * deg, dPhi);
        auto* layerLV = new G4LogicalVolume(layerS, defaultMaterial, vol.name + "_Layer");
        new G4PVPlacement(0, G4ThreeVector(0, 0, z_center_layer), layerLV, vol.name + "_Layer", calorLV, false, i, m_checkOverlaps);

        G4double z_center_abso = -layerThickness / 2.0 + absoThickness / 2.0;
        auto* absoS = new G4Tubs(vol.name + "_Abso", calorRmin, calorRmax, absoThickness / 2.0, 0 * deg, dPhi);
        auto* absoLV = new G4LogicalVolume(absoS, absorberMaterial, vol.name + "_Abso");
        m_absorberPV = new G4PVPlacement(0, G4ThreeVector(0, 0, z_center_abso), absoLV, vol.name + "_Abso", layerLV, false, i, m_checkOverlaps);

        if (gapThickness > 1e-5) {
            G4double z_center_gap = z_center_abso + absoThickness / 2.0 + gapThickness / 2.0;
            auto* gapS = new G4Tubs(vol.name + "_Gap", calorRmin, calorRmax, gapThickness / 2.0, 0 * deg, dPhi);
            auto* gapLV = new G4LogicalVolume(gapS, gapMaterial, vol.name + "_Gap");
            m_gapPV = new G4PVPlacement(0, G4ThreeVector(0, 0, z_center_gap), gapLV, vol.name + "_Gap", layerLV, false, i, m_checkOverlaps);
        }
    }
}

void DetectorConstruction_v2::CreatePolycone(G4LogicalVolume* worldLV,
                                             const Volume& vol,
                                             G4Material* material,
                                             G4Region* region)
{
    if (!material || vol.polyconePlanes.z.size() < 2) return;

    G4double dPhi = (!m_cutOnPhi) ? (360 * deg) : (235 * deg);

    auto* solid = new G4Polycone(vol.name, 0 * deg, dPhi, (G4int)vol.polyconePlanes.z.size(),
                                 vol.polyconePlanes.z.data(),
                                 vol.polyconePlanes.rmin.data(),
                                 vol.polyconePlanes.rmax.data());
    auto* lv = new G4LogicalVolume(solid, material, vol.name);
    new G4PVPlacement(0, G4ThreeVector(vol.x * mm, vol.y * mm, vol.z * mm), lv, vol.name, worldLV, false, 0, m_checkOverlaps);
    region->AddRootLogicalVolume(lv);
}

G4Region* DetectorConstruction_v2::GetRegion(const std::string& name)
{
    auto* reg = G4RegionStore::GetInstance()->GetRegion(name, false);
    return reg ? reg : new G4Region(name);
}

void DetectorConstruction_v2::ConstructSDandField()
{
    if (m_useMagneticField) {
        MSG_INFO("Set global magnetic field (2 Tesla)");
        G4ThreeVector fieldValue(0.0, 0.0, 2 * tesla);
        m_magFieldMessenger = new G4GlobalMagFieldMessenger(fieldValue);
        m_magFieldMessenger->SetVerboseLevel(1);
        G4AutoDelete::Register(m_magFieldMessenger);
    }

    if (m_useSolenoidField && m_solenoidLV) {
        MSG_INFO("Set solenoid magnetic field (2 Tesla inside solenoid envelope)");
        auto* solenoidField = new G4UniformMagField(G4ThreeVector(0.0, 0.0, 2 * tesla));
        auto* fieldManager = new G4FieldManager();
        fieldManager->SetDetectorField(solenoidField);
        fieldManager->CreateChordFinder(solenoidField);
        m_solenoidLV->SetFieldManager(fieldManager, true);
        G4AutoDelete::Register(solenoidField);
    }
}

} // namespace ATLAS
