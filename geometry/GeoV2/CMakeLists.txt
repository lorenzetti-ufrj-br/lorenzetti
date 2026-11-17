file(GLOB SOURCES src/*.cxx)
# The import of the ATLAS geometry (F41 conserto 27) uses the GeoModel headers, which need C++20
if( GEOMODEL_LIBRARIES )
  set_source_files_properties( src/AtlasGeoModelImport.cxx PROPERTIES COMPILE_OPTIONS
    "-std=c++20;-isystem;${GEOMODEL_DIR}/include;-isystem;${GEOMODEL_DIR}/include/eigen3" )
endif()

# The ported ATLAS charge collection of the EM end-cap (F41 conserto 29): compiled as in the Athena release 23.0.14 (-O2 -DNDEBUG; in
# Athena the asserts of these files are off, and the code must go on where an assert would stop it)
file(GLOB EMEC_PORT_SOURCES src/GeoSpecialShapes_*.cxx src/LArG4EC_*.cxx)
set_source_files_properties( ${EMEC_PORT_SOURCES} PROPERTIES COMPILE_OPTIONS "-O2;-DNDEBUG" )

file(GLOB_RECURSE HEADERS GeoV2/*.h)
set(DICT_HEADERS GeoV2/DetectorConstruction_v2.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)
include_directories(${CMAKE_SOURCE_DIR}/magfield/MagField)
include_directories(${CMAKE_SOURCE_DIR}/magfield/MagFieldElements)

ROOT_GENERATE_DICTIONARY(GeoV2Dict ${DICT_HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE GeoV2)
add_library(GeoV2 OBJECT ${SOURCES} GeoV2Dict.cxx)
install(DIRECTORY GeoV2/ DESTINATION geometry/GeoV2)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python GeoV2)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data GeoV2)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts GeoV2)
