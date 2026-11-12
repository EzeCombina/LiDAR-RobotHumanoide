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
#   Además compara el último dato recibido con la hora de fin de la grabación
#   (descripcion.txt, lo escribe grabar_lidar.sh): si el sensor dejó de enviar
#   datos antes del final (cable desconectado o sin alimentación hasta que se
#   cortó la grabación), lo informa. Ese corte no aparece como "hueco".
#   Valores esperados para el L2: /unilidar/cloud ~12 Hz (83 ms) y
#   /unilidar/imu ~250 Hz (4 ms).
#   Además revisa el ARRANQUE: en los primeros 4 s de IMU calcula cuánto se
#   movió el sensor (desvío del giróscopo) y hacia dónde apunta la gravedad.
#   Point-LIO mide la gravedad al empezar y con eso nivela todo el mapa: si el
#   sensor no estaba quieto, el mapa puede quedar inclinado.
#
#   No necesita el sensor ni el driver. Solo lee el archivo.
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/grabacion/revisar_grabacion.py bags/<carpeta>
# =============================================================================
import os
import sys
from datetime import datetime

import numpy as np
import rosbag2_py
import yaml
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Imu

SEGUNDOS_ARRANQUE = 4.0
MARGEN_FINAL = 5.0  # s: tolerancia entre el último dato y el fin de la grabación
GIRO_QUIETO = 0.1  # rad/s: desvío del giróscopo por debajo del cual se considera "quieto"


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
    acel, giro = [], []
    while lector.has_next():
        topico, datos, t = lector.read_next()
        tiempos.setdefault(topico, []).append(t * 1e-9)
        if topico == "/unilidar/imu" and t * 1e-9 - tiempos[topico][0] <= SEGUNDOS_ARRANQUE:
            m = deserialize_message(datos, Imu)
            acel.append([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z])
            giro.append([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])

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

    # ¿Siguieron llegando datos hasta el final? (hora de fin según descripcion.txt)
    cortada = False
    ruta_desc = os.path.join(carpeta, "descripcion.txt")
    if os.path.isfile(ruta_desc) and "/unilidar/cloud" in tiempos:
        horas = {}
        for linea in open(ruta_desc):
            if linea.startswith(("Inicio:", "Fin:")):
                clave, valor = linea.split(":", 1)
                horas[clave] = datetime.strptime(valor.strip(), "%Y-%m-%d %H:%M:%S").timestamp()
        if "Inicio" in horas and "Fin" in horas:
            ultimo = tiempos["/unilidar/cloud"][-1]
            print(f"\nDuración de la grabación (descripcion.txt): {horas['Fin'] - horas['Inicio']:.0f} s"
                  f" | último dato a los {ultimo - horas['Inicio']:.0f} s"
                  f" ({datetime.fromtimestamp(ultimo).strftime('%H:%M:%S')})")
            if horas["Fin"] - ultimo > MARGEN_FINAL:
                cortada = True
                print(f"  ATENCIÓN: no llegaron datos durante los últimos {horas['Fin'] - ultimo:.0f} s."
                      " El sensor dejó de enviar datos (¿cable desconectado o sin alimentación?).")
                print("  Solo sirve la parte grabada antes del corte.")

    if hay_huecos or cortada:
        print("\nResultado: GRABACIÓN INCOMPLETA: revisar los avisos de arriba")
    else:
        print("\nResultado: grabación completa")

    if len(acel) > 10:
        a, g = np.array(acel).mean(axis=0), np.array(giro).std(axis=0)
        eje = int(np.argmax(np.abs(a)))
        otros = [i for i in range(3) if i != eje]
        angulo = np.degrees(np.arctan2(np.linalg.norm(a[otros]), abs(a[eje])))
        quieto = g.max() < GIRO_QUIETO
        print(f"\nArranque (primeros {SEGUNDOS_ARRANQUE:.0f} s de IMU, {len(acel)} muestras):")
        print(f"  aceleración media [m/s²]: x={a[0]:.2f} y={a[1]:.2f} z={a[2]:.2f} "
              f"(módulo {np.linalg.norm(a):.2f})")
        print(f"  gravedad sobre el eje {'xyz'[eje]} del sensor, a {angulo:.1f}° de ese eje")
        print(f"  desvío del giróscopo [rad/s]: x={g[0]:.3f} y={g[1]:.3f} z={g[2]:.3f} "
              f"-> {'QUIETO' if quieto else 'EN MOVIMIENTO'} (límite {GIRO_QUIETO} rad/s)")
        if not quieto:
            print("  ATENCIÓN: el sensor se movía al empezar. El mapa puede quedar inclinado;")
            print("  conviene repetir la grabación arrancando con el sensor apoyado y quieto.")


if __name__ == "__main__":
    main()
