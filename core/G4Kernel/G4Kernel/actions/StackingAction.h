#ifndef StackingAction_h
#define StackingAction_h

#include "G4UserStackingAction.hh"
#include <unordered_map>

class G4LogicalVolume;

/**
 * @class StackingAction
 * @brief The stacking action of the ATLAS simulation (F41 conserto 24; simu_trf.py --atlas-g4), as AthenaStackingAction of the Athena
 *        release 23.0.14 with the settings of the production we compare with (G4UserActionsConfig.py, G4Optimizations.py):
 *
 * 1. kill every neutrino (KillAllNeutrinos);
 * 2. kill photons of total energy below 50 eV (always, in the code);
 * 3. neutron Russian roulette: a neutron of weight below 10 and kinetic energy below 2 MeV survives with probability 1/10, with
 *    weight 10 (ApplyNRR, NRRThreshold 2 MeV, NRRWeight 10);
 * 4. photon Russian roulette: the same for a photon born in a volume of the LAr tree (AtlasG4Settings::larTreeVolumes) with kinetic
 *    energy below 0.5 MeV (ApplyPRR, PRRThreshold 0.5 MeV, PRRWeight 10); primaries (no origin touchable) are not touched.
 * The secondaries inherit the weight (Geant4), and the hit makers multiply the deposits by it.
 */
class StackingAction : public G4UserStackingAction
{
  public:
    StackingAction() = default;
    G4ClassificationOfNewTrack ClassifyNewTrack( const G4Track *track ) override;
  private:
    bool isLArTree( const G4LogicalVolume *lv );
    std::unordered_map<const G4LogicalVolume*, bool> m_larTree;   // cache per thread (one action per worker)
};

#endif
