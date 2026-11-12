# Herramientas propias para el LiDAR Unitree L2, basadas en la librería
# precompilada del SDK oficial (unilidar_sdk2):
#   - cambiar_modo_lidar: cambia la interfaz de datos (Ethernet <-> serie/USB)
#   - estado_lidar:       muestra el estado interno (motores, temperaturas, etc.)
#
# Compilación (requiere el SDK clonado en ~/lidar_ws/unilidar_sdk2):
#   cd scripts/sensor && mkdir -p build && cd build
#   cmake .. && make
# Otra ubicación del SDK:
#   cmake -DUNILIDAR_SDK_DIR=/ruta/unitree_lidar_sdk ..
# Los ejecutables quedan en scripts/sensor/build/.
cmake_minimum_required(VERSION 3.10)
project(herramientas_sensor CXX)

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

foreach(programa cambiar_modo_lidar estado_lidar)
  add_executable(${programa} ${programa}.cpp)
  target_include_directories(${programa} PRIVATE "${UNILIDAR_SDK_DIR}/include")
  target_link_libraries(${programa} PRIVATE "${LIB_SDK}" Threads::Threads)
endforeach()
