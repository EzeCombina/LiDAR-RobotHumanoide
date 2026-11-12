#!/usr/bin/env bash
# =============================================================================
# procesar_grabacion.sh — Genera un mapa 3D a partir de una grabación (Point-LIO)
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Verifica que no haya otra fuente publicando /unilidar/cloud (el driver
#      del sensor o un "ros2 bag play" abierto), para no mezclar datos.
#   2. Lanza Point-LIO (paquete point_lio, configuración del L2).
#   3. Reproduce la grabación indicada una sola vez.
#   4. Detiene Point-LIO con SIGINT (como Ctrl+C), que es cuando guarda el mapa
#      en <carpeta fuente de point_lio>/PCD/scans.pcd.
#   5. Guarda todo en una carpeta nueva, mapas/<fecha>_<nombre>/ (Point-LIO
#      sobrescribe scans.pcd en cada corrida):
#        mapa.pcd         el mapa 3D
#        resumen.txt      datos del mapa y de la trayectoria, con el ERROR DE CIERRE
#        trayectoria.csv  posición estimada del sensor (registrar_trayectoria.py)
#        pointlio.log     registro de Point-LIO
#
#   Los mapas .pcd NO se suben a git (pesan decenas o cientos de MB).
#
# Requisitos:
#   - Point-LIO compilado en ~/lidar_ws/point_lio_ws (ver docs/pasos/05_slam_pointlio.md).
#     Otra ubicación: POINT_LIO_WS=/ruta ./scripts/mapas/procesar_grabacion.sh ...
#   - El driver del sensor detenido.
#
# Cómo se usa:
#   ./scripts/mapas/procesar_grabacion.sh <carpeta_de_la_grabación> [nombre_del_mapa] [--rviz]
#
#   Ejemplos:
#   ./scripts/mapas/procesar_grabacion.sh bags/2026-11-12_1016_sala_quieta
#   ./scripts/mapas/procesar_grabacion.sh bags/2026-11-20_1500_departamento departamento --rviz
#
#   --rviz abre la ventana de RViz de Point-LIO para ver el mapa mientras se arma
#   (solo desde una terminal del escritorio).
# =============================================================================
set -euo pipefail

BAG="${1:-}"
NOMBRE="${2:-}"
RVIZ=false
for arg in "$@"; do [ "$arg" = "--rviz" ] && RVIZ=true; done
[ "$NOMBRE" = "--rviz" ] && NOMBRE=""

if [ -z "$BAG" ] || [ "$BAG" = "--rviz" ]; then
    sed -n '/^# Cómo se usa/,/^#   (solo/p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "ERROR: '$BAG' no es una grabación de ROS 2 (falta metadata.yaml)."
    exit 1
fi

# Carpeta del repositorio (este script está en <repo>/scripts/mapas/).
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
POINT_LIO_WS="${POINT_LIO_WS:-$HOME/lidar_ws/point_lio_ws}"
PCD_ORIGEN="$POINT_LIO_WS/src/point_lio_ros2/PCD/scans.pcd"
[ -z "$NOMBRE" ] && NOMBRE="$(basename "$BAG" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}_//')"
DESTINO="$REPO/mapas/$(date +%Y-%m-%d_%H%M)_${NOMBRE}"

# --- Entorno -----------------------------------------------------------------
if [ ! -f "$POINT_LIO_WS/install/setup.bash" ]; then
    echo "ERROR: no se encuentra Point-LIO compilado en $POINT_LIO_WS"
    exit 1
fi
set +u   # los setup.bash de ROS usan variables sin definir
source /opt/ros/jazzy/setup.bash
source "$POINT_LIO_WS/install/setup.bash"
set -u

# --- Controles previos -------------------------------------------------------
if timeout 3 ros2 topic echo --once /unilidar/cloud --field header.frame_id >/dev/null 2>&1; then
    echo "ERROR: ya hay algo publicando /unilidar/cloud (¿el driver o un 'ros2 bag play'?)."
    echo "Detenerlo antes de procesar una grabación."
    exit 1
fi
if pgrep -f 'lib/point_lio/pointlio_mapping' >/dev/null; then
    echo "ERROR: ya hay un Point-LIO corriendo. Cerrarlo antes."
    exit 1
fi

if [ -e "$DESTINO" ]; then
    echo "ERROR: ya existe $DESTINO"
    exit 1
fi
mkdir -p "$DESTINO"
# Se renombra el mapa anterior para saber con certeza que el nuevo es de esta corrida.
[ -f "$PCD_ORIGEN" ] && mv "$PCD_ORIGEN" "$PCD_ORIGEN.anterior"

echo "Grabación: $BAG"
echo "Carpeta del mapa: $DESTINO"
echo

# --- Point-LIO -----------------------------------------------------------------
# setsid: Point-LIO queda en su propio grupo de procesos, para poder enviarle
# SIGINT a todo el grupo (launch + nodo + RViz) al final.
LOG="$(mktemp)"
setsid ros2 launch point_lio mapping_unilidar_l2.launch.py rviz:="$RVIZ" > "$LOG" 2>&1 < /dev/null &
PID_SLAM=$!

detener_slam() {
    kill -INT -- -"$PID_SLAM" 2>/dev/null || true
}
trap 'echo; echo "Interrumpido: se detiene Point-LIO."; detener_slam; exit 1' INT TERM

# Espera a que el nodo esté listo (hasta 20 s).
for _ in $(seq 1 20); do
    grep -q "file opened" "$LOG" && break
    sleep 1
done
if ! grep -q "file opened" "$LOG"; then
    echo "ERROR: Point-LIO no arrancó. Registro:"
    cat "$LOG"
    detener_slam
    exit 1
fi
echo "Point-LIO en marcha. Reproduciendo la grabación (tarda lo mismo que duró)..."

# --- Registro de la trayectoria -----------------------------------------------
TRAY_CSV="$(mktemp --suffix=.csv)"
TRAY_RES="$(mktemp)"
python3 "$REPO/scripts/mapas/registrar_trayectoria.py" "$TRAY_CSV" > "$TRAY_RES" 2>&1 < /dev/null &
PID_TRAY=$!

# --- Reproducción --------------------------------------------------------------
# "< /dev/null": ros2 bag play no intenta leer el teclado (ver grabar_lidar.sh).
ros2 bag play "$BAG" < /dev/null > /dev/null 2>&1
sleep 3   # deja que Point-LIO procese los últimos mensajes
kill -INT "$PID_TRAY" 2>/dev/null || true
wait "$PID_TRAY" 2>/dev/null || true

# --- Cierre y guardado ---------------------------------------------------------
echo "Reproducción terminada. Deteniendo Point-LIO y guardando el mapa..."
detener_slam
for _ in $(seq 1 120); do
    kill -0 "$PID_SLAM" 2>/dev/null || break
    sleep 1
done
trap - INT TERM

if [ ! -f "$PCD_ORIGEN" ]; then
    echo "ERROR: Point-LIO no guardó $PCD_ORIGEN. Registro en $LOG"
    exit 1
fi
cp "$PCD_ORIGEN" "$DESTINO/mapa.pcd"
cp "$LOG" "$DESTINO/pointlio.log"
cp "$TRAY_CSV" "$DESTINO/trayectoria.csv"
rm -f "$LOG" "$TRAY_CSV"

PUNTOS=$(head -c 1000 "$DESTINO/mapa.pcd" | grep -a '^POINTS' | awk '{print $2}')
{
    echo "Mapa: $(basename "$DESTINO")/mapa.pcd"
    echo "Generado: $(date '+%Y-%m-%d %H:%M:%S') en $(hostname)"
    echo "Grabación de origen: $BAG"
    echo "SLAM: Point-LIO (point_lio_ros2), config/unilidar_l2.yaml + mapping_unilidar_l2.launch.py"
    echo "Puntos: $PUNTOS"
    echo "Tamaño: $(du -h "$DESTINO/mapa.pcd" | cut -f1)"
    echo "Commit del proyecto: $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo desconocido)"
    cat "$TRAY_RES"
    echo "Trayectoria guardada en: $(basename "$DESTINO")/trayectoria.csv"
} > "$DESTINO/resumen.txt"
rm -f "$TRAY_RES"

echo
cat "$DESTINO/resumen.txt"
echo
echo "Para verlo:    ./scripts/mapas/ver_mapa.sh mapas/$(basename "$DESTINO")"
echo "Para medirlo:  ./scripts/mapas/analizar_mapa.py mapas/$(basename "$DESTINO")"
