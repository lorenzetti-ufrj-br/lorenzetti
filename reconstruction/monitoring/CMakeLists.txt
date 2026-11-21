file(GLOB SOURCES src/*.cxx)
file(GLOB HEADERS src/*.h)
list(REMOVE_ITEM HEADERS ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/events/EventInfo)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCluster)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloCell)
include_directories(${CMAKE_SOURCE_DIR}/events/Egamma)
include_directories(${CMAKE_SOURCE_DIR}/events/CaloRings)
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)
include_directories(${CMAKE_SOURCE_DIR}/kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(MonitoringDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE Monitoring)

add_library(Monitoring OBJECT ${SOURCES} MonitoringDict.cxx)
install(FILES ${HEADERS} DESTINATION Monitoring)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python EgammaMonitoring)
gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python Monitoring)
gaugi_install_scripts_modules(${CMAKE_CURRENT_SOURCE_DIR}/scripts monitoring)
gaugi_install_scripts_modules(${CMAKE_CURRENT_SOURCE_DIR}/scripts reco)
