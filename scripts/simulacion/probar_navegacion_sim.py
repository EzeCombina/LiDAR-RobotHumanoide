#!/usr/bin/env python3
# =============================================================================
# probar_navegacion_sim.py — Prueba automática de los dos objetivos en Gazebo
# -----------------------------------------------------------------------------
# Qué hace (con scripts/simulacion/simulacion.launch.py ya corriendo):
#   1. Espera a que Nav2 esté activo y manda al robot del punto "inicio" al punto
#      "destino" de <mapa>/gazebo/puntos.yaml.
#   2. OBJETIVO 1 (ubicarse en el mapa y moverse por él): durante todo el
#      recorrido compara la pose que estima AMCL (/amcl_pose) con la pose REAL del
#      robot en Gazebo (inicio + odometría exacta) y mide el error.
#   3. OBJETIVO 2 (esquivar con el LiDAR en vivo): cuando el robot recorrió
#      --distancia-caja m, hace aparecer una caja (0,4 x 0,4 x 0,8 m) sobre el
#      plan, --adelante m por delante del robot. La caja NO está en el mapa: solo
#      la puede ver el LiDAR. Mide la distancia mínima entre el robot y la caja y
#      comprueba que el plan nuevo la rodea.
#   4. Cuando el robot ya pasó al lado de la caja (la distancia vuelve a crecer),
#      la quita y, 5 s después, comprueba que el costmap global la BORRA. Se hace
#      en ese momento porque el LiDAR solo borra lo que puede volver a ver: desde
#      el destino, la mesa tapa la zona de la caja.
#   5. Guarda en resultados/<fecha>_simulacion_<mapa>/: resumen.txt,
#      recorrido.csv y recorrido.png (mapa, plan, recorrido real, estimación de
#      AMCL y caja).
#
# Requisitos: simulacion.launch.py corriendo (con rviz:=false si es por SSH);
#   python3-matplotlib.
#
# Cómo se usa:
#   ./scripts/simulacion/probar_navegacion_sim.py
#   ./scripts/simulacion/probar_navegacion_sim.py --mapa mapas/sala_de_prueba --sin-caja
#   ./scripts/simulacion/probar_navegacion_sim.py --distancia-caja 2.0 --adelante 1.2
# =============================================================================
import argparse
import math
import os
import subprocess
import sys
import time

import numpy as np
import rclpy
import yaml
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))

CAJA_SDF = """<sdf version='1.9'><model name='caja'><static>true</static><link name='l'>
<collision name='c'><pose>0 0 {z} 0 0 0</pose><geometry><box><size>{l} {l} {a}</size></box></geometry></collision>
<visual name='v'><pose>0 0 {z} 0 0 0</pose><geometry><box><size>{l} {l} {a}</size></box></geometry>
<material><ambient>0.9 0.3 0.1 1</ambient><diffuse>0.9 0.3 0.1 1</diffuse></material></visual>
</link></model></sdf>"""


def yaw_de(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def pose(nav, x, y, yaw):
    p = PoseStamped()
    p.header.frame_id = "map"
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = float(x), float(y)
    p.pose.orientation.z, p.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    return p


class Registro:
    """Guarda lo que publican la simulación y Nav2 durante la prueba."""

    def __init__(self, nav, inicio):
        self.nav, self.inicio = nav, inicio
        self.real = None            # (x, y, yaw) real en el mapa
        self.amcl = None            # (x, y, yaw) estimado por AMCL
        self.plan = []              # último plan global [(x, y)]
        self.costmap = None
        self.filas = []             # t, real x y yaw, amcl x y yaw
        qos_mapa = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                              durability=DurabilityPolicy.TRANSIENT_LOCAL)
        nav.create_subscription(Odometry, "/odom", self.al_odom, 20)
        nav.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self.al_amcl, 10)
        nav.create_subscription(Path, "/plan", self.al_plan, 10)
        nav.create_subscription(OccupancyGrid, "/global_costmap/costmap", self.al_costmap, qos_mapa)

    def al_odom(self, m):
        # La odometría de Gazebo (OdometryPublisher) da la pose en coordenadas del
        # MUNDO, que son las del mapa: es la pose real del robot.
        p = m.pose.pose
        self.real = (p.position.x, p.position.y, yaw_de(p.orientation))

    def al_amcl(self, m):
        p = m.pose.pose
        self.amcl = (p.position.x, p.position.y, yaw_de(p.orientation))

    def al_plan(self, m):
        self.plan = [(q.pose.position.x, q.pose.position.y) for q in m.poses]

    def al_costmap(self, m):
        self.costmap = m

    def anotar(self, t):
        if self.real and self.amcl:
            self.filas.append((t,) + self.real + self.amcl)

    def valor_costmap(self, x, y, medio_lado):
        """Valor MÁXIMO del costmap en el cuadrado de la caja (el LiDAR solo ve sus
        caras: el centro nunca se marca)."""
        m = self.costmap
        if m is None:
            return None
        g = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
        r, ox, oy = m.info.resolution, m.info.origin.position.x, m.info.origin.position.y
        i0, i1 = int((x - medio_lado - ox) / r), int((x + medio_lado - ox) / r) + 1
        j0, j1 = int((y - medio_lado - oy) / r), int((y + medio_lado - oy) / r) + 1
        zona = g[max(j0, 0):max(j1, 0), max(i0, 0):max(i1, 0)]
        return int(zona.max()) if zona.size else None


