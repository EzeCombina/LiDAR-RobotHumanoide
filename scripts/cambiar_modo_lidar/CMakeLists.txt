# Herramienta propia para cambiar el modo de comunicación del LiDAR L2
# (Ethernet <-> serie/USB). Usa la librería precompilada del SDK oficial.
#
# La ruta del SDK se puede cambiar con:
#   cmake -DUNILIDAR_SDK_DIR=/otra/ruta/unitree_lidar_sdk ..
cmake_minimum_required(VERSION 3.10)
project(cambiar_modo_lidar CXX)

set(CMAKE_CXX_STANDARD 17)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(UNILIDAR_SDK_DIR "$ENV{HOME}/lidar_ws/unilidar_sdk2/unitree_lidar_sdk"
    CACHE PATH "Carpeta unitree_lidar_sdk del repositorio unilidar_sdk2")

# La librería viene compilada para x86_64 y aarch64 (Jetson, Raspberry Pi).
set(LIB_SDK "${UNILIDAR_SDK_DIR}/lib/${CMAKE_SYSTEM_PROCESSOR}/libunilidar_sdk2.a")
if(NOT EXISTS "${LIB_SDK}")
  message(FATAL_ERROR "No se encontró ${LIB_SDK}. Indicar la ruta con -DUNILIDAR_SDK_DIR=...")
endif()

find_package(Threads REQUIRED)

add_executable(cambiar_modo_lidar cambiar_modo_lidar.cpp)
target_include_directories(cambiar_modo_lidar PRIVATE "${UNILIDAR_SDK_DIR}/include")
target_link_libraries(cambiar_modo_lidar PRIVATE "${LIB_SDK}" Threads::Threads)
