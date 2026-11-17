file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS MagFieldElements/*.h MagFieldElements/*.icc)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/kernel/GaugiKernel)

add_library(MagFieldElements OBJECT ${SOURCES})
install(FILES ${HEADERS} DESTINATION MagFieldElements)
