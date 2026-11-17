# F41 conserto 29: the algorithm that calls the EnergyCalculator of Athena (services of libAtlasGeant4.so)
atlas_subdir( EmecHarness )
find_package( CLHEP )
find_package( Geant4 )
atlas_add_component( EmecHarness src/*.cxx
   INCLUDE_DIRS /cvmfs/atlas.cern.ch/repo/sw/software/23.0/Athena/23.0.14/InstallArea/x86_64-centos7-gcc11-opt/include ${CLHEP_INCLUDE_DIRS} ${GEANT4_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR}/athena_private
   DEFINITIONS ${CLHEP_DEFINITIONS}
   LINK_LIBRARIES ${CLHEP_LIBRARIES} ${GEANT4_LIBRARIES} AthenaBaseComps GaudiKernel GeoSpecialShapes
   /cvmfs/atlas.cern.ch/repo/sw/software/23.0/Athena/23.0.14/InstallArea/x86_64-centos7-gcc11-opt/lib/libAtlasGeant4.so )
