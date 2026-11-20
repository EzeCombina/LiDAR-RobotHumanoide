#!/usr/bin/env python3
# =============================================================================
# filtro_cuerpo.py — Quita de la nube los puntos del propio robot
# -----------------------------------------------------------------------------
# Qué hace:
#   El LiDAR montado en el robot ve partes del propio robot (torso, brazos,
#   piernas). Si esos puntos llegan a Nav2, el robot se ve a sí mismo como un
#   obstáculo pegado a él y no se mueve (el collision_monitor lo frena: se
#   comprobó en la simulación, 2026-11-20). Este nodo:
#     1. Recibe la nube (--entrada) y busca la transformada de su marco al marco
#        del robot (base_footprint) en el instante de la nube.
#     2. Descarta los puntos que caen dentro de la CAJA DEL CUERPO (en
#        base_footprint) y los que no son números (NaN, infinito).
#     3. Publica la nube filtrada (--salida) en el MISMO marco que la original
#        (el del sensor), para que Nav2 trace los rayos desde el sensor.
#
# Parámetros (ROS):
#   entrada   nube original (/cloud_registered_body con el L2, /lidar/points en Gazebo)
#   salida    nube filtrada (/nube_obstaculos)
#   caja      [x_min, x_max, y_min, y_max, z_min, z_max] del cuerpo en m, en
#             base_footprint. Por defecto [-0.20, 0.20, -0.28, 0.28, -0.05, 1.70]
#             (R1 aproximado, A VERIFICAR; con el sensor en la mano no hace falta).
#
# Cómo se usa (normalmente lo lanza navegacion.launch.py):
#   python3 scripts/navegacion/filtro_cuerpo.py --ros-args -p entrada:=/lidar/points
# =============================================================================
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformException, TransformListener


def matriz(t):
    """Matriz 4x4 de una geometry_msgs/Transform."""
    q, p = t.rotation, t.translation
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), p.x],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), p.y],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), p.z],
        [0, 0, 0, 1]])


class FiltroCuerpo(Node):
    def __init__(self):
        super().__init__("filtro_cuerpo")
        self.declare_parameter("entrada", "/cloud_registered_body")
        self.declare_parameter("salida", "/nube_obstaculos")
        self.declare_parameter("marco_robot", "base_footprint")
        self.declare_parameter("caja", [-0.20, 0.20, -0.28, 0.28, -0.05, 1.70])
        g = lambda n: self.get_parameter(n).value  # noqa: E731
        self.marco = g("marco_robot")
        self.caja = [float(v) for v in g("caja")]
        self.tf = Buffer()
        # spin_thread=True: las transformadas se reciben en un hilo aparte.
        self.escucha = TransformListener(self.tf, self, spin_thread=True)
        self.pub = self.create_publisher(PointCloud2, g("salida"), qos_profile_sensor_data)
        self.create_subscription(PointCloud2, g("entrada"), self.al_recibir, qos_profile_sensor_data)
        self.avisado = False
        self.get_logger().info(f"{g('entrada')} -> {g('salida')}; caja del cuerpo {self.caja} en {self.marco}")

    def al_recibir(self, msg):
        # Sin esperas (una espera con el reloj de una grabación puede colgar el
        # nodo): la transformada del instante de la nube y, si todavía no llegó
        # (unos milisegundos), la más reciente. A 0,3 m/s, 10 ms son 3 mm.
        try:
            t = self.tf.lookup_transform(self.marco, msg.header.frame_id, Time.from_msg(msg.header.stamp))
        except TransformException:
            try:
                t = self.tf.lookup_transform(self.marco, msg.header.frame_id, Time())
            except TransformException as e:
                if not self.avisado:
                    self.get_logger().warn(f"sin transformada {msg.header.frame_id} -> {self.marco}: {e}")
                    self.avisado = True
                return
        xyz = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True)
        xyz = xyz[np.isfinite(xyz).all(axis=1)]
        T = matriz(t.transform)
        en_robot = xyz @ T[:3, :3].T + T[:3, 3]
        x0, x1, y0, y1, z0, z1 = self.caja
        dentro = ((en_robot[:, 0] > x0) & (en_robot[:, 0] < x1) & (en_robot[:, 1] > y0) & (en_robot[:, 1] < y1)
                  & (en_robot[:, 2] > z0) & (en_robot[:, 2] < z1))
        salida = point_cloud2.create_cloud_xyz32(msg.header, xyz[~dentro].astype(np.float32))
        self.pub.publish(salida)


def main():
    rclpy.init()
    nodo = FiltroCuerpo()
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
