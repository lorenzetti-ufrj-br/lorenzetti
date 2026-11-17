// Lorenzetti port (F41 conserto 29): the EMECData of Athena (GeoSpecialShapes/EMECData.h), which toEMECData fills from the geometry
// database in Athena 23.0.14, filled from the CSV file written by geometry/scripts/emec_tables_from_geomdb.py (the same tables and
// tags, from the SQLite copy of the ATLAS geometry database in CVMFS).
#ifndef LARG4EC_EMECDATACSV_H
#define LARG4EC_EMECDATACSV_H
#include <string>
#include "GeoSpecialShapes/EMECData.h"
EMECData readEMECDataCSV(const std::string &path);
#endif
