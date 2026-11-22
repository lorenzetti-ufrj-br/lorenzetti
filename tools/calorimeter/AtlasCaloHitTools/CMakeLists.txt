file(GLOB SOURCES src/*.cxx src/freerunning/*.cxx)
file(GLOB HEADERS src/*.h src/freerunning/*.h)
list(REMOVE_ITEM HEADERS ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src/freerunning)
include_directories(${CMAKE_SOURCE_DIR}/reconstruction/calorimeter/CaloHitBuilder)
include_directories(${CMAKE_SOURCE_DIR}/tools/calorimeter/CaloHitTools)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCell)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloHit)
include_directories(${CMAKE_SOURCE_DIR}/events/EventInfo)
include_directories(${CMAKE_SOURCE_DIR}/events/TruthParticle)
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)
include_directories(${CMAKE_SOURCE_DIR}/geometry/ATLAS)
include_directories(${CMAKE_SOURCE_DIR}/geometry/GeoV2)

ROOT_GENERATE_DICTIONARY(AtlasCaloHitToolsDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE AtlasCaloHitTools)

add_library(AtlasCaloHitTools OBJECT ${SOURCES} AtlasCaloHitToolsDict.cxx)
install(FILES ${HEADERS} DESTINATION AtlasCaloHitTools)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python AtlasCaloHitTools)
