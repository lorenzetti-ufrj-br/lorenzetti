/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
#ifndef FCalFrozenShowerModel_h
#define FCalFrozenShowerModel_h

#include "G4VFastSimulationModel.hh"
#include "FCalShowerLib.h"
#include <map>
#include <memory>
#include <string>

/**
 * @class FCalFrozenShowerModel
 * @brief The frozen showers of the ATLAS FCal (F41 conserto 23), as the ATLAS simulation applies them.
 *
 * Port of LArFastShower and LArG4ShowerLibSvc of the Athena release 23.0.14 (copies in the F41 notes of the group,
 * c23_chuveiros_congelados/fontes_athena/r23.0.14/), configured as LArG4FastSimulationConfig.py of that release (FCALFastShower for
 * the region of FCal1, FCAL2FastShower for FCal2 and FCal3, both with the libraries of FCAL2 in FCal2 and FCal3). Kept as in ATLAS,
 * although they look unintended (notes of the group, achados_athena_para_reportar.md): the positron is never frozen (the library is
 * looked up with the signed PDG code); FCal1 never checks containment (ContainLow false with AbsLowEta 4.0 accepts every eta); the
 * shower is deposited with weight 1.
 *
 * - IsApplicable: e-, gamma or neutron with a library of this region (and so not e+).
 * - ModelTrigger: kinetic energy strictly inside (EMin, EMax) of the particle; then ForcedAccept; else the containment check of six
 *   points against the solid of the envelope with Z and R of the library.
 * - DoIt: kill the particle, take a shower with randomShift = (int)(Gauss(0, 2.5) + 0.5), rotate its spots to the direction of the
 *   particle (rotateUz), move them to its position, shift their time by the global time of the particle minus |r|/c, and hand each
 *   spot to the hit makers as a G4Step without touchable (the spot energy in the total energy deposit, the spot time in the global
 *   time of the pre-step point), through the user stepping action; the FCal makers take the cell from the position.
 */
class FCalFrozenShowerModel : public G4VFastSimulationModel
{
  public:

    struct Config {
      std::string library;                      // "FCAL1" or "FCAL2"
      double eMin, eMax, gMin, gMax, nMin, nMax; // kinetic energy limits (MeV) of e-, gamma and neutron
      bool containLow, containHigh, containCrack;
      double absLowEta, absHighEta, absCrackEta1, absCrackEta2;
    };

    FCalFrozenShowerModel( const std::string &name, G4Region *region, const Config &config,
                           const std::map<int, std::shared_ptr<const FCalShowerLib>> &libraries );

    G4bool IsApplicable( const G4ParticleDefinition &particle ) override;
    G4bool ModelTrigger( const G4FastTrack &fastTrack ) override;
    void DoIt( const G4FastTrack &fastTrack, G4FastStep &fastStep ) override;

    /*! The libraries of a directory: LArG4ShowerLib.FCAL<1,2>.<11,22,2112>.root, by PDG code and library name ("FCAL1", "FCAL2");
        read once and shared by the threads. */
    static std::map<std::string, std::map<int, std::shared_ptr<const FCalShowerLib>>> loadLibraries( const std::string &dir );

  private:

    const FCalShowerLib* library( int pdg ) const;
    bool energyLimits( const G4ParticleDefinition &particle, double &emin, double &emax ) const;
    bool forcedAccept( const G4FastTrack &fastTrack ) const;
    bool checkContainment( const G4FastTrack &fastTrack ) const;

    Config m_config;
    std::map<int, std::shared_ptr<const FCalShowerLib>> m_libraries;   // by signed PDG code
};

#endif
