#!/bin/bash
# F41 conserto 29: builds evaluate_port.cxx against the port in the fork and runs it on the steps.
# Usage: build_port.sh <geometry directory of the fork> <work directory> <label>
# geant4-config and root-config of the environment: in the Lorenzetti container, its own; on lxplus, after asetup Athena,23.0.14,
# those of the release (the Geant4 of ATLAS with CLHEP 2.4.1.3 and the ROOT of the release).
set -e
G=$1; W=$2; TAG=$3
cd $W
SRC="$G/src/GeoSpecialShapes_*.cxx $G/src/LArG4EC_*.cxx"
OPT="-O2 -DNDEBUG"
G4C="$(geant4-config --cflags)"
# in Athena geant4-config calls a clhep-config that does not answer --include: cut its usage message and add the CLHEP include
G4C="${G4C%%Usage:*} -I$(dirname $(which geant4-config))/../include"
INC="$G4C $(root-config --cflags)"
LIB="$(geant4-config --libs) $(root-config --libs) -lMatrix"
g++ -std=c++17 $OPT -o evaluate_port_$TAG evaluate_port.cxx $SRC -I$G -I. $INC $LIB -Wall 2>&1 | grep -E "error|undefined" | head -20
./evaluate_port_$TAG $G/data/EmecTables-ATLAS-P2-RUN4-01-01-00.csv $G/data/ec.fieldzv03 $G/data/HVEMECMap_v02.dat steps.txt port_$TAG.txt > port_$TAG.log 2>&1
tail -2 port_$TAG.log
