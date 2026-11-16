
#include "DetectorConstruction_v2.h"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Polycone.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4PVReplica.hh"
#include "G4RotationMatrix.hh"
#include "G4Transform3D.hh"
#include "FCalFrozenShowerModel.h"
#include "AtlasDeadMaterialShower.h"
#include "AtlasGeoModelImport.h"
#include "AtlasMagneticField.h"
#include "TightMuonSteppingFieldManager.h"
#include "SwitchingFieldManager.h"
#include "G4LogicalVolumeStore.hh"
#include "SimpleFastKiller.h"
#include "G4AtlasRK4.h"
#include "G4IntegrationDriver.hh"
#include "G4Mag_UsualEqRhs.hh"
#include "G4ChordFinder.hh"
#include <mutex>
#include <algorithm>
#include <cmath>
#include "G4Kernel/AtlasG4Settings.h"
#include "G4GlobalMagFieldMessenger.hh"
#include "G4ProductionCuts.hh"
#include "G4AutoDelete.hh"
#include "G4GeometryManager.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4SolidStore.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"
#include "G4UniformMagField.hh"
#include "G4ProductionCuts.hh"
#include "G4TransportationManager.hh"
#include "G4FieldManager.hh"
#include "G4RegionStore.hh"
#include <string>
#include <sstream>

namespace{
template <typename T> int sign(T val) {
    return (T(0) < val) - (val < T(0));
}
}

G4ThreadLocal G4GlobalMagFieldMessenger* DetectorConstruction_v2::m_magFieldMessenger = nullptr;


/**
 * @class DetectorConstruction_v2
 * @brief Defines the full detector geometry for the simulation.
 * 
 * This class implements the G4VUserDetectorConstruction interface to build the 
 * Lorenzetti detector (calorimeters) using Geant4 geometry primitives.
 * It manages materials, logical volumes, and placements for both horizontal 
 * and vertical calorimeter plates.
 * 
 * Properties:
 * - UseMagneticField: Toggle global magnetic field (2 Tesla).
 * - UseSolenoidField: Uniform 2 Tesla axial field confined to the volume inside the ATLAS
 *   central solenoid (inner radius 1.23 m, axial length 5.8 m), with no field elsewhere.
 *   Cannot be combined with UseMagneticField.
 * - CutOnPhi: Restrict the detector to a phi wedge (used for debugging/visualization).
 */
DetectorConstruction_v2::DetectorConstruction_v2(std::string name)
 : 
  IMsgService(name), 
   G4VUserDetectorConstruction(),
   m_checkOverlaps(true)
{
  declareProperty( "UseMagneticField"           , m_useMagneticField=true     );
  declareProperty( "UseSolenoidField"           , m_useSolenoidField=false    );
  // Radius of the solenoid field volume (1230 mm, JINST table 2.1; 1229 mm, where the coil starts, with the ATLAS pieces
  // in front of the barrel accordion, F41 conserto 17c)
  declareProperty( "SolenoidFieldRadius"        , m_solenoidFieldRadius=1230.  );
  declareProperty( "CutOnPhi"                 , m_cutOnPhi=false            );
  // Frozen showers of the ATLAS FCal in the modules built by AddFCalModule (F41 conserto 23; needs the fast simulation process of
  // the RunManager, FastSimulation) and the directory of the libraries LArG4ShowerLib.FCAL<1,2>.<11,22,2112>.root
  declareProperty( "FCalFrozenShowers"          , m_fcalFrozenShowers=false   );
  // Geant4 settings of the ATLAS production (F41 conserto 24)
  declareProperty( "AtlasG4"                    , m_atlasG4=false             );
  declareProperty( "LArTreeVolumes"             , m_larTreeVolumes            );
  // The ATLAS Run 4 geometry of the simulation (--atlas-run4; F41 conserto 27): the inner detector (ITk, HGTD), the beam pipe and the
  // end-cap cryostats of the LAr imported from the GeoModel dump AtlasRun4Geometry; world of air up to |z| = 21 m
  declareProperty( "AtlasRun4"                  , m_atlasRun4=false           );
  declareProperty( "AtlasRun4Geometry"          , m_atlasRun4Geometry=""      );
  // the ATLAS material outside the calorimeters, imported from the same dump (--atlas-forward-shielding; F41 conserto 32): the whole
  // MuonSys (toroids, forward shielding JD/JT/JF, NSW, muon stations, calorimeter saddle) and the parts of the tile calorimeter that
  // Lorenzetti does not build (the girder of each module, the fingers, the saddles of the extended barrels); world of air of 30 m
  declareProperty( "AtlasForwardShielding"      , m_atlasForwardShielding=false );
  // the field of the ATLAS simulation as in the production (--atlas-full-field; F41 conserto 33; needs AtlasForwardShielding): the map in
  // the whole world (not only in the cylinder of the calorimeters) and the SwitchingFieldManager of ATLAS (MuonsOnlyInCaloFieldManager,
  // MuonFieldOnlyInCalo = True in the reference HITS) on the barrel EM calorimeter: only the muons see the field in its shell
  declareProperty( "AtlasFullField"             , m_atlasFullField=false      );
  // the dead material of ATLAS in the gap between the barrel and the extended barrel, from the same dump (--atlas-barrel-gap-services;
  // F41 conserto 34; needs AtlasForwardShielding): the LAr::DM::* children of LAr::Barrel::Cryostat::MotherVolume, the signal feedthroughs
  // and their cables, and the saddles of the tile barrel, instead of the services of conserto 11 (DM::ITC::Services, 5% of aluminium)
  declareProperty( "AtlasBarrelGapServices"     , m_atlasBarrelGapServices=false );
  // the tile extended barrel, ITC, gap and crack at the positions of the ATLAS simulation of Run 4 (--tile-atlas-run4; F41 conserto 35;
  // the volumes and cells are moved in python, AtlasRun4.py): with it the sector and bridge envelopes of the LAr services no longer cross
  // the gap and crack scintillators and are imported by AtlasBarrelGapServices
  declareProperty( "TileAtlasRun4"              , m_tileAtlasRun4=false       );
  // the field map of the ATLAS simulation for --atlas-run4 (bfieldmap_7730_20400_14m.root, the GlobalMap of /GLOBAL/BField/Maps)
  declareProperty( "AtlasFieldMap"              , m_atlasFieldMap=""          );
  declareProperty( "DeadMaterialVolumes"        , m_deadMaterialVolumes       );
  declareProperty( "FCalShowerLibDir"           , m_fcalShowerLibDir=""       );
  declareProperty( "OutputLevel"                , m_outputLevel=0             ); 
}


DetectorConstruction_v2::~DetectorConstruction_v2()
{;}



//
// Add volume
//
void DetectorConstruction_v2::AddVolume(std::string region,
                                        int plates,
                                        std::string absorberMaterial,
                                        std::string gapMaterial,
                                        int nofLayers,
                                        double absoThickness,
                                        double gapThickness,
                                        double layerClearance,
                                        double rMin,
                                        double rMax,
                                        double zSize,
                                        double x,
                                        double y,
                                        double z,
                                        // production cuts
                                        double electronCut,
                                        double positronCut,
                                        double gammaCut,
                                        double photonCut
                                        )
{
  m_volumes.push_back(Volume{region,plates,absorberMaterial,gapMaterial,nofLayers,absoThickness,gapThickness,layerClearance,rMin,rMax,zSize,x,y,z,
                      electronCut,positronCut,gammaCut,photonCut});
}

void DetectorConstruction_v2::SetAbsorberSplit(std::string region, double zSplit, std::string absorberMaterial2,
                                               double absoThickness2)
{
  m_absorberSplit[region] = AbsorberSplit{zSplit, absorberMaterial2, absoThickness2};
}

void DetectorConstruction_v2::AddMixture(std::string name, double density, std::vector<std::string> symbols,
                                         std::vector<double> fractions)
{
  m_mixtures.push_back(Mixture{name, density, symbols, fractions});
}

void DetectorConstruction_v2::SetPolycone(std::string region, std::vector<double> z, std::vector<double> rmin,
                                          std::vector<double> rmax)
{
  m_polycones[region] = PolyconePlanes{z, rmin, rmax};
}

void DetectorConstruction_v2::SetInSolenoidField(std::string region)
{
  m_inSolenoidField.insert(region);
}

