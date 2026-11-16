/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
#ifndef FCalShowerLib_h
#define FCalShowerLib_h

#include "G4ThreeVector.hh"
#include <map>
#include <string>
#include <vector>

class G4Track;

/**
 * @class FCalShowerLib
 * @brief A frozen shower library of the ATLAS FCal (F41 conserto 23), read and used as the ATLAS simulation does it.
 *
 * Port of ShowerLib::FCALDistEtaEnergyShowerLib of the Athena release 23.0.14 (LArCalorimeter/LArG4/LArG4ShowerLib; copy in the F41
 * notes of the group, c23_chuveiros_congelados/fontes_athena/r23.0.14/), the release of the ATLAS production we compare with. The file
 * (LArG4ShowerLib.FCAL<1,2>.<11,22,2112>.root, from the ATLAS GroupData in CVMFS) has a TParameter<int> "version" (5, or 3 for the
 * old format with fixed rod grid), a tree "meta" (detector, particle, ...) and a flat tree "library" (x, y, z, e, time) read in
 * sequence: the library header (rod grid: x and y of a rod, step), then for each |eta| bin its header (number of distance bins,
 * minimum |eta|), for each distance bin its header (number of showers, minimum distance), for each shower its header (number of
 * spots, R and Z for the containment check, energy) and its spots (position in mm in the frame where the particle goes along +z
 * from the origin, energy in MeV, time in ns).
 */
class FCalShowerLib
{
  public:

    struct Spot { G4ThreeVector position; double energy; double time; };
    struct Shower { std::vector<Spot> spots; float rSize = 0; float zSize = 0; };

    /*! Read the library from a ROOT file; throws std::runtime_error on failure. */
    explicit FCalShowerLib( const std::string &fileName );

    const std::string& detector() const { return m_detector; }
    int particle() const { return m_particle; }

    /*! The shower for the track (FCALDistEtaEnergyShowerLib::getShower): the |eta| bin of the position, the bin of the distance of
        the global (x, y) to the nearest rod of the grid, the shower of nearest kinetic energy moved by randomShift places within 1%,
        spots scaled by E_kin / E_shower. False when there is no shower (|eta| < 3 or empty bin). Spots in the shower frame. */
    bool getShower( const G4Track *track, int randomShift, std::vector<Spot> &out ) const;
    /*! Mean Z and R sizes of up to five showers of nearest energy (getContainmentZ, getContainmentR); 0 when there is none. */
    double getContainmentZ( const G4Track *track ) const;
    double getContainmentR( const G4Track *track ) const;

  private:

    typedef std::map<float, Shower> distbin;      // energy -> shower
    typedef std::map<float, distbin> etabin;      // minimum distance -> showers
    typedef std::map<float, etabin> library;      // minimum |eta| -> distance bins

    float distance( double x, double y ) const;
    // the distance bin of the track and the shower of nearest energy; false if none
    bool find( const G4Track *track, const distbin *&bin, distbin::const_iterator &nearest ) const;
    double containment( const G4Track *track, bool zSize ) const;

    std::string m_detector;
    int m_particle = 0;
    double m_xrodcent = 0, m_yrodcent = 0, m_step = 0;
    library m_libData;
};

#endif
