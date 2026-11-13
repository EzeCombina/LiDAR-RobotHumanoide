#!/usr/bin/env python3
# =============================================================================
# limpiar_mapa.py — Nivela, alinea y limpia un mapa 3D (.pcd)
# -----------------------------------------------------------------------------
# Qué hace (en este orden):
#   1. Reduce la densidad: un solo punto por celda de 3 cm (--voxel). Los mapas
#      de Point-LIO repiten muchas veces los mismos puntos; así el archivo pasa
#      de decenas de MB a pocos MB sin perder forma.
#   2. Quita puntos sueltos: los que están mucho más lejos de sus vecinos que
#      el promedio (ruido, reflejos aislados). Ajustable con --vecinos/--sigma.
#   3. NIVELA el mapa: busca el piso (el plano casi horizontal más bajo, con
#      RANSAC) y rota la nube para que quede perfectamente horizontal y a
#      altura z = 0. Corrige la inclinación que deja el SLAM (por ejemplo, si el
#      sensor no estaba quieto al empezar a grabar).
#   4. ALINEA las paredes con los ejes x e y (giro alrededor del eje vertical),
#      para que la habitación quede "derecha" respecto de la grilla de RViz y
#      del mapa 2D. Se puede desactivar con --sin-alinear.
#   5. Guarda en la carpeta del mapa:
#        mapa_limpio.pcd          la nube resultante (x y z intensity)
#        trayectoria_limpia.csv   la trayectoria con la misma transformación
#        transformacion.txt       la matriz 4x4 aplicada (mapa original -> limpio)
#        limpieza.txt             el resumen de lo que se hizo
#
# ¿Sirve para cualquier mapa? Sí: cualquier .pcd con campos x, y, z, de
# cualquier lugar y con el sensor en cualquier orientación. Limitación: para
# nivelar necesita VER EL PISO. Si el mapa no tiene piso (por ejemplo, grabado
# con el sensor horizontal, que solo ve hacia arriba), usar --referencia techo
# o --sin-nivelar. Si no encuentra el plano pedido, avisa y no nivela.
#
# Requisitos: python3-numpy y python3-scipy (paso 00). No necesita ROS ni el sensor.
#
# Cómo se usa:
#   ./scripts/mapas/limpiar_mapa.py mapas/<carpeta_del_mapa>
#   ./scripts/mapas/limpiar_mapa.py mapas/<carpeta> --voxel 0.05 --sin-alinear
#   ./scripts/mapas/limpiar_mapa.py mapas/<carpeta> --referencia techo
#   ./scripts/mapas/limpiar_mapa.py --ayuda   (lista de opciones)
# =============================================================================
import argparse
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

# Lectura de PCD y búsqueda de planos: las mismas funciones que analizar_mapa.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analizar_mapa import leer_pcd, ransac_plano  # noqa: E402


def leer_pcd_con_intensidad(ruta):
    """Devuelve (xyz Nx3, intensidad N) leyendo el PCD con leer_pcd."""
    enc, xyz = leer_pcd(ruta)
    # leer_pcd devuelve solo xyz; la intensidad se vuelve a leer si existe.
    intensidad = np.zeros(len(xyz))
    if "intensity" in enc["FIELDS"]:
        campos = enc["FIELDS"]
        tam = [int(s) for s in enc["SIZE"]]
        n = int(enc["POINTS"][0])
        if enc["DATA"][0] == "binary" and all(t == "F" for t in enc["TYPE"]) and set(tam) == {4}:
            with open(ruta, "rb") as f:
                while not f.readline().startswith(b"DATA"):
                    pass
                datos = np.frombuffer(f.read(n * 4 * len(campos)), dtype=np.float32).reshape(n, len(campos))
            ok = np.isfinite(datos[:, :3]).all(axis=1)
            intensidad = datos[ok, campos.index("intensity")].astype(np.float64)
    return xyz, intensidad


def miles(n):
    """Número entero con punto como separador de miles (1.234.567)."""
    return f"{n:,}".replace(",", ".")


