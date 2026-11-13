# 5. Conexión y puesta en marcha del sensor

## 5.1 Conexión física

El cable del sensor termina en el **módulo adaptador**:

| Conector del módulo | Se conecta a |
|---|---|
| Entrada de alimentación (plug DC 3,5 × 1,35 mm) | Fuente de 12 V / 1 A |
| RJ45 (Ethernet) | Placa Ethernet libre de la PC |
| USB-C | PC, solo en modo serie (punto 5.7) |

Pasos:

1. Apoyar el sensor sobre su almohadilla de goma, en una superficie firme.
2. Cable Ethernet del módulo a la placa libre de la PC.
3. Fuente al módulo. El sensor empieza a girar solo. En frío puede tardar unos minutos en entregar
   puntos, porque primero se calienta.

## 5.2 Configuración de red

El sensor viene de fábrica con la IP `192.168.1.62` y envía sus datos a `192.168.1.2`, puerto UDP
6201. Por eso la placa de la PC conectada al sensor tiene que tener **exactamente** la IP
`192.168.1.2`.

```bash
./scripts/red/configurar_red_lidar.sh eno1      # eno1 = nombre de la placa (capítulo 4.5)
```

El script:

1. Verifica que ninguna otra placa esté en la red `192.168.1.x` (choque de redes).
2. Crea un perfil de red llamado `lidar-l2` con IP fija `192.168.1.2/24` y **sin puerta de
   enlace**, para que internet siga saliendo por el Wi-Fi. El perfil se activa solo cada vez que se
   conecta el cable.
3. Si el firewall `ufw` está activo, abre el puerto UDP 6201 en esa placa (pide la contraseña).

Salida esperada (última línea): `eno1   UP   192.168.1.2/24`.

**Lo mismo, a mano:**

```bash
nmcli connection add type ethernet con-name lidar-l2 ifname eno1
nmcli connection modify lidar-l2 connection.autoconnect yes connection.autoconnect-priority 10 \
    ipv4.method manual ipv4.addresses 192.168.1.2/24 ipv4.gateway "" ipv4.never-default yes \
    ipv6.method disabled
nmcli connection up lidar-l2
sudo ufw allow in on eno1 to any port 6201 proto udp comment "LiDAR Unitree L2"
```

Para deshacerlo: `nmcli connection delete lidar-l2` y
`sudo ufw delete allow in on eno1 to any port 6201 proto udp`.

!!! importante "Choque de redes"
    Si el Wi-Fi (u otra placa) ya está en una red `192.168.1.x`, los datos del sensor no llegan bien.
    En ese caso hay que cambiar la red del sensor con el SDK (función `setLidarIpAddressConfig`;
    procedimiento todavía no probado en este proyecto).

## 5.3 Verificar la comunicación

**¿El sensor está en la red?**

```bash
ping -c 4 192.168.1.62
```

```text
64 bytes from 192.168.1.62: icmp_seq=1 ttl=128 time=0.171 ms
...
4 packets transmitted, 4 received, 0% packet loss
```

**¿Llegan los datos?** El `ping` no alcanza: hay que ver que lleguen paquetes al puerto 6201. El
script del proyecto solo escucha (no le envía nada al sensor) y no necesita `sudo`:

```bash
./scripts/red/verificar_udp_lidar.py
```

```text
Escuchando 192.168.1.2:6201 durante 5 s...
segundo  paquetes por tamaño (bytes: cantidad)
      0  80: 240, 1044: 204, 1124: 11
      1  80: 239, 1044: 204, 1124: 12
...
Origen: 192.168.1.62:6101
Tráfico promedio: 1.96 Mbit/s
```

Los paquetes de 1044 bytes (unos 205 por segundo) son los **puntos**; los de 80 bytes (unos 240
por segundo), la **IMU**. Alternativa clásica: `sudo tcpdump -i eno1 udp port 6201 -c 10`.

## 5.4 SDK del sensor y programa de ejemplo

El SDK de Unitree se descarga **fuera** del repositorio del proyecto, en `~/lidar_ws/`:

```bash
mkdir -p ~/lidar_ws && cd ~/lidar_ws
git clone https://github.com/unitreerobotics/unilidar_sdk2.git
cd unilidar_sdk2
git checkout 0e3c51f512e6b8ff60b8c32f160b412cb48445c2      # versión probada (v2.0.10)
cd unitree_lidar_sdk && mkdir -p build && cd build
cmake .. && make -j"$(nproc)"
```

Termina con `[100%] Built target ...`. El aviso de CMake `Compatibility with CMake < 3.5 will be
removed` no afecta. El mismo SDK se puede bajar como `.zip` desde la página de Unitree: es idéntico
a esta versión.

!!! peligro "No ejecutar set_ip_address"
    Junto con el ejemplo se compilan `set_ip_address` y `set_to_serial_mode`, que tienen IPs fijas
    de otra red (`192.168.123.110` / `.120`). **`set_ip_address` cambia la IP del sensor**, que deja
    de responder en `192.168.1.62`.

