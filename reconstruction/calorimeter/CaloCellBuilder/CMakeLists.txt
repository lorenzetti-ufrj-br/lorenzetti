
file(GLOB SOURCES src/*.cxx )
file(GLOB_RECURSE HEADERS src/C*.h src/OptimalFilter.h src/ShoweShapes.h src/CrossTalkMaker.h src/ConstrainedOptimalFilter.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCluster)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCell)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloHit)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/EventInfo)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/TruthParticle)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloRings)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../core/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../core/G4Kernel)

# CPS (Calorimetry Pulse Simulator): pulse-shaping logic used by PulseGenerator and
# ConstrainedOptimalFilter. Headers live in <prefix>/include/cps, libcps in <prefix>/lib.
find_path(CPS_INCLUDE_DIR NAMES cps/AnalogPulse.h)
include_directories(${CPS_INCLUDE_DIR})



ROOT_GENERATE_DICTIONARY(CaloCellBuilderDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE CaloCellBuilder)

add_library(CaloCellBuilder  OBJECT ${SOURCES} CaloCellBuilderDict.cxx)
install(FILES ${HEADERS}  DESTINATION CaloCellBuilder)


gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python CaloCellBuilder)