void DetectorConstruction_v2::AddFCalModule(std::string name, std::string absorberMaterial, std::string rodMaterial,
                                            std::string troughMaterial, double rMin, double rMax, double z, double halfZ,
                                            double gapRMin, double gapRMax, double rodR, double troughRMin, double troughRMax,
                                            double troughSPhi, double troughDPhi, std::vector<double> troughAngles,
                                            std::vector<double> x, std::vector<double> y,
                                            double electronCut, double positronCut, double gammaCut, double photonCut)
{
  m_fcalModules.push_back(FCalModule{name, absorberMaterial, rodMaterial, troughMaterial, rMin, rMax, z, halfZ, gapRMin, gapRMax,
                                     rodR, troughRMin, troughRMax, troughSPhi, troughDPhi, troughAngles, x, y,
                                     electronCut, positronCut, gammaCut, photonCut});
}



G4VPhysicalVolume* DetectorConstruction_v2::Construct()
{
  // volumes of the LAr tree, for the photon Russian roulette of the ATLAS stacking action (F41 conserto 24)
  if (m_atlasG4) AtlasG4Settings::instance().larTreeVolumes = m_larTreeVolumes;
  // Define materials
  DefineMaterials();
  // Define volumes

  G4Material* defaultMaterial  = G4Material::GetMaterial("Vacuum");

  //
  // World
  //
  G4VSolid* worldS = new G4Tubs( "World",     // its name
                                 0,           // R min
                                 m_atlasForwardShielding ? 30*m : 6*m,         // R max (the MuonSys of ATLAS, --atlas-forward-shielding; JNSH reaches beyond 26 m)
                                 m_atlasForwardShielding ? 30*m : ( m_atlasRun4 ? 21*m : 10*m ),  // Z max (the forward beam pipe of ATLAS reaches |z| = 20.94 m)
                                 0*deg,       // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)      // phi_max
                                 );

  // the world of the ATLAS simulation is air (--atlas-run4)
  G4Material *worldMaterial = m_atlasRun4 ? G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR") : defaultMaterial;
  G4LogicalVolume* worldLV = new G4LogicalVolume(
                                 worldS,           // its solid
                                 worldMaterial,    // its material
                                 "World");         // its name

  G4VPhysicalVolume* worldPV = new G4PVPlacement(
                 0,                // no rotation
                 G4ThreeVector(),  // at (0,0,0)
                 worldLV,          // its logical volume
                 "World",          // its name
                 0,                // its mother  volume
                 false,            // no boolean operation
                 0,                // copy number
                 m_checkOverlaps);  // checking overlaps

  //
  // Solenoid field volume
  //
  // Vacuum cylinder filling the inside of the ATLAS central solenoid, which carries the
  // solenoid field (see ConstructSDandField). Dimensions from JINST 3 (2008) S08003, table 2.1:
  // inner diameter 2.46 m, axial length 5.8 m. The coil and its cryostat are not modelled.
  if (m_useSolenoidField && m_atlasRun4){
    MSG_INFO( "AtlasRun4: no solenoid field volume (the inner detector of ATLAS fills it)" );
  }
  if (m_useSolenoidField && !m_atlasRun4){
    if (m_useMagneticField){
      MSG_FATAL("UseSolenoidField and UseMagneticField cannot be enabled together. Abort!");
    }
    const double solenoidInnerRadius = m_solenoidFieldRadius*mm;
    const double solenoidHalfLength  = 2900*mm;
    G4VSolid* solenoidS = new G4Tubs( "SolenoidField",
                                      0,
                                      solenoidInnerRadius,
                                      solenoidHalfLength,
                                      0*deg,
                                      (!m_cutOnPhi)?(360*deg):(235*deg) );
    m_solenoidLV = new G4LogicalVolume( solenoidS, defaultMaterial, "SolenoidField" );
    new G4PVPlacement( 0, G4ThreeVector(), m_solenoidLV, "SolenoidField", worldLV, false, 0, m_checkOverlaps );
    MSG_INFO( "Creating solenoid field volume: R < " << solenoidInnerRadius/mm << " mm, |z| < "
              << solenoidHalfLength/mm << " mm" );
  }


  if (m_atlasRun4) BuildAtlasRun4( worldLV );

  for (auto &volume : m_volumes){

    MSG_INFO( "Creating Volume with name " << volume.name );
    // Mother: the world, or the solenoid field volume for the volumes that sit inside it (F41 conserto 17c)
    G4LogicalVolume *motherLV = worldLV;
    if (m_inSolenoidField.count(volume.name)){
      if (m_solenoidLV){ motherLV = m_solenoidLV; }
      else{ MSG_INFO( "No solenoid field volume: " << volume.name << " placed in the world" ); }
    }
    // inside the deepest imported ATLAS volume that contains it (--atlas-run4): points of its (r, z) outline at four phi
    if (!m_atlasContainers.empty()){
      std::vector<G4ThreeVector> pts;
      std::vector<std::pair<double,double>> rz;
      auto pc = m_polycones.find(volume.name);
      if (volume.plates == 2 && pc != m_polycones.end()){
        for (size_t k = 0; k < pc->second.z.size(); ++k){
          rz.push_back({pc->second.rmin[k], pc->second.z[k]}); rz.push_back({pc->second.rmax[k], pc->second.z[k]});
          rz.push_back({0.5*(pc->second.rmin[k] + pc->second.rmax[k]), pc->second.z[k]});
        }
      }else{
        for (double r : {volume.rMin, 0.5*(volume.rMin + volume.rMax), volume.rMax})
          for (double z : {volume.z - 0.5*volume.zSize, volume.z, volume.z + 0.5*volume.zSize}) rz.push_back({r, z});
      }
      for (auto &p : rz)
        for (double phi : {0.1, 1.67, 3.24, 4.81}) pts.push_back( G4ThreeVector( p.first*std::cos(phi), p.first*std::sin(phi), p.second ) );
      motherLV = MotherFor( pts, worldLV );
    }

    if(volume.plates == 0){ //Plates::Horizontal){

      if (volume.layerClearance != 0){
        MSG_FATAL("LayerClearance is only implemented for vertical plates (volume " << volume.name << "). Abort!");
      }
      auto region = GetRegion(volume.name);


      // Create a region
      CreateHorizontalPlates( motherLV,
                    volume.name,
                    defaultMaterial, // default
                    G4Material::GetMaterial(volume.absorberMaterial), // absorber
                    G4Material::GetMaterial(volume.gapMaterial), // gap
                    volume.nofLayers, // ATLAS-like
                    volume.absoThickness, // abso
                    volume.gapThickness, // gap
                    volume.rMin, // start radio,
                    volume.zSize ,// z
                    G4ThreeVector(volume.x,volume.y,volume.z),
                    region );
      G4ProductionCuts* cuts=new G4ProductionCuts();
      cuts->SetProductionCut(volume.gammaCut,"gamma");
      cuts->SetProductionCut(volume.electronCut,"e-");
      cuts->SetProductionCut(volume.positronCut,"e+");
      cuts->SetProductionCut(volume.photonCut,"proton");
      // assign cuts to the region and return succesfully
      region->SetProductionCuts(cuts);
      
    }else if (volume.plates == 1){ //Plates::Vertical){

      auto region = GetRegion(volume.name);
      // Create a region
      CreateVerticalPlates( motherLV,
                    volume.name,
                    defaultMaterial, // default
                    G4Material::GetMaterial(volume.absorberMaterial), // absorber
                    G4Material::GetMaterial(volume.gapMaterial), // gap
                    volume.nofLayers, // ATLAS-like
                    volume.absoThickness, // abso
                    volume.gapThickness, // gap
                    volume.layerClearance, // empty space per layer
                    volume.rMin, // start radio,
                    volume.rMax,
                    volume.zSize ,// z
                    G4ThreeVector(volume.x,volume.y,volume.z),
                    region );


      G4ProductionCuts* cuts=new G4ProductionCuts();
      cuts->SetProductionCut(volume.gammaCut,"gamma");
      cuts->SetProductionCut(volume.electronCut,"e-");
      cuts->SetProductionCut(volume.positronCut,"e+");
      cuts->SetProductionCut(volume.photonCut,"proton");
      // assign cuts to the region and return succesfully
      region->SetProductionCuts(cuts);
    
    }else if (volume.plates == 2){ //Plates::Polycone

      auto planes = m_polycones.find(volume.name);
      if (planes == m_polycones.end()){
        MSG_FATAL("Polycone " << volume.name << " without planes (SetPolycone). Abort!");
      }
      auto region = GetRegion(volume.name);
      CreatePolycone( motherLV, volume.name, G4Material::GetMaterial(volume.absorberMaterial), planes->second, region );
      G4ProductionCuts* cuts=new G4ProductionCuts();
      cuts->SetProductionCut(volume.gammaCut,"gamma");
      cuts->SetProductionCut(volume.electronCut,"e-");
      cuts->SetProductionCut(volume.positronCut,"e+");
      cuts->SetProductionCut(volume.photonCut,"proton");
      region->SetProductionCuts(cuts);

    }else{
      MSG_FATAL("Volume type is not recognize. Abort!");
    }
  }// Loop over volumes

  // Modules of the ATLAS FCal with their electrodes (F41 conserto 22)
  for (auto &fm : m_fcalModules){
    MSG_INFO( "Creating FCal module " << fm.name << " with " << fm.x.size() << " electrodes" );
    auto region = GetRegion(fm.name);
    G4LogicalVolume *fcalMother = worldLV;
    if (!m_atlasContainers.empty()){
      std::vector<G4ThreeVector> pts;
      for (double r : {fm.rMin, fm.rMax}) for (double z : {fm.z - fm.halfZ, fm.z + fm.halfZ}) for (double phi : {0.1, 1.67, 3.24, 4.81})
        pts.push_back( G4ThreeVector( r*std::cos(phi), r*std::sin(phi), z ) );
      fcalMother = MotherFor( pts, worldLV );
    }
    CreateFCalModule( fcalMother, fm, region );
    G4ProductionCuts* cuts=new G4ProductionCuts();
    cuts->SetProductionCut(fm.gammaCut,"gamma");
    cuts->SetProductionCut(fm.electronCut,"e-");
    cuts->SetProductionCut(fm.positronCut,"e+");
    cuts->SetProductionCut(fm.photonCut,"proton");
    region->SetProductionCuts(cuts);
  }

  return worldPV;
}


