# Paso R01 — El LiDAR en el robot Unitree R1 (Jetson Orin NX)

> **PENDIENTE DE VALIDAR CON EL ROBOT.** El robot todavía no está disponible (2026-11-20). Este
> paso se escribió a partir de la referencia del R1
> (`docs/referencias/Unitree_R1_Conexiones_y_Acceso_Terminales.pdf`), del código del SDK y de lo
> verificado en la PC (pasos 00–07). Cada dato sin comprobar está marcado **A VERIFICAR**. La
> sección 2 se puede ensayar **sin el robot**, con el sensor y la PC.

## Objetivo

Dejar el L2 montado sobre el R1, conectado a su computadora de desarrollo (PC2, una NVIDIA Jetson
Orin NX), y **grabar a bordo** mientras el robot se maneja con el control remoto (Fase 1 del
proyecto). El mapa se genera después en la PC, igual que en los pasos 04–07.

```text
 L2 ──RJ45──► panel del R1 ──► switch interno ──► Jetson (192.168.123.164): driver + grabación
 L2 ◄─12 V── conversor DC-DC ◄── XT30 24 V del panel                 │
                                                                     ▼ (rsync, después)
                                              PC con Ubuntu: Point-LIO, mapa 3D y mapa 2D
```

## Qué está verificado y qué no

| Tema | Estado |
|---|---|
| Driver, grabación, Point-LIO y productos del mapa en una PC x86 con Jazzy | Verificado (pasos 03–07) |
| `cambiar_ip_lidar` (herramienta propia para cambiar la red del sensor) | Compila y valida las IPs; **no probada con el sensor** |
| Librería del SDK para aarch64 (`lib/aarch64/libunilidar_sdk2.a`) | Existe en el repositorio; **no compilada todavía** |
| Sistema operativo, JetPack y ROS de la Jetson | **A VERIFICAR** (probable Ubuntu 20.04 + JetPack 5.x + Foxy) |
| Interfaz de red de la Jetson, IPs libres de la red del robot | **A VERIFICAR** |
| Destino del USB-C del panel, Wi-Fi propio de la Jetson | **A VERIFICAR** |
| Alimentación desde el XT30, montaje mecánico | **A VERIFICAR** (diseño propio) |

## Requisitos

- Pasos 00–07 completos en la PC (es la que procesa los mapas).
- Sensor en **modo Ethernet** (paso 02, sección "cómo saber en qué modo está").
- Para la sección 2 (ensayo sin robot): el sensor y la PC del paso 01.
- Para las secciones 3 en adelante: el robot, un **switch Ethernet** chico (ver 3.2), un
  **conversor DC-DC de 24 V a 12 V de 2 A o más**, cables y el soporte del sensor.

!!! concepto "Red interna del robot"
    El R1 tiene adentro una red Ethernet `192.168.123.0/24` sin router ni DHCP: cada equipo tiene
    una IP fija. La Jetson es la `.164`; la computadora de movimiento, probablemente la `.161`
    (A VERIFICAR). El RJ45 del panel del robot está conectado a esa red. Por eso el sensor tiene
    que pasar a una IP `192.168.123.x` y enviar los datos a la `.164`.

## 1. Datos del robot (según la referencia)

| Dato | Valor | Estado |
|---|---|---|
| Computadora de desarrollo | NVIDIA Jetson Orin NX, `192.168.123.164`, usuario `unitree` | Confirmado en la referencia |
| Acceso | `ssh unitree@192.168.123.164` (contraseña de fábrica en la referencia; **cambiarla** con `passwd`) | Confirmado en la referencia |
| Panel superior | 1 RJ45 gigabit, 1 USB-C, XT30 de 24 V / 3 A y 36 V / 5 A, parada de emergencia GH1.25 | Confirmado en la referencia |
| IPs a evitar | `.161`, `.164` y los bloques `.1–.30` y `.120–.170` (usados por Unitree en otros modelos) | Prudencia (referencia) |
| IP sugerida para una PC externa | `192.168.123.51` | Referencia (MYBOTSHOP) |
| Sistema de la Jetson | Probablemente Ubuntu 20.04, JetPack 5.x, ROS 2 Foxy, CycloneDDS 0.10.x | **A VERIFICAR** |
| Nombre de la interfaz cableada | `eth0` o `eth10` | **A VERIFICAR** |
| RAM / disco | 16 GB / 2 TB según un distribuidor | **A VERIFICAR** |

