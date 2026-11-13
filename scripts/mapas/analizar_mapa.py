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
#   Acepta la carpeta de un mapa (la que genera procesar_grabacion.sh, con
#   mapa.pcd y trayectoria.csv) o un archivo .pcd suelto.
#
#   2. Busca los planos principales (con RANSAC sobre una muestra de puntos):
#      - planos casi horizontales (piso, techo): cuánto se inclinan respecto
#        de la horizontal. Point-LIO alinea el mapa con la gravedad, así que
#        deberían dar menos de 1-2°; si dan más, el mapa quedó "torcido";
#      - la pared principal: su ángulo en planta respecto del eje X. Que las
#        paredes no sean paralelas a la grilla de RViz es NORMAL: la dirección
#        de los ejes x e y la fija hacia dónde apuntaba el sensor al empezar.
#   3. Si se indica el CSV de la trayectoria (lo genera procesar_grabacion.sh),
#      muestra el resumen (largo, zona recorrida, error de cierre) y una tabla
#      con la posición cada 10 segundos.
#
#   Solo usa NumPy (viene con ROS 2). No necesita el sensor.
#
# Cómo se usa:
#   ./scripts/mapas/analizar_mapa.py mapas/<carpeta_del_mapa>
#   ./scripts/mapas/analizar_mapa.py <archivo.pcd> [trayectoria.csv]
# =============================================================================
import os
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


def ransac_plano(P, condicion, iteraciones=1500, tolerancia=0.03, rng=None):
    """Plano con más puntos a menos de 'tolerancia' m, cuya normal cumpla 'condicion'.
    Devuelve (normal, d, máscara de puntos del plano) o None."""
    rng = rng or np.random.default_rng(0)
    mejor, mejor_n, mejor_d = None, None, None
    for _ in range(iteraciones):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        if not condicion(n):
            continue
        d = -n @ a
        dentro = np.abs(P @ n + d) < tolerancia
        if mejor is None or dentro.sum() > mejor.sum():
            mejor, mejor_n, mejor_d = dentro, n, d
    if mejor is None:
        return None
    # Ajuste fino por mínimos cuadrados con los puntos del plano.
    Q = P[mejor]
    centro = Q.mean(axis=0)
    n = np.linalg.svd(Q - centro, full_matrices=False)[2][2]
    if n[2] < 0:
        n = -n
    return n, -n @ centro, mejor


def refinar_plano(xyz, n, d, tolerancia=0.05):
    """Reajusta un plano con TODOS los puntos del mapa a menos de 'tolerancia' m
    (RANSAC trabaja sobre una muestra y en planos con pocos puntos puede mezclar
    bordes de muebles). Devuelve la normal refinada (con z positiva)."""
    # Se repite: con el plano reajustado se vuelven a elegir los puntos cercanos.
    # Una sola pasada hereda el error inicial (la franja elegida está torcida igual).
    for _ in range(10):
        Q = xyz[np.abs(xyz @ n + d) < tolerancia]
        if len(Q) < 50:
            break
        centro = Q.mean(axis=0)
        nueva = np.linalg.svd(Q - centro, full_matrices=False)[2][2]
        nueva = nueva if nueva[2] >= 0 else -nueva
        cambio = np.degrees(np.arccos(min(1.0, abs(nueva @ n))))
        n, d = nueva, -nueva @ centro
        if cambio < 0.01:
            break
    return n


def analizar_planos(xyz, muestra=40000):
    rng = np.random.default_rng(1)
    P = xyz[rng.choice(len(xyz), min(muestra, len(xyz)), replace=False)]
    print("\n  Planos principales (muestra de %d puntos):" % len(P))
    restantes = P
    for _ in range(2):  # piso y techo
        r = ransac_plano(restantes, lambda n: abs(n[2]) > np.cos(np.radians(30)), rng=rng)
        if r is None or r[2].sum() < 0.03 * len(P):
            break
        n, d, dentro = r
        n = refinar_plano(xyz, n, d)
        ang = np.degrees(np.arccos(min(1.0, abs(n[2]))))
        z = restantes[dentro][:, 2].mean()
        print(f"    plano horizontal a z = {z:5.2f} m: inclinación {ang:4.1f}° "
              f"({100 * dentro.sum() / len(P):.0f} % de los puntos)")
        restantes = restantes[~dentro]
    r = ransac_plano(P, lambda n: abs(n[2]) < np.sin(np.radians(20)), rng=rng)
    if r is not None:
        n = r[0]
        rumbo = np.degrees(np.arctan2(n[1], n[0])) % 90
        print(f"    pared principal: girada {rumbo:4.1f}° respecto del eje X en planta "
              f"(equivale a {rumbo - 90:5.1f}°; es normal, depende de la orientación inicial)")
    print("    Inclinación de piso/techo de más de 1-2°: el mapa no quedó nivelado.")


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
        print("Uso: analizar_mapa.py <carpeta_del_mapa | mapa.pcd> [trayectoria.csv]")
        sys.exit(1)
    entrada = sys.argv[1]
    if os.path.isdir(entrada):
        pcd = os.path.join(entrada, "mapa.pcd")
        tray = os.path.join(entrada, "trayectoria.csv")
    else:
        pcd = entrada
        tray = os.path.join(os.path.dirname(pcd), "trayectoria.csv")
    if len(sys.argv) > 2:
        tray = sys.argv[2]
    if not os.path.isfile(pcd):
        print(f"ERROR: no existe {pcd}")
        sys.exit(1)
    enc, xyz = leer_pcd(pcd)
    print(f"Mapa: {pcd}")
    print(f"  puntos: {len(xyz):,}".replace(",", "."))
    print(f"  campos: {' '.join(enc['FIELDS'])}")
    mn, mx = xyz.min(axis=0), xyz.max(axis=0)
    p1, p99 = np.percentile(xyz, 1, axis=0), np.percentile(xyz, 99, axis=0)
    print("\n  eje   mínimo   máximo  |  útil (1 %-99 %)   extensión útil")
    for i, eje in enumerate("xyz"):
        print(f"   {eje}  {mn[i]:7.2f}  {mx[i]:7.2f}  |  {p1[i]:6.2f} a {p99[i]:6.2f}   {p99[i] - p1[i]:6.2f} m")
    print("\n  El eje z es vertical (Point-LIO alinea el mapa con la gravedad); el origen")
    print("  (0, 0, 0) es la posición del sensor al empezar la grabación.")
    analizar_planos(xyz)
    if os.path.isfile(tray):
        analizar_trayectoria(tray)
    else:
        print(f"\n(Sin trayectoria: no existe {tray})")


if __name__ == "__main__":
    main()
