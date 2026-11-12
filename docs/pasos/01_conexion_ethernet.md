# Paso 01 — Conexión del LiDAR por Ethernet

## Objetivo

Conectar el LiDAR L2 a la PC por Ethernet, configurar la red, comprobar que llegan los datos y leer
las versiones de hardware y firmware del sensor con el programa de ejemplo del SDK oficial.

Ethernet es el **modo de fábrica** del sensor y es la conexión que se va a usar en el robot. Además,
es obligatorio pasar por este paso para poder habilitar la conexión USB (paso 02).

## Requisitos

- Paso 00 completo (ROS 2 Jazzy, herramientas de compilación, repositorio clonado).
- LiDAR Unitree L2 con su módulo adaptador, la fuente de 12 V y un cable Ethernet.
- Una placa Ethernet libre en la PC (en la PC del laboratorio: `eno1`).
- Multímetro.

> **¿Qué es un LiDAR?** Un sensor que mide distancias con pulsos de luz láser. El L2 gira y barre
> el espacio a su alrededor: en cada segundo mide unos 64.000 puntos. Cada punto tiene coordenadas
> X, Y, Z (en metros) y una intensidad. El conjunto de puntos de una vuelta se llama **nube de
> puntos**. El L2 trae además una **IMU** (*Inertial Measurement Unit*): un acelerómetro y un
> giróscopo que miden cómo se mueve el sensor.

## 1. Conexión física

El cable del sensor termina en un **módulo adaptador** que tiene tres conectores:

| Conector del módulo | Se conecta a |
|---|---|
| Entrada de alimentación (plug DC 3,5 × 1,35 mm) | Fuente de 12 V / 1 A incluida |
| RJ45 (Ethernet) | Placa Ethernet libre de la PC |
| USB-C | PC (solo en modo serie, ver paso 02) |

### 1.1 Medir la polaridad de la fuente antes de conectarla

El manual del L2 no especifica la polaridad del plug. Antes de conectar una fuente por primera vez
(y siempre que se use una fuente distinta de la original):

1. Enchufar la fuente a 220 V **sin conectarla al sensor**.
2. Multímetro en tensión continua (V DC), escala de 20 V.
3. Punta roja **dentro** del plug (pin central), punta negra en la parte **exterior**.
4. Lectura esperada: **+12 V aproximadamente** (centro positivo).

Medición en la fuente original del laboratorio: **A VERIFICAR (pendiente de registrar)**.

> **Atención:** el L2 se alimenta con **12 V**. No conectarlo nunca a 24 V ni a 36 V (por ejemplo, a
> las salidas XT30 del robot): hace falta un conversor DC-DC.

### 1.2 Conectar

1. Cable Ethernet del módulo adaptador a la placa libre de la PC.
2. Fuente al módulo adaptador.
3. El sensor empieza a girar solo (modo de fábrica: arranque automático). Si está frío, puede
   tardar en entregar puntos porque primero se calienta.

## 2. Configuración de red

El sensor de fábrica tiene la IP `192.168.1.62` y envía sus datos a la IP `192.168.1.2`, puerto UDP
6201. Por eso la placa de la PC conectada al sensor tiene que tener **exactamente** la IP
`192.168.1.2`.

| Parámetro | Valor de fábrica |
|---|---|
| IP del sensor | `192.168.1.62` / 24 |
| IP de destino (la PC) | `192.168.1.2` |
| Puertos UDP | sensor 6101 → PC 6201 |

> **Choque de redes:** si otra placa de la PC (por ejemplo, el Wi-Fi) ya está en una red
> `192.168.1.x`, hay conflicto. Revisar con `ip -br addr`. En ese caso hay que cambiar la red del
> sensor con el SDK (función `setLidarIpAddressConfig`; procedimiento A VERIFICAR) y pasarle la
> IP nueva al script y al driver.

