# GeoKernel CMakeLists.txt
gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python GeoKernel)
gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python/visualizer visualizer)
gaugi_install_data_modules(${CMAKE_CURRENT_SOURCE_DIR}/data GeoKernel)
gaugi_install_scripts_modules(${CMAKE_CURRENT_SOURCE_DIR}/scripts visualizer_trf.py)
