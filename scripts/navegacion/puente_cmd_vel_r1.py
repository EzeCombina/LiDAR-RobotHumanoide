#!/usr/bin/env python3
# =============================================================================
# puente_cmd_vel_r1.py — Velocidades de Nav2 (/cmd_vel) hacia la marcha del R1
# -----------------------------------------------------------------------------
# Qué hace:
#   Nav2 pide velocidades en el tópico /cmd_vel (geometry_msgs/Twist): hacia
#   adelante (linear.x), de costado (linear.y) y de giro (angular.z). El R1 no
#   entiende ROS: su marcha se maneja con el SDK de Unitree (LocoClient.Move y
#   LocoClient.StopMove). Este nodo:
#     1. Recibe /cmd_vel y LIMITA cada velocidad a los máximos configurados
#        (nunca manda más que eso, aunque Nav2 lo pida).
#     2. Envía la última velocidad al robot a frecuencia fija (--frecuencia Hz).
#     3. WATCHDOG: si no llega un /cmd_vel en --vigilancia s (Nav2 se colgó, se
#        cortó la red), DETIENE el robot con StopMove() y no vuelve a moverlo hasta
#        que lleguen órdenes nuevas.
#     4. Al cerrarse (Ctrl+C o error) llama a StopMove().
#   Solo usa la marcha de ALTO NIVEL del robot; nunca el control de bajo nivel
#   (rt/lowcmd) ni el de brazos (rt/arm_sdk).
#
#   Modo --simular: no usa el SDK de Unitree; escribe en pantalla lo que enviaría.
#   Sirve para probar límites y watchdog sin el robot (por ejemplo con la
#   simulación de Gazebo o con "ros2 topic pub").
#
#   ESTADO: el modo --simular está probado. El envío real al R1 NO está probado:
#   los nombres del módulo y de los métodos del SDK para el R1 son A VERIFICAR
#   (referencia del R1: unitree_sdk2py.r1.loco.r1_loco_client.LocoClient). También
#   A VERIFICAR que el SDK (CycloneDDS propio) y ROS 2 convivan en el mismo
#   proceso; si no, separar en dos procesos.
#
# Requisitos (modo real): unitree_sdk2_python instalado; robot en modo de marcha
#   normal, con la persona a cargo del control remoto lista para detenerlo.
#
# Cómo se usa:
#   ./scripts/navegacion/puente_cmd_vel_r1.py --simular
#   ./scripts/navegacion/puente_cmd_vel_r1.py --interfaz eth0          # robot real (A VERIFICAR)
#   ./scripts/navegacion/puente_cmd_vel_r1.py --interfaz eth0 --vx-max 0.2 --wz-max 0.4
# =============================================================================
import argparse
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class RobotSimulado:
    """Hace de robot: escribe lo que se enviaría, como mucho una vez por segundo."""

    def __init__(self):
        self.ultimo = 0.0

    def mover(self, vx, vy, wz):
        if time.time() - self.ultimo >= 1.0:
            self.ultimo = time.time()
            print(f"[simulado] Move(vx={vx:+.2f} m/s, vy={vy:+.2f} m/s, vyaw={wz:+.2f} rad/s)", flush=True)

    def detener(self):
        print("[simulado] StopMove()", flush=True)


class RobotR1:
    """Marcha de alto nivel del R1 con unitree_sdk2_python (A VERIFICAR)."""

    def __init__(self, interfaz):
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize
        from unitree_sdk2py.r1.loco.r1_loco_client import LocoClient   # A VERIFICAR
        ChannelFactoryInitialize(0, interfaz)          # DDS dominio 0 de Unitree
        self.cliente = LocoClient()
        self.cliente.SetTimeout(10.0)
        self.cliente.Init()

    def mover(self, vx, vy, wz):
        self.cliente.Move(vx, vy, wz)

    def detener(self):
        self.cliente.StopMove()


def limitar(v, maximo, minimo=None):
    minimo = -maximo if minimo is None else minimo
    return max(minimo, min(maximo, v))


class Puente(Node):
    def __init__(self, a, robot):
        super().__init__("puente_cmd_vel_r1")
        self.a, self.robot = a, robot
        self.orden = (0.0, 0.0, 0.0)
        self.ultima_orden = None       # hora (reloj de la PC) del último /cmd_vel
        self.detenido = True
        self.create_subscription(Twist, a.topico, self.al_recibir, 10)
        self.create_timer(1.0 / a.frecuencia, self.enviar)
        self.get_logger().info(
            f"límites: vx {a.vx_min}..{a.vx_max} m/s, |vy| <= {a.vy_max} m/s, |wz| <= {a.wz_max} rad/s; "
            f"watchdog {a.vigilancia} s; {'SIMULADO' if a.simular else 'ROBOT REAL'}")

    def al_recibir(self, m):
        self.orden = (limitar(m.linear.x, self.a.vx_max, self.a.vx_min),
                      limitar(m.linear.y, self.a.vy_max),
                      limitar(m.angular.z, self.a.wz_max))
        self.ultima_orden = time.monotonic()

    def enviar(self):
        sin_ordenes = self.ultima_orden is None or time.monotonic() - self.ultima_orden > self.a.vigilancia
        if sin_ordenes:
            if not self.detenido:
                self.get_logger().warn(f"WATCHDOG: sin /cmd_vel hace más de {self.a.vigilancia} s -> StopMove()")
                self.robot.detener()
                self.detenido = True
            return
        self.detenido = False
        self.robot.mover(*self.orden)


def main():
    p = argparse.ArgumentParser(description="Puente /cmd_vel -> marcha del R1 con límites y watchdog.")
    p.add_argument("--simular", action="store_true", help="no usar el SDK: escribir lo que se enviaría")
    p.add_argument("--interfaz", default="eth0", help="interfaz de red del robot para el SDK (A VERIFICAR)")
    p.add_argument("--topico", default="/cmd_vel")
    p.add_argument("--frecuencia", type=float, default=20.0, help="Hz de envío al robot (20)")
    p.add_argument("--vigilancia", type=float, default=0.5, help="s sin órdenes para detener (0.5)")
    p.add_argument("--vx-max", type=float, default=0.30)
    p.add_argument("--vx-min", type=float, default=-0.10)
    p.add_argument("--vy-max", type=float, default=0.10)
    p.add_argument("--wz-max", type=float, default=0.60)
    a = p.parse_args(rclpy.utilities.remove_ros_args(sys.argv)[1:])

    robot = RobotSimulado() if a.simular else RobotR1(a.interfaz)
    rclpy.init()
    nodo = Puente(a, robot)
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        robot.detener()            # siempre detener al salir
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
