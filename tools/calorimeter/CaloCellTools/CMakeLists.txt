file(GLOB SOURCES src/*.cxx )
file(GLOB HEADERS src/*.h )
list(REMOVE_ITEM HEADERS ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCell)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloHit)
include_directories(${CMAKE_SOURCE_DIR}/events/EventInfo)
include_directories(${CMAKE_SOURCE_DIR}/events/TruthParticle)
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(CaloCellToolsDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE CaloCellTools)

add_library(CaloCellTools OBJECT ${SOURCES} CaloCellToolsDict.cxx)
install(FILES ${HEADERS} DESTINATION CaloCellTools)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python CaloCellTools)