def reducir_voxel(xyz, intensidad, tam):
    """Un punto por celda cúbica de lado 'tam' (promedio de los puntos de la celda)."""
    idx = np.floor(xyz / tam).astype(np.int64)
    _, inversa, cuenta = np.unique(idx, axis=0, return_inverse=True, return_counts=True)
    inversa = inversa.ravel()
    suma = np.zeros((len(cuenta), 3))
    np.add.at(suma, inversa, xyz)
    suma_i = np.bincount(inversa, weights=intensidad, minlength=len(cuenta))
    return suma / cuenta[:, None], suma_i / cuenta


def quitar_sueltos(xyz, intensidad, vecinos, sigma):
    """Filtro estadístico: quita los puntos cuya distancia media a sus 'vecinos'
    más cercanos supera el promedio + sigma desvíos."""
    arbol = cKDTree(xyz)
    dist, _ = arbol.query(xyz, k=vecinos + 1)
    media = dist[:, 1:].mean(axis=1)
    umbral = media.mean() + sigma * media.std()
    ok = media <= umbral
    return xyz[ok], intensidad[ok], int((~ok).sum())


def rotacion_entre(a, b):
    """Matriz de rotación que lleva el vector unitario a al vector unitario b."""
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def buscar_planos_horizontales(xyz, rng, muestra=40000, maximo=5, minimo=0.01):
    """Planos casi horizontales (normal a menos de 30° de la vertical), de mayor a
    menor cantidad de puntos. Devuelve lista de (normal, altura media, fracción,
    puntos del plano)."""
    P = xyz[rng.choice(len(xyz), min(muestra, len(xyz)), replace=False)]
    restantes, planos = P, []
    for _ in range(maximo):
        if len(restantes) < 100:
            break
        r = ransac_plano(restantes, lambda n: abs(n[2]) > np.cos(np.radians(30)), rng=rng)
        if r is None or r[2].sum() < minimo * len(P):
            break
        n, _, dentro = r
        planos.append((n, restantes[dentro][:, 2].mean(), dentro.sum() / len(P), restantes[dentro]))
        restantes = restantes[~dentro]
    return planos


