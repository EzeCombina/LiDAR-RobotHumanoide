#!/usr/bin/env python3
# =============================================================================
# evaluar_localizacion.py — Mide qué tan bien se ubica AMCL en un mapa guardado
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe a /amcl_pose (la pose que estima AMCL en el marco del mapa) y, al
#   terminar, la compara con una referencia:
#     - Si en la carpeta del mapa está trayectoria_limpia.csv (limpiar_mapa.py,
#       paso 07) y la grabación reproducida es LA MISMA con la que se hizo el
#       mapa, esa trayectoria es la posición "verdadera" del sensor en el mapa.
#       Se compara la posición en el plano (x, y) en los mismos instantes
#       (interpolando) y se informa el error medio, el máximo y el final, y cuánto
#       tardó en bajar de --umbral m (útil si se arrancó con una pose inicial
#       equivocada a propósito).
#     - Si no hay referencia (otra grabación del mismo lugar), informa solo la
#       incertidumbre que declara AMCL (desvío estándar de x, y y del ángulo).
#
# Requisitos: scripts/navegacion/navegacion.launch.py modo:=localizacion con una
#   grabación (bag:=...), y use_sim_time (lo pone probar_con_grabacion.sh).
#
# Cómo se usa:
#   ./scripts/navegacion/evaluar_localizacion.py --mapa mapas/<carpeta> --duracion 70 \
#       --ros-args -p use_sim_time:=true
#   (normalmente lo corre scripts/navegacion/probar_con_grabacion.sh localizacion ...)
# =============================================================================
import argparse
import math
import os
import sys
import time

import numpy as np
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


