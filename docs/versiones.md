# Versiones de software, repositorios y firmware

Registrar todo lo que se instale o clone, para que la implementación sea reproducible.
Los datos de la PC se obtienen con `./scripts/relevar_sistema.sh`.

## PC de implementación

Relevada el 2026-11-06 (host `eze-laptop`).

| Elemento | Versión | Cómo se obtuvo |
|---|---|---|
| Ubuntu | 24.04.5 LTS (noble) | `lsb_release -a` |
| Kernel | 7.0.0-42-generic (x86_64) | `uname -r` |
| CPU / RAM | AMD Ryzen 5 4600H (12 hilos) / 22 GiB | `lscpu`, `free -h` |
| Disco (`/home`) | 57 GB, 39 GB libres | `df -h ~` |
| ROS 2 | Jazzy — `ros-jazzy-desktop` 0.11.0-1noble.20261006.040109 | `dpkg -l` |
| RViz 2 | `ros-jazzy-rviz2` 14.1.24-1noble.20260915.204213 | `dpkg -l` |
| colcon | `python3-colcon-common-extensions` 0.3.0-100 | `dpkg -l` |
| Compilador | gcc / g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) | `gcc --version` |
| CMake | 3.28.3 | `cmake --version` |
| Python | 3.12.3 | `python3 --version` |
| git | 2.43.0 | `git --version` |

### Red de la PC

| Interfaz | Uso | Dirección (2026-11-06) |
|---|---|---|
| `eno1` | Ethernet libre → **LiDAR** | sin configurar, sin cable |
| `wlp4s0` | Wi-Fi (internet) | `192.168.20.161/24` → **no choca** con la red de fábrica del L2 (`192.168.1.x`) |

Firewall `ufw`: **activo** (habrá que abrir el puerto UDP 6201 en el paso 01).

## Sensor

| Elemento | Versión | Cómo se obtuvo |
|---|---|---|
| Hardware del L2 | (completar) | salida de `example_lidar_udp` |
| Firmware del L2 | (completar) | salida de `example_lidar_udp` |

## Repositorios de terceros

| Repositorio | URL | Commit | Fecha de clonado |
|---|---|---|---|
| unilidar_sdk2 | https://github.com/unitreerobotics/unilidar_sdk2 | | |
| point_lio_ros2 | https://github.com/dfloreaa/point_lio_ros2 | | |

## Paquetes apt

Lista completa de lo que se instala en una Ubuntu 24.04 limpia siguiendo el paso 00. La columna
"Versión de referencia" es la que tiene la PC del laboratorio; sirve para reproducir el entorno si en
el futuro una versión nueva rompe algo.

> La PC del laboratorio ya tenía instalada parte de este software antes del proyecto (incluido ROS 2,
> agregado con el método anterior de `ros2.list` + llavero, sin `ros2-apt-source`). La documentación
> se escribe igual **como si se partiera de cero**.

| Paquete | Versión de referencia | Para qué | Paso |
|---|---|---|---|
| `build-essential` | 12.10ubuntu1 | Compiladores C/C++ | 00 |
| `cmake` | 3.28.3-1build7 | Compilación del SDK y paquetes ROS 2 | 00 |
| `git` | 1:2.43.0-1ubuntu7.4 | Repositorios | 00 |
| `curl` | 8.5.0-2ubuntu10.16 | Descargas | 00 |
| `tcpdump` | 4.99.4-3ubuntu4.24.04.1 | Diagnóstico de red del LiDAR | 00 |
| `tmux` | 3.4-1ubuntu0.2 (instalado 2026-11-06) | Procesos largos por SSH | 00 |
| `software-properties-common` | 0.99.49.4 | `add-apt-repository` | 00 |
| `ros2-apt-source` | no usado en la PC del laboratorio (método anterior) | Repositorio de ROS 2 | 00 |
| `ros-jazzy-desktop` | 0.11.0-1noble.20261006.040109 | ROS 2 Jazzy + RViz | 00 |
| `ros-dev-tools` | 1.0.3 (instalado 2026-11-06) | colcon, rosdep, vcstool | 00 |
| `python3-colcon-common-extensions` | 0.3.0-100 | Compilar espacios de trabajo ROS 2 | 00 |
| `python3-vcstool` | 0.3.0-1 (instalado 2026-11-06, con `ros-dev-tools`) | Descarga de varios repositorios | 00 |
| `python3-rosdep` | 0.27.0-1 (instalado 2026-11-06, con `ros-dev-tools`) | Dependencias de paquetes ROS 2 | 00 |
| `ros-jazzy-pcl-ros` | 2.6.5-1noble.20260916.065720 (instalado 2026-11-06) | Driver ROS 2 del L2 | 00 |
| `ros-jazzy-pcl-conversions` | 2.6.5-1noble.20260912.165932 | Driver ROS 2 del L2 | 00 |
| `libpcl-dev` | 1.14.0+dfsg-1 | Driver del L2 / Point-LIO | 00 |
| `libeigen3-dev` | 3.4.0-4build0.1 | Driver del L2 / Point-LIO | 00 |
| `gh` | 2.45.0-1ubuntu0.3 (instalado 2026-11-06) | Autenticación con GitHub (opcional) | 00 |
