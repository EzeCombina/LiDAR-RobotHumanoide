# 3. El robot y su red

## 3.1 Las computadoras del R1

El R1 EDU tiene dos computadoras:

- La **computadora de movimiento** controla la marcha y el equilibrio. Es de Unitree y no se
  puede programar: solo se le envían órdenes (por ejemplo, "caminar a tal velocidad") con el SDK
  de Unitree.
- La **computadora de desarrollo** (PC2) es una **NVIDIA Jetson Orin NX**. Es para el código
  propio: acá van el driver del LiDAR y la grabación.

| Dato | Valor | Estado |
|---|---|---|
| Computadora de desarrollo | Jetson Orin NX, IP `192.168.123.164`, usuario `unitree` | Confirmado en la documentación |
| Computadora de movimiento | Probablemente `192.168.123.161` | **A VERIFICAR** |
| Acceso | `ssh unitree@192.168.123.164` (la contraseña de fábrica se cambia la primera vez con `passwd`) | Confirmado en la documentación |
| Sistema de la Jetson | Probablemente Ubuntu 20.04, JetPack 5.x y ROS 2 Foxy | **A VERIFICAR** |
| Interfaz cableada de la Jetson | `eth0` o `eth10` | **A VERIFICAR** |
| Panel superior | 1 RJ45 gigabit, 1 USB-C, salidas XT30 de 24 V / 3 A y 36 V / 5 A, entrada de parada de emergencia | Confirmado en la documentación |

!!! concepto "¿Qué es la Jetson?"
    Una computadora chica de NVIDIA pensada para robots, con un procesador ARM (arquitectura
    `aarch64`, la misma de los celulares y la Raspberry Pi) y una GPU. Usa Ubuntu adaptado por
    NVIDIA (JetPack). Los programas compilados para una PC común (`x86_64`) no corren en ella: hay
    que compilarlos de nuevo. El SDK del L2 ya trae su librería para las dos arquitecturas.

## 3.2 La red interna

!!! concepto "Red interna del robot"
    Las computadoras del R1 están unidas por una red Ethernet interna, `192.168.123.0/24`. No hay
    router ni DHCP: cada equipo tiene una IP fija configurada a mano. El RJ45 del panel está
    conectado a esa red: lo que se enchufa ahí "ve" a la Jetson y a la computadora de movimiento.

El sensor sale de fábrica en otra red (`192.168.1.62`, enviando los datos a `192.168.1.2`). Para
usarlo en el robot hay que cambiarle la red: que tenga una IP `192.168.123.x` libre y que envíe los
datos a la Jetson (`192.168.123.164`). Así **no se toca nada de la red de la Jetson**: el sensor es
el que se adapta (capítulo 5).

IPs a evitar en la red del robot:

| IP o bloque | Por qué |
|---|---|
| `.164` | La Jetson |
| `.161` | Probablemente la computadora de movimiento |
| `.1–.30` y `.120–.170` | Unitree los usa en otros modelos (LiDAR, cámaras, computadoras opcionales); por prudencia |
| `.51` | IP sugerida para una PC externa |

Se propone **`192.168.123.62`** para el sensor: está fuera de los bloques reservados y conserva el
último número de la IP de fábrica. Hay que comprobar con el robot que esté libre (capítulo 4).

!!! peligro "No tocar la red de la Jetson"
    No cambiar la configuración de la interfaz que tiene la `192.168.123.164`, no conectar un
    router ni un servidor DHCP a la red del robot y no hacer actualizaciones masivas del sistema
    de la Jetson (`apt upgrade`, cambiar JetPack). Se puede perder el acceso o romper los servicios
    de Unitree.
