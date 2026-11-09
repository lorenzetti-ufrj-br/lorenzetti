#ifndef DetectorConstruction_v2_h
#define DetectorConstruction_v2_h

#include "GaugiKernel/MsgStream.h"
#include "GaugiKernel/Property.h"
#include "G4VUserDetectorConstruction.hh"
#include "G4Material.hh"
#include "G4ThreeVector.hh"
#include "G4Region.hh"
#include "globals.hh"
#include "G4Cache.hh"
#include "G4Transform3D.hh"
#include <memory>
#include <map>
#include <set>
#include <vector>


//enum Plates{
//    Horizontal       = 0,
//    Vertical         = 1,
//};

class G4VPhysicalVolume;

class G4GlobalMagFieldMessenger;
class AtlasGeoModelImport;

class DetectorConstruction_v2 : public G4VUserDetectorConstruction, public MsgService, public Gaugi::PropertyService
{
  public:


    struct Volume{
      std::string name;
      int plates;
      std::string absorberMaterial;
      std::string gapMaterial;
      int nofLayers;
      double absoThickness;
      double gapThickness;
      double layerClearance; // empty space (envelope material) per layer, vertical plates only
      double rMin;
      double rMax;
      double zSize;
      double x;
      double y;
      double z;

      double electronCut;
      double positronCut;
      double gammaCut;
      double photonCut;
    };

    // A cloned ATLAS volume that holds Lorenzetti volumes (--atlas-run4; F41 conserto 27)
    struct AtlasContainer { G4LogicalVolume *lv; G4Transform3D x; int depth; std::string name; };

    DetectorConstruction_v2(std::string);
    virtual ~DetectorConstruction_v2();
    virtual G4VPhysicalVolume* Construct();
    virtual void ConstructSDandField();

    // get methods
    const G4VPhysicalVolume* GetAbsorberPV() const;
    const G4VPhysicalVolume* GetGapPV() const;

    void AddVolume(std::string region,
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
                   );

    // Horizontal plates whose absorber changes for |z| > zSplit, with the same layer thickness (the gap takes the rest
    // of the layer): used for the lead of the ATLAS barrel EM calorimeter (1.53 mm below |eta| = 0.8, 1.13 mm above;
    // option AtlasEmb in geometry/python). Must be called after AddVolume for the same region.
    void SetAbsorberSplit(std::string region, double zSplit, std::string absorberMaterial2, double absoThickness2);
    struct AbsorberSplit{ double z; std::string material; double thickness; };

    // A material from elements, defined by the geometry in Python (density in g/cm3, mass fractions by element symbol):
    // the phi-averaged mixtures of the ATLAS pieces in front of the barrel accordion (F41 conserto 17c).
    void AddMixture(std::string name, double density, std::vector<std::string> symbols, std::vector<double> fractions);
    // Plates::Polycone (2): one G4Polycone of the absorber material with these planes. Call after AddVolume.
    void SetPolycone(std::string region, std::vector<double> z, std::vector<double> rmin, std::vector<double> rmax);
    // Place this volume inside the solenoid field volume (UseSolenoidField) instead of the world. Call after AddVolume.
    void SetInSolenoidField(std::string region);
    struct Mixture{ std::string name; double density; std::vector<std::string> symbols; std::vector<double> fractions; };
    struct PolyconePlanes{ std::vector<double> z, rmin, rmax; };

    // One module of the ATLAS FCal with its electrodes (F41 conserto 22; geometry/python/v1/FCAL.py), as in the ATLAS geometry
    // (FCALConstruction.cxx): a tube of absorber (rMin-rMax, centred at z, half length halfZ) holding the cable troughs
    // (troughRMin-troughRMax, sector troughSPhi..troughSPhi+troughDPhi rotated about z by each of troughAngles) and then one
    // gap of liquid argon per electrode at (x[k], y[k]), copy number k: a ring gapRMin-gapRMax, or, with rodR > 0, a cylinder
    // holding a rod of rodMaterial. Lengths in mm, angles in rad. The gap is the sensitive volume <name>::Gap.
    void AddFCalModule(std::string name, std::string absorberMaterial, std::string rodMaterial, std::string troughMaterial,
                       double rMin, double rMax, double z, double halfZ, double gapRMin, double gapRMax, double rodR,
                       double troughRMin, double troughRMax, double troughSPhi, double troughDPhi,
                       std::vector<double> troughAngles, std::vector<double> x, std::vector<double> y,
                       double electronCut, double positronCut, double gammaCut, double photonCut);
    struct FCalModule{
      std::string name, absorberMaterial, rodMaterial, troughMaterial;
      double rMin, rMax, z, halfZ, gapRMin, gapRMax, rodR, troughRMin, troughRMax, troughSPhi, troughDPhi;
      std::vector<double> troughAngles, x, y;
      double electronCut, positronCut, gammaCut, photonCut;
    };

