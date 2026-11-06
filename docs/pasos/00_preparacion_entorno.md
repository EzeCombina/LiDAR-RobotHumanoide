# Paso 00 — Preparación del entorno y del repositorio

## Objetivo

Partir de una PC con **Ubuntu 24.04 recién instalada** y dejarla lista para trabajar con el LiDAR L2:

- herramientas de compilación y de diagnóstico de red;
- **ROS 2 Jazzy** y sus herramientas de desarrollo;
- las librerías que necesitan el driver del LiDAR y el SLAM;
- acceso de lectura y escritura al repositorio del proyecto en GitHub.

## Requisitos

- PC con **Ubuntu 24.04 LTS** (escritorio), arquitectura x86_64.
- Una placa **Ethernet libre** (va a quedar dedicada al LiDAR). La conexión a internet se hace por
  Wi-Fi o por otra placa.
- Conexión a internet y usuario con permisos de `sudo`.
- Una cuenta de GitHub con acceso al repositorio `EzeCombina/LiDAR-RobotHumanoide`.
- Alrededor de 10 GB libres en disco para ROS 2, más espacio para grabaciones (del orden de 1 a 2 GB
  cada 10 minutos).

> **¿Qué es ROS 2?** *Robot Operating System 2* no es un sistema operativo: es un conjunto de
> librerías y herramientas que permiten que distintos programas (llamados **nodos**) intercambien
> datos de un robot. Cada versión de ROS 2 se llama **distribución** (Foxy, Humble, Jazzy…) y está
> atada a una versión de Ubuntu. Este proyecto usa **Jazzy**, que corresponde a Ubuntu 24.04.

> **Convención:** las líneas que empiezan con `sudo` modifican el sistema y piden la contraseña del
> usuario. Antes de correrlas, leer la explicación que las acompaña.

## 1. Herramientas base del sistema

```bash
sudo apt update
sudo apt install -y build-essential cmake git curl tcpdump tmux software-properties-common
```

| Paquete | Para qué se usa |
|---|---|
| `build-essential` | Compiladores de C/C++ (`gcc`, `g++`, `make`) |
| `cmake` | Sistema de compilación que usan el SDK del LiDAR y los paquetes ROS 2 |
| `git` | Descargar repositorios y versionar este proyecto |
| `curl` | Descargar archivos desde la terminal |
| `tcpdump` | Ver si llegan los paquetes de red del LiDAR (paso 01) |
| `tmux` | Mantener vivos los procesos largos (driver, grabaciones) aunque se corte la sesión SSH |
| `software-properties-common` | Provee `add-apt-repository`, usado al instalar ROS 2 |

## 2. Instalar ROS 2 Jazzy

Procedimiento oficial de ROS 2 para Ubuntu 24.04 (documentación de Jazzy, sección *Ubuntu (deb
packages)*).

### 2.1 Idioma del sistema en UTF-8

ROS 2 necesita una configuración regional (*locale*) con codificación UTF-8. Verificar:

```bash
locale
```

Si `LANG` termina en `.UTF-8` (por ejemplo `es_AR.UTF-8`, `es_ES.UTF-8` o `en_US.UTF-8`), no hay
que hacer nada. Si no:

```bash
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 2.2 Agregar el repositorio de paquetes de ROS 2

Primero se habilita el repositorio *universe* de Ubuntu. Después se instala el paquete
`ros2-apt-source`, que agrega a `apt` el repositorio de ROS 2 junto con su llave de firma (la llave
permite que `apt` verifique que los paquetes son auténticos).

```bash
sudo add-apt-repository universe

# Averigua la última versión publicada del paquete ros2-apt-source
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
echo "$ROS_APT_SOURCE_VERSION"   # debe mostrar un número de versión, no una línea vacía

# Lo descarga (para Ubuntu 24.04 "noble") y lo instala
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

