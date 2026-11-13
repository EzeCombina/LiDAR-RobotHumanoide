#!/usr/bin/env python3
# =============================================================================
# generar_mapa_2d.py — Mapa 2D de ocupación para Nav2 a partir del mapa 3D
# -----------------------------------------------------------------------------
# Qué hace:
#   A partir del mapa 3D NIVELADO (mapa_limpio.pcd, generado con
#   limpiar_mapa.py: piso horizontal y en z = 0) arma una grilla vista desde
#   arriba, con celdas de 5 cm (--resolucion), y clasifica cada celda:
#     - OCUPADA (negro): tiene al menos --min-puntos puntos entre --altura-min y
#       --altura-max sobre el piso. Es la "franja de alturas" que puede chocar
#       el robot: lo que está más abajo (el piso, alfombras) y más arriba
#       (techo, lámparas por encima del robot) no cuenta como obstáculo.
#     - LIBRE (blanco): se vio el piso (puntos a menos de --piso del z = 0) y no
#       hay obstáculos; o pasó por ahí la persona que llevaba el sensor
#       (trayectoria_limpia.csv). Se rellenan huecos chicos del piso libre
#       (--cerrar).
#     - DESCONOCIDA (gris): no se vio.
#   Guarda en la carpeta del mapa:
#     mapa_2d.pgm   imagen (formato de Nav2: 0 ocupada, 254 libre, 205 desconocida)
#     mapa_2d.yaml  metadatos para nav2_map_server (resolución, origen, umbrales)
#     mapa_2d.png   la misma imagen en PNG, para verla o usarla en documentos
#
# ¿Sirve para cualquier mapa? Para cualquier mapa NIVELADO con el piso en z = 0
# y en el que se vea el piso (si no se ve el piso, casi todo queda
# "desconocido"; la trayectoria ayuda a marcar como libre por donde se caminó).
#
# Requisitos: python3-numpy y python3-scipy (paso 00); python3-pil para el PNG
# (opcional). No necesita ROS ni el sensor.
#
# Cómo se usa:
#   ./scripts/mapas/generar_mapa_2d.py mapas/<carpeta_del_mapa>
#   ./scripts/mapas/generar_mapa_2d.py mapas/<carpeta> --altura-max 1.30 --resolucion 0.10
#   ./scripts/mapas/generar_mapa_2d.py --ayuda
# =============================================================================
import argparse
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analizar_mapa import leer_pcd  # noqa: E402

OCUPADA, LIBRE, DESCONOCIDA = 0, 254, 205


