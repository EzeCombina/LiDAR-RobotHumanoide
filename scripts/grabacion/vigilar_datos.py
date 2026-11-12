#!/usr/bin/env python3
# =============================================================================
# vigilar_datos.py — Avisa si el LiDAR deja de enviar datos durante una grabación
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe a /unilidar/cloud y, si pasa más de 1,5 s sin recibir una nube
#   (lo normal es una cada 83 ms), muestra un aviso en la terminal y hace sonar
#   la campana del sistema (carácter BEL) cada 2 segundos, hasta que vuelvan
#   los datos. Cuando vuelven, también lo informa.
#
#   Causas típicas: se desconecta o afloja el cable Ethernet o el de
#   alimentación, o se desconecta el sensor creyendo que la grabación ya se
#   había cortado (Ctrl+C mal apretado). Sin este aviso, la grabación queda
#   abierta sin datos y no se nota (pasó el 2026-11-12).
#
#   Lo usa scripts/grabacion/grabar_lidar.sh; también se puede usar solo.
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/grabacion/vigilar_datos.py          (Ctrl+C para terminar)
# =============================================================================
import sys
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2

SIN_DATOS = 1.5   # segundos sin nubes para considerar que se cortaron los datos
REPETIR = 2.0     # segundos entre avisos mientras sigue el corte


def main():
    rclpy.init()
    nodo = Node("vigilar_datos")
    estado = {"ultimo": time.monotonic(), "cortado": False, "aviso": 0.0, "inicio_corte": 0.0}

    def recibir(_):
        ahora = time.monotonic()
        if estado["cortado"]:
            print(f"\n*** Los datos del LiDAR VOLVIERON después de "
                  f"{ahora - estado['inicio_corte']:.0f} s sin datos. ***\n", file=sys.stderr, flush=True)
            estado["cortado"] = False
        estado["ultimo"] = ahora

    def revisar():
        ahora = time.monotonic()
        if ahora - estado["ultimo"] > SIN_DATOS:
            if not estado["cortado"]:
                estado["cortado"] = True
                estado["inicio_corte"] = estado["ultimo"]
            if ahora - estado["aviso"] >= REPETIR:
                estado["aviso"] = ahora
                print(f"\a\n*** ATENCIÓN: NO LLEGAN DATOS DEL LiDAR desde hace "
                      f"{ahora - estado['inicio_corte']:.0f} s. Revisar el cable Ethernet y la "
                      f"alimentación.\n*** Si ya terminaste: la grabación SIGUE ABIERTA, cortala con "
                      f"Ctrl+C y esperá el resumen antes de desconectar el sensor. ***\n", file=sys.stderr, flush=True)

    nodo.create_subscription(PointCloud2, "/unilidar/cloud", recibir, qos_profile_sensor_data)
    nodo.create_timer(0.5, revisar)
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