### 2.3 Instalar ROS 2 y las herramientas de desarrollo

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ros-jazzy-desktop ros-dev-tools
```

- `ros-jazzy-desktop`: ROS 2 completo con **RViz** (visualizador 3D) y ejemplos. Descarga varios
  cientos de MB; tarda.
- `ros-dev-tools`: herramientas para compilar paquetes propios y de terceros: `colcon` (compilador
  de espacios de trabajo), `rosdep` (instala dependencias) y `vcstool`.

> `sudo apt upgrade` es importante: el instalador de ROS 2 advierte que, en una Ubuntu sin
> actualizar, la instalación puede borrar paquetes críticos del sistema.

### 2.4 Cargar el entorno de ROS 2 en cada terminal

Cada terminal nueva tiene que "cargar" ROS 2 para que existan los comandos `ros2`, `colcon`, etc.
Para no hacerlo a mano cada vez, se agrega al final de `~/.bashrc`:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Hacerlo **una sola vez** (si se repite, la línea queda duplicada; no rompe nada, pero conviene
borrar las copias con un editor).

### 2.5 Verificar ROS 2

En una terminal:

```bash
ros2 run demo_nodes_cpp talker
```

En otra terminal:

```bash
ros2 run demo_nodes_cpp listener
```

**Salida esperada:** el `talker` muestra `Publishing: 'Hello World: 1'`, `2`, `3`… y el `listener`
muestra `I heard: [Hello World: 1]`… Cortar ambos con **Ctrl+C**.

> **¿Qué es un tópico?** Es un "canal" con nombre por el que un nodo publica mensajes y otros nodos
> los reciben. En el ejemplo, el `talker` publica en el tópico `/chatter` y el `listener` lo
> escucha. El driver del LiDAR va a publicar la nube de puntos en el tópico `/unilidar/cloud` y la
> IMU en `/unilidar/imu`.

## 3. Librerías del driver del LiDAR y del SLAM

```bash
sudo apt install -y ros-jazzy-pcl-ros ros-jazzy-pcl-conversions libpcl-dev libeigen3-dev
```

| Paquete | Para qué se usa |
|---|---|
| `libpcl-dev` | **PCL** (*Point Cloud Library*): librería de C++ para procesar nubes de puntos |
| `ros-jazzy-pcl-ros`, `ros-jazzy-pcl-conversions` | Conversión entre los mensajes de ROS 2 y las nubes de PCL |
| `libeigen3-dev` | **Eigen**: álgebra lineal (matrices, rotaciones), usada por el driver y por Point-LIO |

## 4. Inicializar rosdep

`rosdep` lee los archivos `package.xml` de los paquetes de terceros e instala lo que les falta. Se
inicializa una sola vez por PC:

```bash
sudo rosdep init
rosdep update
```

> `sudo rosdep init` crea `/etc/ros/rosdep/sources.list.d/20-default.list`. `rosdep update` se corre
> **sin** `sudo`.

## 5. Git y acceso a GitHub

### 5.1 Identidad de git

Los commits llevan el nombre y el correo de quien los hace. Configurarlos una vez por PC:

```bash
git config --global user.name  "Nombre Apellido"
git config --global user.email "correo@ejemplo.com"
```

### 5.2 Autenticación

GitHub no acepta la contraseña de la cuenta desde la terminal. Hay dos formas de autenticarse;
alcanza con una.

**Opción A — GitHub CLI (`gh`):**

```bash
sudo apt install -y gh
gh auth login        # elegir: GitHub.com → HTTPS → Login with a web browser
gh auth setup-git    # hace que git use las credenciales de gh
gh auth status       # verificación: debe decir "Logged in to github.com"
```

**Opción B — clave SSH:**

```bash
ssh-keygen -t ed25519 -C "correo@ejemplo.com"   # Enter para aceptar la ruta por defecto
cat ~/.ssh/id_ed25519.pub                         # copiar la línea completa
```

Pegar la clave pública en GitHub → *Settings* → *SSH and GPG keys* → *New SSH key*. Verificar:

```bash
ssh -T git@github.com    # la primera vez pide aceptar la huella del servidor: responder "yes"
```

Salida esperada: `Hi <usuario>! You've successfully authenticated, but GitHub does not provide shell access.`

