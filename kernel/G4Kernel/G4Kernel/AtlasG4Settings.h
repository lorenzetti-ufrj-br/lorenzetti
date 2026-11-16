#ifndef AtlasG4Settings_h
#define AtlasG4Settings_h

#include <string>
#include <vector>

/**
 * @struct AtlasG4Settings
 * @brief The Geant4 settings of the ATLAS production we compare with (F41 conserto 24; simu_trf.py --atlas-g4), shared by the run
 *        manager, the geometry and the user actions. Filled before the run starts (RunManager, DetectorConstruction_v1) and only read
 *        during the event loop.
 *
 * - enabled: the ATLAS stacking action (StackingAction) and the looper killer (SteppingAction) are on;
 * - larTreeVolumes: prefixes of the names of the physical volumes that stand for volumes of the LAr tree of the ATLAS geometry (whose
 *   physical volume names begin with "LAr"), where the photon Russian roulette acts (AthenaStackingAction of the Athena release
 *   23.0.14, AthenaStackingAction.cxx:94-110).
 */
struct AtlasG4Settings
{
  bool enabled = false;
  std::vector<std::string> larTreeVolumes;

  static AtlasG4Settings& instance()
  {
    static AtlasG4Settings s;
    return s;
  }
};

#endif
