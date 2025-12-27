file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS generic/*.h )


include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../core/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../core/G4Kernel)

ROOT_GENERATE_DICTIONARY(genericDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE generic)   
add_library(generic  OBJECT ${SOURCES} genericDict.cxx)
install(FILES ${HEADERS}  DESTINATION generic)



gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python generic)










gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python ATLAS)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data ATLAS)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts ATLAS)







