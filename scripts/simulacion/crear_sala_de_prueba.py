#!/usr/bin/env python3
# =============================================================================
# crear_sala_de_prueba.py — Mapa 2D de una sala de prueba para la simulación
# -----------------------------------------------------------------------------
# Qué hace:
#   Dibuja el mapa 2D de ocupación de una sala ficticia y lo guarda con el MISMO
#   formato que generar_mapa_2d.py (mapa_2d.pgm + mapa_2d.yaml + mapa_2d.png),
#   en mapas/sala_de_prueba/. Con generar_mundo_gazebo.py se convierte en el
#   mundo de Gazebo, así el mapa coincide exactamente con el mundo simulado.
#
#   Los mapas tomados con el sensor en la mano (habitación, oficina) tienen
#   muebles y ruido y casi no dejan zonas libres con espacio para el robot; la
#   sala de prueba sirve para probar la navegación de punto a punto.
#
#   Sala de 7 x 5 m (interior), paredes de 10 cm:
#     - una pared interior en x = 3,5 m con una puerta de 1 m (de y = 3,0 a 4,0 m);
#     - una mesa de 1,2 x 0,8 m en la mitad izquierda;
#     - un mueble de 0,4 x 1,5 m contra la pared derecha.
#   Fuera de la sala, desconocido. Origen del mapa en la esquina inferior
#   izquierda exterior (0, 0).
#
# Cómo se usa:
#   ./scripts/simulacion/crear_sala_de_prueba.py            # -> mapas/sala_de_prueba/
#   ./scripts/simulacion/crear_sala_de_prueba.py --carpeta mapas/otra_sala
# =============================================================================
import argparse
import os

import numpy as np
from PIL import Image

RES = 0.05            # m por celda, igual que generar_mapa_2d.py
ANCHO, ALTO = 7.2, 5.2  # exterior, en m (interior 7 x 5 + paredes de 0,1)
MARGEN = 0.5          # zona desconocida alrededor, en m


def main():
    p = argparse.ArgumentParser(description="Crea el mapa 2D de la sala de prueba.")
    p.add_argument("--carpeta", default="mapas/sala_de_prueba", help="carpeta de salida")
    a = p.parse_args()

    n_x, n_y = round((ANCHO + 2 * MARGEN) / RES), round((ALTO + 2 * MARGEN) / RES)
    img = np.full((n_y, n_x), 205, dtype=np.uint8)       # desconocido

    def celda(x, y):
        return round((x + MARGEN) / RES), round((y + MARGEN) / RES)

    def rect(x0, y0, x1, y1, valor):
        c0, f0 = celda(x0, y0)
        c1, f1 = celda(x1, y1)
        img[f0:f1, c0:c1] = valor

    rect(0, 0, ANCHO, ALTO, 0)                 # paredes (todo ocupado) ...
    rect(0.1, 0.1, ANCHO - 0.1, ALTO - 0.1, 254)  # ... y el interior libre
    rect(3.5, 0.1, 3.6, 3.1, 0)                # pared interior, abajo de la puerta
    rect(3.5, 4.1, 3.6, ALTO - 0.1, 0)         # pared interior, arriba de la puerta
    rect(1.2, 1.6, 2.4, 2.4, 0)                # mesa
    rect(ANCHO - 0.5, 1.0, ANCHO - 0.1, 2.5, 0)  # mueble contra la pared derecha

    os.makedirs(a.carpeta, exist_ok=True)
    # Fila 0 de la imagen = borde superior (y máxima), como en generar_mapa_2d.py
    Image.fromarray(img[::-1]).save(os.path.join(a.carpeta, "mapa_2d.pgm"))
    Image.fromarray(img[::-1]).save(os.path.join(a.carpeta, "mapa_2d.png"))
    with open(os.path.join(a.carpeta, "mapa_2d.yaml"), "w") as f:
        f.write("# Mapa 2D de la sala de prueba (scripts/simulacion/crear_sala_de_prueba.py)\n"
                "image: mapa_2d.pgm\nmode: trinary\n"
                f"resolution: {RES}\norigin: [{-MARGEN}, {-MARGEN}, 0.0]\n"
                "negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n")
    print(f"Sala de prueba: {ANCHO} x {ALTO} m, {n_x} x {n_y} celdas -> {a.carpeta}/mapa_2d.*")


if __name__ == "__main__":
    main()
