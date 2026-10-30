file(GLOB_RECURSE SOURCES src/*.cxx )
file(GLOB_RECURSE HEADERS src/*.h )
list(FILTER HEADERS EXCLUDE REGEX "LinkDef\\.h$")

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src/electronics)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCluster)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCell)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloHit)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/EventInfo)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/TruthParticle)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloRings)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../kernel/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(CaloCellBuilderDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE CaloCellBuilder)

add_library(CaloCellBuilder OBJECT ${SOURCES} CaloCellBuilderDict.cxx)
install(FILES ${HEADERS} DESTINATION CaloCellBuilder)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python CaloCellBuilder)
