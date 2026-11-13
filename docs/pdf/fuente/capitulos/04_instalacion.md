# 4. Instalación del entorno

Este capítulo parte de una PC con **Ubuntu 24.04 recién instalada** y la deja lista para trabajar
con el sensor. Todo se hace desde una terminal (**Ctrl+Alt+T**).

!!! importante "Comandos con sudo"
    Las líneas que empiezan con `sudo` modifican el sistema y piden la contraseña del usuario.
    Antes de correrlas, leer qué hacen.

## 4.1 Herramientas base

```bash
sudo apt update
sudo apt install -y build-essential cmake git curl tcpdump tmux software-properties-common
```

| Paquete | Para qué se usa |
|---|---|
| `build-essential` | Compiladores de C/C++ (`gcc`, `g++`, `make`) |
| `cmake` | Sistema de compilación del SDK y de los paquetes de ROS 2 |
| `git` | Descargar repositorios |
| `curl` | Descargar archivos desde la terminal |
| `tcpdump` | Ver si llegan los paquetes de red del sensor |
| `tmux` | Mantener vivos los procesos largos (driver, grabaciones) aunque se cierre la terminal o se corte una sesión SSH |
| `software-properties-common` | Provee `add-apt-repository`, que se usa al instalar ROS 2 |

## 4.2 ROS 2 Jazzy

Procedimiento oficial de ROS 2 para Ubuntu 24.04.

**1. Idioma del sistema en UTF-8.** Verificar con `locale` que `LANG` termine en `.UTF-8` (por
ejemplo `es_AR.UTF-8`). Si no:

```bash
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

**2. Repositorio de paquetes de ROS 2.** Se habilita *universe* y se instala `ros2-apt-source`,
que agrega a `apt` el repositorio de ROS 2 con su llave de firma:

```bash
sudo add-apt-repository universe
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
echo "$ROS_APT_SOURCE_VERSION"      # debe mostrar un número de versión
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

**3. ROS 2 y herramientas de desarrollo:**

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ros-jazzy-desktop ros-dev-tools
```

`ros-jazzy-desktop` trae ROS 2 completo con RViz; `ros-dev-tools` trae `colcon` (compila paquetes
de ROS 2), `rosdep` (instala dependencias) y `vcstool`. El `apt upgrade` es necesario: en una
Ubuntu sin actualizar, la instalación puede borrar paquetes del sistema.

**4. Cargar ROS 2 en cada terminal.** Cada terminal nueva tiene que "cargar" ROS 2 para que existan
los comandos `ros2`, `colcon`, etc. Se agrega una vez al final de `~/.bashrc`:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

**5. Verificar.** En una terminal `ros2 run demo_nodes_cpp talker` y en otra
`ros2 run demo_nodes_cpp listener`. El primero muestra `Publishing: 'Hello World: 1'`… y el
segundo `I heard: [Hello World: 1]`… Cortar ambos con **Ctrl+C**.

## 4.3 Librerías del sensor, del SLAM y de los mapas

```bash
sudo apt install -y ros-jazzy-pcl-ros ros-jazzy-pcl-conversions libpcl-dev libeigen3-dev
sudo apt install -y python3-numpy python3-scipy python3-pil \
    ros-jazzy-nav2-map-server ros-jazzy-nav2-util
```

| Paquete | Para qué se usa |
|---|---|
| `libpcl-dev`, `ros-jazzy-pcl-ros`, `ros-jazzy-pcl-conversions` | **PCL** (*Point Cloud Library*) y su conexión con ROS 2: los usan el driver y Point-LIO |
| `libeigen3-dev` | Álgebra lineal (matrices, rotaciones) |
| `python3-numpy`, `python3-scipy`, `python3-pil` | Scripts de Python del proyecto (análisis y productos del mapa) |
| `ros-jazzy-nav2-map-server`, `ros-jazzy-nav2-util` | Cargar y verificar el mapa 2D como lo hace Nav2 |

Inicializar `rosdep`, una vez por PC (`rosdep update` va **sin** `sudo`):

```bash
sudo rosdep init
rosdep update
```

## 4.4 Repositorio del proyecto

Configurar la identidad de git y autenticarse en GitHub (GitHub no acepta la contraseña de la
cuenta desde la terminal; la forma más simple es la herramienta `gh`):

```bash
git config --global user.name  "Nombre Apellido"
git config --global user.email "correo@ejemplo.com"
sudo apt install -y gh
gh auth login        # GitHub.com → HTTPS → Login with a web browser
gh auth setup-git
```

Clonar el repositorio:

```bash
mkdir -p ~/Documentos && cd ~/Documentos
git clone https://github.com/EzeCombina/LiDAR-RobotHumanoide.git
cd LiDAR-RobotHumanoide
```

!!! nota "Carpeta de trabajo"
    Todos los comandos de los capítulos siguientes se ejecutan desde
    `~/Documentos/LiDAR-RobotHumanoide`, salvo que se indique otra carpeta. Los repositorios de
    terceros (SDK y Point-LIO) se descargan aparte, en `~/lidar_ws/`.

## 4.5 Verificación: relevamiento del sistema

El script `scripts/sistema/relevar_sistema.sh` muestra todo lo instalado. No modifica nada y no
necesita `sudo`:

```bash
./scripts/sistema/relevar_sistema.sh
```

```text
== Sistema operativo ==
Ubuntu 24.04.5 LTS
Kernel: 7.0.0-42-generic  |  Arquitectura: x86_64
...
== ROS 2 ==
Distribuciones en /opt/ros: jazzy
ROS_DISTRO en esta terminal: jazzy
  ros-jazzy-desktop                    0.11.0-1noble.20261006.040109
  ros-jazzy-pcl-ros                    2.6.5-...
...
== Interfaces de red ==
eno1             DOWN
wlp4s0           UP             192.168.20.161/24 ...
```

Ningún paquete instalado en este capítulo debe figurar como `NO INSTALADO`. En la sección de red:

- **Placa Ethernet libre:** anotar su nombre (en esta PC, `eno1`); se usa en el capítulo 5.
- **Choque de redes:** si alguna placa ya tiene una dirección `192.168.1.x` (por ejemplo, el Wi-Fi
  de una casa cuyo router usa esa red), choca con la red de fábrica del sensor (capítulo 5).
