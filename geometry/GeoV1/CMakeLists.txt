file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS GeoV1/*.h)
set(DICT_HEADERS GeoV1/DetectorConstruction_v1.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(GeoV1Dict ${DICT_HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE GeoV1)
add_library(GeoV1 OBJECT ${SOURCES} GeoV1Dict.cxx)
install(FILES ${HEADERS} DESTINATION geometry/GeoV1)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python GeoV1)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts GeoV1)
