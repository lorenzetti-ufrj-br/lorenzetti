
file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS GaugiKernel/*.h )
file(GLOB_RECURSE CXXUTILS_HEADERS CxxUtils/*.h )
file(GLOB_RECURSE GAUDI_HEADERS GaudiKernel/*.h )
include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})

ROOT_GENERATE_DICTIONARY(GaugiKernelDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h  MODULE GaugiKernel)
                                      
add_library(GaugiKernel  OBJECT ${SOURCES} GaugiKernelDict.cxx)
install(FILES ${HEADERS}  DESTINATION GaugiKernel)
install(FILES ${CXXUTILS_HEADERS} DESTINATION CxxUtils)
install(FILES ${GAUDI_HEADERS} DESTINATION GaudiKernel)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python GaugiKernel)








