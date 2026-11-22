/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
#ifndef AtlasDeadMaterialShower_h
#define AtlasDeadMaterialShower_h

#include "G4VFastSimulationModel.hh"
#include <string>

/**
 * @class AtlasDeadMaterialShower
 * @brief Port of DeadMaterialShower of the Athena release 23.0.14 (F41 conserto 24; simu_trf.py --atlas-g4), switched on in the ATLAS
 *        production we compare with by FrozenShowersFCalOnly in the region DeadMaterial (the endcap cryostat cylinders and cones, the
 *        forward shielding and the beam pipe sections F191 to F199): with |z| >= ZCutoff (5698 mm) every e-, e+, pi+, pi-, gamma and
 *        neutron of kinetic energy up to HighEnergy (1000 GeV) is killed without depositing; below ZCutoff only e+- under LowEnergy (0,
 *        so none). In the Lorenzetti it acts in the volumes of the ATLAS endcap cryostat (DM::EndcapCryostat).
 */
class AtlasDeadMaterialShower : public G4VFastSimulationModel
{
  public:
    AtlasDeadMaterialShower( const std::string &name, G4Region *region, double highEnergy, double lowEnergy, double zCutoff );
    G4bool IsApplicable( const G4ParticleDefinition &particle ) override;
    G4bool ModelTrigger( const G4FastTrack &fastTrack ) override;
    void DoIt( const G4FastTrack &fastTrack, G4FastStep &fastStep ) override;
  private:
    double m_highEnergy, m_lowEnergy, m_zCutoff;
};

#endif
