#!/usr/bin/env bash
# =============================================================================
# ver_mapa.sh — Muestra un mapa .pcd en RViz
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Publica el archivo .pcd en el tópico /cloud_pcd (marco "map") con el
#      programa pcd_to_pointcloud de pcl_ros (viene con ROS 2, no hay que
#      instalar nada).
#   2. Abre RViz con config/rviz/ver_mapa.rviz.
#   3. Al cerrar RViz, detiene la publicación.
#
# Requisitos: ROS 2 Jazzy con ros-jazzy-pcl-ros (paso 00). Correrlo desde una
#             terminal del escritorio de Ubuntu (RViz es una ventana gráfica; no
#             desde la terminal integrada de VS Code instalado como snap).
#
# Cómo se usa:
#   ./scripts/ver_mapa.sh <archivo.pcd>
#
#   Ejemplo:
#   ./scripts/ver_mapa.sh mapas/2026-11-12_1047_sala_quieta_pointlio.pcd
# =============================================================================
set -euo pipefail

PCD="${1:-}"
if [ -z "$PCD" ] || [ ! -f "$PCD" ]; then
    echo "Uso: $0 <archivo.pcd>"
    [ -n "$PCD" ] && echo "ERROR: no existe '$PCD'"
    exit 1
fi
PCD="$(realpath "$PCD")"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

set +u
source /opt/ros/jazzy/setup.bash
set -u

echo "Publicando $PCD en /cloud_pcd (cada 2 s)..."
ros2 run pcl_ros pcd_to_pointcloud --ros-args \
    -p file_name:="$PCD" -p tf_frame:=map -p publishing_period_ms:=2000 \
    > /dev/null 2>&1 < /dev/null &
PID_PUB=$!
trap 'kill -INT "$PID_PUB" 2>/dev/null || true' EXIT

echo "Abriendo RViz (cerrar la ventana para terminar)..."
rviz2 -d "$REPO/config/rviz/ver_mapa.rviz"