### 2.1 Con el script del proyecto

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/configurar_red_lidar.sh eno1
```

El script:

1. Verifica que no haya choque de redes.
2. Crea un perfil de NetworkManager llamado `lidar-l2` en la placa indicada, con IP fija
   `192.168.1.2/24`, **sin puerta de enlace** (así internet sigue saliendo por el Wi-Fi) y con
   prioridad 10 (le gana al perfil por DHCP que Ubuntu crea solo para cada placa).
3. Si el firewall `ufw` está activo, abre el puerto UDP 6201 solo en esa placa (pide la contraseña
   de `sudo`).

**Salida esperada (última línea):**

```text
== Estado final
eno1             UP             192.168.1.2/24
```

### 2.2 Qué hace el script, comando por comando

Para entenderlo o hacerlo a mano:

```bash
nmcli connection add type ethernet con-name lidar-l2 ifname eno1
nmcli connection modify lidar-l2 connection.autoconnect yes connection.autoconnect-priority 10 \
    ipv4.method manual ipv4.addresses 192.168.1.2/24 ipv4.gateway "" ipv4.never-default yes \
    ipv6.method disabled
nmcli connection up lidar-l2
sudo ufw allow in on eno1 to any port 6201 proto udp comment "LiDAR Unitree L2"
```

Para deshacerlo:

```bash
nmcli connection delete lidar-l2
sudo ufw delete allow in on eno1 to any port 6201 proto udp
```

## 3. Verificar la comunicación

### 3.1 Ping

```bash
ping -c 4 192.168.1.62
```

**Salida esperada:**

```text
64 bytes from 192.168.1.62: icmp_seq=1 ttl=128 time=0.171 ms
...
4 packets transmitted, 4 received, 0% packet loss
```

### 3.2 Llegada de los datos

`ping` solo prueba que el sensor está en la red. Lo importante es que **lleguen los datos** al
puerto 6201. Con el script del proyecto (no necesita `sudo`, no le envía nada al sensor):

```bash
./scripts/verificar_udp_lidar.py
```

**Salida esperada** (PC del laboratorio, 2026-11-12):

```text
Escuchando 192.168.1.2:6201 durante 5 s...
segundo  paquetes por tamaño (bytes: cantidad)
      0  80: 240, 1044: 204, 1124: 11
      1  80: 239, 1044: 204, 1124: 12
...
Origen: 192.168.1.62:6101
Tráfico promedio: 1.96 Mbit/s
```

| Tamaño | Cantidad por segundo | Contenido |
|---|---|---|
| 1044 bytes | ~205 | Puntos de la nube 3D |
| 80 bytes | ~240 | IMU |
| 1124 bytes | ~11 | Tipo no identificado (**A VERIFICAR**) |

> Con el sensor recién encendido se observaron solo los paquetes de 1044 bytes. Los de IMU
> aparecieron después de conectarse una vez con el programa de ejemplo del punto 4.

Alternativa clásica, con `sudo`:

```bash
sudo tcpdump -i eno1 udp port 6201 -c 10
```

## 4. Programa de ejemplo del SDK y versiones del sensor

### 4.1 Descargar y compilar el SDK

El SDK se clona **fuera** del repositorio del proyecto, en `~/lidar_ws`:

```bash
mkdir -p ~/lidar_ws && cd ~/lidar_ws
git clone https://github.com/unitreerobotics/unilidar_sdk2.git
cd unilidar_sdk2
git checkout 0e3c51f512e6b8ff60b8c32f160b412cb48445c2   # versión probada (SDK v2.0.10)

cd unitree_lidar_sdk
mkdir -p build && cd build
cmake ..
make -j"$(nproc)"
```

> **Alternativa sin git:** la página oficial (`https://www.unitree.com/download/L2`) ofrece el
> "Unilidar SDK 2 Software Package" como `unilidar_sdk2-2.0.10.zip`. Se verificó que su contenido
> es idéntico al commit `0e3c51f` (tag `v2.0.10`). Descomprimirlo en `~/lidar_ws/` y renombrar la
> carpeta a `unilidar_sdk2`. El paquete trae tres carpetas: `unitree_lidar_sdk/` (SDK en C++),
> `unitree_lidar_ros2/` (driver ROS 2, el que usa este proyecto) y `unitree_lidar_ros/` (driver
> ROS 1, que no aplica en Ubuntu 24.04).

