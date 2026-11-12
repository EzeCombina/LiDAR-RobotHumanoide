#!/usr/bin/env python3
# =============================================================================
# medir_vibracion_imu.py — Mide la vibración del LiDAR L2 con su propia IMU
# -----------------------------------------------------------------------------
# Qué hace:
#   Se suscribe al tópico de la IMU del L2 (/unilidar/imu) durante unos
#   segundos y muestra:
#     - la aceleración media y su módulo (con el sensor quieto debe dar ~9,8 m/s²);
#     - el desvío estándar y el valor pico a pico de la aceleración (vibración);
#     - el desvío estándar de la velocidad angular (con el sensor quieto, ~0);
#     - las frecuencias dominantes de la vibración en cada eje (FFT).
#   Opcionalmente guarda las muestras en un CSV para analizarlas o enviarlas
#   al soporte técnico.
#
#   Sirve para tener un registro objetivo del estado mecánico del sensor
#   (por ejemplo, si hace ruido al girar) y comparar mediciones en el tiempo.
#   Medir SIEMPRE con el sensor quieto, sobre su almohadilla y en el piso o en
#   una superficie firme.
#
# Requisitos: driver del L2 corriendo; numpy (python3-numpy).
#
# Cómo se usa:
#   source /opt/ros/jazzy/setup.bash
#   ./scripts/sensor/medir_vibracion_imu.py                       # 15 s
#   ./scripts/sensor/medir_vibracion_imu.py --segundos 30 --csv imu_2026-11-12.csv
# =============================================================================
import argparse
import sys
import time

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


def main():
    p = argparse.ArgumentParser(description="Mide la vibración del L2 con su IMU.")
    p.add_argument("--topico", default="/unilidar/imu")
    p.add_argument("--segundos", type=float, default=15.0)
    p.add_argument("--csv", help="archivo donde guardar las muestras (opcional)")
    a = p.parse_args()

    rclpy.init()
    nodo = Node("medir_vibracion_imu")
    t, acel, giro = [], [], []

    def recibir(m):
        t.append(m.header.stamp.sec + m.header.stamp.nanosec * 1e-9)
        acel.append([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z])
        giro.append([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])

    nodo.create_subscription(Imu, a.topico, recibir, 1000)

    # Espera el primer mensaje (hasta 10 s).
    inicio = time.time()
    while not t and time.time() - inicio < 10:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    if not t:
        print(f"ERROR: no llegan mensajes en {a.topico}. ¿Está corriendo el driver?")
        sys.exit(1)

    print(f"Midiendo {a.segundos:.0f} s en {a.topico}... (no mover el sensor)")
    inicio = time.time()
    while time.time() - inicio < a.segundos:
        rclpy.spin_once(nodo, timeout_sec=0.1)
    nodo.destroy_node()
    rclpy.shutdown()

    t = np.array(t)
    acel = np.array(acel)
    giro = np.array(giro)
    fs = (len(t) - 1) / (t[-1] - t[0])

    np.set_printoptions(precision=3, suppress=True)
    media = acel.mean(axis=0)
    print(f"Muestras: {len(t)}  |  frecuencia de muestreo: {fs:.0f} Hz")
    print(f"Aceleración media [m/s²] (x, y, z): {media}  |  módulo: {np.linalg.norm(media):.3f}")
    print(f"Aceleración, desvío [m/s²]:         {acel.std(axis=0)}")
    print(f"Aceleración, pico a pico [m/s²]:    {acel.max(axis=0) - acel.min(axis=0)}")
    print(f"Velocidad angular, media [rad/s]:   {giro.mean(axis=0)}")
    print(f"Velocidad angular, desvío [rad/s]:  {giro.std(axis=0)}")

    # Frecuencias dominantes de la vibración (se descarta la componente continua).
    f = np.fft.rfftfreq(len(t), 1 / fs)
    for i, eje in enumerate("xyz"):
        espectro = np.abs(np.fft.rfft(acel[:, i] - acel[:, i].mean()))
        mayores = np.argsort(espectro[1:])[-3:][::-1] + 1
        print(f"Eje {eje}, frecuencias dominantes [Hz]: "
              + ", ".join(f"{f[k]:.1f}" for k in mayores))

    if a.csv:
        datos = np.column_stack([t, acel, giro])
        np.savetxt(a.csv, datos, delimiter=",", fmt="%.6f",
                   header="t_s,ax,ay,az,gx,gy,gz", comments="")
        print(f"Muestras guardadas en {a.csv}")


if __name__ == "__main__":
    main()