void DetectorConstruction_v2::DefineMaterials()
{
  // Lead material defined using NIST Manager
  G4NistManager* nistManager = G4NistManager::Instance();
  nistManager->FindOrBuildMaterial("G4_Cu");
  nistManager->FindOrBuildMaterial("G4_Pb");
  nistManager->FindOrBuildMaterial("G4_Fe");
  nistManager->FindOrBuildMaterial("G4_Al");
  nistManager->FindOrBuildMaterial("G4_Si");
  nistManager->FindOrBuildMaterial("G4_CESIUM_IODIDE");
  nistManager->FindOrBuildMaterial("PLASTIC SCINTILLATOR");
  G4Element* elH = new G4Element("Hydrogen", "H", 1., 1.0079 * g/mole);
  G4Element* elC = new G4Element("Carbon", "C", 6., 12.011 * g/mole);
  G4Material* scinti = new G4Material("PLASTIC SCINTILLATOR", 1.032 * g/cm3, 2); // Organic plastic scintillator, polystyrene
  scinti->AddElement(elH, 8.5*perCent);
  scinti->AddElement(elC, 91.5*perCent);

  // Liquid argon material
  G4double a;  // mass of a mole;
  G4double z;  // z=mean number of protons;
  G4double density;
  // The argon by NIST Manager is a gas with a different density
  // With the ATLAS Geant4 settings, std::LiquidArgon of the ATLAS geometry: pure argon, 1.396 g/cm3, A = 39.948 g/mol (F41 conserto 24)
  if (m_atlasG4) new G4Material("liquidArgon", z=18., a= 39.948*g/mole, density= 1.396*g/cm3);
  else           new G4Material("liquidArgon", z=18., a= 39.95*g/mole, density= 1.390*g/cm3);

  // Vacuum
  new G4Material("Vacuum", z=1., a=1.01*g/mole,density= universe_mean_density,kStateGas, 2.73*kelvin, 3.e-18*pascal);

  // Absorbers of the ATLAS barrel EM calorimeter (option AtlasEmb, geometry/python/v1/ECAL.py), as homogeneous mixtures
  // with the masses per unit area of one absorber: lead (1.53 mm below |eta| = 0.8, 1.13 mm above), two 0.2 mm sheets of
  // stainless steel (taken as iron) and 0.832 mm of polyimide for the glue and the readout electrode (JINST 3 (2008)
  // S08003, sec. 5.2.1; the polyimide thickness is not given there and is fitted to the X0 of fig. 5.1 at eta = 0).
  // Not used by the default geometry.
  {
    G4Material *pb = nistManager->FindOrBuildMaterial("G4_Pb");
    G4Material *fe = nistManager->FindOrBuildMaterial("G4_Fe");
    G4Material *kapton = nistManager->FindOrBuildMaterial("G4_KAPTON");
    const double tfe = 0.4, tkapton = 0.832; // mm
    for( double tpb : {1.53, 1.13} ){
      const double mpb = tpb*pb->GetDensity(), mfe = tfe*fe->GetDensity(), mk = tkapton*kapton->GetDensity();
      const double m = mpb + mfe + mk;
      const std::string matName = (tpb > 1.3) ? "ATLAS_EMB_ABSORBER_153" : "ATLAS_EMB_ABSORBER_113";
      G4Material *mix = new G4Material(matName, m/(tpb + tfe + tkapton), 3);
      mix->AddMaterial(pb, mpb/m);
      mix->AddMaterial(fe, mfe/m);
      mix->AddMaterial(kapton, mk/m);
    }
  }

  // Absorbers of the ATLAS-like EM end-cap (option AtlasEmec, geometry/python/v1/EMEC.py), as homogeneous mixtures with
  // the masses per unit area of one absorber and one electrode: lead (1.7 mm in the outer wheel, 2.2 mm in the inner one;
  // JINST 3 (2008) S08003, sec. 5.2.1), two 0.2 mm sheets of stainless steel (taken as iron), two 0.15 mm prepreg sheets
  // (taken as polyimide; LAr TDR, CERN/LHCC 96-41, sec. 7.2) and the readout electrode of 0.275 mm, with 0.105 mm of
  // copper and 0.170 mm of polyimide and glue (taken as polyimide; LAr TDR, fig. 6-16). Not used by the default geometry.
  {
    G4Material *pb = nistManager->FindOrBuildMaterial("G4_Pb");
    G4Material *fe = nistManager->FindOrBuildMaterial("G4_Fe");
    G4Material *kapton = nistManager->FindOrBuildMaterial("G4_KAPTON");
    G4Material *cu = nistManager->FindOrBuildMaterial("G4_Cu");
    const double tfe = 0.4, tkapton = 0.3 + 0.170, tcu = 0.105; // mm
    for( double tpb : {1.7, 2.2} ){
      const double mpb = tpb*pb->GetDensity(), mfe = tfe*fe->GetDensity(), mk = tkapton*kapton->GetDensity();
      const double mcu = tcu*cu->GetDensity();
      const double m = mpb + mfe + mk + mcu;
      const std::string matName = (tpb < 2.0) ? "ATLAS_EMEC_ABSORBER_OUTER" : "ATLAS_EMEC_ABSORBER_INNER";
      G4Material *mix = new G4Material(matName, m/(tpb + tfe + tkapton + tcu), 4);
      mix->AddMaterial(pb, mpb/m);
      mix->AddMaterial(fe, mfe/m);
      mix->AddMaterial(kapton, mk/m);
      mix->AddMaterial(cu, mcu/m);
    }
  }

  // LArElectronics of the ATLAS barrel cryostat (behind the end of the ATLAS-like barrel, geometry/python/v1/ECAL.py,
  // --atlas-emb-cells): 1.58 g/cm3, mass fractions copper 0.13, kapton 0.07, argon 0.80 (ATLAS geometry database,
  // LArMaterials-12 and its components). Not used by the default geometry.
  {
    G4Material *mix = new G4Material("ATLAS_LAR_ELECTRONICS", 1.58*g/cm3, 3);
    mix->AddMaterial(nistManager->FindOrBuildMaterial("G4_Cu"), 0.13);
    mix->AddMaterial(nistManager->FindOrBuildMaterial("G4_KAPTON"), 0.07);
    mix->AddMaterial(G4Material::GetMaterial("liquidArgon"), 0.80);
  }

  // Mixtures defined by the geometry in Python (AddMixture)
  for (auto &mix : m_mixtures){
    if (G4Material::GetMaterial(mix.name, false)) continue;
    auto *mat = new G4Material(mix.name, mix.density*g/cm3, (G4int)mix.symbols.size());
    for (size_t i = 0; i < mix.symbols.size(); ++i){
      auto *el = nistManager->FindOrBuildElement(mix.symbols[i]);
      // braces needed: MSG_FATAL is several statements
      if (!el){ MSG_FATAL("Mixture " << mix.name << ": unknown element " << mix.symbols[i] << ". Abort!"); }
      mat->AddElement(el, mix.fractions[i]);
    }
  }

  // Print materials
  G4cout << *(G4Material::GetMaterialTable()) << G4endl;
}







