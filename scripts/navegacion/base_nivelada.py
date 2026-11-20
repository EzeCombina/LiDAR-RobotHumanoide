#!/usr/bin/env python3
# =============================================================================
# base_nivelada.py — Odometría del robot (odom -> base_footprint) a partir de Point-LIO
# -----------------------------------------------------------------------------
# Qué hace:
#   Point-LIO estima la posición del SENSOR (marco "body", la IMU del L2) en su
#   propio marco fijo "pointlio_odom" (origen donde arrancó el sensor, eje z
#   alineado con la gravedad). Nav2 necesita la posición del ROBOT sobre el piso,
#   sin inclinación. Este nodo:
#     1. Publica la transformada fija odom -> pointlio_odom, subiendo el origen
#        de Point-LIO a la altura inicial del sensor sobre el piso. Así, en el
#        marco "odom" el piso queda en z = 0 (las alturas de obstáculos de Nav2
#        se miden desde el piso).
#     2. Con cada odometría de Point-LIO calcula la pose de base_link
#        (cuerpo del robot) usando el montaje del sensor, y publica
#        odom -> base_footprint: misma posición x, y; z = 0; solo el giro
#        alrededor de la vertical (yaw). Es un marco NIVELADO: no cabecea aunque
#        el torso del robot (o la mano) se incline.
#     3. Publica la odometría en /odom (nav_msgs/Odometry), con la velocidad
#        expresada en base_footprint (la usa el controlador de Nav2).
#
# Árbol de marcos resultante:
#   map -(AMCL)-> odom -(este nodo, fija)-> pointlio_odom -(Point-LIO)-> body
#                 odom -(este nodo)-> base_footprint
#
# Parámetros:
#   altura_inicial  altura del sensor sobre el piso al arrancar Point-LIO, en m.
#   montaje_xyz     posición del sensor (IMU) en base_link, en m [x, y, z].
#   montaje_rpy     orientación del sensor en base_link, en rad [roll, pitch, yaw].
#                   Con el robot salen del CAD del soporte. En la mano: [0,0,0]
#                   (base_link = el sensor).
#   eje_adelante    dirección "adelante" en base_link para calcular el yaw.
#                   Robot: [1, 0, 0]. En la mano con el sensor vertical (cúpula
#                   hacia adelante) conviene [1, 0, 1]: es horizontal tanto con
#                   el sensor apoyado como levantado en vertical.
#   frecuencia_max  límite de publicación en Hz (Point-LIO publica a la
#                   frecuencia de la IMU, unos 250 Hz).
#   topico_odom_pointlio  odometría de entrada (/aft_mapped_to_init).
#
# Requisitos: Point-LIO lanzado con odom_header_frame_id=pointlio_odom y
#             odom_child_frame_id=body (lo hace lidar_odometria.launch.py).
#
# Cómo se usa (normalmente lo lanza scripts/navegacion/lidar_odometria.launch.py):
#   python3 scripts/navegacion/base_nivelada.py --ros-args -p altura_inicial:=0.87
# =============================================================================
import math

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster


def matriz_de_cuaternion(x, y, z, w):
    """Matriz de rotación 3x3 de un cuaternión (x, y, z, w)."""
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def matriz_de_rpy(r, p, y):
    """Matriz de rotación de roll, pitch, yaw (convención de ROS: Rz·Ry·Rx)."""
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ])


def normalizar_angulo(a):
    return math.atan2(math.sin(a), math.cos(a))