**Salida esperada:** termina con `[100%] Built target ...` para los cinco programas. CMake muestra
un aviso `CMake Deprecation Warning ... Compatibility with CMake < 3.5 will be removed`: no afecta.

Los ejecutables quedan en `~/lidar_ws/unilidar_sdk2/unitree_lidar_sdk/bin/`.

> **No ejecutar `set_ip_address`** (ni `set_to_serial_mode`): se compilan junto con el ejemplo, pero
> tienen IPs fijas de otra red (`192.168.123.110` / `.120`). `set_ip_address` **cambia la IP del
> sensor** y deja de responder en `192.168.1.62`.

### 4.2 Ejecutar el ejemplo

```bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_sdk/bin
./example_lidar_udp
```

El programa no termina solo: se corta con **Ctrl+C**. Antes de leer datos, le reenvía al sensor el
modo de trabajo 0 (el de fábrica, no cambia nada) y lo reinicia.

**Salida obtenida (resumida):**

```text
[UDPHandler] bind udp port success. port 6201.
Unilidar initialization succeed!
set Lidar work mode to: 0
lidar hardware version = 2.2.1.1
lidar firmware version = 2.8.11.1
lidar sdk version = 2.0.9
stop lidar rotation ...
start lidar rotation ...
dirty percentage = 4.806547 %
time delay (second) = 0.002589
An IMU msg is parsed!
	quaternion (x, y, z, w) = [0.9973, -0.0137, 0.0084, 0.0426]
	angular_velocity (x, y, z) = [0.0422, 0.1214, 0.0055]
	linear_acceleration (x, y, z) = [-1.0475, -0.3436, 10.4363]
...
A Cloud msg is parsed!
	cloud size  = 5112, ringNum = 18
```

Qué indica cada dato:

- **hardware / firmware version:** registrarlas en `docs/versiones.md`.
- **lidar sdk version:** la librería informa 2.0.9 aunque el repositorio está en v2.0.10 (el último
  cambio de v2.0.10 es del driver de ROS, no de la librería).
- **dirty percentage:** porcentaje estimado de suciedad de la ventana del sensor. Si es alto,
  limpiar la tapa con un paño suave.
- **linear_acceleration:** con el sensor quieto y apoyado, el eje Z marca cerca de 9,8 m/s²
  (la gravedad).
- **cloud size / ringNum:** unos 5.100 puntos por mensaje, 18 anillos.

## Verificación final

- [ ] `ping 192.168.1.62` sin pérdidas.
- [ ] `verificar_udp_lidar.py` recibe paquetes de 1044 bytes (puntos).
- [ ] `example_lidar_udp` muestra las versiones y mensajes de IMU y de nube.
- [ ] Versiones registradas en `docs/versiones.md`.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ping` sin respuesta, `eno1` en `DOWN` o `NO-CARRIER` | Sin enlace: cable, alimentación o placa equivocada | Revisar la fuente y el cable; `cat /sys/class/net/eno1/carrier` debe dar `1` |
| `ping` responde pero no llegan paquetes UDP | Firewall bloqueando el puerto 6201, o la PC no tiene exactamente la IP `192.168.1.2` | Revisar `ip -br addr` y la regla de `ufw` |
| `example_lidar_udp` se queda sin mostrar nada después de `set Lidar work mode` | El programa espera la versión del sensor sin límite de tiempo: no llegan datos | Verificar con `verificar_udp_lidar.py`; revisar red y firewall |
| `ERROR al abrir 192.168.1.2:6201: [Errno 98] Address already in use` | Otro programa (ejemplo del SDK o driver) está usando el puerto | Cerrarlo antes |
| `Cannot assign requested address` | La PC no tiene la IP `192.168.1.2` | Volver a correr `configurar_red_lidar.sh` |
| El sensor gira pero hay pocos o ningún punto | Arranque en frío: el sensor se calienta antes de medir | Esperar unos minutos |
| El sensor dejó de responder en `192.168.1.62` | Se ejecutó `set_ip_address`, o está en modo serie | Probar `ping 192.168.123.110`; si está en modo serie, ver paso 02 |