!!! peligro "No tocar la red de la Jetson"
    No modificar la configuración de la interfaz que tiene la `192.168.123.164`, ni instalar un
    servidor DHCP en esa red, ni hacer `apt upgrade` masivos o cambiar JetPack. Se puede perder el
    acceso a la Jetson o romper los servicios de Unitree. Todo lo de este paso funciona **sin
    cambiar nada en la red de la Jetson**: es el sensor el que se adapta.

## 2. Red del sensor para el robot (se puede ensayar sin el robot)

### 2.1 Elegir la IP del sensor

Se propone **`192.168.123.62`** para el sensor y **`192.168.123.164`** (la Jetson) como destino:

- `.62` está fuera de los bloques reservados y conserva el último número de la IP de fábrica
  (`.62`), fácil de recordar.
- **A VERIFICAR** con el robot que esté libre (sección 3.3). Si no lo está, elegir otra fuera de
  `.1–.30`, `.51`, `.120–.170` y `.222`.

!!! nota "Por qué no se usa el ejemplo del SDK"
    El ejemplo `set_ip_address` del SDK trae las IPs escritas en el código (`192.168.123.110` →
    `192.168.123.120`) y no valida nada. La herramienta propia `cambiar_ip_lidar` recibe las IPs
    como argumentos, comprueba que estén en la misma red, que no sean de los bloques reservados del
    robot, confirma que el sensor responde y pide confirmación antes de escribir.

### 2.2 Compilar `cambiar_ip_lidar`

Está en `scripts/sensor/` junto con `cambiar_modo_lidar` y `estado_lidar`, y se compila igual
(paso 01):

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor
mkdir -p build && cd build
cmake .. && make
```

**Salida obtenida** (2026-11-20, PC x86):

```text
[ 83%] Building CXX object CMakeFiles/cambiar_ip_lidar.dir/cambiar_ip_lidar.cpp.o
[100%] Linking CXX executable cambiar_ip_lidar
[100%] Built target cambiar_ip_lidar
```

Controles de los argumentos (verificados, no tocan el sensor):

```text
$ ./cambiar_ip_lidar 192.168.123.150 192.168.123.164
ERROR: 192.168.123.150 está en un bloque que Unitree usa en la red del robot
       (.1-.30 y .120-.170). Elegir otra IP libre (comprobar con nmap).
$ ./cambiar_ip_lidar 192.168.123.62 192.168.124.164
ERROR: el sensor y el destino tienen que estar en la misma red /24
```

### 2.3 Ensayo en la PC, sin el robot (A VERIFICAR: pendiente de hacer)

La PC hace de "Jetson": se le pone la IP de destino `192.168.123.164` en su placa del LiDAR. Es
una IP de la **PC**, no de la Jetson, así que no hay riesgo para el robot. Hacerlo **lejos del
robot** (dos equipos con la misma IP en la misma red chocan).

1. Con el sensor en la red de fábrica y el driver **detenido**, cambiar su red:

   ```bash
   cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor/build
   ./cambiar_ip_lidar 192.168.123.62 192.168.123.164
   ```

   Salida esperada (A VERIFICAR):

   ```text
   Conectando por Ethernet: sensor 192.168.1.62:6101 -> PC 192.168.1.2:6201
   Comunicación confirmada (hardware 2.2.1.1, firmware 2.8.11.1).
   Configuración nueva:
     IP del sensor     : 192.168.123.62 (puerto 6101)
     IP de destino     : 192.168.123.164 (puerto 6201)
   ...
   ¿Aplicar? Escribir SI y Enter: SI
   Listo. APAGAR Y PRENDER el sensor ...
   ```

2. **Apagar y prender** el sensor (desenchufar la fuente unos segundos).
3. Cambiar la IP de la PC en la placa del LiDAR (`eno1` en la PC del laboratorio). El script del
   paso 01 actualiza el perfil `lidar-l2`; pide `sudo` solo para el firewall:

   ```bash
   cd ~/Documentos/LiDAR-RobotHumanoide
   ./scripts/red/configurar_red_lidar.sh eno1 192.168.123.164/24
   ```

4. Verificar que llegan los datos y lanzar el driver con las IPs nuevas:

   ```bash
   ping -c 3 192.168.123.62
   sudo tcpdump -i eno1 udp port 6201 -c 10
   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false \
       lidar_ip:=192.168.123.62 local_ip:=192.168.123.164
   ros2 topic hz /unilidar/cloud      # en otra terminal: ~10 Hz esperado
   ```

5. Si se va a llevar al robot, **dejarlo así** y pegarle al sensor una etiqueta con la red nueva.
   Si no, volver a fábrica (sección 2.4).

### 2.4 Volver a la red de fábrica

La PC tiene que estar con la IP de destino **actual** (`192.168.123.164`) para poder hablar con el
sensor:

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor/build
./cambiar_ip_lidar 192.168.1.62 192.168.1.2 192.168.123.62 192.168.123.164
# apagar y prender el sensor
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/red/configurar_red_lidar.sh eno1             # PC de nuevo en 192.168.1.2/24
ping -c 3 192.168.1.62
```

