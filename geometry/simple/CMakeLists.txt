file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS generic_calorimeter/*.h )


include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../core/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../core/G4Kernel)

ROOT_GENERATE_DICTIONARY(generic_calorimeterDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE generic_calorimeter)   
add_library(generic_calorimeter  OBJECT ${SOURCES} generic_calorimeterDict.cxx)
install(FILES ${HEADERS}  DESTINATION generic_calorimeter)




gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python generic_calorimeter)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data generic_calorimeter)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts generic_calorimeter)







