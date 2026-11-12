#!/usr/bin/env python3
# =============================================================================
# publicar_trayectoria.py — Muestra en RViz la trayectoria de un mapa
# -----------------------------------------------------------------------------
# Qué hace:
#   Lee el CSV de trayectoria que genera procesar_grabacion.sh
#   (mapas/<mapa>_trayectoria.csv) y lo publica cada 2 segundos:
#     - /trayectoria          (nav_msgs/Path): el recorrido del sensor;
#     - /trayectoria_extremos (visualization_msgs/MarkerArray): una esfera
#       VERDE en el punto de partida y una ROJA en el de llegada. La distancia
#       entre ambas es el error de cierre.
#   Todo en el marco "map", el mismo que usa ver_mapa.sh para el .pcd (la
#   trayectoria y el mapa de Point-LIO están en el mismo sistema de coordenadas).
#
#   Lo usa scripts/ver_mapa.sh; también se puede usar solo, con RViz abierto.
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/publicar_trayectoria.py mapas/<mapa>_trayectoria.csv
#   (Ctrl+C para terminar)
# =============================================================================
import csv
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.executors import ExternalShutdownException
from nav_msgs.msg import Path
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray


def leer_csv(ruta):
    with open(ruta) as f:
        return [{k: float(v) for k, v in fila.items()} for fila in csv.DictReader(f)]


def main():
    if len(sys.argv) < 2:
        print("Uso: publicar_trayectoria.py <trayectoria.csv>")
        sys.exit(1)
    filas = leer_csv(sys.argv[1])
    if not filas:
        print("ERROR: la trayectoria está vacía.")
        sys.exit(1)

    rclpy.init()
    nodo = Node("publicar_trayectoria")
    pub_path = nodo.create_publisher(Path, "/trayectoria", 1)
    pub_marcas = nodo.create_publisher(MarkerArray, "/trayectoria_extremos", 1)

    path = Path()
    path.header.frame_id = "map"
    for f in filas:
        p = PoseStamped()
        p.header.frame_id = "map"
        p.pose.position.x, p.pose.position.y, p.pose.position.z = f["x"], f["y"], f["z"]
        p.pose.orientation.x, p.pose.orientation.y = f["qx"], f["qy"]
        p.pose.orientation.z, p.pose.orientation.w = f["qz"], f["qw"]
        path.poses.append(p)

    marcas = MarkerArray()
    for i, (f, color) in enumerate(((filas[0], (0.0, 1.0, 0.0)), (filas[-1], (1.0, 0.0, 0.0)))):
        m = Marker()
        m.header.frame_id = "map"
        m.ns, m.id, m.type, m.action = "extremos", i, Marker.SPHERE, Marker.ADD
        m.pose.position.x, m.pose.position.y, m.pose.position.z = f["x"], f["y"], f["z"]
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = m.scale.z = 0.15
        m.color.r, m.color.g, m.color.b = color
        m.color.a = 1.0
        marcas.markers.append(m)

    def publicar():
        ahora = nodo.get_clock().now().to_msg()
        path.header.stamp = ahora
        for m in marcas.markers:
            m.header.stamp = ahora
        pub_path.publish(path)
        pub_marcas.publish(marcas)

    nodo.create_timer(2.0, publicar)
    publicar()
    print(f"Publicando {len(filas)} poses en /trayectoria (verde = partida, rojo = llegada). "
          "Ctrl+C para terminar.")
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl+C o cierre desde ver_mapa.sh
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
