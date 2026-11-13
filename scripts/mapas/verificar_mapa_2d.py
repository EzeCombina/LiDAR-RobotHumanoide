#!/usr/bin/env python3
# =============================================================================
# verificar_mapa_2d.py — Comprueba cómo interpreta Nav2 un mapa 2D
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe al tópico /map (el que publica nav2_map_server con el mapa
#   cargado) y muestra el tamaño, la resolución, el origen y qué porcentaje de
#   celdas recibe Nav2 como ocupadas (100), libres (0) y desconocidas (-1).
#   Los porcentajes tienen que coincidir con los que informó generar_mapa_2d.py.
#   Si no coinciden (o aparecen "otros valores"), los umbrales del .yaml
#   (occupied_thresh / free_thresh) no son los correctos.
#
# Requisitos: nav2_map_server corriendo y activado con el mapa (lo hace
#             ver_mapa_2d.sh, o los comandos manuales del paso 07).
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/mapas/verificar_mapa_2d.py
# =============================================================================
import sys

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


def main():
    rclpy.init()
    nodo = Node("verificar_mapa_2d")
    recibido = {}
    # nav2_map_server publica /map una sola vez, con durabilidad "transient local":
    # hay que suscribirse con la misma durabilidad para recibir el último mensaje.
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    nodo.create_subscription(OccupancyGrid, "/map", lambda m: recibido.update(m=m), qos)
    for _ in range(20):
        rclpy.spin_once(nodo, timeout_sec=0.5)
        if "m" in recibido:
            break
    if "m" not in recibido:
        print("ERROR: no llegó ningún mapa en /map. ¿Está nav2_map_server cargado y activado?")
        sys.exit(1)
    m = recibido["m"]
    d = np.array(m.data)
    i = m.info
    print(f"Mapa en /map: {i.width} x {i.height} celdas de {i.resolution * 100:.0f} cm "
          f"({i.width * i.resolution:.2f} x {i.height * i.resolution:.2f} m), "
          f"origen ({i.origin.position.x:.3f}, {i.origin.position.y:.3f}), marco '{m.header.frame_id}'")
    print(f"Nav2 recibe: ocupadas (100) {100 * np.mean(d == 100):.1f} %, libres (0) "
          f"{100 * np.mean(d == 0):.1f} %, desconocidas (-1) {100 * np.mean(d == -1):.1f} %, "
          f"otros valores {100 * np.mean(~np.isin(d, [0, 100, -1])):.1f} %")
    nodo.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