class BaseNivelada(Node):
    def __init__(self):
        super().__init__("base_nivelada")
        self.declare_parameter("altura_inicial", 0.0)
        self.declare_parameter("montaje_xyz", [0.0, 0.0, 0.0])
        self.declare_parameter("montaje_rpy", [0.0, 0.0, 0.0])
        self.declare_parameter("eje_adelante", [1.0, 0.0, 0.0])
        self.declare_parameter("frecuencia_max", 50.0)
        self.declare_parameter("topico_odom_pointlio", "/aft_mapped_to_init")
        self.declare_parameter("marco_odom", "odom")
        self.declare_parameter("marco_pointlio", "pointlio_odom")
        self.declare_parameter("marco_base", "base_footprint")

        g = lambda n: self.get_parameter(n).value  # noqa: E731
        self.marco_odom, self.marco_base = g("marco_odom"), g("marco_base")
        self.altura = float(g("altura_inicial"))
        # Pose del sensor (body) en base_link: T_base_body = [R_m | t_m]
        self.R_m = matriz_de_rpy(*[float(v) for v in g("montaje_rpy")])
        self.t_m = np.array([float(v) for v in g("montaje_xyz")])
        self.adelante = np.array([float(v) for v in g("eje_adelante")])
        self.periodo_min = 1.0 / float(g("frecuencia_max"))

        # 1. Transformada fija odom -> pointlio_odom (piso en z = 0)
        self.estatica = StaticTransformBroadcaster(self)
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.marco_odom
        t.child_frame_id = g("marco_pointlio")
        t.transform.translation.z = self.altura
        t.transform.rotation.w = 1.0
        self.estatica.sendTransform(t)

        self.tf = TransformBroadcaster(self)
        self.pub_odom = self.create_publisher(Odometry, "/odom", 20)
        self.create_subscription(Odometry, g("topico_odom_pointlio"), self.al_recibir, 50)

        self.anterior = None      # (tiempo, x, y, yaw) de la última pose publicada
        self.yaw = 0.0
        self.velocidad = np.zeros(3)  # vx, vy, wz filtradas (en base_footprint)
        self.get_logger().info(
            f"altura_inicial={self.altura:.3f} m, montaje_xyz={self.t_m.tolist()}, "
            f"eje_adelante={self.adelante.tolist()}")

    def al_recibir(self, msg):
        tiempo = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self.anterior is not None and tiempo - self.anterior[0] < self.periodo_min:
            return

        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        # Pose del sensor en odom (se suma la altura inicial)
        R_s = matriz_de_cuaternion(q.x, q.y, q.z, q.w)
        t_s = np.array([p.x, p.y, p.z + self.altura])
        # Pose de base_link en odom: T_odom_base = T_odom_body · inv(T_base_body)
        R_b = R_s @ self.R_m.T
        t_b = t_s - R_b @ self.t_m

        # Yaw: dirección "adelante" del robot proyectada sobre el plano horizontal
        d = R_b @ self.adelante
        if math.hypot(d[0], d[1]) > 0.2 * np.linalg.norm(self.adelante):
            self.yaw = math.atan2(d[1], d[0])
        # (si "adelante" queda casi vertical se conserva el yaw anterior)

        # Velocidad en base_footprint, por diferencias, con un filtro simple
        if self.anterior is not None:
            dt = tiempo - self.anterior[0]
            if 0.0 < dt < 0.5:
                dx, dy = t_b[0] - self.anterior[1], t_b[1] - self.anterior[2]
                c, s = math.cos(self.yaw), math.sin(self.yaw)
                medida = np.array([(c * dx + s * dy) / dt, (-s * dx + c * dy) / dt,
                                   normalizar_angulo(self.yaw - self.anterior[3]) / dt])
                self.velocidad = 0.7 * self.velocidad + 0.3 * medida
        self.anterior = (tiempo, t_b[0], t_b[1], self.yaw)

        qz, qw = math.sin(self.yaw / 2), math.cos(self.yaw / 2)
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = self.marco_odom
        t.child_frame_id = self.marco_base
        t.transform.translation.x, t.transform.translation.y = float(t_b[0]), float(t_b[1])
        t.transform.rotation.z, t.transform.rotation.w = qz, qw
        self.tf.sendTransform(t)

        o = Odometry()
        o.header = t.header
        o.child_frame_id = self.marco_base
        o.pose.pose.position.x, o.pose.pose.position.y = float(t_b[0]), float(t_b[1])
        o.pose.pose.orientation.z, o.pose.pose.orientation.w = qz, qw
        o.twist.twist.linear.x, o.twist.twist.linear.y = float(self.velocidad[0]), float(self.velocidad[1])
        o.twist.twist.angular.z = float(self.velocidad[2])
        self.pub_odom.publish(o)


def main():
    rclpy.init()
    nodo = BaseNivelada()
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass   # Ctrl+C o cierre del launch: salir sin mensajes de error
    finally:
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
