file(GLOB SOURCES src/*.cxx)
# The import of the ATLAS geometry (F41 conserto 27) uses the GeoModel headers, which need C++20
if( GEOMODEL_LIBRARIES )
  set_source_files_properties( src/AtlasGeoModelImport.cxx PROPERTIES COMPILE_OPTIONS
    "-std=c++20;-isystem;${GEOMODEL_DIR}/include;-isystem;${GEOMODEL_DIR}/include/eigen3" )
endif()
file(GLOB_RECURSE HEADERS v2/*.h)
set(DICT_HEADERS v2/DetectorConstruction_v2.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)
include_directories(${CMAKE_SOURCE_DIR}/magfield)

ROOT_GENERATE_DICTIONARY(geometry_v2Dict ${DICT_HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE geometry_v2)
add_library(geometry_v2 OBJECT ${SOURCES} geometry_v2Dict.cxx)
install(FILES ${HEADERS} DESTINATION geometry/v2)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python geometry/v2)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data geometry/v2)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts geometry/v2)