/**
 * @brief Constructs the horizontal plates of a calorimeter module (Barrel).
 * 
 * Creates a "sandwich" structure of absorber, gap, and absorber layers arranged 
 * radially (for cylindrical/barrel geometry).
 * 
 * @param worldLV Mother logical volume.
 * @param name Unique name for the volume.
 * @param defaultMaterial Envelope material (usually Vacuum).
 * @param absorberMaterial Absorber material (e.g., Pb, Fe).
 * @param gapMaterial Active material (e.g., LAr, Scintillator).
 * @param nofLayers Number of repeating layers.
 * @param absoThickness Thickness of the absorber plate.
 * @param gapThickness Thickness of the active gap.
 * @param calorRmin Inner radius.
 * @param calorZ Total length in Z.
 * @param center_pos Center position (displacement).
 * @param region G4Region associated with this detector part.
 */
void DetectorConstruction_v2::CreateHorizontalPlates(  G4LogicalVolume *worldLV, 
                                                    std::string name,  
                                                    G4Material *defaultMaterial,
                                                    G4Material *absorberMaterial,
                                                    G4Material *gapMaterial,
                                                    int nofLayers,
                                                    double absoThickness,
                                                    double gapThickness,
                                                    double calorRmin,
                                                    double calorZ,
                                                    const G4ThreeVector &center_pos,
                                                    G4Region *region
                                                    ) 