!!! importante "Si no se sabe qué IP tiene el sensor"
    Conectarlo directo a la PC y mirar qué paquetes manda: `sudo tcpdump -i eno1 -n -c 5`. La IP
    de origen es la del sensor y la de destino es la que la PC debe tener. Otra salida: pasar el
    sensor a USB (paso 02), que no depende de la red, y cambiar la IP desde ahí (A VERIFICAR: la
    herramienta actual solo habla por Ethernet).

## 3. Conexión física en el robot

### 3.1 Alimentación

!!! peligro "El L2 es de 12 V"
    Las salidas XT30 del panel son de **24 V y 36 V**. Conectar el sensor directo lo **daña**.
    Siempre a través de un conversor DC-DC.

- Desde el XT30 de **24 V / 3 A**: conversor DC-DC **24 V → 12 V, 2 A o más** (el sensor consume
  1 A típico y tiene picos de 13 W al calentarse).
- Salida del conversor a un plug **DC 3,5 × 1,35 mm**. Respetar la polaridad que se midió en la
  fuente original (paso 01). **Medir con el multímetro la salida del conversor antes de enchufar
  el sensor.**
- Si el switch de la sección 3.2 es de 12 V, puede alimentarse del mismo conversor (sumar su
  consumo).
- Conector XT30 hembra/macho y polaridad del panel: **A VERIFICAR** con el robot.

### 3.2 Datos: un solo RJ45 en el panel

El panel del R1 tiene **un solo RJ45**. El sensor ocupa ese puerto, y la PC también lo necesita
para entrar por SSH a la Jetson. Opciones:

| Opción | Cómo | Estado |
|---|---|---|
| **A. Switch chico (recomendada)** | Switch Ethernet no administrable de 5 puertos sobre el robot: panel ↔ switch ↔ sensor, y un puerto libre para la PC | A VERIFICAR |
| B. Wi-Fi de la Jetson | El sensor en el RJ45 y la PC por Wi-Fi | A VERIFICAR (no se sabe si la Jetson tiene `wlan0`) |
| C. Sensor por USB | Sensor en modo serie (paso 02) al USB-C del panel; el RJ45 queda para la PC | A VERIFICAR (no se sabe si el USB-C va a la Jetson) |

Con la opción A, la PC se conecta solo para arrancar y detener la grabación (sección 5): durante
el recorrido se puede desenchufar porque todo corre en `tmux` en la Jetson.

!!! nota "Switch no administrable"
    Un switch "tonto" (sin configuración) solo reparte el tráfico: no tiene IP ni DHCP y no
    modifica la red del robot. No conectar un **router**: su DHCP interrumpiría la red interna.

### 3.3 Mapear la red del robot

Desde la PC, conectada al switch con la IP `192.168.123.51/24` (perfil aparte, sin puerta de
enlace; no usar el perfil `lidar-l2`):

```bash
sudo nmcli connection add type ethernet ifname eno1 con-name r1 \
    ipv4.method manual ipv4.addresses 192.168.123.51/24
sudo nmcli connection up r1
ping -c 3 192.168.123.164
sudo apt install -y nmap
nmap -sn 192.168.123.0/24       # equipos presentes: comprobar que .62 está libre
```

`nmcli` crea el perfil `r1` en la PC (no toca el robot). Para quitarlo:
`sudo nmcli connection delete r1`. Anotar en `docs/versiones.md` la lista de IPs encontradas.

## 4. Software en la Jetson