def main():
    p = argparse.ArgumentParser(description="Nivela, alinea y limpia un mapa .pcd.", add_help=False)
    p.add_argument("entrada", nargs="?", help="carpeta del mapa (con mapa.pcd) o archivo .pcd")
    p.add_argument("--voxel", type=float, default=0.03, help="tamaño de celda en m (defecto 0.03)")
    p.add_argument("--vecinos", type=int, default=10, help="vecinos del filtro de puntos sueltos (10)")
    p.add_argument("--sigma", type=float, default=2.0, help="umbral del filtro, en desvíos (2.0)")
    p.add_argument("--referencia", choices=["piso", "techo"], default="piso",
                   help="plano usado para nivelar (defecto piso)")
    p.add_argument("--sin-nivelar", action="store_true", help="no nivelar")
    p.add_argument("--sin-alinear", action="store_true", help="no alinear las paredes con los ejes")
    p.add_argument("--salida", help="carpeta de salida (defecto: la del mapa)")
    p.add_argument("--ayuda", "-h", action="help", help="muestra esta ayuda")
    a = p.parse_args()
    if not a.entrada:
        p.print_help()
        sys.exit(1)

    if os.path.isdir(a.entrada):
        pcd = os.path.join(a.entrada, "mapa.pcd")
        tray = os.path.join(a.entrada, "trayectoria.csv")
    else:
        pcd, tray = a.entrada, os.path.join(os.path.dirname(a.entrada), "trayectoria.csv")
    if not os.path.isfile(pcd):
        print(f"ERROR: no existe {pcd}")
        sys.exit(1)
    salida = a.salida or os.path.dirname(os.path.abspath(pcd))
    os.makedirs(salida, exist_ok=True)
    rng = np.random.default_rng(0)
    informe = [f"Mapa de entrada: {pcd}"]

    def log(texto):
        print(texto)
        informe.append(texto)

    # 1. Densidad
    xyz, inten = leer_pcd_con_intensidad(pcd)
    n0 = len(xyz)
    xyz, inten = reducir_voxel(xyz, inten, a.voxel)
    log(f"1. Reducción a celdas de {a.voxel * 100:.0f} cm: {miles(n0)} -> {miles(len(xyz))} puntos")

    # 2. Puntos sueltos
    xyz, inten, quitados = quitar_sueltos(xyz, inten, a.vecinos, a.sigma)
    log(f"2. Puntos sueltos quitados: {miles(quitados)} (vecinos={a.vecinos}, sigma={a.sigma}) "
        f"-> quedan {miles(len(xyz))}")

    R = np.eye(3)
    t = np.zeros(3)

    # 3. Nivelación
    if a.sin_nivelar:
        log("3. Nivelación: omitida (--sin-nivelar)")
    else:
        planos = buscar_planos_horizontales(xyz, rng)
        for n, z, f, _ in planos:
            ang = np.degrees(np.arccos(min(1.0, abs(n[2]))))
            log(f"   plano horizontal a z = {z:6.2f} m, inclinación {ang:4.1f}°, {f * 100:4.1f} % de los puntos")
        if not planos:
            log("3. Nivelación: NO se encontraron planos horizontales; el mapa no se nivela.")
        else:
            elegido = min(planos, key=lambda q: q[1]) if a.referencia == "piso" else max(planos, key=lambda q: q[1])
            n, z_ref, _, puntos_plano = elegido
            if a.referencia == "piso" and len(planos) > 1 and max(q[1] for q in planos) - z_ref < 1.0:
                log("   ATENCIÓN: los planos horizontales están a menos de 1 m de altura entre sí; "
                    "puede que el plano elegido no sea el piso. Revisar el resultado.")
            R = rotacion_entre(n / np.linalg.norm(n), np.array([0.0, 0.0, 1.0]))
            rotado = xyz @ R.T
            # Altura del plano de referencia después de rotar: mediana de sus puntos.
            z_plano = float(np.median((puntos_plano @ R.T)[:, 2]))
            # Control: el piso es la superficie más baja, casi no puede haber puntos debajo.
            debajo = float(np.mean(rotado[:, 2] < z_plano - 0.10))
            if a.referencia == "piso" and debajo > 0.05:
                log(f"3. Nivelación: NO se hace. El plano más bajo (z = {z_ref:.2f} m) tiene el "
                    f"{debajo * 100:.0f} % de los puntos por debajo: no es el piso (¿el mapa no ve el piso?).")
                log("   Probar con --referencia techo, o --sin-nivelar.")
                R = np.eye(3)
                planos = None
            else:
                xyz = rotado
        if planos:
            desplazamiento = -z_plano if a.referencia == "piso" else 0.0
            xyz[:, 2] += desplazamiento
            t[2] += desplazamiento
            corr = np.degrees(np.arccos(min(1.0, abs(n[2]))))
            log(f"3. Nivelación con el {a.referencia}: inclinación corregida {corr:.1f}°"
                + (f"; piso llevado a z = 0 (desplazamiento {desplazamiento:+.2f} m)" if a.referencia == "piso" else ""))
            # Segunda pasada (solo con el piso): reajuste con todos los puntos de la franja
            # del piso (±5 cm de z = 0), más preciso que RANSAC sobre una muestra.
            if a.referencia == "piso":
                franja = xyz[np.abs(xyz[:, 2]) < 0.05]
                if len(franja) > 100:
                    c = franja.mean(axis=0)
                    n2 = np.linalg.svd(franja - c, full_matrices=False)[2][2]
                    cerca = franja[np.abs((franja - c) @ n2) < 0.02]
                    c = cerca.mean(axis=0)
                    n2 = np.linalg.svd(cerca - c, full_matrices=False)[2][2]
                    n2 = n2 if n2[2] > 0 else -n2
                    R2 = rotacion_entre(n2, np.array([0.0, 0.0, 1.0]))
                    xyz = xyz @ R2.T
                    dz = -float(np.median((cerca @ R2.T)[:, 2]))
                    xyz[:, 2] += dz
                    R, t = R2 @ R, R2 @ t + np.array([0, 0, dz])
                    log(f"   Refinamiento con la franja del piso ({miles(len(cerca))} puntos): "
                        f"{np.degrees(np.arccos(min(1.0, n2[2]))):.2f}° adicionales")

    # 4. Alineación de paredes
    if a.sin_alinear:
        log("4. Alineación de paredes: omitida (--sin-alinear)")
    else:
        P = xyz[rng.choice(len(xyz), min(40000, len(xyz)), replace=False)]
        r = ransac_plano(P, lambda n: abs(n[2]) < np.sin(np.radians(15)), rng=rng)
        if r is None:
            log("4. Alineación: no se encontró una pared vertical; se omite.")
        else:
            n = r[0]
            rumbo = np.arctan2(n[1], n[0])
            giro = -(((rumbo + np.pi / 4) % (np.pi / 2)) - np.pi / 4)   # menor giro que deja la pared sobre x o y
            c, s = np.cos(giro), np.sin(giro)
            Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
            xyz = xyz @ Rz.T
            R = Rz @ R
            t = Rz @ t
            log(f"4. Alineación de paredes: giro de {np.degrees(giro):+.1f}° alrededor del eje vertical")

    # 5. Guardado
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, t
    ruta_pcd = os.path.join(salida, "mapa_limpio.pcd")
    escribir_pcd(ruta_pcd, xyz, inten)
    np.savetxt(os.path.join(salida, "transformacion.txt"), T, fmt="%.6f",
               header="Matriz 4x4: punto_limpio = T * punto_original (coordenadas homogéneas)")
    log(f"5. Guardado {ruta_pcd}: {miles(len(xyz))} puntos, "
        f"{os.path.getsize(ruta_pcd) / 1e6:.1f} MB")
    if os.path.isfile(tray):
        transformar_trayectoria(tray, os.path.join(salida, "trayectoria_limpia.csv"), R, t)
        log("   trayectoria_limpia.csv: trayectoria con la misma transformación")
    lo, hi = np.percentile(xyz, 1, axis=0), np.percentile(xyz, 99, axis=0)
    log(f"   Extensión útil (1 %-99 %): x {hi[0] - lo[0]:.2f} m, y {hi[1] - lo[1]:.2f} m, "
        f"z {lo[2]:.2f} a {hi[2]:.2f} m")
    with open(os.path.join(salida, "limpieza.txt"), "w") as f:
        f.write("\n".join(informe) + "\n")


