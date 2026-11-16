/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: removed the unused include GaudiKernel/ServiceHandle.h.

/**
 * @author R.D.Schaffer -at- cern.ch
 * @date end 2019
 * @brief Local cache for magnetic field (based on
 * MagFieldServices/AtlasFieldSvcTLS.h)
 */

#ifndef MAGFIELDCONDITIONS_ATLASFIELDMAP_H
#define MAGFIELDCONDITIONS_ATLASFIELDMAP_H 1

// MagField includes
#include "CxxUtils/restrict.h"
#include "MagFieldElements/BFieldCache.h"
#include "MagFieldElements/BFieldCacheZR.h"
#include "MagFieldElements/BFieldCond.h"
#include "MagFieldElements/BFieldMeshZR.h"
#include "MagFieldElements/BFieldZone.h"

#include <iostream>
#include <memory>

// forward declarations
class TFile;

namespace MagField {

/** @class AtlasFieldMap
 *
 *  @brief Map for magnetic field
 *
 *  @author R.D.Schaffer -at- cern.ch
 */
class AtlasFieldMap
{
public:
  AtlasFieldMap() = default;
  ~AtlasFieldMap() { delete m_meshZR; }

  // initialize map from root file
  bool initializeMap(TFile* rootfile,
                     float solenoidCurrent,
                     float toroidCurrent);

  // Functions used by getField[ZR] in AtlasFieldCache
  // search for a "zone" to which the point (z,r,phi) belongs
  const BFieldZone* findBFieldZone(double z, double r, double phi) const;

  // fast 2d map (made of one zone)
  const BFieldMeshZR* getBFieldMesh() const;

  /** status of the magnets */
  bool solenoidOn() const { return solenoidCurrent() > 0.0; }
  bool toroidOn() const { return toroidCurrent() > 0.0; }
  // magnet currents read with map - needed for scaling
  float solenoidCurrent() const { return m_solenoidCurrent; }
  float toroidCurrent() const { return m_toroidCurrent; }
  int solenoidZoneId() const { return m_solenoidZoneId; }

private:
  AtlasFieldMap& operator=(AtlasFieldMap&& other) = delete;
  AtlasFieldMap(const AtlasFieldMap& other) = delete;
  AtlasFieldMap& operator=(const AtlasFieldMap& other) = delete;
  AtlasFieldMap(AtlasFieldMap&& other) = delete;

  // slow zone search is used during initialization to build the LUT
  BFieldZone* findZoneSlow(double z, double r, double phi);

  // utility functions used by readMap
  int read_packed_data(std::istream& input, std::vector<int>& data) const;
  int read_packed_int(std::istream& input, int& n) const;
  void buildLUT();
  void buildZR();

  /** approximate memory footprint in bytes */
  int memSize() const;

  /** Data Members **/

  // field map name
  std::string m_filename;

  // currents read in with map
  float m_solenoidCurrent{ 0 }; // solenoid current in ampere
  float m_toroidCurrent{ 0 };   // toroid current in ampere
  int m_solenoidZoneId{ -1 };   // solenoid zone id

  // full 3d map (made of multiple zones)
  std::vector<BFieldZone> m_zone;

  // fast 2d map (made of one zone)
  BFieldMeshZR* m_meshZR{ nullptr };

  // data members used in zone-finding
  std::vector<double> m_edge[3];            // zone boundaries in z, r, phi
  std::vector<int> m_edgeLUT[3];            // look-up table for zone edges
  double m_invq[3];                         // 1/stepsize in m_edgeLUT
  std::vector<const BFieldZone*> m_zoneLUT; // look-up table for zones
  // more data members to speed up zone-finding
  double m_zmin{ 0 }; // minimum z
  double m_zmax{ 0 }; // maximum z
  int m_nz{ 0 };      // number of z bins in zoneLUT
  double m_rmax{ 0 }; // maximum r
  int m_nr{ 0 };      // number of r bins in zoneLUT
  int m_nphi{ 0 };    // number of phi bins in zoneLUT
  bool m_mapIsInitialized{ false };
};

} // namespace MagField

#include "AtlasFieldMap.icc"
#endif // MAGFIELDCONDITIONS_ATLASFIELDMAP_H
