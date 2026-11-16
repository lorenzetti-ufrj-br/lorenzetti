/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: removed the unused include GaudiKernel/ServiceHandle.h; GaudiKernel/SystemOfUnits.h is a local shim with the Gaudi values.

/**
 * @author R.D.Schaffer -at- cern.ch
 * @date July 2019
 * @brief Local cache for magnetic field (based on
 * MagFieldServices/AtlasFieldSvcTLS.h)
 */

#ifndef MAGFIELDCONDITIONS_ATLASMTFIELDCACHE_H
#define MAGFIELDCONDITIONS_ATLASMTFIELDCACHE_H 1

// MagField includes
#include "CxxUtils/restrict.h"
#include "GaudiKernel/SystemOfUnits.h"
#include "MagFieldElements/AtlasFieldMap.h"
#include "MagFieldElements/BFieldCache.h"
#include "MagFieldElements/BFieldCacheZR.h"
#include "MagFieldElements/BFieldCond.h"
#include "MagFieldElements/BFieldMeshZR.h"
#include "MagFieldElements/BFieldZone.h"

#include <memory>
namespace MagField {

/** @class AtlasFieldCache
 *
 *  @brief Local cache for magnetic field (based on
 * MagFieldServices/AtlasFieldSvcTLS.h)
 *
 *  We keep track of the
 *  - magnetic field map
 *  - solenoid/toroid scales from the currents
 *  - The current zone
 *  - The current/cached cell in the zone.
 *
 *  @author R.D.Schaffer -at- cern.ch
 */
class AtlasFieldCache
{
public:
  AtlasFieldCache() = default;
  /** constructor to setup with field scale
   * and magnetic field map for
   * first access to field */
  AtlasFieldCache(double solFieldScale,
                  double torFieldScale,
                  const AtlasFieldMap* fieldMap);

  /**
   * Move-able but not copy-able
   */
  AtlasFieldCache& operator=(AtlasFieldCache&& other) = default;
  AtlasFieldCache(AtlasFieldCache&& other) = default;
  ~AtlasFieldCache() = default;

  /** get B field value at given position
   * xyz[3] is in mm, bxyz[3] is in kT
   * if deriv[9] is given, field derivatives are returned in kT/mm
   * */
  void getField(const double* ATH_RESTRICT xyz,
                double* ATH_RESTRICT bxyz,
                double* ATH_RESTRICT deriv = nullptr);

  /** get B field valaue on the z-r plane at given position
   * works only inside the solenoid.
   * Otherwise call getField above.
   * xyz[3] is in mm, bxyz[3] is in kT
   * if deriv[9] is given, field
   * derivatives are returned in kT/mm
   * */
  void getFieldZR(const double* ATH_RESTRICT xyz,
                  double* ATH_RESTRICT bxyz,
                  double* ATH_RESTRICT deriv = nullptr);

  /** status of the magnets */
  bool solenoidOn() const;
  bool toroidOn() const;

private:
  AtlasFieldCache(const AtlasFieldCache& other) = delete;
  AtlasFieldCache& operator=(const AtlasFieldCache& other) = delete;

  /// fill given magnetic field zone */
  bool fillFieldCache(double z, double r, double phi);
  /// fill Z-R cache for solenoid */
  bool fillFieldCacheZR(double z, double r);

  /// magnetic field scales from currents
  double m_solScale{ 1 };
  double m_torScale{ 1 };
  double m_scaleToUse{ 1 };

  // Solenoid zone ID number - needed to set solScale.
  // Assumes only one Solenoid zone.
  int m_solZoneId{ -1 };

  /// handle to the magnetic field map - not owned
  const AtlasFieldMap* m_fieldMap{ nullptr };

  /// A zone of the full 3d field.
  /// This can be solenoid or one of the
  /// toroid etc zones
  /// Owned by AtlasFieldMap
  const BFieldZone* m_zone3d{ nullptr };

  /// Full 3d field cell/cache
  /// This will be a cell inside
  /// a 3d field zone
  BFieldCache m_cache3d;

  /// Pointer to the conductors in the current field zone (to compute
  /// Biot-Savart component) Owned by AtlasFieldMap.
  const std::vector<BFieldCond>* m_cond{ nullptr };

  /// fast 2d map made of one zone
  /// assuming phi/roatational symmetry
  /// Owned by AtlasFieldMap.
  const BFieldMeshZR* m_meshZR{ nullptr };

  /// Fast 2d field cell/cache
  BFieldCacheZR m_cacheZR;
};

} // namespace MagField
#include "AtlasFieldCache.icc"
#endif // MAGFIELDCONDITIONS_ATLASMTFIELDCACHE_H
