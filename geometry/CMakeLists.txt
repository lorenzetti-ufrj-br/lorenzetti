add_subdirectory(v1)
add_subdirectory(v2)

gaugi_install_python_modules( ${CMAKE_CURRENT_SOURCE_DIR}/python geometry)
gaugi_install_data_modules( ${CMAKE_CURRENT_SOURCE_DIR}/data geometry)
gaugi_install_scripts_modules( ${CMAKE_CURRENT_SOURCE_DIR}/scripts geometry)
