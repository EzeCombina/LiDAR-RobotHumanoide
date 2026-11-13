#!/usr/bin/env bash
# =============================================================================
# ver_mapa_2d.sh — Carga un mapa 2D de ocupación con Nav2 y lo muestra en RViz
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Lanza nav2_map_server con el mapa_2d.yaml indicado: es el mismo programa
#      que va a usar el robot para cargar el mapa, así que si se ve bien acá, el
#      formato es correcto para Nav2.
#   2. Lo activa (nav2_util lifecycle_bringup: configure + activate). Los nodos
#      de Nav2 no publican nada hasta que se activan.
#   3. Publica el marco "map" en /tf (evita el aviso "No tf data" de RViz).
#   4. Abre RViz con config/rviz/ver_mapa_2d.rviz (vista desde arriba).
#   5. Al cerrar RViz, detiene todo.
#
# Requisitos: ros-jazzy-nav2-map-server y ros-jazzy-nav2-util (paso 00). Desde una
#             terminal del escritorio de Ubuntu (no la de VS Code instalado como snap).
#
# Cómo se usa:
#   ./scripts/mapas/ver_mapa_2d.sh <carpeta_del_mapa | archivo.yaml>
#
#   Ejemplo:
#   ./scripts/mapas/ver_mapa_2d.sh mapas/2026-11-12_1445_habitacion_vertical_rapido
# =============================================================================
set -euo pipefail

ENTRADA="${1:-}"
if [ -d "$ENTRADA" ]; then
    YAML="$ENTRADA/mapa_2d.yaml"
else
    YAML="$ENTRADA"
fi
if [ -z "$ENTRADA" ] || [ ! -f "$YAML" ]; then
    echo "Uso: $0 <carpeta_del_mapa | archivo.yaml>"
    [ -n "$ENTRADA" ] && echo "ERROR: no existe '$YAML' (¿se ejecutó generar_mapa_2d.py?)"
    exit 1
fi
YAML="$(realpath "$YAML")"
# Carpeta del repositorio (este script está en <repo>/scripts/mapas/).
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

set +u
source /opt/ros/jazzy/setup.bash
set -u

PIDS=()
# Al salir (normalmente, con Ctrl+C o con SIGTERM) se detienen los procesos lanzados.
# - Cada programa se lanza con "setsid", en su propio grupo de procesos, y al salir
#   se termina el grupo entero con SIGTERM (envoltorio "ros2 run" + programa real).
# - No se usa SIGINT: en un script, los procesos en segundo plano lo ignoran.
# - Sin el "trap ... INT TERM", bash no limpia si lo terminan con una señal.
limpiar() { for p in "${PIDS[@]}"; do kill -TERM -- "-$p" 2>/dev/null || true; done; }
trap limpiar EXIT
trap 'exit 1' INT TERM

echo "Cargando $YAML con nav2_map_server..."
setsid ros2 run nav2_map_server map_server --ros-args -p yaml_filename:="$YAML" \
    > /dev/null 2>&1 < /dev/null &
PIDS+=($!)
sleep 2
ros2 run nav2_util lifecycle_bringup map_server > /dev/null 2>&1 < /dev/null

setsid ros2 run tf2_ros static_transform_publisher --frame-id map --child-frame-id mapa_origen \
    > /dev/null 2>&1 < /dev/null &
PIDS+=($!)

echo "Abriendo RViz (cerrar la ventana para terminar)..."
rviz2 -d "$REPO/config/rviz/ver_mapa_2d.rviz"