Ejecutar el ejemplo (se corta con **Ctrl+C**):

```bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_sdk/bin
./example_lidar_udp
```

```text
Unilidar initialization succeed!
set Lidar work mode to: 0
lidar hardware version = 2.2.1.1
lidar firmware version = 2.8.11.1
lidar sdk version = 2.0.9
...
dirty percentage = 4.806547 %
An IMU msg is parsed!
	linear_acceleration (x, y, z) = [-1.0475, -0.3436, 10.4363]
...
A Cloud msg is parsed!
	cloud size  = 5112, ringNum = 18
```

- **hardware / firmware version:** las versiones del sensor (anotarlas).
- **dirty percentage:** suciedad estimada de la ventana; si es alta, limpiarla con un paño suave.
- **linear_acceleration:** con el sensor quieto, un eje marca cerca de 9,8 m/s² (la gravedad).
- **cloud size / ringNum:** unos 5.000 puntos por mensaje, 18 anillos.

## 5.5 Estado interno del sensor

Cada paquete de puntos trae también el **estado interno** del sensor. La herramienta del proyecto
`estado_lidar` lo muestra (cerrar antes el ejemplo o el driver, que usan el mismo puerto):

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor
mkdir -p build && cd build
cmake .. && make
./estado_lidar udp 20        # 20 segundos
```

```text
Resumen del estado (4325 paquetes de puntos):
                            mínimo     promedio      máximo
  sys_rotation_period      4621.000     4624.262     4629.000
  com_rotation_period    229426.000   230091.540   231579.000
  dirty_index                 0.000        5.074       36.000
  packet_lost_up              0.000        0.000        0.000
  packet_lost_down            0.000        0.000        0.000
  apd_temperature            41.001       41.528       41.982
  apd_voltage               150.080      152.303      154.219
  laser_voltage              49.487       49.749       49.991
  imu_temperature            59.219       60.703       61.762
```

| Campo | Interpretación |
|---|---|
| `sys_rotation_period` | Período del motor del **espejo** en µs: 1 / 4.621 µs ≈ **216 Hz**, igual al barrido vertical del manual |
| `com_rotation_period` | Período del motor del **cabezal** en µs: ≈ **4,35 Hz** (el manual indica 5,55 Hz de barrido horizontal; a consultar con Unitree) |
| `packet_lost_*` | Pérdida de paquetes internos: tiene que ser 0 |
| `apd_temperature`, `apd_voltage` | Fotodetector: la tensión sube con la temperatura (compensación térmica) |
| `imu_temperature` | La IMU tiene calefacción controlada (~60 °C) |

Lo importante es que los períodos de los motores sean **estables**: en el sensor del laboratorio
varían menos de ±0,2 % (espejo) y ±0,7 % (cabezal).

## 5.6 Vibración del sensor

Con el driver corriendo (capítulo 6) y el sensor quieto sobre su almohadilla, la IMU permite medir
la vibración:

```bash
./scripts/sensor/medir_vibracion_imu.py --segundos 20 --csv docs/mediciones/imu_reposo_<fecha>.csv
```

Muestra la aceleración media, su variación, la velocidad angular y las frecuencias dominantes de la
vibración en cada eje. Con el sensor quieto, la velocidad angular tiene que estar cerca de 0 (si
no, la medición no es válida).

!!! nota "Observación sobre el sensor del laboratorio"
    El sensor del laboratorio hace un ruido notorio al girar. La medición mostró una vibración
    vertical de 9,2 m/s² pico a pico en **8,7 Hz, el doble exacto de la rotación del cabezal**, y
    una aceleración media en reposo de 7,8 m/s² en lugar de 9,8. La vibración está ligada a la
    parte que gira; no hay un valor de referencia de un L2 sano para comparar. Igualmente, el sensor
    funciona y los mapas obtenidos son buenos. Los datos están en `docs/mediciones/` para una
    consulta con Unitree.

## 5.7 Conexión por USB (pendiente de probar)

El L2 también puede enviar sus datos por un puerto serie, a través del USB-C del módulo. Hay un solo
modo activo a la vez, guardado en el sensor; de fábrica viene en Ethernet.

- Para pasar a USB hay que comunicarse primero por Ethernet y cambiar el modo con la herramienta
  del proyecto `scripts/sensor/build/cambiar_modo_lidar serie`. Después, apagar y prender el sensor.
  Para volver: `cambiar_modo_lidar ethernet` (conectado por USB).
- El driver se lanza con `modo:=usb` (capítulo 6), que usa el modo de trabajo 8. Con el `launch`
  original de Unitree, usar USB sin cambiar también el modo de trabajo devuelve el sensor a
  Ethernet y se corta la conexión.

Este procedimiento está preparado pero **todavía no se probó** con el sensor. Para usar el sensor
en el robot, tiene que quedar en **modo Ethernet**.