def main():
    p = argparse.ArgumentParser(description="Mapa 2D de ocupación (Nav2) desde un mapa 3D nivelado.",
                                add_help=False)
    p.add_argument("entrada", nargs="?", help="carpeta del mapa (con mapa_limpio.pcd) o .pcd nivelado")
    p.add_argument("--resolucion", type=float, default=0.05, help="tamaño de celda en m (0.05)")
    p.add_argument("--altura-min", type=float, default=0.10, help="altura mínima de obstáculo en m (0.10)")
    p.add_argument("--altura-max", type=float, default=1.80, help="altura máxima de obstáculo en m (1.80)")
    p.add_argument("--piso", type=float, default=0.05, help="tolerancia del piso en m (0.05)")
    p.add_argument("--min-puntos", type=int, default=2, help="puntos para considerar ocupada una celda (2)")
    p.add_argument("--cerrar", type=int, default=2, help="iteraciones de relleno de huecos del piso (2)")
    p.add_argument("--margen", type=float, default=0.5, help="borde alrededor del mapa en m (0.5)")
    p.add_argument("--ayuda", "-h", action="help", help="muestra esta ayuda")
    a = p.parse_args()
    if not a.entrada:
        p.print_help()
        sys.exit(1)

    if os.path.isdir(a.entrada):
        carpeta = a.entrada
        pcd = os.path.join(carpeta, "mapa_limpio.pcd")
        if not os.path.isfile(pcd):
            print(f"ERROR: no existe {pcd}. Ejecutar antes: ./scripts/mapas/limpiar_mapa.py {carpeta}")
            sys.exit(1)
    else:
        pcd, carpeta = a.entrada, os.path.dirname(os.path.abspath(a.entrada))
        print("Atención: se asume que el .pcd está nivelado y con el piso en z = 0.")
    _, xyz = leer_pcd(pcd)
    tray = os.path.join(carpeta, "trayectoria_limpia.csv")

    # Grilla que cubre los puntos útiles (sin el 0,5 % más alejado) más un margen.
    lo = np.percentile(xyz[:, :2], 0.5, axis=0) - a.margen
    hi = np.percentile(xyz[:, :2], 99.5, axis=0) + a.margen
    ancho, alto = np.ceil((hi - lo) / a.resolucion).astype(int)

    def celdas(puntos):
        ij = np.floor((puntos[:, :2] - lo) / a.resolucion).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 0] < ancho) & (ij[:, 1] >= 0) & (ij[:, 1] < alto)
        return ij[ok]

    def contar(puntos):
        ij = celdas(puntos)
        c = np.zeros((ancho, alto), dtype=np.int32)
        np.add.at(c, (ij[:, 0], ij[:, 1]), 1)
        return c

    z = xyz[:, 2]
    ocupada = contar(xyz[(z >= a.altura_min) & (z <= a.altura_max)]) >= a.min_puntos
    piso = contar(xyz[np.abs(z) <= a.piso]) >= 1
    libre = piso.copy()
    if os.path.isfile(tray):
        d = np.loadtxt(tray, delimiter=",", skiprows=1, ndmin=2)
        recorrido = np.zeros_like(libre)
        ij = celdas(d[:, 1:4])
        recorrido[ij[:, 0], ij[:, 1]] = True
        # Por donde caminó la persona (unos 20 cm alrededor) está libre.
        libre |= ndimage.binary_dilation(recorrido, iterations=max(1, int(0.2 / a.resolucion)))
    if a.cerrar > 0:
        libre = ndimage.binary_closing(libre, iterations=a.cerrar)
    libre &= ~ocupada

    grilla = np.full((ancho, alto), DESCONOCIDA, dtype=np.uint8)
    grilla[libre] = LIBRE
    grilla[ocupada] = OCUPADA
    # Imagen: filas de arriba hacia abajo = y de mayor a menor (convención de Nav2).
    imagen = np.flipud(grilla.T)

    ruta_pgm = os.path.join(carpeta, "mapa_2d.pgm")
    with open(ruta_pgm, "wb") as f:
        f.write(f"P5\n# Mapa 2D generado con generar_mapa_2d.py\n{ancho} {alto}\n255\n".encode("ascii"))
        f.write(imagen.tobytes())
    ruta_yaml = os.path.join(carpeta, "mapa_2d.yaml")
    with open(ruta_yaml, "w") as f:
        f.write(
            "# Mapa 2D de ocupación para nav2_map_server (generar_mapa_2d.py)\n"
            f"# Franja de obstáculos: {a.altura_min:.2f} a {a.altura_max:.2f} m sobre el piso; "
            f"min_puntos={a.min_puntos}; piso ±{a.piso:.2f} m\n"
            "image: mapa_2d.pgm\n"
            "mode: trinary\n"
            f"resolution: {a.resolucion}\n"
            f"origin: [{lo[0]:.3f}, {lo[1]:.3f}, 0.0]\n"
            "negate: 0\n"
            "occupied_thresh: 0.65\n"
            # Nav2 calcula p = (255 - valor) / 255. Desconocida (205) da p = 0.19608: con
            # free_thresh = 0.196 queda desconocida; con un umbral mayor pasaría a LIBRE.
            "free_thresh: 0.196\n")
    try:
        from PIL import Image
        Image.fromarray(imagen).save(os.path.join(carpeta, "mapa_2d.png"))
        png = " y mapa_2d.png"
    except ImportError:
        png = " (sin PNG: falta python3-pil)"

    total = ancho * alto
    print(f"Mapa 3D: {pcd}")
    print(f"Grilla: {ancho} x {alto} celdas de {a.resolucion * 100:.0f} cm = "
          f"{ancho * a.resolucion:.2f} x {alto * a.resolucion:.2f} m")
    print(f"Origen (esquina inferior izquierda): x = {lo[0]:.3f} m, y = {lo[1]:.3f} m")
    print(f"Franja de obstáculos: {a.altura_min:.2f} a {a.altura_max:.2f} m sobre el piso")
    print(f"Celdas: ocupadas {100 * ocupada.sum() / total:.1f} %, libres {100 * libre.sum() / total:.1f} %, "
          f"desconocidas {100 * (total - ocupada.sum() - libre.sum()) / total:.1f} %")
    print(f"Trayectoria usada como zona libre: {'sí' if os.path.isfile(tray) else 'no (no existe ' + tray + ')'}")
    print(f"Guardado: {ruta_pgm}, {ruta_yaml}{png}")


if __name__ == "__main__":
    main()
