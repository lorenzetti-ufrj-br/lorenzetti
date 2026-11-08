#!/bin/bash
# Builds the GeoModel libraries needed by simu_trf.py --atlas-run4 (F41 conserto 27) in the Lorenzetti container (gcc 11, Geant4 11.2):
# GeoModelCore, GeoModelIO and GeoModelG4 of the GeoModel project, release 6.29.0 (the one of Athena 25.0.75), installed in $PREFIX
# (default ~/geomodel). Then run cmake for Lorenzetti with GEOMODEL_DIR=$PREFIX.
#
#     bash build_geomodel.sh [prefix]
#
# Changes needed by gcc 11, with no effect on the geometry: the header <format> (missing in gcc 11) forwarded to the {fmt} library
# (10.2.1, headers only); explicit conversion to RotationMatrix3D in GeoDefinitions.cxx (ambiguous overload); static_assert(false) in a
# template branch of ReadGeoModel.tpp (accepted only from gcc 13) written as static_assert(sizeof(T) == 0).
set -e
PREFIX=${1:-$HOME/geomodel}
W=$(mktemp -d)
D0=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $W
git clone -q --depth 1 -b 6.29.0 https://gitlab.cern.ch/GeoModelDev/GeoModel.git geomodel-src
git clone -q --depth 1 -b 10.2.1 https://github.com/fmtlib/fmt.git fmt-src
mkdir -p compat/include
D=$D0
cp $D/geomodel_compat_format.h compat/include/format
cp -r fmt-src/include/fmt compat/include/
(cd geomodel-src && git apply $D/geomodel-6.29.0-gcc11.patch)
apt-get update -qq > /dev/null && apt-get install -y -qq libsqlite3-dev > /dev/null 2>&1
G4DIR=$(dirname $(find /opt/geant4 -name Geant4Config.cmake | head -1))
mkdir build && cd build
cmake ../geomodel-src -DCMAKE_INSTALL_PREFIX=$PREFIX -DCMAKE_BUILD_TYPE=Release -DGEOMODEL_BUILD_GEOMODELG4=ON       -DGEOMODEL_USE_BUILTIN_EIGEN3=ON -DGEOMODEL_USE_BUILTIN_JSON=ON -DCMAKE_CXX_FLAGS="-isystem $W/compat/include" -DGeant4_DIR=$G4DIR
make -j4 && make install
cp /usr/include/sqlite3.h $PREFIX/include/
cp -r $W/compat/include/* $PREFIX/include/
echo "GeoModel installed in $PREFIX"
