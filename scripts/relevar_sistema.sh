#!/usr/bin/env bash
# =============================================================================
# relevar_sistema.sh — Relevamiento del sistema para el proyecto LiDAR L2
# -----------------------------------------------------------------------------
# Qué hace:
#   Muestra (sin modificar nada) los datos de la computadora que hay que
#   registrar en docs/versiones.md: sistema operativo, kernel, CPU, memoria,
#   disco, compiladores, ROS 2, librerías que usa el driver del LiDAR,
#   herramientas auxiliares e interfaces de red.
#
# Cómo se usa:
#   ./scripts/relevar_sistema.sh                 # muestra el informe en pantalla
#   ./scripts/relevar_sistema.sh > relevamiento.txt   # lo guarda en un archivo
#
# No requiere sudo. Sirve tanto en la PC con Ubuntu como en la Jetson del robot.
# =============================================================================

# Fuerza mensajes en inglés para que la salida sea igual en cualquier PC.
export LC_ALL=C

titulo() { printf '\n== %s ==\n' "$1"; }

# Muestra la versión instalada de un paquete apt, o "NO INSTALADO".
version_apt() {
    local v
    v=$(dpkg-query -W -f='${Status} ${Version}' "$1" 2>/dev/null | awk '/install ok installed/ {print $4}')
    printf '  %-36s %s\n' "$1" "${v:-NO INSTALADO}"
}

# Muestra la primera línea de "<programa> --version", o "NO ENCONTRADO".
version_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        printf '  %-12s %s\n' "$1" "$("$@" 2>&1 | head -n1)"
    else
        printf '  %-12s %s\n' "$1" "NO ENCONTRADO"
    fi
}

echo "Relevamiento del sistema — $(date '+%Y-%m-%d %H:%M') — host: $(hostname)"

titulo "Sistema operativo"
lsb_release -ds 2>/dev/null || grep PRETTY_NAME /etc/os-release
echo "Kernel: $(uname -r)  |  Arquitectura: $(uname -m)"
# En una Jetson, este archivo indica la versión de L4T (JetPack).
[ -f /etc/nv_tegra_release ] && echo "L4T: $(head -n1 /etc/nv_tegra_release)"

titulo "Hardware"
lscpu | grep -E '^Model name' | sed 's/  */ /g'
echo "Núcleos: $(nproc)"
free -h | awk '/^Mem:/ {print "Memoria RAM total: " $2}'
df -h "$HOME" | awk 'NR==2 {print "Disco (" $6 "): " $2 " total, " $4 " libres"}'

titulo "Compiladores y herramientas de compilación"
version_apt build-essential
version_cmd gcc --version
version_cmd g++ --version
version_cmd cmake --version
version_cmd python3 --version
version_cmd git --version

titulo "ROS 2"
if [ -d /opt/ros ]; then
    echo "Distribuciones en /opt/ros: $(ls /opt/ros | tr '\n' ' ')"
else
    echo "No hay ROS 2 instalado en /opt/ros"
fi
echo "ROS_DISTRO en esta terminal: ${ROS_DISTRO:-(no cargado; falta 'source /opt/ros/<distro>/setup.bash')}"
for distro in $(ls /opt/ros 2>/dev/null); do
    version_apt "ros-${distro}-desktop"
    version_apt "ros-${distro}-ros-base"
    version_apt "ros-${distro}-rviz2"
    version_apt "ros-${distro}-pcl-ros"
    version_apt "ros-${distro}-pcl-conversions"
done
version_apt ros-dev-tools
version_apt python3-colcon-common-extensions
version_apt python3-rosdep
version_apt ros2-apt-source
# Método anterior de agregar el repositorio de ROS 2 (no debe convivir con ros2-apt-source).
[ -f /etc/apt/sources.list.d/ros2.list ] && echo "  Repositorio de ROS 2 agregado con el método anterior: /etc/apt/sources.list.d/ros2.list"

titulo "Librerías del driver del LiDAR"
version_apt libpcl-dev
version_apt libeigen3-dev

titulo "Herramientas auxiliares"
version_cmd tmux -V
version_cmd tcpdump --version
version_cmd docker --version
version_cmd gh --version

titulo "Interfaces de red"
ip -br addr
echo
echo "Estado de las placas Ethernet cableadas:"
for ifc in $(ls /sys/class/net); do
    # Solo placas cableadas físicas (no wifi, no loopback, no virtuales).
    if [ -d "/sys/class/net/$ifc/device" ] && [ ! -d "/sys/class/net/$ifc/wireless" ]; then
        echo "  $ifc: carrier=$(cat /sys/class/net/$ifc/carrier 2>/dev/null || echo 0)" \
             "(1 = hay enlace, 0 = sin cable o sin enlace)"
    fi
done

titulo "Firewall"
if command -v systemctl >/dev/null 2>&1; then
    echo "ufw: $(systemctl is-active ufw 2>/dev/null)"
fi
