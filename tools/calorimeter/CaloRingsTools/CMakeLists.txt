file(GLOB SOURCES src/*.cxx)
file(GLOB HEADERS src/*.h)
list(FILTER HEADERS EXCLUDE REGEX "LinkDef.h")

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCell)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCluster)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloRings)
include_directories(${CMAKE_SOURCE_DIR}/events/EventInfo)
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(CaloRingsToolsDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE CaloRingsTools)

add_library(CaloRingsTools OBJECT ${SOURCES} CaloRingsToolsDict.cxx)
install(FILES ${HEADERS} DESTINATION CaloRingsTools)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python CaloRingsTools)
