file(GLOB SOURCES src/*.cxx)
# The import of the ATLAS geometry (F41 conserto 27) uses the GeoModel headers, which need C++20
if( GEOMODEL_LIBRARIES )
  set_source_files_properties( src/AtlasGeoModelImport.cxx PROPERTIES COMPILE_OPTIONS
    "-std=c++20;-isystem;${GEOMODEL_DIR}/include;-isystem;${GEOMODEL_DIR}/include/eigen3" )
endif()
file(GLOB_RECURSE HEADERS src/*.h )
# The ported ATLAS charge collection of the EM end-cap (F41 conserto 29): compiled as in the Athena release 23.0.14 (-O2 -DNDEBUG; in
# Athena the asserts of these files are off, and the code must go on where an assert would stop it)
file(GLOB EMEC_PORT_SOURCES src/GeoSpecialShapes_*.cxx src/LArG4EC_*.cxx)
set_source_files_properties( ${EMEC_PORT_SOURCES} PROPERTIES COMPILE_OPTIONS "-O2;-DNDEBUG" )
file(GLOB_RECURSE HEADERS src/D*.h )


include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../core/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../core/G4Kernel)

ROOT_GENERATE_DICTIONARY(geometryDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE geometry)   
add_library(geometry  OBJECT ${SOURCES} geometryDict.cxx)
install(FILES ${HEADERS}  DESTINATION geometry)




gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python geometry)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data geometry)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts geometry)