def esperar(nav, segundos):
    fin = time.time() + segundos
    while time.time() < fin:
        rclpy.spin_once(nav, timeout_sec=0.1)


def gz_crear_caja(x, y, lado, alto):
    sdf = CAJA_SDF.format(l=lado, a=alto, z=alto / 2)
    return subprocess.run(["ros2", "run", "ros_gz_sim", "create", "-world", "gemelo", "-name", "caja",
                           "-string", sdf, "-x", str(x), "-y", str(y), "-z", "0.0"],
                          capture_output=True, text=True, timeout=30).returncode == 0


def gz_quitar_caja():
    pedido = 'name: "caja" type: MODEL'
    return subprocess.run(["gz", "service", "-s", "/world/gemelo/remove", "--reqtype", "gz.msgs.Entity",
                           "--reptype", "gz.msgs.Boolean", "--timeout", "3000", "--req", pedido],
                          capture_output=True, text=True, timeout=30).returncode == 0


def punto_adelante(plan, robot, adelante):
    """Punto del plan a 'adelante' m (medidos sobre el plan) del punto más cercano al robot."""
    if len(plan) < 2:
        return None
    d = [math.hypot(px - robot[0], py - robot[1]) for px, py in plan]
    k = int(np.argmin(d))
    recorrido = 0.0
    for i in range(k, len(plan) - 1):
        recorrido += math.dist(plan[i], plan[i + 1])
        if recorrido >= adelante:
            return plan[i + 1]
    return None


def dibujar(carpeta_mapa, reg, planes, caja, destino_png, inicio, destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    datos = yaml.safe_load(open(os.path.join(carpeta_mapa, "mapa_2d.yaml")))
    img = np.array(Image.open(os.path.join(carpeta_mapa, datos["image"])).convert("L"))
    res, (ox, oy) = datos["resolution"], datos["origin"][:2]
    alto, ancho = img.shape
    fig, ax = plt.subplots(figsize=(8, 8 * alto / ancho + 0.5), dpi=130)
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, extent=(ox, ox + ancho * res, oy, oy + alto * res))
    if planes:
        p = np.array(planes[0])
        ax.plot(p[:, 0], p[:, 1], "--", color="tab:blue", lw=1.2, label="Plan inicial")
        if len(planes) > 1:
            p = np.array(planes[-1])
            ax.plot(p[:, 0], p[:, 1], ":", color="tab:purple", lw=1.4, label="Plan con la caja")
    f = np.array(reg.filas)
    if len(f):
        ax.plot(f[:, 1], f[:, 2], color="tab:green", lw=2.2, label="Recorrido real")
        ax.plot(f[:, 4], f[:, 5], color="tab:red", lw=1.0, label="Estimación de AMCL")
    if caja:
        lado = caja[2]
        ax.add_patch(plt.Rectangle((caja[0] - lado / 2, caja[1] - lado / 2), lado, lado,
                                   color="tab:orange", label="Caja (no está en el mapa)"))
    ax.plot(inicio["x"], inicio["y"], "o", color="black", ms=7, label="Inicio")
    ax.plot(destino["x"], destino["y"], "*", color="black", ms=12, label="Destino")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(destino_png)


