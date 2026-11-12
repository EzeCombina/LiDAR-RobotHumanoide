#!/usr/bin/env python3
# =============================================================================
# verificar_udp_lidar.py — Verifica que llegan los datos del LiDAR L2 por Ethernet
# -----------------------------------------------------------------------------
# Qué hace:
#   Escucha el puerto UDP donde el sensor envía sus datos (6201 por defecto)
#   durante unos segundos y muestra, por cada segundo, cuántos paquetes llegaron
#   de cada tamaño. NO le envía nada al sensor: solo escucha.
#
#   Es una alternativa sin sudo a "sudo tcpdump -i <placa> udp port 6201".
#   Si este script recibe paquetes, quiere decir que la red está bien
#   configurada y que el firewall deja pasar los datos.
#
#   Tamaños observados con el firmware 2.8.11.1 (2026-11-12):
#     1044 bytes ~205/s  -> puntos de la nube 3D
#       80 bytes ~240/s  -> IMU (puede no aparecer hasta que un programa del SDK
#                           o el driver se conecte al sensor)
#     1124 bytes  ~11/s  -> tipo no identificado (A VERIFICAR)
#
# Cómo se usa:
#   ./scripts/verificar_udp_lidar.py                     # 5 s en 192.168.1.2:6201
#   ./scripts/verificar_udp_lidar.py --segundos 10
#   ./scripts/verificar_udp_lidar.py --ip 192.168.10.2   # si se cambió la red
#
# Importante: cerrar antes el driver o los ejemplos del SDK, porque usan el
# mismo puerto ("Address already in use").
# =============================================================================
import argparse
import collections
import socket
import sys
import time


def main():
    p = argparse.ArgumentParser(description="Cuenta los paquetes UDP del LiDAR L2.")
    p.add_argument("--ip", default="192.168.1.2", help="IP de la PC en la placa del LiDAR")
    p.add_argument("--puerto", type=int, default=6201, help="puerto UDP de la PC")
    p.add_argument("--segundos", type=float, default=5.0, help="duración de la escucha")
    a = p.parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind((a.ip, a.puerto))
    except OSError as e:
        print(f"ERROR al abrir {a.ip}:{a.puerto}: {e}")
        print("¿La PC tiene esa IP (ip -br addr)? ¿Hay otro programa usando el puerto?")
        sys.exit(1)
    s.settimeout(0.5)

    print(f"Escuchando {a.ip}:{a.puerto} durante {a.segundos:.0f} s...")
    por_segundo = collections.defaultdict(collections.Counter)
    origenes = set()
    total_bytes = 0
    t0 = time.time()
    while time.time() - t0 < a.segundos:
        try:
            datos, origen = s.recvfrom(65535)
        except socket.timeout:
            continue
        por_segundo[int(time.time() - t0)][len(datos)] += 1
        origenes.add(f"{origen[0]}:{origen[1]}")
        total_bytes += len(datos)

    if not por_segundo:
        print("No llegó ningún paquete. Revisar: alimentación del sensor, cable, IP de la PC,")
        print("firewall (puerto UDP abierto) y que el sensor esté en modo Ethernet.")
        sys.exit(2)

    print("segundo  paquetes por tamaño (bytes: cantidad)")
    for seg in sorted(por_segundo):
        detalle = ", ".join(f"{t}: {n}" for t, n in sorted(por_segundo[seg].items()))
        print(f"{seg:7d}  {detalle}")
    print(f"Origen: {', '.join(sorted(origenes))}")
    print(f"Tráfico promedio: {total_bytes * 8 / a.segundos / 1e6:.2f} Mbit/s")


if __name__ == "__main__":
    main()
