file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS v1/*.h)
set(DICT_HEADERS v1/DetectorConstruction_v1.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(geometry_v1Dict ${DICT_HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE geometry_v1)
add_library(geometry_v1 OBJECT ${SOURCES} geometry_v1Dict.cxx)
install(FILES ${HEADERS} DESTINATION geometry/v1)
