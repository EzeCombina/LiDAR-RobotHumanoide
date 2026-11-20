#!/usr/bin/env bash
# =============================================================================
# probar_con_grabacion.sh — Prueba la navegación con una grabación, sin sensor
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Lanza scripts/navegacion/navegacion.launch.py con la grabación indicada
#      (sin RViz), en segundo plano, guardando su salida en un archivo .log.
#   2. Según la prueba, corre el evaluador correspondiente mientras se reproduce:
#        obstaculos   -> evaluar_obstaculos.py   (OBJETIVO 2)
#        localizacion -> evaluar_localizacion.py (OBJETIVO 1)
#   3. Al terminar, cierra todo con SIGINT (como Ctrl+C) y espera a que los
#      nodos terminen, para que no queden procesos colgados.
#   Los resultados quedan en <carpeta de resultados>/ (por defecto
#   resultados/<fecha>_<prueba>_<grabación>/): launch.log, evaluacion.txt e
#   imágenes del costmap (en la prueba de obstáculos).
#
# Requisitos: paso R02 completo; source de /opt/ros/jazzy/setup.bash y de
#   ~/lidar_ws/point_lio_ws/install/setup.bash.
#
# Cómo se usa:
#   ./scripts/navegacion/probar_con_grabacion.sh obstaculos <grabación> <altura_inicial> [segundos]
#   ./scripts/navegacion/probar_con_grabacion.sh localizacion <grabación> <carpeta_mapa> [segundos] [inicio] [altura]
#
#   Ejemplos:
#   ./scripts/navegacion/probar_con_grabacion.sh obstaculos bags/2026-11-12_1028_persona_caminando 0.05 50
#   ./scripts/navegacion/probar_con_grabacion.sh localizacion \
#       bags/2026-11-12_1442_habitacion_vertical_rapido \
#       mapas/2026-11-12_1445_habitacion_vertical_rapido 70
#   (inicio: "mapa" por defecto, o x,y,yaw para probar una pose inicial equivocada;
#    con x,y,yaw hay que dar la altura inicial del sensor en m, por ejemplo 0.873)
#
#   Otra carpeta de resultados: RESULTADOS=/ruta ./scripts/navegacion/probar_con_grabacion.sh ...
# =============================================================================
set -euo pipefail

PRUEBA="${1:-}"
BAG="${2:-}"
if [ -z "$PRUEBA" ] || [ -z "$BAG" ]; then
    sed -n '/^# Cómo se usa/,/^#   Otra carpeta/p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "ERROR: $BAG no es una grabación (falta metadata.yaml)."
    exit 1
fi
if ! command -v ros2 >/dev/null 2>&1; then
    echo "ERROR: falta 'source /opt/ros/jazzy/setup.bash' (y el de Point-LIO)."
    exit 1
fi
# Otra prueba o simulación abierta mezclaría los datos (dos Point-LIO, dos
# reproducciones): se buscan los procesos (más confiable que "ros2 node list").
if pgrep -f "[p]ointlio_mapping|[b]ase_nivelada.py|[g]z sim|[b]ag play" >/dev/null; then
    echo "ERROR: ya hay procesos de navegación o simulación corriendo:"
    pgrep -fa "[p]ointlio_mapping|[b]ase_nivelada.py|[g]z sim|[b]ag play" | cut -c1-100
    echo "Cerrarlos antes (Ctrl+C en su terminal)."
    exit 1
fi

NOMBRE_BAG="$(basename "$BAG")"
DESTINO="${RESULTADOS:-$REPO/resultados}/$(date +%Y-%m-%d_%H%M)_${PRUEBA}_${NOMBRE_BAG}"
mkdir -p "$DESTINO"

case "$PRUEBA" in
    obstaculos)
        ALTURA="${3:?Falta la altura inicial del sensor (m)}"
        SEGUNDOS="${4:-50}"
        ARGS=(modo:=obstaculos "bag:=$BAG" "altura_inicial:=$ALTURA")
        EVALUAR=(./scripts/navegacion/evaluar_obstaculos.py --duracion "$SEGUNDOS"
                 --imagenes "$DESTINO/costmap" --cada 10)
        ;;
    localizacion)
        MAPA="${3:?Falta la carpeta del mapa}"
        SEGUNDOS="${4:-60}"
        INICIO="${5:-mapa}"
        ARGS=(modo:=localizacion "bag:=$BAG" "mapa:=$MAPA" "inicio:=$INICIO")
        if [ -n "${6:-}" ]; then ARGS+=("altura_inicial:=$6"); fi
        EVALUAR=(./scripts/navegacion/evaluar_localizacion.py --mapa "$MAPA" --duracion "$SEGUNDOS"
                 --csv "$DESTINO/error.csv")
        ;;
    *)
        echo "ERROR: prueba '$PRUEBA' desconocida (obstaculos | localizacion)."
        exit 1
        ;;
esac

echo "Prueba: $PRUEBA   Grabación: $BAG"
echo "Resultados: $DESTINO"
# setsid: el launch queda en su propio grupo de procesos, para cerrarlo entero.
setsid ros2 launch scripts/navegacion/navegacion.launch.py "${ARGS[@]}" rviz:=false \
    > "$DESTINO/launch.log" 2>&1 &
PID_LAUNCH=$!
cerrar() {
    kill -INT -- "-$PID_LAUNCH" 2>/dev/null || true
    for _ in $(seq 20); do kill -0 "$PID_LAUNCH" 2>/dev/null || break; sleep 0.5; done
    kill -KILL -- "-$PID_LAUNCH" 2>/dev/null || true
}
trap cerrar EXIT
sleep 3

"${EVALUAR[@]}" --ros-args -p use_sim_time:=true < /dev/null | tee "$DESTINO/evaluacion.txt"

{
    echo "Prueba: $PRUEBA"
    echo "Grabación: $BAG"
    echo "Argumentos del launch: ${ARGS[*]}"
    echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Commit del proyecto: $(git rev-parse --short HEAD 2>/dev/null || echo desconocido)"
} > "$DESTINO/descripcion.txt"
echo "Errores en el launch.log:"
grep -E "\[ERROR\]|process has died" "$DESTINO/launch.log" | grep -v "base_nivelada.*KeyboardInterrupt" | head -10 || echo "  ninguno"
