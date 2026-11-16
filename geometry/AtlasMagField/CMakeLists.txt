file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS AtlasMagField/*.h MagFieldElements/*.h MagFieldElements/*.icc)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${Geant4_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../AtlasAthenaUtils/include)

add_library(AtlasMagField OBJECT ${SOURCES})
install(FILES ${HEADERS} DESTINATION AtlasMagField)
