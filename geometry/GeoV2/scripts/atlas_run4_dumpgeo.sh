#!/bin/bash
# Writes the GeoModel dump of the ATLAS geometry of the simulation read by simu_trf.py --atlas-run4 (--atlas-run4-geometry or
# LORENZETTI_ATLAS_RUN4_GEOMETRY; F41 conserto 27), with the DumpGeo of an Athena release, on a machine with CVMFS (for instance lxplus):
#
#     bash atlas_run4_dumpgeo.sh [release (25.0.75)] [geometry tag (ATLAS-P2-RUN4-01-01-00)]
#
# The dump is made in the SIMULATION mode (Common.ProductionStep=Simulation): in any other mode the LAr geometry of Athena is the one of
# the reconstruction (LArGMConfig.py sets GeometryConfig = RECO), whose end-cap cryostats have only two of their cylinders. The alignment
# of the LAr is off (the dump has no conditions), so the geometry is the nominal one of the simulation. ATLAS-P2-RUN4-01-01-00 is the
# geometry of the reference production of Run 4 (e8481_s4038_s4045, Athena 23.0.14). Output: geometry-<tag>-sim.db (about 71 MB).
REL=${1:-25.0.75}; TAG=${2:-ATLAS-P2-RUN4-01-01-00}
ulimit -v unlimited   # without it the DumpGeo cannot load the libraries of the HGTD on lxplus ("failed to map segment")
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh -q
asetup Athena,$REL > asetup.log 2>&1
python -m DumpGeo.DumpGeoConfig --detDescr=$TAG --outFilename=geometry-$TAG-sim.db -f        Common.ProductionStep=ProductionStep.Simulation LAr.doAlign=False > dumpgeo.log 2>&1
echo dumpgeo_exit=$?
ls -la geometry-$TAG-sim.db
