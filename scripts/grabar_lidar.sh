#!/usr/bin/env bash
# =============================================================================
# grabar_lidar.sh — Graba la nube de puntos y la IMU del LiDAR L2 (rosbag2)
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Verifica que el entorno de ROS 2 esté cargado, que el driver esté
#      publicando y que haya espacio en disco.
#   2. Graba /unilidar/cloud y /unilidar/imu con "ros2 bag record" en formato
#      MCAP, en una carpeta nueva: <carpeta de grabaciones>/<fecha>_<nombre>/
#   3. Al terminar, guarda un archivo descripcion.txt (qué, cuándo, con qué
#      versión del proyecto) y muestra el resumen de "ros2 bag info".
#
#   Las grabaciones NO se suben a git (la carpeta bags/ está en .gitignore).
#   Volumen medido: ~117 MB por minuto (unos 1,2 GB cada 10 minutos).
#
# Requisitos: driver del L2 corriendo (ver docs/pasos/03_driver_ros2.md) y
#             "source /opt/ros/jazzy/setup.bash" en la terminal.
#
# Cómo se usa:
#   ./scripts/grabar_lidar.sh <nombre> [segundos] ["descripción"]
#
#   Ejemplos:
#   ./scripts/grabar_lidar.sh sala_quieta 90 "Sensor en el piso, nadie se mueve"
#   ./scripts/grabar_lidar.sh recorrido_mano          # hasta cortar con Ctrl+C
#
#   Otra carpeta de destino:  BAGS_DIR=/media/disco/bags ./scripts/grabar_lidar.sh ...
#
# Conviene correrlo dentro de tmux si se trabaja por SSH.
# =============================================================================
set -euo pipefail

TOPICOS=(/unilidar/cloud /unilidar/imu)
ESPACIO_MINIMO_GB=5

NOMBRE="${1:-}"
SEGUNDOS="${2:-}"
DESCRIPCION="${3:-}"

if [ -z "$NOMBRE" ]; then
    sed -n '/^# Cómo se usa/,/^# Conviene/p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi
if [ -n "$SEGUNDOS" ] && ! [[ "$SEGUNDOS" =~ ^[0-9]+$ ]]; then
    echo "ERROR: la duración tiene que ser un número entero de segundos."
    exit 1
fi

# Carpeta del repositorio (este script está en <repo>/scripts/).
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BAGS_DIR="${BAGS_DIR:-$REPO/bags}"
DESTINO="$BAGS_DIR/$(date +%Y-%m-%d_%H%M)_${NOMBRE}"

# --- Controles previos -------------------------------------------------------
if ! command -v ros2 >/dev/null 2>&1; then
    echo "ERROR: no se encuentra 'ros2'. Correr: source /opt/ros/jazzy/setup.bash"
    exit 1
fi

for t in "${TOPICOS[@]}"; do
    if ! timeout 5 ros2 topic echo --once "$t" --field header.frame_id >/dev/null 2>&1; then
        echo "ERROR: no llegan mensajes en $t. ¿Está corriendo el driver?"
        exit 1
    fi
done

mkdir -p "$BAGS_DIR"
LIBRE_GB=$(df -BG --output=avail "$BAGS_DIR" | tail -1 | tr -dc '0-9')
if [ "$LIBRE_GB" -lt "$ESPACIO_MINIMO_GB" ]; then
    echo "ERROR: quedan ${LIBRE_GB} GB libres en $BAGS_DIR (mínimo ${ESPACIO_MINIMO_GB} GB)."
    exit 1
fi
if [ -e "$DESTINO" ]; then
    echo "ERROR: ya existe $DESTINO"
    exit 1
fi

echo "Grabando ${TOPICOS[*]}"
echo "Destino: $DESTINO  (${LIBRE_GB} GB libres)"
if [ -n "$SEGUNDOS" ]; then
    echo "Duración: $SEGUNDOS s"
else
    echo "Duración: hasta cortar con Ctrl+C"
fi
echo "Recordatorio: quedarse quieto 5 a 10 s al empezar y al terminar."
echo

INICIO=$(date '+%Y-%m-%d %H:%M:%S')

# --- Grabación ---------------------------------------------------------------
# Ctrl+C: el script lo atrapa con un manejador vacío (':') para no terminar y
# poder escribir la descripción; "ros2 bag record" lo recibe y cierra el archivo.
# (No usar trap '' INT: una señal ignorada se hereda y el grabador la ignoraría.)
#
# "< /dev/null": desactiva el manejo de teclado de ros2 bag record (pausa con la
# barra espaciadora). Así no se pausa por accidente y, sobre todo, no queda
# congelado al intentar leer la terminal (ver docs/pasos/04_grabacion.md).
trap ':' INT
if [ -n "$SEGUNDOS" ]; then
    # timeout envía SIGINT (como Ctrl+C) al cumplirse la duración, para que el
    # archivo se cierre bien. --foreground mantiene la grabación en primer plano,
    # así un Ctrl+C del usuario también la corta antes de tiempo.
    timeout --foreground -s INT "$SEGUNDOS" \
        ros2 bag record -s mcap -o "$DESTINO" --topics "${TOPICOS[@]}" < /dev/null || true
else
    ros2 bag record -s mcap -o "$DESTINO" --topics "${TOPICOS[@]}" < /dev/null || true
fi
trap - INT

if [ ! -f "$DESTINO/metadata.yaml" ]; then
    echo "ERROR: la grabación no se cerró correctamente (falta metadata.yaml)."
    exit 1
fi

# --- Descripción y resumen ---------------------------------------------------
{
    echo "Grabación: $NOMBRE"
    echo "Inicio: $INICIO"
    echo "Fin: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Descripción: ${DESCRIPCION:-(sin descripción)}"
    echo "Equipo: $(hostname)"
    echo "Tópicos: ${TOPICOS[*]}"
    echo "Commit del proyecto: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo 'desconocido')"
} > "$DESTINO/descripcion.txt"

echo
ros2 bag info "$DESTINO"
echo
echo "Tamaño en disco: $(du -sh "$DESTINO" | cut -f1)"
echo "Descripción guardada en $DESTINO/descripcion.txt"
