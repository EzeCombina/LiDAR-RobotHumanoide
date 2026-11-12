#!/usr/bin/env python3
# =============================================================================
# revisar_grabacion.py — Revisa que una grabación del L2 esté completa
# -----------------------------------------------------------------------------
# Qué hace:
#   Lee una grabación de ROS 2 (carpeta con metadata.yaml y .mcap) y muestra,
#   para cada tópico:
#     - cantidad de mensajes y frecuencia promedio;
#     - intervalo medio y máximo entre mensajes;
#     - "huecos": intervalos mayores a 3 veces el intervalo medio (por ejemplo,
#       si se cortó el cable de red durante la grabación).
#   Valores esperados para el L2: /unilidar/cloud ~12 Hz (83 ms) y
#   /unilidar/imu ~250 Hz (4 ms).
#
#   No necesita el sensor ni el driver. Solo lee el archivo.
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/revisar_grabacion.py bags/<carpeta>
# =============================================================================
import sys

import numpy as np
import rosbag2_py
import yaml


def main():
    if len(sys.argv) < 2:
        print("Uso: revisar_grabacion.py <carpeta_de_la_grabación>")
        sys.exit(1)
    carpeta = sys.argv[1].rstrip("/")
    try:
        meta = yaml.safe_load(open(f"{carpeta}/metadata.yaml"))
    except OSError:
        print(f"ERROR: '{carpeta}' no tiene metadata.yaml (¿es una grabación de ROS 2?)")
        sys.exit(1)
    formato = meta["rosbag2_bagfile_information"]["storage_identifier"]

    lector = rosbag2_py.SequentialReader()
    lector.open(rosbag2_py.StorageOptions(uri=carpeta, storage_id=formato),
                rosbag2_py.ConverterOptions("cdr", "cdr"))
    tiempos = {}
    while lector.has_next():
        topico, _, t = lector.read_next()
        tiempos.setdefault(topico, []).append(t * 1e-9)

    print(f"Grabación: {carpeta} (formato {formato})")
    hay_huecos = False
    for topico, lista in sorted(tiempos.items()):
        t = np.array(lista)
        if len(t) < 2:
            print(f"\n{topico}: {len(t)} mensaje(s), no alcanza para analizar")
            continue
        dt = np.diff(t)
        medio = dt.mean()
        print(f"\n{topico}")
        print(f"  mensajes: {len(t)} en {t[-1] - t[0]:.2f} s -> {len(t) / (t[-1] - t[0]):.2f} por segundo")
        print(f"  intervalo medio: {medio * 1000:.1f} ms | máximo: {dt.max() * 1000:.1f} ms")
        huecos = np.where(dt > 3 * medio)[0]
        if len(huecos):
            hay_huecos = True
            print(f"  HUECOS ({len(huecos)}): ", end="")
            print(", ".join(f"a los {t[i] - t[0]:.1f} s ({dt[i]:.2f} s)" for i in huecos[:10]))
        else:
            print("  sin huecos")

    print("\nResultado:", "HAY HUECOS: revisar la grabación" if hay_huecos else "grabación completa")


if __name__ == "__main__":
    main()
