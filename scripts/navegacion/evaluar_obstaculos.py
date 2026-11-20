#!/usr/bin/env python3
# =============================================================================
# evaluar_obstaculos.py — Mide cómo marca y libera obstáculos el costmap en vivo
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe a un costmap de Nav2 (nav_msgs/OccupancyGrid) y, cada segundo
#   (del tiempo del mensaje), compara las celdas OCUPADAS (valor 100, obstáculo
#   detectado por la nube) con las del segundo anterior:
#     - ocupadas: cuántas hay;
#     - nuevas:   ocupadas ahora y no antes (algo apareció o se movió hacia ahí);
#     - liberadas: ocupadas antes y no ahora (el obstáculo se fue y el costmap lo
#       BORRÓ: es el "raytrace" de la nube que limpia el espacio libre).
#   Las celdas del borde de paredes y muebles "parpadean" (ruido normal del
#   sensor), así que nuevas y liberadas nunca llegan a 0. Por eso, al terminar,
#   separa:
#     - FONDO: celdas ocupadas en al menos el 80 % de los segundos (paredes,
#       muebles: lo que no se mueve);
#     - DINÁMICO: celdas ocupadas en un segundo que no son fondo; se agrupan las
#       vecinas y se mide el GRUPO MÁS GRANDE. El ruido da celdas sueltas; una
#       persona da un grupo compacto (unas 20 a 60 celdas de 5 cm).
#   Al terminar (Ctrl+C o --duracion) escribe un resumen y, con --imagenes,
#   guarda una imagen PNG del costmap cada --cada segundos (negro = obstáculo,
#   gris = zona inflada, blanco = libre, celeste claro = desconocido).
#
# Requisitos: python3-numpy, python3-pil; un costmap publicándose
#   (scripts/navegacion/navegacion.launch.py modo:=obstaculos).
#
# Cómo se usa:
#   ./scripts/navegacion/evaluar_obstaculos.py
#   ./scripts/navegacion/evaluar_obstaculos.py --topico /local_costmap/costmap --duracion 60
#   ./scripts/navegacion/evaluar_obstaculos.py --imagenes /tmp/costmap --cada 10
# =============================================================================
import argparse
import os
import sys

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