### 5.3 Clonar el repositorio del proyecto

```bash
mkdir -p ~/Documentos && cd ~/Documentos
git clone https://github.com/EzeCombina/LiDAR-RobotHumanoide.git        # con la opción A
# git clone git@github.com:EzeCombina/LiDAR-RobotHumanoide.git          # con la opción B
cd LiDAR-RobotHumanoide
git pull
```

Si el repositorio ya estaba clonado por HTTPS y se eligió la opción B, cambiar el remoto:

```bash
git remote set-url origin git@github.com:EzeCombina/LiDAR-RobotHumanoide.git
```

## 6. Verificación final: relevamiento del sistema

El script `scripts/relevar_sistema.sh` muestra todo lo que hay que registrar en `docs/versiones.md`.
No modifica nada y no necesita `sudo`. También sirve en la Jetson del robot.

```bash
./scripts/relevar_sistema.sh
```

**Salida esperada** (resumida; PC del laboratorio, 2026-11-06):

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

Ningún paquete de los puntos 1 a 4 debe figurar como `NO INSTALADO` o `NO ENCONTRADO` (`docker` y
`gh` son opcionales).

### Qué mirar en la sección de red

- **Placa Ethernet libre:** es la que se va a usar para el LiDAR (en esta PC, `eno1`). Anotar su
  nombre: se usa en el paso 01.
- **Choque de redes:** el LiDAR viene de fábrica en la red `192.168.1.x`. Si alguna placa de la PC
  ya tiene una dirección `192.168.1.x` (por ejemplo, la del Wi-Fi de la casa), hay conflicto y habrá
  que cambiar la red del sensor (ver paso 01). En la PC del laboratorio el Wi-Fi está en
  `192.168.20.x`: **no hay choque**.

## Problemas frecuentes

| Síntoma (error literal) | Causa | Solución |
|---|---|---|
| `fatal: could not read Username for 'https://github.com': No existe el dispositivo o la dirección` | El remoto es HTTPS y no hay credenciales guardadas | Autenticarse con la opción A o B del punto 5.2 |
| `Host key verification failed.` | Primera conexión SSH a GitHub sin haber aceptado la huella del servidor | Correr `ssh -T git@github.com` en una terminal interactiva y responder `yes` |
| `Permission denied (publickey).` | La clave SSH no está cargada en la cuenta de GitHub | Repetir el paso de copiar `~/.ssh/id_ed25519.pub` en GitHub |
| `Author identity unknown` al hacer `git commit` | Falta configurar nombre y correo | Punto 5.1 |
| `apt update`: `Conflicting values set for option Signed-By` | La PC ya tenía el repositorio de ROS 2 agregado con el método anterior (`/etc/apt/sources.list.d/ros2.list`) y se instaló además `ros2-apt-source` | Dejar uno solo: borrar `ros2.list` (`sudo rm /etc/apt/sources.list.d/ros2.list`) y volver a correr `sudo apt update` |
| `E: Unable to locate package ros-jazzy-desktop` | No se agregó el repositorio de ROS 2, o falta `sudo apt update` después de agregarlo | Repetir los puntos 2.2 y 2.3 |
| `ros2: orden no encontrada` | La terminal no cargó el entorno de ROS 2 | Punto 2.4, o abrir una terminal nueva |
| `sudo rosdep init`: `ERROR: default sources list file already exists` | `rosdep` ya estaba inicializado | Ignorarlo y seguir con `rosdep update` |
| `ROS_APT_SOURCE_VERSION` vacío | Sin internet, o la API de GitHub limitó las consultas | Revisar la conexión y reintentar; como alternativa, buscar la última versión a mano en `https://github.com/ros-infrastructure/ros-apt-source/releases` |
