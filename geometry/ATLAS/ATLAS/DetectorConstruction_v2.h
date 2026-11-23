#ifndef ATLAS_DetectorConstruction_v2_h
#define ATLAS_DetectorConstruction_v2_h

#include "GaugiKernel/MsgStream.h"
#include "GaugiKernel/Property.h"
#include "G4VUserDetectorConstruction.hh"
#include "G4Material.hh"
#include "G4ThreeVector.hh"
#include "G4Region.hh"
#include "globals.hh"
#include <memory>
#include <string>
#include <vector>

class G4VPhysicalVolume;
class G4LogicalVolume;
class G4GlobalMagFieldMessenger;

namespace ATLAS {

/**
 * @class DetectorConstruction_v2
 * @brief Modern, declarative Geant4 detector construction for the ATLAS calorimeter.
 *
 * Loads detector geometry directly from a canonical JSON specification via LoadGeometryFile,
 * eliminating runtime PyROOT loops and constructing the geometry in native C++ (~1 ms).
 */
class DetectorConstruction_v2 : public G4VUserDetectorConstruction, public MsgService, public Gaugi::PropertyService
{
public:
    struct PolyconePlanes {
        std::vector<double> z;
        std::vector<double> rmin;
        std::vector<double> rmax;
    };

    struct Volume {
        std::string name;
        int plates; // 0 = Horizontal, 1 = Vertical, 2 = Polycone
        std::string absorberMaterial;
        std::string gapMaterial;
        int nofLayers;
        double absoThickness;
        double gapThickness;
        double rMin;
        double rMax;
        double zSize;
        double x;
        double y;
        double z;
        bool inSolenoidField;

        PolyconePlanes polyconePlanes;

        // Production cuts
        double electronCut;
        double positronCut;
        double gammaCut;
        double photonCut;
    };

    DetectorConstruction_v2(std::string name);
    virtual ~DetectorConstruction_v2();

    virtual G4VPhysicalVolume* Construct() override;
    virtual void ConstructSDandField() override;

    bool LoadGeometryFile(const std::string& filepath);

    const G4VPhysicalVolume* GetAbsorberPV() const { return m_absorberPV; }
    const G4VPhysicalVolume* GetGapPV() const { return m_gapPV; }

private:
    std::vector<Volume> m_volumes;

    void DefineMaterials();
    G4VPhysicalVolume* DefineVolumes();

    void CreateHorizontalPlates(G4LogicalVolume* worldLV,
                                const Volume& vol,
                                G4Material* defaultMaterial,
                                G4Material* absorberMaterial,
                                G4Material* gapMaterial,
                                G4Region* region);

    void CreateVerticalPlates(G4LogicalVolume* worldLV,
                              const Volume& vol,
                              G4Material* defaultMaterial,
                              G4Material* absorberMaterial,
                              G4Material* gapMaterial,
                              G4Region* region);

    void CreatePolycone(G4LogicalVolume* worldLV,
                        const Volume& vol,
                        G4Material* material,
                        G4Region* region);

    G4Region* GetRegion(const std::string& name);

    bool m_checkOverlaps;
    bool m_useMagneticField;
    bool m_useSolenoidField;
    bool m_cutOnPhi;
    int m_outputLevel;
    std::string m_geometryFile;

    G4VPhysicalVolume* m_absorberPV;
    G4VPhysicalVolume* m_gapPV;
    G4LogicalVolume* m_solenoidLV;

    static G4ThreadLocal G4GlobalMagFieldMessenger* m_magFieldMessenger;
};

} // namespace ATLAS

#endif
