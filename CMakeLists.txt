cmake_minimum_required(VERSION 3.0)
project(lorenzetti)


set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -DDROP_CGAL")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)


# Set by hand pythia and fastjet
set( FASTJET_INCLUDE_DIRS $ENV{FASTJET_INCLUDE})
set( PYTHIA8_INCLUDE_DIRS $ENV{PYTHIA8_INCLUDE})
set( HEPMC_INCLUDE_DIRS $ENV{HEPMC_INCLUDE})
file(GLOB FASTJET_LIBRARIES $ENV{FASTJET_LIBRARIES}/*.dylib $ENV{FASTJET_LIBRARIES}/*.so)
file(GLOB PYTHIA8_LIBRARIES $ENV{PYTHIA8_LIBRARIES}/*.a $ENV{PYTHIA8_LIBRARIES}/*.so)


# CPS (Calorimetry Pulse Simulator): provides the calorimeter pulse-shaping logic
# consumed by reconstruction/calorimeter/CaloCellBuilder. Following the project
# convention, it is normally installed under /usr/local (libcps + headers in cps/)
# by the base Docker image and just located here. As a fallback (e.g. an image that
# predates the CPS layer, or a local build without it), CPS is fetched and built
# from source so the configure step still succeeds. Both branches expose the same
# CPS_LIBRARY and CPS_INCLUDE_DIR variables to the rest of the build.
find_library(CPS_LIBRARY NAMES cps)
find_path(CPS_INCLUDE_DIR NAMES cps/AnalogPulse.h)

if(CPS_LIBRARY AND CPS_INCLUDE_DIR)
  message(STATUS "Found CPS library: ${CPS_LIBRARY}")
else()
  message(STATUS "CPS not found on the system; fetching and building it from source.")
  include(FetchContent)
  # CPS builds a SWIG Python module by default, which is not needed here.
  set(BUILD_PYTHON OFF CACHE BOOL "" FORCE)
  set(BUILD_TESTS  OFF CACHE BOOL "" FORCE)
  set(BUILD_DOCS   OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    cps
    GIT_REPOSITORY https://github.com/ingoncalves/calorimetry-pulse-simulator.git
    GIT_TAG        v1.1.0
  )
  FetchContent_MakeAvailable(cps)
  # The 'cps' CMake target can be used directly as a link dependency.
  set(CPS_LIBRARY cps)
  # CPS's source tree keeps headers flat in include/; recreate the installed-style
  # include/cps/ layout so that `#include "cps/..."` resolves in both cases.
  set(CPS_INCLUDE_DIR ${CMAKE_BINARY_DIR}/cps_include)
  file(MAKE_DIRECTORY ${CPS_INCLUDE_DIR}/cps)
  file(GLOB _cps_headers ${cps_SOURCE_DIR}/include/*.h)
  file(COPY ${_cps_headers} DESTINATION ${CPS_INCLUDE_DIR}/cps)
endif()


find_package(OpenMP)
if(OpenMP_FOUND)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()



#----------------------------------------------------------------------------
# Find Geant4 package, activating all available UI and Vis drivers by default
# You can set WITH_GEANT4_UIVIS to OFF via the command line or ccmake/cmake-gui
# to build a batch mode only executable
option(WITH_GEANT4_UIVIS "Build example with Geant4 UI and Vis drivers" ON)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

#----------------------------------------------------------------------------
# Setup Geant4 include directories and compile definitions
include(${Geant4_USE_FILE})
include_directories(${CMAKE_SOURCE_DIR} ${Geant4_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})


#----------------------------------------------------------------------------
# Find ROOT (required package)
find_package(ROOT COMPONENTS EG Eve Geom Gui GuiHtml GenVector Hist Physics Matrix Graf RIO Tree Gpad RGL MathCore)
include(${ROOT_USE_FILE})


#----------------------------------------------------------------------------
include(core/GaugiKernel/cmake/InstallGaugiFunctions.cmake)
gaugi_initialize()




#set( Python_ADDITIONAL_VERSIONS 3.0)
find_package( PythonInterp REQUIRED)
find_package( PythonLibs REQUIRED)
#find_package( Boost COMPONENTS python system filesystem)
#include_directories( ${Boost_INCLUDE_DIR} )
#link_directories( ${Boost_LIBRARY_DIR} )

# include simulation tools
include_directories( ${FASTJET_INCLUDE_DIRS} )
include_directories( ${PYTHIA8_INCLUDE_DIRS} )
include_directories( ${HEPMC_INCLUDE_DIRS} )


# core
add_subdirectory( core/GaugiKernel )
add_subdirectory( core/G4Kernel )



# event packages
add_subdirectory( events/CaloHit )
add_subdirectory( events/CaloCell )
add_subdirectory( events/SpacePoint )
add_subdirectory( events/CaloCluster )
add_subdirectory( events/EventInfo )
add_subdirectory( events/TruthParticle )
add_subdirectory( events/CaloRings )
add_subdirectory( events/Egamma)

# detector definitions
add_subdirectory( geometry )



# reconstruction package

add_subdirectory( reconstruction/calorimeter/CaloCellBuilder )
add_subdirectory( reconstruction/calorimeter/CaloClusterBuilder )
add_subdirectory( reconstruction/calorimeter/CaloRingsBuilder )
add_subdirectory( reconstruction/calorimeter/CaloHitBuilder )


add_subdirectory( reconstruction/io/RootStreamBuilder )
add_subdirectory( reconstruction/physics/EgammaBuilder )
add_subdirectory( reconstruction/reco )



# generator package
add_subdirectory( generator/genkernel )
add_subdirectory( generator/filters )
add_subdirectory( generator/evtgen )






add_library(lorenzetti SHARED
  $<TARGET_OBJECTS:GaugiKernel>
  $<TARGET_OBJECTS:G4Kernel>
  $<TARGET_OBJECTS:CaloHit>
  $<TARGET_OBJECTS:CaloCell>
  $<TARGET_OBJECTS:CaloCluster>
  $<TARGET_OBJECTS:EventInfo>
  $<TARGET_OBJECTS:TruthParticle>
  $<TARGET_OBJECTS:CaloRings>
  $<TARGET_OBJECTS:Egamma>
  $<TARGET_OBJECTS:SpacePoint>
  $<TARGET_OBJECTS:geometry>
  $<TARGET_OBJECTS:CaloHitBuilder>
  $<TARGET_OBJECTS:CaloCellBuilder>
  $<TARGET_OBJECTS:CaloClusterBuilder>
  $<TARGET_OBJECTS:CaloRingsBuilder>
  $<TARGET_OBJECTS:RootStreamBuilder>
  $<TARGET_OBJECTS:EgammaBuilder>
  $<TARGET_OBJECTS:GenKernel>
  $<TARGET_OBJECTS:filters>
  $<TARGET_OBJECTS:evtgen>
)

message( STATUS ${FASTJET_LIBRARIES} )
message( STATUS ${PYTHIA8_LIBRARIES} )
message( STATUS ${HEPMC_LIBRARIES} )

target_link_Libraries(lorenzetti ${ROOT_LIBRARIES} 
                                 ${ROOT_COMPONENT_LIBRARIES} 
                                 #${Boost_PYTHON_LIBRARIES} 
                                 ${PYTHON_LIBRARIES} 
                                 #${Boost_FILESYSTEM_LIBRARY} 
                                 #${Boost_SYSTEM_LIBRARY} 
                                 ${Geant4_LIBRARIES}
                                 ${FASTJET_LIBRARIES}
                                 ${HEPMC_LIBRARIES}
                                 ${PYTHIA8_LIBRARIES}
                                 ${CPS_LIBRARY} )



