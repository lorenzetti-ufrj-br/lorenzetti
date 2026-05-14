file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS src/*.h )
file(GLOB_RECURSE HEADERS src/D*.h )


include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../core/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../core/G4Kernel)

ROOT_GENERATE_DICTIONARY(geometryDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE geometry)   
add_library(geometry  OBJECT ${SOURCES} geometryDict.cxx)
install(FILES ${HEADERS}  DESTINATION geometry)




gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python geometry)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data geometry)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts geometry)







