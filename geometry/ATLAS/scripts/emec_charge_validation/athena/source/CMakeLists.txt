# F41 conserto 29: minimal work project on top of Athena 23.0.14, with only the harness of the EMEC charge collection
cmake_minimum_required( VERSION 3.10 )
project( WorkDir VERSION 1.0.0 LANGUAGES C CXX )
find_package( Athena 23.0.14 REQUIRED )
atlas_ctest_setup()
atlas_project( USE Athena ${Athena_VERSION} )
lcg_generate_env( SH_FILE ${CMAKE_BINARY_DIR}/${ATLAS_PLATFORM}/env_setup.sh )
install( FILES ${CMAKE_BINARY_DIR}/${ATLAS_PLATFORM}/env_setup.sh DESTINATION . )
