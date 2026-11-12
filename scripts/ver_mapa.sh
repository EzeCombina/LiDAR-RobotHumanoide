#!/usr/bin/env bash
# =============================================================================
# ver_mapa.sh — Muestra un mapa .pcd (y su trayectoria) en RViz
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Publica el archivo .pcd en el tópico /cloud_pcd (marco "map") con el
#      programa pcd_to_pointcloud de pcl_ros (viene con ROS 2, no hay que
#      instalar nada).
#   2. Si existe la trayectoria del mapa (<mapa>_trayectoria.csv, la genera
#      procesar_grabacion.sh) o se indica otra, la publica con
#      publicar_trayectoria.py: recorrido en /trayectoria, esfera verde en la
#      partida y roja en la llegada.
#   3. Publica el marco "map" en /tf (evita el aviso "No tf data" de RViz).
#   4. Abre RViz con config/rviz/ver_mapa.rviz.
#   5. Al cerrar RViz, detiene las publicaciones.
#
# Requisitos: ROS 2 Jazzy con ros-jazzy-pcl-ros (paso 00). Correrlo desde una
#             terminal del escritorio de Ubuntu (RViz es una ventana gráfica; no
#             desde la terminal integrada de VS Code instalado como snap).
#
# Cómo se usa:
#   ./scripts/ver_mapa.sh <archivo.pcd> [trayectoria.csv]
#
#   Ejemplo:
#   ./scripts/ver_mapa.sh mapas/2026-11-12_1339_departamento_vertical_pointlio.pcd
#   (busca solo mapas/2026-11-12_1339_departamento_vertical_pointlio_trayectoria.csv)
# =============================================================================
set -euo pipefail

PCD="${1:-}"
if [ -z "$PCD" ] || [ ! -f "$PCD" ]; then
    echo "Uso: $0 <archivo.pcd> [trayectoria.csv]"
    [ -n "$PCD" ] && echo "ERROR: no existe '$PCD'"
    exit 1
fi
PCD="$(realpath "$PCD")"
TRAY="${2:-${PCD%.pcd}_trayectoria.csv}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

set +u
source /opt/ros/jazzy/setup.bash
set -u

PIDS=()
trap 'for p in "${PIDS[@]}"; do kill -INT "$p" 2>/dev/null || true; done' EXIT

# Publica el marco "map" en /tf (transformada fija, vacía). Sin esto RViz muestra
# el aviso "Fixed Frame: No tf data" aunque el mapa se vea bien.
ros2 run tf2_ros static_transform_publisher --frame-id map --child-frame-id mapa_origen \
    > /dev/null 2>&1 < /dev/null &
PIDS+=($!)

echo "Publicando $PCD en /cloud_pcd (cada 2 s)..."
ros2 run pcl_ros pcd_to_pointcloud --ros-args \
    -p file_name:="$PCD" -p tf_frame:=map -p publishing_period_ms:=2000 \
    > /dev/null 2>&1 < /dev/null &
PIDS+=($!)

if [ -f "$TRAY" ]; then
    echo "Publicando la trayectoria $TRAY (verde = partida, rojo = llegada)..."
    python3 "$REPO/scripts/publicar_trayectoria.py" "$TRAY" > /dev/null 2>&1 < /dev/null &
    PIDS+=($!)
else
    echo "Sin trayectoria (no existe $TRAY)."
fi

echo "Abriendo RViz (cerrar la ventana para terminar)..."
rviz2 -d "$REPO/config/rviz/ver_mapa.rviz"