def main():
    p = argparse.ArgumentParser(description="Prueba automática de navegación en la simulación.")
    p.add_argument("--mapa", default="mapas/sala_de_prueba", help="carpeta del mapa (con gazebo/puntos.yaml)")
    p.add_argument("--distancia-caja", type=float, default=1.5, help="m recorridos antes de poner la caja")
    p.add_argument("--adelante", type=float, default=1.3, help="m por delante del robot (sobre el plan)")
    p.add_argument("--sin-caja", action="store_true", help="no poner la caja (solo objetivo 1)")
    p.add_argument("--limite", type=float, default=240.0, help="tiempo máximo de la prueba en s")
    a = p.parse_args()

    carpeta = a.mapa if os.path.isabs(a.mapa) else os.path.join(REPO, a.mapa)
    puntos = yaml.safe_load(open(os.path.join(carpeta, "gazebo", "puntos.yaml")))
    inicio, destino, caja_def = puntos["inicio"], puntos["destino"], puntos["obstaculo"]

    rclpy.init()
    nav = BasicNavigator()
    nav.set_parameters([rclpy.parameter.Parameter("use_sim_time", rclpy.Parameter.Type.BOOL, True)])
    reg = Registro(nav, inicio)
    print("Esperando que Nav2 esté activo ...", flush=True)
    # Pose inicial = punto de inicio. Sin esto, BasicNavigator publica (0, 0, 0)
    # en /initialpose y AMCL "salta" a un lugar equivocado.
    nav.setInitialPose(pose(nav, inicio["x"], inicio["y"], inicio["yaw"]))
    nav.waitUntilNav2Active(localizer="amcl")
    esperar(nav, 3.0)
    gz_quitar_caja()   # por si quedó de una prueba anterior

    nav.goToPose(pose(nav, destino["x"], destino["y"], destino["yaw"]))
    t0 = time.time()
    caja, planes, recorrido, ultimo = None, [], 0.0, None
    min_dist_caja, plan_rodea = float("inf"), None
    t_quitada, borrado, antes = None, None, None
    while not nav.isTaskComplete():
        rclpy.spin_once(nav, timeout_sec=0.1)
        t = time.time() - t0
        reg.anotar(t)
        if reg.plan and not planes:
            planes.append(list(reg.plan))
        if reg.real:
            if ultimo:
                recorrido += math.dist(ultimo, reg.real[:2])
            ultimo = reg.real[:2]
        # OBJETIVO 2: caja sobre el plan, por delante del robot
        if not a.sin_caja and caja is None and recorrido >= a.distancia_caja and reg.real:
            punto = punto_adelante(reg.plan, reg.real, a.adelante) or (caja_def["x"], caja_def["y"])
            if gz_crear_caja(punto[0], punto[1], caja_def["lado"], caja_def["alto"]):
                caja = (punto[0], punto[1], caja_def["lado"])
                t_caja = t
                print(f"[{t:5.1f} s] Caja puesta en x={punto[0]:.2f} y={punto[1]:.2f} "
                      f"({a.adelante} m por delante, sobre el plan)", flush=True)
        if caja and reg.real:
            d_caja = math.dist(reg.real[:2], caja[:2])
            min_dist_caja = min(min_dist_caja, d_caja)
            # Ya la pasó (se aleja 0,3 m del punto más cercano): quitar la caja
            if t_quitada is None and plan_rodea is not None and d_caja > min_dist_caja + 0.3:
                antes = reg.valor_costmap(caja[0], caja[1], caja[2] / 2)
                if gz_quitar_caja():
                    t_quitada = t
                    print(f"[{t:5.1f} s] Caja quitada (el robot está a {d_caja:.2f} m); "
                          f"costmap global en la caja: {antes}", flush=True)
            if t_quitada is not None and borrado is None and t - t_quitada >= 5.0:
                borrado = (antes, reg.valor_costmap(caja[0], caja[1], caja[2] / 2))
                print(f"[{t:5.1f} s] 5 s después: costmap global en la caja: {borrado[1]}", flush=True)
            if plan_rodea is None and t - t_caja > 4.0 and reg.plan:
                d_plan = min(math.dist(q, caja[:2]) for q in reg.plan)
                plan_rodea = d_plan
                planes.append(list(reg.plan))
                print(f"[{t:5.1f} s] Plan nuevo: pasa a {d_plan:.2f} m del centro de la caja", flush=True)
        if t > a.limite:
            nav.cancelTask()
            break
    resultado = nav.getResult()
    duracion = time.time() - t0

    # Si la prueba terminó antes de medir el borrado, se mide ahora
    if caja and borrado is None:
        antes = reg.valor_costmap(caja[0], caja[1], caja[2] / 2)
        gz_quitar_caja()
        esperar(nav, 5.0)
        borrado = (antes, reg.valor_costmap(caja[0], caja[1], caja[2] / 2))
    gz_quitar_caja()

    # --- Resultados --------------------------------------------------------
    f = np.array(reg.filas)
    err = np.hypot(f[:, 1] - f[:, 4], f[:, 2] - f[:, 5]) if len(f) else np.array([np.nan])
    err_yaw = (np.degrees(np.abs(np.arctan2(np.sin(f[:, 3] - f[:, 6]), np.cos(f[:, 3] - f[:, 6]))))
               if len(f) else np.array([np.nan]))
    final = reg.real or (float("nan"),) * 3
    d_final = math.dist(final[:2], (destino["x"], destino["y"]))
    nombre_res = {TaskResult.SUCCEEDED: "LLEGÓ", TaskResult.CANCELED: "CANCELADA (tiempo límite)",
                  TaskResult.FAILED: "FALLÓ", TaskResult.UNKNOWN: "SIN TERMINAR (tiempo límite)"}.get(
                      resultado, str(resultado))
    lineas = [
        f"Prueba de navegación en simulación — {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Mapa: {os.path.relpath(carpeta, REPO)}",
        f"Inicio: ({inicio['x']}, {inicio['y']})  Destino: ({destino['x']}, {destino['y']})",
        f"Resultado: {nombre_res} en {duracion:.1f} s (reloj de la PC); recorrido real {recorrido:.2f} m",
        f"Distancia final al destino: {d_final:.2f} m (tolerancia de Nav2: 0,25 m)",
        "",
        "OBJETIVO 1 — Ubicarse en el mapa (AMCL frente a la pose real)",
        f"  error de posición: medio {np.nanmean(err):.3f} m, máximo {np.nanmax(err):.3f} m, "
        f"final {err[-1]:.3f} m",
        f"  error de orientación: medio {np.nanmean(err_yaw):.1f}°, máximo {np.nanmax(err_yaw):.1f}°",
        "",
        "OBJETIVO 2 — Esquivar con el LiDAR en vivo",
    ]
    if caja:
        lineas += [
            f"  caja de {caja[2]} m puesta en ({caja[0]:.2f}, {caja[1]:.2f}), sobre el plan",
            f"  el plan nuevo pasa a {plan_rodea:.2f} m del centro de la caja" if plan_rodea is not None
            else "  no se registró un plan nuevo",
            f"  distancia mínima robot-caja (centros): {min_dist_caja:.2f} m "
            f"(choque si < {caja[2] / 2 + 0.2:.2f} m: medio lado de la caja + medio ancho del robot)",
            f"  costmap global en la huella de la caja (valor máximo): {borrado[0]} con la caja -> "
            f"{borrado[1]} 5 s después de quitarla (100 = obstáculo; menos de 99 = sin obstáculo, solo inflado)",
        ]
    else:
        lineas.append("  (sin caja: --sin-caja)")

    destino_res = os.path.join(REPO, "resultados",
                               f"{time.strftime('%Y-%m-%d_%H%M')}_simulacion_{os.path.basename(carpeta)}")
    os.makedirs(destino_res, exist_ok=True)
    with open(os.path.join(destino_res, "resumen.txt"), "w") as fh:
        fh.write("\n".join(lineas) + "\n")
    with open(os.path.join(destino_res, "recorrido.csv"), "w") as fh:
        fh.write("t,x_real,y_real,yaw_real,x_amcl,y_amcl,yaw_amcl\n")
        for fila in reg.filas:
            fh.write(",".join(f"{v:.4f}" for v in fila) + "\n")
    dibujar(carpeta, reg, planes, caja, os.path.join(destino_res, "recorrido.png"), inicio, destino)
    print("\n" + "\n".join(lineas))
    print(f"\nResultados en {os.path.relpath(destino_res, REPO)}/")
    nav.destroy_node()
    rclpy.try_shutdown()
    sys.exit(0 if resultado == TaskResult.SUCCEEDED else 1)


if __name__ == "__main__":
    main()
