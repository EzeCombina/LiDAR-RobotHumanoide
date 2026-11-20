#!/usr/bin/env python3
# =============================================================================
# generar_mundo_gazebo.py — Gemelo del lugar para Gazebo a partir del mapa 2D
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Lee el mapa 2D de ocupación de la carpeta del mapa (mapa_2d.pgm + .yaml,
#      paso 07).
#   2. Convierte las celdas OCUPADAS en paredes: junta las celdas vecinas en
#      rectángulos (para tener pocas cajas) y las levanta a --altura m. Las celdas
#      libres y desconocidas quedan vacías.
#   3. Escribe <carpeta del mapa>/gazebo/mundo.sdf: piso, luz, las paredes y los
#      plugins de Gazebo necesarios (física, sensores, comandos para agregar o
#      quitar objetos durante la simulación).
#   4. Elige puntos para la prueba automática y los guarda en
#      <carpeta del mapa>/gazebo/puntos.yaml:
#        inicio    zona libre con espacio para el robot (lejos de paredes);
#        destino   el punto libre alcanzable más lejano del inicio, mirando
#                  hacia el inicio (no contra una pared);
#        obstaculo un punto a mitad de camino, donde aparece una caja.
#      Solo se usan celdas libres CONOCIDAS, con al menos --margen m hasta la
#      pared más cercana.
#
#   El mundo usa las mismas coordenadas que el mapa (marco "map"): un punto (x, y)
#   del mapa 2D es el mismo (x, y) en Gazebo.
#
# Requisitos: python3-numpy, python3-scipy, python3-pil, python3-yaml.
#
# Cómo se usa:
#   ./scripts/simulacion/generar_mundo_gazebo.py mapas/<carpeta>
#   ./scripts/simulacion/generar_mundo_gazebo.py mapas/<carpeta> --altura 2.0 --margen 0.45
# =============================================================================
import argparse
import math
import os
import sys

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

PLANTILLA = """<?xml version="1.0" ?>
<!-- Mundo generado por scripts/simulacion/generar_mundo_gazebo.py a partir de
     {origen}. No editar a mano: volver a generarlo. -->
<sdf version="1.9">
  <world name="gemelo">
    <physics name="1ms" type="ignored">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <gravity>0 0 -9.8</gravity>
    <scene>
      <ambient>0.6 0.6 0.6 1</ambient>
      <background>0.8 0.85 0.9 1</background>
    </scene>
    <light type="directional" name="sol">
      <cast_shadows>false</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse>
      <direction>-0.3 0.2 -0.9</direction>
    </light>
    <model name="piso">
      <static>true</static>
      <link name="piso">
        <collision name="c">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <surface><friction><ode><mu>0.8</mu><mu2>0.8</mu2></ode></friction></surface>
        </collision>
        <visual name="v">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <material><ambient>0.75 0.75 0.7 1</ambient><diffuse>0.75 0.75 0.7 1</diffuse></material>
        </visual>
      </link>
    </model>
    <model name="paredes">
      <static>true</static>
      <link name="paredes">
{cajas}
      </link>
    </model>
  </world>
</sdf>
"""

CAJA = """        <collision name="c{i}"><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 0</pose>
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry></collision>
        <visual name="v{i}"><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 0</pose>
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>0.55 0.6 0.7 1</ambient><diffuse>0.55 0.6 0.7 1</diffuse></material></visual>"""


def leer_mapa(carpeta):
    datos = yaml.safe_load(open(os.path.join(carpeta, "mapa_2d.yaml")))
    img = np.array(Image.open(os.path.join(carpeta, datos["image"])).convert("L"))
    # Fila 0 de la imagen = borde SUPERIOR del mapa (y máxima): se invierte para
    # que la fila i corresponda a y = origen_y + i·resolución.
    img = img[::-1]
    ocupada = img < 100          # negro (0)
    libre = img > 250            # blanco (254)
    return datos, ocupada, libre


def rectangulos(ocupada):
    """Junta celdas ocupadas en rectángulos: tramos por fila y, después, tramos
    iguales de filas consecutivas. Devuelve (fila, columna, alto, ancho)."""
    abiertos, salida = {}, []
    for f in range(ocupada.shape[0] + 1):
        tramos = set()
        if f < ocupada.shape[0]:
            fila, c = ocupada[f], 0
            while c < len(fila):
                if fila[c]:
                    c0 = c
                    while c < len(fila) and fila[c]:
                        c += 1
                    tramos.add((c0, c - c0))
                else:
                    c += 1
        nuevos = {}
        for t, (f0, alto) in abiertos.items():
            if t in tramos:
                nuevos[t] = (f0, alto + 1)
            else:
                salida.append((f0, t[0], alto, t[1]))
        for t in tramos:
            nuevos.setdefault(t, (f, 1))
        abiertos = nuevos
    return salida


def main():
    p = argparse.ArgumentParser(description="Genera el mundo de Gazebo a partir del mapa 2D.")
    p.add_argument("carpeta", help="carpeta del mapa (con mapa_2d.yaml)")
    p.add_argument("--altura", type=float, default=2.0, help="altura de las paredes en m (2.0)")
    p.add_argument("--margen", type=float, default=0.45,
                   help="distancia mínima a una pared para inicio y destino, en m (0.45)")
    a = p.parse_args()

    carpeta = os.path.abspath(a.carpeta)
    if not os.path.isfile(os.path.join(carpeta, "mapa_2d.yaml")):
        sys.exit(f"ERROR: no existe {carpeta}/mapa_2d.yaml (generarlo con generar_mapa_2d.py, paso 07)")
    datos, ocupada, libre = leer_mapa(carpeta)
    res = float(datos["resolution"])
    ox, oy = float(datos["origin"][0]), float(datos["origin"][1])

    # --- Paredes -------------------------------------------------------------
    cajas = []
    for i, (f0, c0, alto, ancho) in enumerate(rectangulos(ocupada)):
        cajas.append(CAJA.format(i=i, x=ox + (c0 + ancho / 2) * res, y=oy + (f0 + alto / 2) * res,
                                 z=a.altura / 2, sx=ancho * res, sy=alto * res, sz=a.altura))
    destino = os.path.join(carpeta, "gazebo")
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "mundo.sdf"), "w") as f:
        f.write(PLANTILLA.format(origen=os.path.relpath(carpeta), cajas="\n".join(cajas)))

    # --- Puntos de la prueba ---------------------------------------------------
    # Distancia de cada celda a la ocupada más cercana (en m).
    distancia = ndimage.distance_transform_edt(~ocupada) * res
    apta = libre & (distancia >= a.margen)
    etiquetas, n = ndimage.label(apta)
    if n == 0:
        sys.exit(f"ERROR: no hay zona libre con {a.margen} m de margen. Probar con --margen menor.")
    tamanos = np.bincount(etiquetas.ravel())[1:]
    zona = etiquetas == (int(np.argmax(tamanos)) + 1)
    filas, columnas = np.nonzero(zona)
    # Inicio: la celda de la zona más alejada de las paredes
    k = int(np.argmax(distancia[filas, columnas]))
    fi, ci = filas[k], columnas[k]
    # Destino: la celda alcanzable (dentro de la zona) más lejana, por recorrido real
    from collections import deque
    dist = np.full(zona.shape, -1, dtype=int)
    previo = {}
    dist[fi, ci] = 0
    cola = deque([(fi, ci)])
    while cola:
        f, c = cola.popleft()
        for df, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g, h = f + df, c + dc
            if 0 <= g < zona.shape[0] and 0 <= h < zona.shape[1] and zona[g, h] and dist[g, h] < 0:
                dist[g, h] = dist[f, c] + 1
                previo[(g, h)] = (f, c)
                cola.append((g, h))
    fd, cd = np.unravel_index(int(np.argmax(dist)), dist.shape)
    # Obstáculo: a mitad del recorrido entre inicio y destino
    recorrido = [(fd, cd)]
    while recorrido[-1] != (fi, ci):
        recorrido.append(previo[recorrido[-1]])
    fo, co = recorrido[len(recorrido) // 2]

    def xy(f, c):
        return round(float(ox + (c + 0.5) * res), 3), round(float(oy + (f + 0.5) * res), 3)

    xi, yi = xy(fi, ci)
    xd, yd = xy(fd, cd)
    xo, yo = xy(fo, co)
    yaw = round(float(math.atan2(yd - yi, xd - xi)), 3)          # inicio: mirando hacia el destino
    yaw_d = round(float(math.atan2(yi - yd, xi - xd)), 3)        # destino: mirando hacia el inicio
    puntos = {
        "inicio": {"x": xi, "y": yi, "yaw": yaw},
        "destino": {"x": xd, "y": yd, "yaw": yaw_d},
        "obstaculo": {"x": xo, "y": yo, "lado": 0.40, "alto": 0.80},
        "recorrido_m": round(float(len(recorrido) * res), 2),
        "margen_m": a.margen,
    }
    with open(os.path.join(destino, "puntos.yaml"), "w") as f:
        f.write("# Puntos de la prueba automática (generar_mundo_gazebo.py). Coordenadas del mapa, en m.\n")
        yaml.safe_dump(puntos, f, sort_keys=False)

    print(f"Mapa: {os.path.relpath(carpeta)}  ({ocupada.shape[1]} x {ocupada.shape[0]} celdas de {res} m)")
    print(f"Celdas ocupadas: {int(ocupada.sum())} -> {len(cajas)} cajas de {a.altura} m de alto")
    print(f"Zona libre apta (margen {a.margen} m): {int(zona.sum()) * res * res:.2f} m²")
    print(f"Inicio:    x={xi} y={yi} yaw={math.degrees(yaw):.0f}°")
    print(f"Destino:   x={xd} y={yd}  (recorrido de unos {puntos['recorrido_m']} m)")
    print(f"Obstáculo: x={xo} y={yo}")
    print(f"Escrito: {os.path.relpath(destino)}/mundo.sdf y puntos.yaml")


if __name__ == "__main__":
    main()
