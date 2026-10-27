file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS src/RootStreamMaker.h src/RootStreamReader.h src/RootStreamNtupleMaker.h src/RootStreamParquetMaker.h)

execute_process(COMMAND python3 -c "import pyarrow; print(pyarrow.get_include())" OUTPUT_VARIABLE PYARROW_INCLUDE OUTPUT_STRIP_TRAILING_WHITESPACE)
include_directories(${PYARROW_INCLUDE})

set_source_files_properties(src/RootStreamParquetMaker.cxx PROPERTIES COMPILE_FLAGS "-std=c++20 -Wno-cpp")

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/Egamma)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCluster)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloCell)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloHit)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/EventInfo)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/TruthParticle)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../events/CaloRings)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../kernel/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../../kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(RootStreamBuilderDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE RootStreamBuilder)

add_library(RootStreamBuilder OBJECT ${SOURCES} RootStreamBuilderDict.cxx)
install(FILES ${HEADERS} DESTINATION RootStreamBuilder)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python RootStreamBuilder)
