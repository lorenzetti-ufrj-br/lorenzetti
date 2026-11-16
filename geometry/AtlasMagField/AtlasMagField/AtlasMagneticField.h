/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Atlas/G4AtlasServices, StandardFieldSvc.h/.cxx) for --atlas-run4 (F41 conserto 27); changes: class AtlasField renamed AtlasMagneticField and reduced to the field-map path (no IMagFieldSvc, no ATLAS_THREAD_SAFE); StandardFieldSvc::createFieldMap turned into the static helper loadMap (no Gaudi service, no PathResolver: the caller gives the ROOT file path).

#ifndef AtlasMagneticField_h
#define AtlasMagneticField_h

#include <memory>
#include <string>

// Geant4
#include "G4MagneticField.hh"

// MagField cache
#include "MagFieldElements/AtlasFieldCache.h"
#include "MagFieldElements/AtlasFieldMap.h"

/// @class AtlasMagneticField
/// @brief G4 wrapper around the main ATLAS magnetic field cache (Athena's
/// AtlasField from StandardFieldSvc.h).
///
/// The cache is not thread safe: as in Athena, each Geant4 worker thread
/// must own its own AtlasMagneticField. The AtlasFieldMap is read-only after
/// initialization and can be shared between threads.
class AtlasMagneticField : public G4MagneticField
{
  public:
    /// Construct the field object from the field map.
    /// The scales are useCurrent/mapCurrent (1 when the map currents are used).
    AtlasMagneticField(const MagField::AtlasFieldMap* fieldMap, double scaleSolenoid = 1., double scaleToroid = 1.)
      : m_fieldCache (MagField::AtlasFieldCache( scaleSolenoid, scaleToroid, fieldMap))
    {
    }

    MagField::AtlasFieldCache& fieldCache() { return m_fieldCache; }

    /// Implementation of G4 method to retrieve field value.
    /// point in mm (Geant4 internal units), field returned in Geant4 internal
    /// units (kT = 1), exactly as in Athena: no unit conversion.
    void GetFieldValue(const double *point, double *field) const override
    {
        m_fieldCache.getField(point, field);
    }

    /// Read the field map from a ROOT file, as StandardFieldSvc::createFieldMap
    /// does in Athena: open the TFile, check the TTree "BFieldMap",
    /// AtlasFieldMap::initializeMap(file, soleCurrent, toroCurrent), close.
    /// Returns nullptr on failure (the reason is printed to std::cerr).
    static std::shared_ptr<MagField::AtlasFieldMap> loadMap(const std::string& rootFile,
                                                            double soleCurrent = 7730.,
                                                            double toroCurrent = 20400.);

  private:
    /// Field cache - mutable because getField modifies the cache
    mutable MagField::AtlasFieldCache m_fieldCache;
};

#endif