{
  if ( ! defaultMaterial || ! absorberMaterial || ! gapMaterial ) {
    G4ExceptionDescription msg;
    msg << "Cannot retrieve materials already defined.";
    G4Exception("DetectorConstruction_v2::DefineVolumes()", "MyCode0001", FatalException, msg);
  }


  G4double layerThickness=absoThickness+gapThickness; 

  G4VSolid* calorimeterS = new G4Tubs( name,// its name
                                 calorRmin, // R min 1700mm
                                 calorRmin+ nofLayers*layerThickness, // R max 48cm+1700mm
                                 calorZ/2,    // Z max, +250cm
                                 0*deg,     // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)    // phi_max
                                 ) ;




  G4LogicalVolume* calorLV = new G4LogicalVolume( calorimeterS,     // its solid
                                                  defaultMaterial,  // its material
                                                  name);   // its name
  PlaceGlobal( calorLV, center_pos, name, worldLV );
  
  region->AddRootLogicalVolume(calorLV);



  auto split = m_absorberSplit.find(name);
  for (G4int layer=0; layer < nofLayers; ++layer){

    G4VSolid* layerS = new G4Tubs(name+ "_Layer",// its name
                                 calorRmin + layer*layerThickness,        // R min 1700mm
                                 calorRmin + (layer+1)*layerThickness,   // R max 48cm+1700mm
                                 calorZ/2,            // Z max, +250cm
                                 0*deg,             // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)            // phi_max
                                 ) ;

    G4LogicalVolume* layerLV = new G4LogicalVolume(
                                                  layerS,           // its solid
                                                  defaultMaterial,  // its material
                                                  name+"_Layer");   // its name


    new G4PVPlacement(
                 0,                 // no rotation
                 G4ThreeVector(0,0,0),
                 //center_pos,        // at (0,0,0)
                 layerLV,           // its logical volume
                 name+"_Layer",     // its name
                 calorLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps
    


    if( split == m_absorberSplit.end() ){
    G4VSolid* absorverS = new G4Tubs( name+"_Abso",// its name
                                 calorRmin + layer*(absoThickness + gapThickness) ,     // R min 1700mm
                                 calorRmin + layer*(absoThickness + gapThickness) + absoThickness,   // R max 48cm+1700mm
                                 calorZ/2,          // Z max, +250cm
                                 0*deg,                 // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)             // phi_max
                                 ) ;

    G4LogicalVolume* absorverLV = new G4LogicalVolume(
                                                  absorverS,           // its solid
                                                  absorberMaterial,  // its material
                                                  name+"_Abso");         // its name


    new G4PVPlacement(
                 0,                 // no rotation
                 G4ThreeVector(0,0,0),
                 //center_pos,        // at (0,0,0)
                 absorverLV,        // its logical volume
                 name+"_Abso",      // its name
                 layerLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps




    G4VSolid* gapS = new G4Tubs( name+"_Gap",// its name
                                 calorRmin + layer*(absoThickness + gapThickness) + absoThickness,   // R max 48cm+1700mm
                                 calorRmin + (layer+1)*(absoThickness + gapThickness),   // R max 48cm+1700mm
                                 calorZ/2,          // Z max, +250cm
                                 0*deg,           // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)          // phi_max
        ); 

    G4LogicalVolume* gapLV = new G4LogicalVolume(
                                                  gapS,           // its solid
                                                  gapMaterial,  // its material
                                                  name+"_Gap");         // its name


    new G4PVPlacement(
                 0,                 // no rotation
                 G4ThreeVector(0,0,0),
                 //center_pos,        // at (0,0,0)
                 gapLV,             // its logical volume
                 name+"_Gap",       // its name
                 layerLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps


    } else {
      // Absorber changing for |z| > zSplit (SetAbsorberSplit): three pieces in z, the same layer thickness, the gap
      // taking the rest of the layer in each piece.
      const AbsorberSplit &sp = split->second;
      G4Material *absorberMaterial2 = G4Material::GetMaterial(sp.material);
      const double zh = calorZ/2;
      if( !absorberMaterial2 || sp.z <= 0 || sp.z >= zh || sp.thickness <= 0 || sp.thickness >= layerThickness ){
        G4ExceptionDescription msg;
        msg << "Invalid absorber split for " << name;
        G4Exception("DetectorConstruction_v2::CreateHorizontalPlates()", "MyCode0002", FatalException, msg);
      }
      const double r0 = calorRmin + layer*layerThickness;
      struct Piece { double halfz; double zc; G4Material *mat; double t; };
      const Piece pieces[3] = { {sp.z, 0., absorberMaterial, absoThickness},
                                {(zh - sp.z)/2,  (zh + sp.z)/2, absorberMaterial2, sp.thickness},
                                {(zh - sp.z)/2, -(zh + sp.z)/2, absorberMaterial2, sp.thickness} };
      for( const auto &piece : pieces ){
        G4VSolid* aS = new G4Tubs( name+"_Abso", r0, r0 + piece.t, piece.halfz, 0*deg, (!m_cutOnPhi)?(360*deg):(235*deg) );
        G4LogicalVolume* aLV = new G4LogicalVolume( aS, piece.mat, name+"_Abso" );
        new G4PVPlacement( 0, G4ThreeVector(0,0,piece.zc), aLV, name+"_Abso", layerLV, false, 0, m_checkOverlaps );
        G4VSolid* gS = new G4Tubs( name+"_Gap", r0 + piece.t, r0 + layerThickness, piece.halfz, 0*deg, (!m_cutOnPhi)?(360*deg):(235*deg) );
        G4LogicalVolume* gLV = new G4LogicalVolume( gS, gapMaterial, name+"_Gap" );
        new G4PVPlacement( 0, G4ThreeVector(0,0,piece.zc), gLV, name+"_Gap", layerLV, false, 0, m_checkOverlaps );
      }
    }
  }// Loop over calorimeter layers
}


void DetectorConstruction_v2::CreateVerticalPlates(  G4LogicalVolume *worldLV, 
                                                  std::string name,  
                                                  G4Material *defaultMaterial,
                                                  G4Material *absorberMaterial,
                                                  G4Material *gapMaterial,
                                                  int nofLayers,
                                                  double absoThickness,
                                                  double gapThickness,
                                                  double layerClearance,
                                                  double calorRmin,
                                                  double calorRmax,
                                                  double calorZ,
                                                  const G4ThreeVector &center_pos,
                                                  G4Region *region
                                                  ) 
{
  if ( ! defaultMaterial || ! absorberMaterial || ! gapMaterial ) {
    G4ExceptionDescription msg;
    msg << "Cannot retrieve materials already defined.";
    G4Exception("DetectorConstruction_v2::DefineVolumes()", "MyCode0001", FatalException, msg);
  }

  const bool evenNofLayers = !(nofLayers % 2);
  const bool invertOrder = center_pos.z() < 0.;

  // Each layer is absorber + gap + clearance. The absorber sits at one end of the layer and the
  // gap at the other, so a non-zero clearance leaves an empty space (envelope material) between
  // the gap and the absorber of the same layer: along the stacking axis the sequence is
  // absorber, gap, clearance, absorber, ... With clearance = 0 the layout is unchanged.
  // Used by the ATLAS-like tile calorimeter: 14 mm steel + 3 mm tile + 1 mm left by the 3 mm
  // tile in its 4 mm pocket, period 18 mm (TILECAL, hep-ex/9904032; JINST 3 S08003, sec. 5.3.1.2).
  G4double layerThickness=absoThickness+gapThickness+layerClearance; 

  G4VSolid* calorimeterS = new G4Tubs( name,// its name
                                 calorRmin,
                                 calorRmax,
                                 calorZ/2, // Size in z
                                 0*deg,     // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)    // phi_max
                                 ) ;

  G4LogicalVolume* calorLV = new G4LogicalVolume( calorimeterS,     // its solid
                                                  defaultMaterial,  // its material
                                                  name);   // its name


  PlaceGlobal( calorLV, center_pos, name, worldLV );
  
  region->AddRootLogicalVolume(calorLV);

  for (G4int layer=-nofLayers/2; layer <= nofLayers/2; ++layer){
    if ( layer == 0 && evenNofLayers){
      continue;
    }

    G4VSolid* layerS = new G4Tubs(name+ "_Layer",// its name
                                 calorRmin,
                                 calorRmax,
                                 layerThickness/2,
                                 0*deg,
                                 (!m_cutOnPhi)?(360*deg):(235*deg)
                                 );

    G4LogicalVolume* layerLV = new G4LogicalVolume(
                                                  layerS,           // its solid
                                                  defaultMaterial,  // its material
                                                  name+"_Layer");   // its name

    const auto layerLVCenter = G4ThreeVector(0,0,
                   ((invertOrder)?-1.:+1.) * 
                   (sign(-layer)*((evenNofLayers)?0.5:0.) + (layer))
                   *layerThickness // center at with respect to the calorimeter center
                 );

    //G4cout << "Creating layer " << layer << " for: " << layerLVCenter << ". Size: " << layerThickness << std::endl;

    new G4PVPlacement(
                 0,                 // no rotation
                 layerLVCenter,     // center
                 layerLV,           // its logical volume
                 name+"_Layer",     // its name
                 calorLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps



    G4VSolid* absorverS = new G4Tubs( name+"_Abso",// its name
                                 calorRmin,     // R min
                                 calorRmax,     // R max
                                 absoThickness/2,  // 
                                 0*deg,         // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)        // phi_max
                                 ) ;

    G4LogicalVolume* absorverLV = new G4LogicalVolume(
                                                  absorverS,           // its solid
                                                  absorberMaterial,  // its material
                                                  name+"_Abso");         // its name


    new G4PVPlacement(
                 0,                 // no rotation
                 G4ThreeVector(0,0,
                   ((invertOrder)?-1.:+1) * 
                   layerThickness/2
                   + ((invertOrder)?+1.:-1)/2 * 
                    absoThickness
                 ),
                 absorverLV,        // its logical volume
                 name+"_Abso",      // its name
                 layerLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps




    G4VSolid* gapS = new G4Tubs( name+"_Gap",// its name
                                 calorRmin,   // R max
                                 calorRmax,   // R max
                                 gapThickness/2,   // Z max,
                                 0*deg,           // phi_min
                                 (!m_cutOnPhi)?(360*deg):(235*deg)          // phi_max
        ); 

    G4LogicalVolume* gapLV = new G4LogicalVolume(
                                                  gapS,           // its solid
                                                  gapMaterial,  // its material
                                                  name+"_Gap");         // its name


    new G4PVPlacement(
                 0,                 // no rotation
                 G4ThreeVector(0,0,
                   ((invertOrder)?+1.:-1) * 
                   layerThickness/2
                   + ((invertOrder)?-1.:+1) * 
                    gapThickness/2
                 ),
                 gapLV,             // its logical volume
                 name+"_Gap",       // its name
                 layerLV,           // its mother  volume
                 false,             // no boolean operation
                 0,                 // copy number
                 m_checkOverlaps);  // checking overlaps
  }// Loop over calorimeter layers

}





void DetectorConstruction_v2::ConstructSDandField(){

  // The field and the beam pipe killer of the ATLAS Run 4 simulation (--atlas-run4; F41 conserto 27)
  if (m_atlasRun4){
    ConstructAtlasField();
    auto *bp = G4RegionStore::GetInstance()->GetRegion( "BeampipeFwdCut", false );
    if (bp) new SimpleFastKiller( "SimpleFastKiller", bp );
  }

  // Dead material shower of the ATLAS settings (F41 conserto 24): HighEnergy 1000 GeV, LowEnergy 0, ZCutoff 5698 mm
  if (m_atlasG4){
    for (const auto &name : m_deadMaterialVolumes){
      auto *region = G4RegionStore::GetInstance()->GetRegion(name);
      if (!region){ MSG_FATAL("No region for the dead material volume " << name); }
      new AtlasDeadMaterialShower( name + "::DeadMaterialShower", region, 1000.*GeV, 0., 5698.*mm );
    }
    MSG_INFO("Dead material shower in " << m_deadMaterialVolumes.size() << " volumes");
  }

  // Frozen showers of the ATLAS FCal (F41 conserto 23): one model per module and side, as LArG4FastSimulationConfig.py of the Athena
  // release 23.0.14 (FCALFastShower in the region of FCal1 with the libraries FCAL1; FCAL2FastShower in FCal2 and FCal3 with the
  // libraries FCAL2). Energies in MeV.
  if (m_fcalFrozenShowers && !m_fcalModules.empty()){
    auto libs = FCalFrozenShowerModel::loadLibraries( m_fcalShowerLibDir );
    for (auto &fm : m_fcalModules){
      const bool fcal1 = fm.name.find("Module1") != std::string::npos;
      FCalFrozenShowerModel::Config cfg;
      cfg.library = fcal1 ? "FCAL1" : "FCAL2";
      cfg.eMin = fcal1 ? 3.0 : 1.0;  cfg.eMax = 1000.;
      cfg.gMin = 0.;  cfg.gMax = 10.;
      cfg.nMin = 0.;  cfg.nMax = 100.;
      cfg.containLow  = !fcal1;  cfg.absLowEta  = fcal1 ? 4.0 : 3.8;
      cfg.containHigh = !fcal1;  cfg.absHighEta = fcal1 ? 4.6 : 4.4;
      cfg.containCrack = true;   cfg.absCrackEta1 = 0.5;  cfg.absCrackEta2 = 1.1;   // not used: ContainCrack is true
      auto *region = G4RegionStore::GetInstance()->GetRegion(fm.name);
      if (!region){ MSG_FATAL("No region for the FCal module " << fm.name); }
      new FCalFrozenShowerModel( fm.name + "::FrozenShower", region, cfg, libs.at(cfg.library) );
      MSG_INFO("Frozen showers (" << cfg.library << ") in " << fm.name);
    }
  }

  if (m_useMagneticField){
    MSG_INFO("Set magnetic field")
    // Create global magnetic field messenger.
    // Uniform magnetic field is then created automatically if
    // the field value is not zero.
    G4ThreeVector fieldValue(0.0 , 0.0, 2*tesla);
    m_magFieldMessenger = new G4GlobalMagFieldMessenger(fieldValue);
    m_magFieldMessenger->SetVerboseLevel(1);

    // Register the field messenger for deleting
    G4AutoDelete::Register(m_magFieldMessenger);
  }

  if (m_useSolenoidField && m_solenoidLV){
    MSG_INFO("Set solenoid magnetic field (2 T, only inside the solenoid volume)")
    // Local field: attached to the solenoid volume only, so particles leaving it
    // (and the showers in the calorimeters) are not bent.
    auto solenoidField = new G4UniformMagField( G4ThreeVector(0.0, 0.0, 2*tesla) );
    auto fieldManager  = new G4FieldManager();
    fieldManager->SetDetectorField( solenoidField );
    fieldManager->CreateChordFinder( solenoidField );
    m_solenoidLV->SetFieldManager( fieldManager, true );
    // The field manager is owned and deleted by the G4FieldManagerStore: registering it
    // with G4AutoDelete as well deletes it twice at exit.
    G4AutoDelete::Register( solenoidField );
  }

}



void DetectorConstruction_v2::CreatePolycone( G4LogicalVolume *motherLV, std::string name, G4Material *material,
                                              const PolyconePlanes &planes, G4Region *region )
{
  if (!material){
    G4ExceptionDescription msg;
    msg << "Cannot retrieve the material of the polycone " << name;
    G4Exception("DetectorConstruction_v2::CreatePolycone()", "MyCode0003", FatalException, msg);
  }
  auto *solid = new G4Polycone( name, 0*deg, (!m_cutOnPhi)?(360*deg):(235*deg), (G4int)planes.z.size(),
                                planes.z.data(), planes.rmin.data(), planes.rmax.data() );
  auto *lv = new G4LogicalVolume( solid, material, name );
  PlaceGlobal( lv, G4ThreeVector(), name, motherLV );
  region->AddRootLogicalVolume(lv);
}


G4Region* DetectorConstruction_v2::GetRegion( std::string name ){
  auto reg = G4RegionStore::GetInstance()->GetRegion(name);
  return reg ? reg : new G4Region(name);
}


// One module of the ATLAS FCal with its electrodes (F41 conserto 22), as the ATLAS geometry builds it (Athena,
// LArCalorimeter/LArGeoModel/LArGeoFcal/src/FCALConstruction.cxx; dimensions and materials of the public GeoModel geometry,
// geometry/python/v1/AtlasFCal.py): the absorber, then its daughters in the order of the GeoModel, the cable troughs and the
// gaps, the gap k with copy number k (GeoSerialIdentifier(0)), with the rod of FCal2 and FCal3 as daughter of the gap. In the
// ATLAS geometry two electrodes of FCal1 reach into a cable trough; they are kept as they are. The overlaps of the troughs and
// of the gaps are not checked here (tens of thousands of daughters).
void DetectorConstruction_v2::CreateFCalModule( G4LogicalVolume *motherLV, const FCalModule &m, G4Region *region )
{
  if (m_cutOnPhi){
    MSG_FATAL("The FCal with its electrodes (" << m.name << ") cannot be built with CutOnPhi. Abort!");
  }
  G4Material *absorber = G4Material::GetMaterial(m.absorberMaterial);
  G4Material *trough   = G4Material::GetMaterial(m.troughMaterial);
  G4Material *lar      = G4Material::GetMaterial("liquidArgon");
  G4Material *rod      = m.rodR > 0 ? G4Material::GetMaterial(m.rodMaterial) : nullptr;
  if ( !absorber || !trough || !lar || (m.rodR > 0 && !rod) || m.x.size() != m.y.size() ){
    G4ExceptionDescription msg;
    msg << "Cannot build the FCal module " << m.name;
    G4Exception("DetectorConstruction_v2::CreateFCalModule()", "MyCode0004", FatalException, msg);
  }

  auto *absS  = new G4Tubs( m.name, m.rMin, m.rMax, m.halfZ, 0*deg, 360*deg );
  auto *absLV = new G4LogicalVolume( absS, absorber, m.name );
  PlaceGlobal( absLV, G4ThreeVector(0, 0, m.z), m.name, motherLV );
  region->AddRootLogicalVolume(absLV);

  // cable troughs
  auto *trS  = new G4Tubs( m.name + "::CableTrough", m.troughRMin, m.troughRMax, m.halfZ, m.troughSPhi, m.troughDPhi );
  auto *trLV = new G4LogicalVolume( trS, trough, m.name + "::CableTrough" );
  for (size_t k = 0; k < m.troughAngles.size(); ++k){
    G4RotationMatrix rot; rot.rotateZ( m.troughAngles[k] );
    new G4PVPlacement( G4Transform3D(rot, G4ThreeVector()), trLV, m.name + "::CableTrough", absLV, false, (G4int)k, false );
  }

  // gaps of liquid argon, one per electrode (the sensitive volume), with the rod inside in FCal2 and FCal3
  auto *gapS  = new G4Tubs( m.name + "::Gap", m.gapRMin, m.gapRMax, m.halfZ, 0*deg, 360*deg );
  auto *gapLV = new G4LogicalVolume( gapS, lar, m.name + "::Gap" );
  if (rod){
    auto *rodS  = new G4Tubs( m.name + "::Rod", 0, m.rodR, m.halfZ, 0*deg, 360*deg );
    auto *rodLV = new G4LogicalVolume( rodS, rod, m.name + "::Rod" );
    new G4PVPlacement( 0, G4ThreeVector(), rodLV, m.name + "::Rod", gapLV, false, 0, false );
  }
  for (size_t k = 0; k < m.x.size(); ++k){
    new G4PVPlacement( 0, G4ThreeVector(m.x[k], m.y[k], 0), gapLV, m.name + "::Gap", absLV, false, (G4int)k, false );
  }
}

// The ATLAS Run 4 geometry of the simulation (--atlas-run4; F41 conserto 27), read from the GeoModel dump of ATLAS-P2-RUN4-01-01-00 made in
// the simulation mode (geometry/scripts/atlas_run4_dumpgeo.sh):
// - the beam pipe (BeamPipeCentral, BeamPipeFwd on both sides), the ITk (ITkPixel, ITkStrip) and the HGTD, whole and passive;
// - the end-cap cryostats of the LAr (the children of LAr::Endcap::Cryostat::MotherVolume, whose own material is the air of the world)
//   without the volumes that Lorenzetti builds (EMEC wheels, HEC modules, FCal modules, end-cap presampler argon); the ATLAS volumes that
//   held them (LAr::Endcap::Cryostat::EmecHecLAr, LAr::EMEC::Mother, LAr::HEC::LiquidArgon, LAr::FCAL::LiquidArgonC, the cold front wall
//   of the presampler) are cloned per side and receive the Lorenzetti volumes (MotherFor, PlaceGlobal);
// - with AtlasG4, the regions of the ATLAS simulation on these volumes (Athena release 23.0.14, G4PhysicsRegionConfig.py, as
//   getATLAS_RegionCreatorList activates them for Run 4): ITkPixel, ITkStrip and HGTD on their sensors (0.05 mm), EMEC on
//   LAr::EMEC::Mother (0.1 mm), HEC on LAr::HEC::LiquidArgon (1 mm), FCAL on LAr::FCAL::LiquidArgonC (0.03 mm) and DeadMaterial (1 mm,
//   with the dead material shower) on the cylinders and cones of the end-cap cryostats and the sections F191-F199 of the forward beam
//   pipe. The volume names are those of the ATLAS configuration, including the two pixel sensor names that do not exist in this
//   geometry (InnerQuadMod_Sensor, OuterQuadMod_Sensor; notes of the group, achados_athena_para_reportar.md, item 8).
void DetectorConstruction_v2::BuildAtlasRun4( G4LogicalVolume *worldLV )
{
  if (!AtlasGeoModelImport::available()){
    MSG_FATAL( "AtlasRun4 needs Lorenzetti built with the GeoModel libraries (GEOMODEL_DIR). Abort!" );
  }
  if (m_atlasRun4Geometry.empty()){
    MSG_FATAL( "AtlasRun4 needs the GeoModel dump of the ATLAS geometry of the simulation (AtlasRun4Geometry). Abort!" );
  }
  MSG_INFO( "AtlasRun4: importing the ATLAS geometry of the simulation from " << m_atlasRun4Geometry );
  m_atlasImport.reset( new AtlasGeoModelImport( m_atlasRun4Geometry ) );
  // the envelopes of the Geant4 geometry of ATLAS: ITK, a cylinder of air with the ITk and the HGTD (G4GeometryToolConfig.py, ITKEnvelopeCfg:
  // r = 28.8-1148 mm, |z| < 3545 mm for Run 4), and BeamPipe, the union of the top volumes of the beam pipe (Geo2G4Builder)
  auto *itkS = new G4Tubs( "ITK", 28.8*mm, 1148.*mm, 3545.*mm, 0*deg, 360*deg );
  m_itkEnvelopeLV = new G4LogicalVolume( itkS, G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR"), "ITK" );
  new G4PVPlacement( 0, G4ThreeVector(), m_itkEnvelopeLV, "ITK", worldLV, false, 0, m_checkOverlaps );
  m_atlasImport->placeWorldChildren( m_itkEnvelopeLV, {"ITkPixel", "ITkStrip", "HGTD"}, m_checkOverlaps );
  m_beamPipeEnvelopeLV = m_atlasImport->placeWorldChildrenInEnvelope( worldLV, "BeamPipe", {"BeamPipeCentral", "BeamPipeFwd"},
                                                                      m_checkOverlaps );
  // the forward beam pipe of the PhaseII campaign (enableBeamPipeKill: Sim.BeamPipeSimMode = FastSim): the region BeampipeFwdCut on the
  // sections F198-F200 (cuts of 10 mm), where the SimpleFastKiller kills every particle (ConstructSDandField)
  {
    auto lvs = m_atlasImport->logicalVolumes( { "BeamPipe::SectionF198", "BeamPipe::SectionF199", "BeamPipe::SectionF200",
                                                "BeamPipeFwd::SectionF198", "BeamPipeFwd::SectionF199", "BeamPipeFwd::SectionF200" } );
    if (lvs.empty()){ MSG_FATAL( "AtlasRun4: no section F198-F200 of the forward beam pipe. Abort!" ); }
    G4Region *r = GetRegion( "BeampipeFwdCut" );
    // as the RegionCreator of Athena: SetRegion before AddRootLogicalVolume (see the region lambda below)
    for (auto *lv : lvs){ lv->SetRegion( r ); r->AddRootLogicalVolume( lv ); }
    auto *cuts = new G4ProductionCuts();
    cuts->SetProductionCut( 10*mm, "gamma" ); cuts->SetProductionCut( 10*mm, "e-" ); cuts->SetProductionCut( 10*mm, "e+" );
    cuts->SetProductionCut( 1*mm, "proton" );
    r->SetProductionCuts( cuts );
    MSG_INFO( "AtlasRun4: region BeampipeFwdCut (10 mm, SimpleFastKiller) on " << lvs.size() << " logical volumes" );
  }
  const std::vector<std::string> dropped = { "LAr::EMEC::Pos::InnerWheel", "LAr::EMEC::Pos::OuterWheel", "LAr::EMEC::Neg::InnerWheel",
                                             "LAr::EMEC::Neg::OuterWheel", "LAr::HEC::Module", "LAr::FCAL::Module",
                                             "LAr::Endcap::Presampler::LiquidArgon" };
  for (auto &c : m_atlasImport->placeUnwrapped( worldLV, "LAr::Endcap::Cryostat::MotherVolume", dropped, m_checkOverlaps )){
    m_atlasContainers.push_back( AtlasContainer{ c.lv, c.x, c.depth, c.name } );
    m_containerX[c.lv] = c.x;
  }
  // the ATLAS material outside the calorimeters (--atlas-forward-shielding; F41 conserto 32): in the material maps of the group the
  // Lorenzetti world had, behind the FCal (|z| >= 6.3 m), 23% of the mass of the ATLAS simulation (no end-cap toroid, no forward shielding
  // with its borated polyethylene) and, around the tile calorimeter, no girder (r = 3830-4240 mm), fingers or saddles
  if (m_atlasForwardShielding){
    // the children of MuonSys placed in the world without its envelope (its own material is the air of the world; the envelope would
    // contain Lorenzetti volumes of the LAr dead material, LAr::DM::Ped)
    m_atlasImport->placeUnwrapped( worldLV, "MuonSys", {}, m_checkOverlaps );
    // not imported: the barrel end plates (EndPlate1/2, inside the TILE::TileCal1-3 envelopes of Lorenzetti) and the barrel saddles
    // (SaddlePos/Neg, where DM::ITC::Services2 of conserto 11 stands)
    const int nb = m_atlasImport->placeDescendants( worldLV, {"TileCentralBarrel"}, {"FingerPos", "FingerNeg", "GirderMother"},
                                                    m_checkOverlaps );
    const int ne = m_atlasImport->placeDescendants( worldLV, {"TileEndcapPos", "TileEndcapNeg"},
                     {"EFinger", "ESaddlePos", "GirderMother"}, m_checkOverlaps );
    MSG_INFO( "AtlasForwardShielding: MuonSys imported; tile calorimeter parts placed: " << nb << " (barrel), " << ne << " (end-caps)" );
  }
  // the dead material of ATLAS in the gap between the barrel and the extended barrel (--atlas-barrel-gap-services; F41 conserto 34): the
  // walls of the barrel cryostat stay those of conserto 14b; the signal feedthroughs without their envelope of air (it crosses the
  // cylinders DM::BarrelCryostat::Cylinder2 and Cylinder7 of conserto 14b, which have no holes for them); not imported: the parts of the
  // feedthroughs that cross those cylinders and the sector and bridge envelopes of the LAr services (LAr::DM::SectorEnvelopes*,
  // LAr::DM::BridgeEnvelopes: in ATLAS they run
  // between the modules of the gap and crack scintillators, which conserto 21 builds as full cylinders)
  if (m_atlasBarrelGapServices){
    std::set<std::string> gap = {"LAr::DM::*", ">LAr::Barrel::SignalFT::Envelope", "LAr::Barrel::SignalFT::*",
                                 "!LAr::Barrel::SignalFT::Pigtail", "!LAr::Barrel::SignalFT::Bellow", "!LAr::Barrel::SignalFT::ColdBox3",
                                 "!LAr::Barrel::SignalFT::VacuumCables", "LAr::Barrel::FTCables"};
    // the sector and bridge envelopes only with the tile gap and crack at the positions of the ATLAS simulation (conserto 35)
    if (!m_tileAtlasRun4){ gap.insert( "!LAr::DM::SectorEnvelopes*" ); gap.insert( "!LAr::DM::BridgeEnvelopes" ); }
    const int nl = m_atlasImport->placeDescendants( worldLV, {"LAr::Barrel::Cryostat::MotherVolume"}, gap, m_checkOverlaps );
    const int ns = m_atlasImport->placeDescendants( worldLV, {"TileCentralBarrel"}, {"SaddlePos", "SaddleNeg"}, m_checkOverlaps );
    MSG_INFO( "AtlasBarrelGapServices: " << nl << " placements of the barrel LAr dead material and feedthroughs, " << ns << " tile saddles" );
  }
  std::stable_sort( m_atlasContainers.begin(), m_atlasContainers.end(),
                    []( const AtlasContainer &a, const AtlasContainer &b ){ return a.depth > b.depth; } );
  for (auto &c : m_atlasContainers) MSG_INFO( "AtlasRun4: container " << c.name << " (depth " << c.depth << ", z "
                                              << c.x.getTranslation().z()/mm << " mm)" );

  if (!m_atlasG4) return;
  auto region = [&]( const std::string &name, const std::set<std::string> &volumes, double cut ){
    auto lvs = m_atlasImport->logicalVolumes( volumes );
    if (lvs.empty()){ MSG_INFO( "AtlasRun4: region " << name << " has no volume in this geometry" ); return; }
    G4Region *r = GetRegion( name );
    // as the RegionCreator of Athena (G4AtlasTools/src/RegionCreator.cxx): SetRegion before AddRootLogicalVolume, so that a volume listed by
    // two regions (the sections F198 and F199 of the forward beam pipe, in BeampipeFwdCut and DeadMaterial) is root of both and ends in the
    // last one created (DeadMaterial), as in the ATLAS simulation (notes of the group, achados_athena_para_reportar.md, item 10)
    for (auto *lv : lvs){ lv->SetRegion( r ); r->AddRootLogicalVolume( lv ); }
    auto *cuts = new G4ProductionCuts();
    cuts->SetProductionCut( cut*mm, "gamma" ); cuts->SetProductionCut( cut*mm, "e-" ); cuts->SetProductionCut( cut*mm, "e+" );
    cuts->SetProductionCut( 1.0*mm, "proton" );
    r->SetProductionCuts( cuts );
    MSG_INFO( "AtlasRun4: region " << name << " (" << cut << " mm) on " << lvs.size() << " logical volumes" );
  };
  region( "ITkPixel", { "ITkPixel::InnerBarrelSingleMod_Sensor", "ITkPixel::InnerRingSingleMod_Sensor", "ITkPixel::InnerQuadMod_Sensor",
                        "ITkPixel::OuterQuadMod_Sensor", "ITkPixel::InclinedQuadMod_Sensor" }, 0.05 );
  region( "ITkStrip", { "ITkStrip::BRLSensorSS", "ITkStrip::BRLSensorMS", "ITkStrip::ECSensor0", "ITkStrip::ECSensor1",
                        "ITkStrip::ECSensor2", "ITkStrip::ECSensor3", "ITkStrip::ECSensor4", "ITkStrip::ECSensor5",
                        "ITkStrip::ECSensorBack0", "ITkStrip::ECSensorBack1", "ITkStrip::ECSensorBack2", "ITkStrip::ECSensorBack3",
                        "ITkStrip::ECSensorBack4", "ITkStrip::ECSensorBack5" }, 0.05 );
  region( "HGTD", { "HGTD::HGTDSiSensorPosL0", "HGTD::HGTDSiSensorPosL1", "HGTD::HGTDSiSensorPosL2", "HGTD::HGTDSiSensorPosL3",
                    "HGTD::HGTDSiSensorNegL0", "HGTD::HGTDSiSensorNegL1", "HGTD::HGTDSiSensorNegL2", "HGTD::HGTDSiSensorNegL3",
                    "HGTD::HGTDSiSensor" }, 0.05 );
  const std::string cryo = "LAr::Endcap::Cryostat::MotherVolume::";
  region( "EMEC", { cryo + "LAr::EMEC::Mother" }, 0.1 );
  region( "HEC" , { cryo + "LAr::HEC::LiquidArgon" }, 1.0 );
  region( "FCAL", { cryo + "LAr::FCAL::LiquidArgonC" }, 0.03 );
  std::set<std::string> dm = { cryo + "LAr::Endcap::Cryostat::Cylinder", cryo + "LAr::Endcap::Cryostat::Cylinder::Mixed",
                               cryo + "LAr::Endcap::Cryostat::Cone::Mixed", cryo + "LAr::Endcap::Cryostat::Cone" };
  for (int k = 191; k < 200; ++k) dm.insert( "BeamPipeFwd::SectionF" + std::to_string(k) );
  region( "DeadMaterial", dm, 1.0 );
  if (G4RegionStore::GetInstance()->GetRegion( "DeadMaterial", false )) m_deadMaterialVolumes.push_back( "DeadMaterial" );
}


// The deepest imported ATLAS volume (--atlas-run4) whose solid contains all the points (global, mm), or the world.
G4LogicalVolume* DetectorConstruction_v2::MotherFor( const std::vector<G4ThreeVector> &points, G4LogicalVolume *worldLV ) const
{
  for (const auto &c : m_atlasContainers){
    const G4Transform3D inv = c.x.inverse();
    bool all = true;
    for (const auto &p : points){
      const G4ThreeVector local = inv * G4Point3D( p );
      if (c.lv->GetSolid()->Inside( local ) == kOutside){ all = false; break; }
    }
    if (all) return c.lv;
  }
  return worldLV;
}


// Places a Lorenzetti volume given at the global position pos (no rotation) in its mother: the world, or an imported ATLAS volume
// (--atlas-run4), with the transformation to the frame of that volume (including the rotation of the C side).
void DetectorConstruction_v2::PlaceGlobal( G4LogicalVolume *lv, const G4ThreeVector &pos, const std::string &name,
                                           G4LogicalVolume *motherLV )
{
  auto it = m_containerX.find( motherLV );
  if (it == m_containerX.end()){
    new G4PVPlacement( 0, pos, lv, name, motherLV, false, 0, m_checkOverlaps );
    return;
  }
  new G4PVPlacement( it->second.inverse() * G4Translate3D( pos ), lv, name, motherLV, false, 0, m_checkOverlaps );
}



// The field of the ATLAS map only inside the cylinder that holds the calorimeters (--atlas-run4; F41 conserto 27, decision of Luciano on
// 14/10/2026): r <= 3860 mm (DM::TileGap, the outermost volume of the calorimeters) and |z| <= 6780.5 mm (the back of the mother of the
// end-cap cryostat of ATLAS); zero outside. Beyond the calorimeters ATLAS has the end-cap toroid, the forward shielding and the muon
// system, which absorb what leaves the calorimeters; Lorenzetti has empty air there, where the field of the map would only make
// particles curl (the timeouts of the first test: electrons below 10 keV at |z| = 8-18 m) and come back. Not modelled either way: the
// albedo of that ATLAS material.
class AtlasCaloBoundedField : public G4MagneticField
{
  public:
    AtlasCaloBoundedField( G4MagneticField *field, double rMax, double zMax ) : m_field( field ), m_r2( rMax*rMax ), m_zMax( zMax ) {}
    void GetFieldValue( const double *point, double *b ) const override
    {
      if( point[0]*point[0] + point[1]*point[1] > m_r2 || std::fabs( point[2] ) > m_zMax ){ b[0] = b[1] = b[2] = 0.; return; }
      m_field->GetFieldValue( point, b );
    }
  private:
    G4MagneticField *m_field;
    double m_r2, m_zMax;
};


// The magnetic field of the ATLAS simulation (--atlas-run4; F41 conserto 27), as the PhaseII campaign of Athena 23.0.14 sets it up
// (G4FieldConfig.py, ATLAS_FieldMgrListCfg in G4GeometryToolConfig.py, StandardFieldSvc): the field map of the production
// (MagFieldElements, ported to geometry/MagFieldElements) with the currents of the map (7730 and 20400 A); the global field manager
// TightMuonSteppingFieldManager (Sim.TightMuonStepping = True), with the stepper AtlasRK4 (Sim.G4Stepper; G4IntegrationDriver, minimum step
// 0.01 mm) and the Geant4 defaults for the other particles; and the field managers of the envelopes BeamPipe and ITK (BeamPipeFieldManager,
// ITkFieldManager: DeltaIntersection 1e-5, DeltaOneStep 1e-4, MaximumEpsilonStep 1e-3, MinimumEpsilonStep 1e-5 mm). The map is read
// once and shared; the field cache is per thread (it is not thread safe).
void DetectorConstruction_v2::ConstructAtlasField()
{
  static std::shared_ptr<MagField::AtlasFieldMap> map;
  static std::mutex mapMutex;
  {
    std::lock_guard<std::mutex> lock( mapMutex );
    if (!map){
      if (m_atlasFieldMap.empty()){ MSG_FATAL( "AtlasRun4 needs the field map of ATLAS (AtlasFieldMap). Abort!" ); }
      map = AtlasMagneticField::loadMap( m_atlasFieldMap, 7730., 20400. );
      if (!map){ MSG_FATAL( "AtlasRun4: cannot read the field map " << m_atlasFieldMap << ". Abort!" ); }
      MSG_INFO( "AtlasRun4: field map " << m_atlasFieldMap );
    }
  }
  auto *atlasField = new AtlasMagneticField( map.get(), 1., 1. );
  G4AutoDelete::Register( atlasField );
  // the map only in the cylinder of the calorimeters (conserto 27), or in the whole world as in ATLAS (--atlas-full-field, conserto 33)
  G4MagneticField *field = atlasField;
  if (!m_atlasFullField){
    field = new AtlasCaloBoundedField( atlasField, 3860.*mm, 6780.5*mm );
    G4AutoDelete::Register( field );
  }
  const G4double minStep = 1e-2*mm;
  auto driverFor = [&]( G4MagneticField *f ) -> G4VIntegrationDriver* {
    auto *eq = new G4Mag_UsualEqRhs( f );
    auto *stepper = new G4AtlasRK4( eq );
    return new G4IntegrationDriver<G4AtlasRK4>( minStep, stepper, stepper->GetNumberOfVariables() );
  };

  // global: TightMuonSteppingFieldManager (GlobalFieldManagerTool with UseTightMuonStepping)
  auto *transport = G4TransportationManager::GetTransportationManager();
  auto *global = new TightMuonSteppingFieldManager();
  transport->SetFieldManager( global );
  global->SetDetectorField( field );
  global->CreateChordFinder( field );
  global->GetChordFinder()->SetIntegrationDriver( driverFor( field ) );

  // the envelopes (DetectorFieldManagerTool): the parameters are set between the two CreateChordFinder of the ATLAS tool
  for (auto *lv : { m_beamPipeEnvelopeLV, m_itkEnvelopeLV }){
    if (!lv) continue;
    auto *fm = new G4FieldManager();
    fm->SetDetectorField( field );
    fm->CreateChordFinder( field );
    fm->SetDeltaOneStep( 0.0001*mm );
    fm->SetDeltaIntersection( 0.00001*mm );
    fm->SetMinimumEpsilonStep( 0.00001 );
    fm->SetMaximumEpsilonStep( 0.001 );
    fm->CreateChordFinder( field );
    fm->GetChordFinder()->SetIntegrationDriver( driverFor( field ) );
    lv->SetFieldManager( fm, true );
    MSG_INFO( "AtlasRun4: field manager of " << lv->GetName() );
  }

  // MuonsOnlyInCaloFieldManager of ATLAS (G4FieldConfig.py, MuonsOnlyInCaloFieldManagerToolCfg, on the physical volume LArBarrel; here on
  // the volumes of the barrel EM calorimeter LAr::EMB1, LAr::EMB2, LAr::EMB3 and their daughters): the SwitchingFieldManager, with the
  // parameters of the ATLAS tool in the same order (its MaximumEpsilonStep of 9e-7 is below its MinimumEpsilonStep of 1e-6: Geant4 11.2
  // sets both to 9e-7, warning Geometry003; what the Geant4 10.6 of ATLAS does with it is not checked)
  if (m_atlasFullField){
    int n = 0;
    for (auto *lv : *G4LogicalVolumeStore::GetInstance()){
      const std::string name = lv->GetName();
      if (name != "LAr::EMB1" && name != "LAr::EMB2" && name != "LAr::EMB3") continue;
      auto *fm = new SwitchingFieldManager( field );
      fm->CreateChordFinder( field );
      fm->SetDeltaOneStep( 0.000001*mm );
      fm->SetDeltaIntersection( 0.00000002*mm );
      fm->SetMinimumEpsilonStep( 0.000001 );
      fm->SetMaximumEpsilonStep( 0.0000009 );
      fm->CreateChordFinder( field );
      fm->GetChordFinder()->SetIntegrationDriver( driverFor( field ) );
      lv->SetFieldManager( fm, true );
      ++n;
    }
    if (!n){ MSG_FATAL( "AtlasFullField: no volume LAr::EMB1-3 for the field of the muons only. Abort!" ); }
    MSG_INFO( "AtlasFullField: field map in the whole world; SwitchingFieldManager (muons only) on " << n << " volumes of the barrel EM" );
  }
}
