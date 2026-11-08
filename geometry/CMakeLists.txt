file(GLOB SOURCES src/*.cxx)
# The import of the ATLAS geometry (F41 conserto 27) uses the GeoModel headers, which need C++20
if( GEOMODEL_LIBRARIES )
  set_source_files_properties( src/AtlasGeoModelImport.cxx PROPERTIES COMPILE_OPTIONS
    "-std=c++20;-isystem;${GEOMODEL_DIR}/include;-isystem;${GEOMODEL_DIR}/include/eigen3" )
endif()
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







