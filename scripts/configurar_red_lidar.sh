#!/usr/bin/env bash
# =============================================================================
# configurar_red_lidar.sh — Red de la PC para el LiDAR Unitree L2
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Crea (o actualiza) un perfil de NetworkManager llamado "lidar-l2" en la
#      placa Ethernet indicada, con IP fija y SIN puerta de enlace. Así el
#      tráfico de internet sigue saliendo por el Wi-Fi y por la placa del LiDAR
#      solo pasa la red del sensor.
#   2. Si el firewall ufw está activo, abre el puerto UDP de llegada de datos
#      (6201) solamente en esa placa. Este paso usa sudo y pide la contraseña.
#
# No modifica ni borra otros perfiles de red. El perfil "lidar-l2" tiene
# prioridad 10: cuando se conecta el cable, gana sobre el perfil por DHCP que
# Ubuntu crea por defecto (prioridad -999).
#
# Cómo se usa:
#   ./scripts/configurar_red_lidar.sh <placa> [ip_de_la_pc/máscara]
#
#   Ejemplos:
#   ./scripts/configurar_red_lidar.sh eno1                     # red de fábrica: 192.168.1.2/24
#   ./scripts/configurar_red_lidar.sh eno1 192.168.10.2/24     # si se cambió la red del sensor
#
# Para deshacerlo:
#   nmcli connection delete lidar-l2
#   sudo ufw delete allow in on <placa> to any port 6201 proto udp
# =============================================================================
set -euo pipefail

PERFIL="lidar-l2"
PUERTO_UDP=6201          # puerto de la PC donde el sensor envía los datos

PLACA="${1:-}"
IP_PC="${2:-192.168.1.2/24}"   # valor de fábrica que espera el L2

if [ -z "$PLACA" ]; then
    echo "Uso: $0 <placa> [ip_de_la_pc/máscara]"
    echo "Placas disponibles:"
    ip -br link | awk '$1 != "lo" {print "  " $1}'
    exit 1
fi

if [ ! -d "/sys/class/net/$PLACA" ]; then
    echo "ERROR: no existe la placa '$PLACA'. Revisar con: ip -br link"
    exit 1
fi

# Aviso de choque de redes: otra placa con una dirección en la misma red.
RED_PC=$(echo "$IP_PC" | cut -d/ -f1 | cut -d. -f1-3)
if ip -br addr | grep -v "^$PLACA " | grep -q " ${RED_PC}\."; then
    echo "ATENCIÓN: otra placa ya tiene una dirección ${RED_PC}.x:"
    ip -br addr | grep -v "^$PLACA " | grep " ${RED_PC}\."
    echo "Hay choque de redes. Cambiar la red del sensor (ver docs/pasos/02_conexion_ethernet.md)."
    exit 1
fi

echo "== 1. Perfil de red '$PERFIL' en $PLACA con IP $IP_PC"
if nmcli -t -f NAME connection show | grep -qx "$PERFIL"; then
    echo "   El perfil ya existe: se actualiza."
else
    nmcli connection add type ethernet con-name "$PERFIL" ifname "$PLACA"
fi
nmcli connection modify "$PERFIL" \
    connection.interface-name "$PLACA" \
    connection.autoconnect yes \
    connection.autoconnect-priority 10 \
    ipv4.method manual \
    ipv4.addresses "$IP_PC" \
    ipv4.gateway "" \
    ipv4.never-default yes \
    ipv6.method disabled

# Activa el perfil. Sin cable conectado falla, pero queda guardado y se activa
# solo al conectar el sensor.
if nmcli connection up "$PERFIL" >/dev/null 2>&1; then
    echo "   Perfil activo."
else
    echo "   No se pudo activar ahora (¿el cable o el sensor no están conectados?)."
    echo "   Queda guardado y se activa solo al conectar el cable."
fi

echo "== 2. Firewall"
if systemctl is-active --quiet ufw; then
    echo "   ufw está activo: se abre UDP $PUERTO_UDP en $PLACA (pide contraseña de sudo)."
    sudo ufw allow in on "$PLACA" to any port "$PUERTO_UDP" proto udp comment "LiDAR Unitree L2"
else
    echo "   ufw no está activo: no hace falta abrir puertos."
fi

echo "== Estado final"
ip -br addr show "$PLACA"