  private:

    std::vector<FCalModule> m_fcalModules;
    // Frozen showers of the ATLAS FCal (F41 conserto 23; FCalFrozenShowerModel): on/off and the directory of the libraries
    bool m_fcalFrozenShowers;
    // Geant4 settings of the ATLAS production (F41 conserto 24): liquid argon of 1.396 g/cm3, the prefixes of the volumes of the LAr
    // tree (photon Russian roulette) and the volumes of the dead material shower (AtlasDeadMaterialShower)
    bool m_atlasG4;
    // The ATLAS Run 4 geometry of the simulation (F41 conserto 27): the GeoModel dump of the ATLAS geometry, its import, and the cloned ATLAS
    // volumes that hold Lorenzetti volumes (deepest first) with their global transformation
    bool m_atlasRun4;
    std::string m_atlasRun4Geometry;
    // the ATLAS material outside the calorimeters (--atlas-forward-shielding; F41 conserto 32): the MuonSys and the girders, fingers and
    // extended-barrel saddles of the tile calorimeter, from the same dump
    bool m_atlasForwardShielding;
    // the field of the ATLAS simulation as in the production (--atlas-full-field; F41 conserto 33): the map in the whole world and only the
    // muons in the field inside the barrel EM calorimeter (MuonFieldOnlyInCalo)
    bool m_atlasFullField;
    // the dead material of ATLAS in the gap between the barrel and the extended barrel (--atlas-barrel-gap-services; F41 conserto 34)
    bool m_atlasBarrelGapServices;
    // the extended barrel, ITC, gap and crack of the tile calorimeter at the positions of the ATLAS simulation of Run 4 (F41 conserto 35)
    bool m_tileAtlasRun4;
    std::unique_ptr<AtlasGeoModelImport> m_atlasImport;
    std::vector<AtlasContainer> m_atlasContainers;
    std::map<G4LogicalVolume*, G4Transform3D> m_containerX;
    void BuildAtlasRun4( G4LogicalVolume *worldLV );
    // the field map of the ATLAS simulation (--atlas-run4) and the envelopes that get their own field manager, as in ATLAS
    std::string m_atlasFieldMap;
    G4LogicalVolume *m_itkEnvelopeLV = nullptr;
    G4LogicalVolume *m_beamPipeEnvelopeLV = nullptr;
    void ConstructAtlasField();
    G4LogicalVolume* MotherFor( const std::vector<G4ThreeVector> &points, G4LogicalVolume *worldLV ) const;
    void PlaceGlobal( G4LogicalVolume *lv, const G4ThreeVector &pos, const std::string &name, G4LogicalVolume *motherLV );
    std::vector<std::string> m_larTreeVolumes;
    std::vector<std::string> m_deadMaterialVolumes;
    std::string m_fcalShowerLibDir;
    void CreateFCalModule( G4LogicalVolume *motherLV, const FCalModule &m, G4Region *region );

    std::vector<Volume> m_volumes;
    std::map<std::string, AbsorberSplit> m_absorberSplit;
    std::vector<Mixture> m_mixtures;
    std::map<std::string, PolyconePlanes> m_polycones;
    std::set<std::string> m_inSolenoidField;
    double m_solenoidFieldRadius;

    void CreatePolycone( G4LogicalVolume *motherLV, std::string name, G4Material *material, const PolyconePlanes &planes,
                         G4Region *region );

    // methods
    void DefineMaterials();
    
    G4VPhysicalVolume* DefineVolumes();


    void CreateHorizontalPlates(  G4LogicalVolume *worldLV, 
                                  std::string name,  
                                  G4Material *defaltMaterial,
                                  G4Material *absorberMaterial,
                                  G4Material *gapMaterial,
                                  int nofLayers,
                                  double absoThickness,
                                  double gapThickness,
                                  double calorRmin,
                                  double calorZ,
                                  const G4ThreeVector &center_pos,
                                  G4Region* region);

    void CreateVerticalPlates(  G4LogicalVolume *worldLV, 
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
                                G4Region *region);

    G4Region* GetRegion( std::string name );


    bool m_checkOverlaps; // option to activate checking of volumes overlaps
    bool m_useMagneticField;
    bool m_useSolenoidField;
    bool m_cutOnPhi;
    int m_outputLevel;

    // Field volume of the solenoid (only built with UseSolenoidField)
    G4LogicalVolume* m_solenoidLV = nullptr;

    static G4ThreadLocal G4GlobalMagFieldMessenger*  m_magFieldMessenger;
};




#endif