### 4.1 Primer acceso y relevamiento (solo lectura)

```bash
ssh unitree@192.168.123.164
passwd                                   # cambiar la contraseña de fábrica la primera vez
cat /proc/device-tree/model; echo
cat /etc/nv_tegra_release                # versión de L4T (JetPack)
lsb_release -a
ls /opt/ros                              # ROS instalado
ip -br addr                              # nombre de la interfaz con .164
df -h ~ ; free -h
docker --version
systemctl list-units --type=service | grep -i -E "unitree|tele|video|ai"
sudo ufw status                          # firewall (si está activo, ver 4.4)
```

También sirve el script del proyecto, que no modifica nada: copiar el repositorio (4.2) y correr
`./scripts/sistema/relevar_sistema.sh`. Registrar todo en `docs/versiones.md` (sección nueva
"Jetson del robot").

!!! importante "Respaldo antes de instalar"
    Antes de instalar cualquier cosa, guardar una copia de `~/`, `/etc/netplan`,
    `/etc/NetworkManager` y la lista de paquetes (`dpkg --get-selections > paquetes.txt`).
    Instalar solo lo necesario.

### 4.2 Copiar el repositorio y el SDK

La Jetson probablemente no tenga internet (A VERIFICAR). Copiar desde la PC:

```bash
# En la PC
rsync -av --exclude bags --exclude mapas --exclude build \
    ~/Documentos/LiDAR-RobotHumanoide/ unitree@192.168.123.164:~/LiDAR-RobotHumanoide/
rsync -av --exclude build --exclude install --exclude log \
    ~/lidar_ws/unilidar_sdk2/ unitree@192.168.123.164:~/lidar_ws/unilidar_sdk2/
```

Si hace falta internet en la Jetson (para `apt` o Docker), la referencia del R1 describe cómo
compartir la conexión de la PC con NAT (sección 3.3 de la referencia). **A VERIFICAR.**

### 4.3 Qué camino seguir según el sistema

El driver y la grabación necesitan ROS 2. Según lo que muestre el relevamiento:

| Jetson con | Camino | Notas |
|---|---|---|
| Ubuntu 24.04 | ROS 2 **Jazzy nativo**, igual que la guía | Poco probable |
| Ubuntu 22.04 | ROS 2 **Humble nativo** | Mismos pasos que en la PC, cambiando `jazzy` por `humble` |
| Ubuntu 20.04 (lo más probable) | **Docker con Jazzy** (recomendado) o **Foxy nativo** | Ver 4.5 y 4.6 |

Docker es el camino recomendado porque deja **las mismas versiones y los mismos scripts** que en la
PC (Jazzy) y no instala nada en el sistema de la Jetson. Foxy nativo es la alternativa si no hay
Docker o no se puede descargar la imagen: el driver del L2 está verificado por Unitree justamente
en 20.04 + Foxy, pero los scripts de grabación del proyecto están hechos para Jazzy (ver 4.6).

### 4.4 Red de la Jetson

No hay que cambiar nada: la Jetson ya tiene la `192.168.123.164`, que es el destino del sensor.
Solo, si el firewall está activo, abrir el puerto de los datos en esa interfaz
(**pedir permiso**; reemplazar `eth0` por el nombre real):

```bash
sudo ufw allow in on eth0 to any port 6201 proto udp
```

Verificar que llegan los datos:

```bash
ping -c 3 192.168.123.62
sudo tcpdump -i eth0 udp port 6201 -c 10
```

### 4.5 Camino A: Docker con Jazzy (recomendado; A VERIFICAR)

La imagen oficial `ros:jazzy-ros-base` existe para `arm64`. Docker solo aporta el espacio de
usuario (Ubuntu 24.04 + Jazzy); el núcleo sigue siendo el de la Jetson, y el driver no usa la GPU.

```bash
# En la Jetson. Descargar la imagen (requiere internet; ~1 GB)
docker pull ros:jazzy-ros-base

# Contenedor permanente con la red del robot (--net=host) y las carpetas del proyecto
docker run -d --name lidar --net=host --restart unless-stopped \
    -v ~/LiDAR-RobotHumanoide:/root/LiDAR-RobotHumanoide \
    -v ~/lidar_ws:/root/lidar_ws \
    ros:jazzy-ros-base sleep infinity

# Dentro del contenedor: dependencias y compilación del driver (como el paso 03)
docker exec -it lidar bash
apt update && apt install -y ros-jazzy-pcl-ros ros-jazzy-pcl-conversions libpcl-dev \
    libeigen3-dev ros-jazzy-rosbag2 ros-jazzy-rosbag2-storage-mcap python3-numpy git tmux
source /opt/ros/jazzy/setup.bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2
colcon build
```