def yaw_de(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class Evaluador(Node):
    def __init__(self, a):
        super().__init__("evaluar_localizacion")
        self.a = a
        self.poses = []      # t, x, y, yaw, sx, sy, syaw
        self.t_primera = None
        self.arranque = time.monotonic()
        self.ultima_llegada = None   # hora de la PC de la última pose (para cortar si no llegan más)
        self.terminado = False
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self.al_recibir, qos)
        print("Escuchando /amcl_pose ... (Ctrl+C para terminar)", flush=True)

    def al_recibir(self, m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        c = m.pose.covariance
        p = m.pose.pose
        self.poses.append((t, p.position.x, p.position.y, yaw_de(p.orientation),
                           math.sqrt(max(c[0], 0)), math.sqrt(max(c[7], 0)), math.sqrt(max(c[35], 0))))
        self.ultima_llegada = time.monotonic()
        if self.t_primera is None:
            self.t_primera = t
        if len(self.poses) % 10 == 1:
            print(f"  t={t - self.t_primera:6.1f} s  x={p.position.x:7.3f}  y={p.position.y:7.3f}  "
                  f"σxy={max(self.poses[-1][4], self.poses[-1][5]):.3f} m", flush=True)

    def revisar_tiempo(self):
        # Fin por inactividad: al terminar una grabación el reloj simulado se
        # detiene y no llegan más poses.
        if self.ultima_llegada is None and time.monotonic() - self.arranque > self.a.espera_max:
            print(f"(no llegó ninguna pose en {self.a.espera_max:.0f} s: fin; revisar el launch)", flush=True)
            self.terminado = True
        if self.ultima_llegada is not None and time.monotonic() - self.ultima_llegada > self.a.inactividad:
            print(f"(sin poses nuevas hace {self.a.inactividad:.0f} s: fin)", flush=True)
            self.terminado = True
        if self.a.duracion and self.t_primera is not None:
            ahora = self.get_clock().now().nanoseconds * 1e-9
            if ahora - self.t_primera >= self.a.duracion:
                self.terminado = True

    def resumen(self):
        if len(self.poses) < 3:
            print("No llegaron suficientes poses de AMCL (¿se movió el sensor? AMCL publica al moverse).")
            return
        p = np.array(self.poses)
        print(f"\nResumen ({len(p)} poses de AMCL en {p[-1, 0] - p[0, 0]:.1f} s)")
        print(f"  incertidumbre final de AMCL: σx={p[-1, 4]:.3f} m  σy={p[-1, 5]:.3f} m  "
              f"σángulo={math.degrees(p[-1, 6]):.1f}°")
        ref = os.path.join(self.a.mapa, "trayectoria_limpia.csv") if self.a.mapa else ""
        if not ref or not os.path.isfile(ref) or self.a.sin_referencia:
            print("  sin trayectoria de referencia: no se calcula el error.")
            return
        r = np.loadtxt(ref, delimiter=",", skiprows=1)
        dentro = (p[:, 0] >= r[0, 0]) & (p[:, 0] <= r[-1, 0])
        if dentro.sum() < 3:
            print("  los tiempos de AMCL no coinciden con trayectoria_limpia.csv: la grabación no es la del mapa.")
            return
        p = p[dentro]
        xr = np.interp(p[:, 0], r[:, 0], r[:, 1])
        yr = np.interp(p[:, 0], r[:, 0], r[:, 2])
        err = np.hypot(p[:, 1] - xr, p[:, 2] - yr)
        t = p[:, 0] - p[0, 0]
        print(f"  referencia: {os.path.relpath(ref)} (trayectoria de Point-LIO en el mapa limpio)")
        print(f"  error de posición: medio {err.mean():.3f} m, mediana {np.median(err):.3f} m, "
              f"máximo {err.max():.3f} m, final {err[-1]:.3f} m")
        bajo = np.nonzero(err < self.a.umbral)[0]
        if len(bajo):
            k = bajo[0]
            despues = err[k:]
            print(f"  primera vez bajo {self.a.umbral} m: a los {t[k]:.1f} s; después de eso, "
                  f"{(despues < self.a.umbral).mean() * 100:.0f} % del tiempo bajo {self.a.umbral} m "
                  f"(máximo {despues.max():.3f} m)")
        else:
            print(f"  el error nunca bajó de {self.a.umbral} m: AMCL no reconoció el lugar.")
        if self.a.csv:
            with open(self.a.csv, "w") as f:
                f.write("t,x_amcl,y_amcl,x_ref,y_ref,error\n")
                for fila in zip(t, p[:, 1], p[:, 2], xr, yr, err):
                    f.write(",".join(f"{v:.4f}" for v in fila) + "\n")
            print(f"  detalle guardado en {self.a.csv}")


def main():
    p = argparse.ArgumentParser(description="Mide la localización de AMCL en un mapa guardado.")
    p.add_argument("--mapa", default="", help="carpeta del mapa (para trayectoria_limpia.csv)")
    p.add_argument("--duracion", type=float, default=0.0, help="segundos a evaluar desde la primera pose (0 = Ctrl+C)")
    p.add_argument("--umbral", type=float, default=0.20, help="error que se considera 'ubicado', en m (0.20)")
    p.add_argument("--sin-referencia", action="store_true", help="no comparar con trayectoria_limpia.csv")
    p.add_argument("--csv", default="", help="guardar el detalle del error en este archivo")
    p.add_argument("--espera-max", type=float, default=90.0,
                   help="terminar si en estos segundos de la PC no llega ninguna pose (90)")
    p.add_argument("--inactividad", type=float, default=60.0,
                   help="terminar si no llegan poses en estos segundos de la PC (60; AMCL publica solo con movimiento)")
    a = p.parse_args(rclpy.utilities.remove_ros_args(sys.argv)[1:])

    rclpy.init()
    nodo = Evaluador(a)
    try:
        while rclpy.ok() and not nodo.terminado:
            rclpy.spin_once(nodo, timeout_sec=0.5)
            nodo.revisar_tiempo()   # con reloj de la PC (los temporizadores de ROS usan
                                    # el reloj simulado, que se detiene con la grabación)
    except KeyboardInterrupt:
        pass
    nodo.resumen()
    nodo.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
