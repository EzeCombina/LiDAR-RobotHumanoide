#!/usr/bin/env python3
# =============================================================================
# analizar_mapa.py — Datos de un mapa .pcd y de su trayectoria
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Lee un mapa .pcd (formato binario o ASCII, como los que guarda Point-LIO)
#      y muestra: cantidad de puntos, campos, extensión mínima y máxima en cada
#      eje y extensión "útil" (percentiles 1 % y 99 %, que descartan puntos
#      sueltos lejanos). Sirve para comprobar que las medidas del lugar son
#      razonables.
#   2. Si se indica el CSV de la trayectoria (lo genera procesar_grabacion.sh),
#      muestra el resumen (largo, zona recorrida, error de cierre) y una tabla
#      con la posición cada 10 segundos.
#
#   Solo usa NumPy (viene con ROS 2). No necesita el sensor.
#
# Cómo se usa:
#   ./scripts/analizar_mapa.py mapas/<mapa>.pcd
#   ./scripts/analizar_mapa.py mapas/<mapa>.pcd mapas/<mapa>_trayectoria.csv
# =============================================================================
import sys

import numpy as np


def leer_pcd(ruta):
    """Devuelve (encabezado como dict, matriz Nx3 con x, y, z)."""
    with open(ruta, "rb") as f:
        enc = {}
        while True:
            linea = f.readline()
            if not linea:
                raise ValueError("archivo PCD sin línea DATA")
            linea = linea.decode("ascii", "replace").strip()
            if linea.startswith("#") or not linea:
                continue
            clave, *valores = linea.split()
            enc[clave] = valores
            if clave == "DATA":
                break
        campos = enc["FIELDS"]
        tamanos = [int(s) for s in enc["SIZE"]]
        tipos = enc["TYPE"]
        n = int(enc["POINTS"][0])
        mapa_tipos = {("F", 4): "f4", ("F", 8): "f8", ("U", 1): "u1", ("U", 2): "u2",
                      ("U", 4): "u4", ("I", 1): "i1", ("I", 2): "i2", ("I", 4): "i4"}
        dtype = np.dtype([(c, mapa_tipos[(t, s)]) for c, t, s in zip(campos, tipos, tamanos)])
        if enc["DATA"][0] == "binary":
            datos = np.frombuffer(f.read(n * dtype.itemsize), dtype=dtype, count=n)
        elif enc["DATA"][0] == "ascii":
            datos = np.loadtxt(f, dtype=dtype, max_rows=n)
        else:
            raise ValueError(f"formato DATA '{enc['DATA'][0]}' no soportado")
    xyz = np.column_stack([datos["x"], datos["y"], datos["z"]]).astype(np.float64)
    return enc, xyz[np.isfinite(xyz).all(axis=1)]


def analizar_trayectoria(ruta):
    d = np.loadtxt(ruta, delimiter=",", skiprows=1, ndmin=2)
    if len(d) < 2:
        print("\nTrayectoria: sin datos suficientes.")
        return
    t, p = d[:, 0] - d[0, 0], d[:, 1:4]
    largo = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
    cierre = p[-1] - p[0]
    rango = p.max(axis=0) - p.min(axis=0)
    print(f"\nTrayectoria: {len(d)} muestras, {t[-1]:.1f} s")
    print(f"  largo del recorrido: {largo:.2f} m")
    print(f"  zona recorrida (x, y, z): {rango[0]:.2f} x {rango[1]:.2f} x {rango[2]:.2f} m")
    print(f"  error de cierre: {np.linalg.norm(cierre):.3f} m "
          f"(horizontal {np.linalg.norm(cierre[:2]):.3f} m, vertical {cierre[2]:+.3f} m)")
    print("\n  t [s]       x       y       z   [m]")
    for s in range(0, int(t[-1]) + 1, 10):
        i = min(np.searchsorted(t, s), len(t) - 1)
        print(f"  {s:5d}  {p[i, 0]:6.2f}  {p[i, 1]:6.2f}  {p[i, 2]:6.2f}")


def main():
    if len(sys.argv) < 2:
        print("Uso: analizar_mapa.py <mapa.pcd> [trayectoria.csv]")
        sys.exit(1)
    enc, xyz = leer_pcd(sys.argv[1])
    print(f"Mapa: {sys.argv[1]}")
    print(f"  puntos: {len(xyz):,}".replace(",", "."))
    print(f"  campos: {' '.join(enc['FIELDS'])}")
    mn, mx = xyz.min(axis=0), xyz.max(axis=0)
    p1, p99 = np.percentile(xyz, 1, axis=0), np.percentile(xyz, 99, axis=0)
    print("\n  eje   mínimo   máximo  |  útil (1 %-99 %)   extensión útil")
    for i, eje in enumerate("xyz"):
        print(f"   {eje}  {mn[i]:7.2f}  {mx[i]:7.2f}  |  {p1[i]:6.2f} a {p99[i]:6.2f}   {p99[i] - p1[i]:6.2f} m")
    print("\n  El eje z es vertical (Point-LIO alinea el mapa con la gravedad); el origen")
    print("  (0, 0, 0) es la posición del sensor al empezar la grabación.")
    if len(sys.argv) > 2:
        analizar_trayectoria(sys.argv[2])


if __name__ == "__main__":
    main()