- `--net=host`: el contenedor usa la red de la Jetson y recibe el UDP del sensor en la `.164`.
- `--restart unless-stopped`: vuelve a arrancar si se reinicia la Jetson.
- La compilación usa `unitree_lidar_sdk/lib/aarch64/libunilidar_sdk2.a` automáticamente (el
  `CMakeLists.txt` del driver elige la carpeta por `CMAKE_SYSTEM_PROCESSOR`).
- Para no descargar la imagen en la Jetson: en la PC,
  `docker pull --platform linux/arm64 ros:jazzy-ros-base` y
  `docker save ros:jazzy-ros-base | gzip > ros_jazzy_arm64.tar.gz`; copiarla con `rsync` y en
  la Jetson `docker load < ros_jazzy_arm64.tar.gz`. **A VERIFICAR.**

Después, todo es como en la PC: los comandos de las secciones 5.1 y 5.2 se corren **dentro** del
contenedor (`docker exec -it lidar bash`).

### 4.6 Camino B: Foxy nativo (A VERIFICAR)

```bash
# En la Jetson (pedir permiso: sudo e instalación)
sudo apt install -y ros-foxy-pcl-ros ros-foxy-pcl-conversions libpcl-dev libeigen3-dev
source /opt/ros/foxy/setup.bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2
colcon build
```

Diferencias con la guía:

- `scripts/grabacion/grabar_lidar.sh` usa opciones de Jazzy (`--topics`, formato `mcap`,
  `ros2 topic echo --once --field`) que **probablemente no existan en Foxy**. Grabar a mano, en
  el formato `sqlite3` de Foxy:

  ```bash
  ros2 bag record -o ~/bags/$(date +%Y-%m-%d_%H%M)_<nombre> /unilidar/cloud /unilidar/imu
  ```

- Jazzy, en la PC, lee las grabaciones `sqlite3` de Foxy (el formato está en `metadata.yaml`, que
  `revisar_grabacion.py` y `ros2 bag play` respetan). **A VERIFICAR.**
- El launch del proyecto (`l2_driver.launch.py`) usa `OpaqueFunction`, que existe en Foxy.
  **A VERIFICAR.**

### 4.7 Que los datos no salgan a la red del robot

Si se graba en la Jetson y nadie mira en vivo, conviene que la nube de puntos (unos 2 MB/s) no
viaje por la red interna del robot, que también usa la computadora de movimiento (DDS, dominio 0):

```bash
export ROS_DOMAIN_ID=1                          # distinto del dominio 0 de Unitree
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST  # Jazzy: solo procesos de la misma máquina
# En Foxy (camino B), en lugar de la anterior: export ROS_LOCALHOST_ONLY=1
```

Poner estas líneas en **todas** las terminales (driver y grabación) o en `~/.bashrc` del
contenedor. **A VERIFICAR** que no afecten a los servicios de Unitree (no deberían: son variables
de los procesos propios).

Para ver en vivo desde la PC (RViz) no usar `LOCALHOST`, y usar la misma distribución en ambos
lados: Jazzy (contenedor) en la Jetson y Jazzy en la PC. Jazzy y Foxy no se comunican de forma
confiable.

## 5. Grabar con el robot (Fase 1)

### 5.1 Arrancar el driver (en la Jetson, en tmux)

```bash
tmux new -s lidar
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
cd ~/LiDAR-RobotHumanoide
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false \
    lidar_ip:=192.168.123.62 local_ip:=192.168.123.164
```

Salir de tmux sin cortarlo: **Ctrl+b** y después **d**. Verificar en otra terminal
`ros2 topic hz /unilidar/cloud` (~10 Hz).

### 5.2 Grabar

```bash
tmux new -s grabar
source /opt/ros/jazzy/setup.bash
cd ~/LiDAR-RobotHumanoide
BAGS_DIR=~/bags ./scripts/grabacion/grabar_lidar.sh robot_<lugar> "" "Robot con control remoto"
```