def escribir_pcd(ruta, xyz, intensidad):
    datos = np.column_stack([xyz, intensidad]).astype(np.float32)
    encabezado = (
        "# .PCD v0.7 - Point Cloud Data file format\n"
        "VERSION 0.7\nFIELDS x y z intensity\nSIZE 4 4 4 4\nTYPE F F F F\nCOUNT 1 1 1 1\n"
        f"WIDTH {len(datos)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {len(datos)}\nDATA binary\n")
    with open(ruta, "wb") as f:
        f.write(encabezado.encode("ascii"))
        f.write(datos.tobytes())


def transformar_trayectoria(origen, destino, R, t):
    d = np.loadtxt(origen, delimiter=",", skiprows=1, ndmin=2)
    p = d[:, 1:4] @ R.T + t
    # Orientación: q_nuevo = q_R * q (q en formato x, y, z, w).
    qr = cuaternion_desde_matriz(R)
    q = np.array([multiplicar_cuaterniones(qr, fila) for fila in d[:, 4:8]])
    np.savetxt(destino, np.column_stack([d[:, 0], p, q]), delimiter=",", fmt="%.6f",
               header="t,x,y,z,qx,qy,qz,qw", comments="")


def cuaternion_desde_matriz(R):
    w = np.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return np.array([x, y, z, w])


def multiplicar_cuaterniones(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz])


if __name__ == "__main__":
    main()