class Evaluador(Node):
    def __init__(self, a):
        super().__init__("evaluar_obstaculos")
        self.a = a
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(OccupancyGrid, a.topico, self.al_recibir, qos)
        self.inicio = None
        self.ultimo_segundo = None
        self.anterior = None        # conjunto de celdas ocupadas (en coordenadas del mundo)
        self.filas = []
        self.historia = []          # (segundo, celdas ocupadas) para el análisis final
        self.ultima_imagen = None
        self.terminado = False
        print(f"Escuchando {a.topico} ... (Ctrl+C para terminar)")
        print(f"{'t (s)':>6} {'ocupadas':>9} {'nuevas':>7} {'liberadas':>10}")

    def celdas_ocupadas(self, msg):
        """Celdas con valor 100 como coordenadas enteras del mundo (resolución del
        costmap), para poder comparar ventanas móviles (rolling window)."""
        info = msg.info
        g = np.array(msg.data, dtype=np.int16).reshape(info.height, info.width)
        filas, columnas = np.nonzero(g == 100)
        ox = round(info.origin.position.x / info.resolution)
        oy = round(info.origin.position.y / info.resolution)
        return set(zip((columnas + ox).tolist(), (filas + oy).tolist())), g

    def al_recibir(self, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self.inicio is None:
            self.inicio = t
        rel = t - self.inicio
        segundo = int(rel)
        if segundo == self.ultimo_segundo:
            return
        self.ultimo_segundo = segundo
        ocupadas, grilla = self.celdas_ocupadas(msg)
        nuevas = liberadas = 0
        if self.anterior is not None:
            nuevas = len(ocupadas - self.anterior)
            liberadas = len(self.anterior - ocupadas)
        self.anterior = ocupadas
        self.historia.append((segundo, ocupadas))
        self.filas.append((segundo, len(ocupadas), nuevas, liberadas))
        print(f"{segundo:6d} {len(ocupadas):9d} {nuevas:7d} {liberadas:10d}", flush=True)

        if self.a.imagenes and (self.ultima_imagen is None or segundo - self.ultima_imagen >= self.a.cada):
            self.ultima_imagen = segundo
            self.guardar_imagen(grilla, segundo)
        if self.a.duracion and rel >= self.a.duracion:
            self.terminado = True

    def guardar_imagen(self, g, segundo):
        from PIL import Image
        img = np.zeros(g.shape + (3,), dtype=np.uint8)
        img[:] = (205, 220, 235)                              # desconocido: celeste claro
        img[g == 0] = (255, 255, 255)                         # libre: blanco
        img[(g > 0) & (g < 100)] = (170, 170, 170)            # zona inflada: gris
        img[g == 100] = (0, 0, 0)                             # obstáculo: negro
        os.makedirs(self.a.imagenes, exist_ok=True)
        ruta = os.path.join(self.a.imagenes, f"costmap_{segundo:04d}s.png")
        Image.fromarray(img[::-1]).resize((g.shape[1] * 3, g.shape[0] * 3), Image.NEAREST).save(ruta)

    def resumen(self):
        if len(self.filas) < 2:
            print("No llegaron suficientes mensajes del costmap.")
            return
        d = np.array(self.filas[1:], dtype=float)
        print("\nResumen")
        print(f"  segundos evaluados       : {len(self.filas)}")
        print(f"  celdas ocupadas (prom.)  : {d[:, 1].mean():.0f}  (mín {d[:, 1].min():.0f}, máx {d[:, 1].max():.0f})")
        print(f"  nuevas por segundo (prom.)    : {d[:, 2].mean():.1f}")
        print(f"  liberadas por segundo (prom.) : {d[:, 3].mean():.1f}")
        self.analizar_dinamico()

    def analizar_dinamico(self):
        """Fondo = celdas ocupadas en >= 80 % de los segundos; grupo dinámico más
        grande por segundo (celdas vecinas, 8-conectividad)."""
        from collections import Counter
        from scipy import ndimage
        n = len(self.historia)
        cuenta = Counter(c for _, celdas in self.historia for c in celdas)
        fondo = {c for c, k in cuenta.items() if k >= 0.8 * n}
        grupos = []
        for segundo, celdas in self.historia:
            dinamicas = celdas - fondo
            if not dinamicas:
                grupos.append((segundo, 0, 0))
                continue
            xs, ys = zip(*dinamicas)
            x0, y0 = min(xs), min(ys)
            g = np.zeros((max(ys) - y0 + 1, max(xs) - x0 + 1), dtype=bool)
            g[np.array(ys) - y0, np.array(xs) - x0] = True
            etiquetas, cantidad = ndimage.label(g, structure=np.ones((3, 3)))
            mayor = int(np.bincount(etiquetas.ravel())[1:].max()) if cantidad else 0
            grupos.append((segundo, len(dinamicas), mayor))
        mayores = np.array([m for _, _, m in grupos])
        print(f"\nFondo (ocupadas >= 80 % del tiempo): {len(fondo)} celdas")
        print("Grupo dinámico más grande por segundo (celdas):")
        print("  " + " ".join(f"{m}" for m in mayores))
        print(f"  mediana {np.median(mayores):.0f}, máximo {mayores.max()}, "
              f"segundos con un grupo de {self.a.grupo} celdas o más: "
              f"{int((mayores >= self.a.grupo).sum())} de {n}")


def main():
    p = argparse.ArgumentParser(description="Mide cómo marca y libera obstáculos un costmap de Nav2.")
    p.add_argument("--topico", default="/obstaculos/costmap", help="costmap a evaluar")
    p.add_argument("--duracion", type=float, default=0.0, help="segundos a evaluar (0 = hasta Ctrl+C)")
    p.add_argument("--imagenes", default="", help="carpeta donde guardar imágenes PNG del costmap")
    p.add_argument("--cada", type=float, default=10.0, help="segundos entre imágenes")
    p.add_argument("--grupo", type=int, default=20,
                   help="tamaño de grupo dinámico (celdas) que se cuenta como obstáculo móvil (20)")
    a = p.parse_args(rclpy.utilities.remove_ros_args(sys.argv)[1:])

    rclpy.init()
    nodo = Evaluador(a)
    try:
        while rclpy.ok() and not nodo.terminado:
            rclpy.spin_once(nodo, timeout_sec=0.5)
    except KeyboardInterrupt:
        pass
    nodo.resumen()
    nodo.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