Procedimiento del recorrido: el del paso 06 (quieto 5 a 10 s al empezar y al terminar, caminar
despacio, giros suaves, terminar en el punto de partida). Con el robot, además:

- El robot camina con su control remoto, en el modo normal de marcha. **No** usar los modos de
  bajo nivel ni el control de brazos (ver la referencia del R1, sección "Riesgos").
- El torso del bípedo cabecea al caminar: Point-LIO lo compensa con la IMU, pero conviene caminar
  más despacio que con el sensor en la mano. **A VERIFICAR** la calidad del mapa.
- Una persona a cargo del control y de la parada de emergencia, área despejada.

Al terminar: Ctrl+C en la sesión `grabar` (y en `lidar` si no se va a grabar más).

### 5.3 Pasar la grabación a la PC y procesarla

```bash
# En la PC
rsync -av --progress unitree@192.168.123.164:~/bags/ ~/Documentos/LiDAR-RobotHumanoide/bags/
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/grabacion/revisar_grabacion.py bags/<carpeta>
./scripts/mapas/procesar_grabacion.sh bags/<carpeta> robot_<lugar>
```

Después, los productos del mapa como en el paso 07. Unos 1,2 GB cada 10 minutos: por cable tarda
segundos; por Wi-Fi, minutos.

### 5.4 Altura del sensor y mapa 2D

`generar_mapa_2d.py` marca como obstáculo lo que está entre 0,10 y 1,80 m sobre el piso. Con el
sensor montado, el robot mide algo menos de 1,8 m (A VERIFICAR con el soporte). Si hace falta,
ajustar con `--altura-max`.

## 6. Alternativa sin tocar el robot: kit de grabación

Si no conviene instalar nada en la Jetson, un kit independiente (L2 + Raspberry Pi 5 + batería
con salida de 12 V) que solo graba, sujeto al robot. La RPi 5 es `aarch64` como la Jetson: se usa
la misma librería del SDK, Ubuntu 24.04 + Jazzy nativo (igual que la guía) y la red de fábrica
del sensor (`192.168.1.x`), sin pasar por la red del robot. **A VERIFICAR** (la RPi 5 no tiene
disponibilidad asegurada).

## 7. Lista de verificación para cuando llegue el robot

- [ ] Modelo de la Jetson, L4T/JetPack, Ubuntu, ROS instalado, Docker (sección 4.1).
- [ ] Nombre de la interfaz con la `.164` y si hay una segunda interfaz o `wlan0`.
- [ ] IPs presentes en `192.168.123.0/24` (`nmap -sn`); `.62` libre.
- [ ] Firewall de la Jetson.
- [ ] Espacio libre en disco (más de 20 GB para grabaciones).
- [ ] Destino del USB-C del panel.
- [ ] Conector y polaridad del XT30 de 24 V; tensión de salida del conversor medida.
- [ ] Switch funcionando con el sensor y la PC a la vez.
- [ ] Puntos de montaje en el robot (diseño del soporte con los 4 M3 del sensor).
- [ ] Driver compilado y `/unilidar/cloud` a ~10 Hz en la Jetson.
- [ ] Una grabación corta, copiada a la PC y procesada con `procesar_grabacion.sh`.
- [ ] Registrar todo en `docs/versiones.md` y en la bitácora, y quitar los "A VERIFICAR" de este
      documento.

## Problemas frecuentes (previstos, A VERIFICAR)

| Síntoma | Causa probable | Solución |
|---|---|---|
| No llegan datos a la Jetson | El sensor sigue en la red de fábrica | Sección 2: cambiar la red con `cambiar_ip_lidar` y apagar y prender |
| `tcpdump` ve paquetes pero el driver no publica | Firewall de la Jetson | Sección 4.4 |
| La PC no llega a la `.164` | PC sin IP fija en `192.168.123.x`, o con otra interfaz en la misma red | Sección 3.3; revisar `ip -br addr` |
| `colcon build` no encuentra `libunilidar_sdk2.a` | Paquete movido de su carpeta | Compilar dentro de `unilidar_sdk2/unitree_lidar_ros2` (paso 03) |
| `grabar_lidar.sh` falla en Foxy | Opciones de Jazzy | Grabar a mano (4.6) o usar el contenedor Jazzy (4.5) |
| Mapa con paredes dobles | Cabeceo del robot o marcha rápida | Caminar más despacio, giros suaves |
