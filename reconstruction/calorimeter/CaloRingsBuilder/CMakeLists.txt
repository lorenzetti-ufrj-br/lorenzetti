file(GLOB SOURCES src/*.cxx)
file(GLOB HEADERS src/*.h)
list(FILTER HEADERS EXCLUDE REGEX "LinkDef.h")

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCluster)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCell)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloRings)
include_directories(${CMAKE_SOURCE_DIR}/events/EventInfo)
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)
include_directories(${CMAKE_SOURCE_DIR}/tools/calorimeter/CaloRingsTools/src)

ROOT_GENERATE_DICTIONARY(CaloRingsBuilderDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE CaloRingsBuilder)

add_library(CaloRingsBuilder OBJECT ${SOURCES} CaloRingsBuilderDict.cxx)
install(FILES ${HEADERS} DESTINATION CaloRingsBuilder)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python CaloRingsBuilder)
