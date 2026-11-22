gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR} geometry)

add_subdirectory(GALTIC)
add_subdirectory(ATLAS)
add_subdirectory(visualizer)

if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/GeoBase/CMakeLists.txt)
  add_subdirectory(GeoBase)
endif()
