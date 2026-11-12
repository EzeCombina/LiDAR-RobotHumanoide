#!/usr/bin/env python3
# =============================================================================
# registrar_trayectoria.py — Guarda la trayectoria estimada por Point-LIO
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe a la odometría de Point-LIO (/aft_mapped_to_init) y guarda la
#   posición y orientación del sensor en un CSV, a lo sumo 10 veces por segundo
#   (Point-LIO la publica a miles de mensajes por segundo).
#   Al terminar (Ctrl+C o SIGTERM) imprime un resumen:
#     - duración y largo del recorrido;
#     - tamaño de la zona recorrida;
#     - ERROR DE CIERRE: distancia entre la posición final y la inicial. Si el
#       recorrido empezó y terminó en el mismo lugar, debería ser de pocos cm;
#       es un buen indicador de la calidad del mapa.
#
#   Lo usa scripts/procesar_grabacion.sh; también se puede usar solo.
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/registrar_trayectoria.py <salida.csv>
# =============================================================================
import math
import signal
import sys

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node

PERIODO_MIN = 0.1  # segundos entre muestras guardadas (10 Hz)


def main():
    if len(sys.argv) < 2:
        print("Uso: registrar_trayectoria.py <salida.csv>")
        sys.exit(1)
    archivo = open(sys.argv[1], "w")
    archivo.write("t,x,y,z,qx,qy,qz,qw\n")
    muestras = []

    rclpy.init()
    nodo = Node("registrar_trayectoria")

    def recibir(m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if muestras and t - muestras[-1][0] < PERIODO_MIN:
            return
        p, q = m.pose.pose.position, m.pose.pose.orientation
        muestras.append((t, p.x, p.y, p.z))
        archivo.write(f"{t:.6f},{p.x:.4f},{p.y:.4f},{p.z:.4f},"
                      f"{q.x:.5f},{q.y:.5f},{q.z:.5f},{q.w:.5f}\n")

    nodo.create_subscription(Odometry, "/aft_mapped_to_init", recibir, 1000)

    seguir = [True]

    def terminar(*_):
        seguir[0] = False

    signal.signal(signal.SIGINT, terminar)
    signal.signal(signal.SIGTERM, terminar)
    while seguir[0]:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    archivo.close()
    nodo.destroy_node()
    rclpy.try_shutdown()

    if len(muestras) < 2:
        print("Trayectoria: sin datos de odometría.")
        return
    largo = sum(math.dist(a[1:], b[1:]) for a, b in zip(muestras, muestras[1:]))
    cierre = math.dist(muestras[0][1:], muestras[-1][1:])
    xs, ys, zs = zip(*[m[1:] for m in muestras])
    print(f"Trayectoria: {len(muestras)} muestras, {muestras[-1][0] - muestras[0][0]:.1f} s")
    print(f"Largo del recorrido: {largo:.2f} m")
    print(f"Zona recorrida (x, y, z): {max(xs) - min(xs):.2f} x {max(ys) - min(ys):.2f} x "
          f"{max(zs) - min(zs):.2f} m")
    print(f"Error de cierre (final vs. inicio): {cierre:.3f} m "
          f"(horizontal {math.dist(muestras[0][1:3], muestras[-1][1:3]):.3f} m, "
          f"vertical {muestras[-1][3] - muestras[0][3]:+.3f} m)")


if __name__ == "__main__":
    main()
