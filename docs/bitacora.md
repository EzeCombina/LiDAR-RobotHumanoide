# Bitácora de trabajo

Cada sesión agrega una entrada con: fecha, qué se hizo, qué funcionó, qué falló (con el error
literal) y cómo se resolvió.

---

## 2026-11-06 — Creación del repositorio

- Se creó la estructura inicial: `CLAUDE.md` (contexto e instrucciones), `README.md`,
  `docs/FORMATO_DOCUMENTO.md`, logo de la UTN FRSF y documentación de referencia del robot.
- Estado: el LiDAR L2 ya está en el laboratorio. El robot todavía no está disponible.
- Próximo paso: Etapa 0 y Etapa 1 de `CLAUDE.md` en la PC con Ubuntu 24.04 + Jazzy.

## 2026-11-06 — Etapa 0: preparación del entorno

**Qué se hizo**

- Relevamiento de la PC de implementación con el nuevo script `scripts/relevar_sistema.sh` (no
  modifica nada, no usa `sudo`, sirve también para la Jetson). Datos cargados en
  `docs/versiones.md`.
- Documento del paso: `docs/pasos/00_preparacion_entorno.md`. Por pedido del usuario, se escribió
  **como instalación desde cero** sobre una Ubuntu 24.04 limpia (incluye ROS 2 Jazzy con el método
  oficial actual, `ros2-apt-source` + `ros-dev-tools`), aunque esta PC ya tenía software instalado
  de antes. Las versiones de esta PC quedan como versiones de referencia.
- Identidad de git configurada a nivel del repositorio (`git config --local`): la PC no tenía
  `~/.gitconfig`.

**Qué se encontró en la PC**

- Ubuntu 24.04.5, kernel 7.0.0-42, ROS 2 Jazzy (`ros-jazzy-desktop` 0.11.0), gcc 13.3.0,
  CMake 3.28.3, PCL 1.14.0, Eigen 3.4.0, `tcpdump` 4.99.4.
- El repositorio de ROS 2 está agregado con el **método anterior** (`/etc/apt/sources.list.d/ros2.list`
  + `/usr/share/keyrings/ros-archive-keyring.gpg`). Funciona; no se toca. Se documentó el conflicto
  `Signed-By` que aparece si se mezclan ambos métodos.
- Red: placa Ethernet libre `eno1` (sin cable por ahora). El Wi-Fi está en `192.168.20.161/24`, así
  que **no hay choque** con la red de fábrica del L2 (`192.168.1.x`).
- `ufw` está activo: en el paso 01 habrá que abrir el puerto UDP 6201.

**Qué falló**

- `git pull` →
  `fatal: could not read Username for 'https://github.com': No existe el dispositivo o la dirección`.
  El remoto es HTTPS y la PC no tiene credenciales (no hay `gh`, ni clave SSH, ni *credential
  helper*). Una prueba con `ssh -T git@github.com` dio `Host key verification failed.`
- Faltan paquetes: `ros-jazzy-pcl-ros`, `ros-dev-tools` (trae `python3-rosdep`), `tmux`, `gh`. No se
  pudieron instalar desde la sesión de Claude porque `sudo` pide contraseña.

**Cómo se resolvió**

- El usuario instaló `ros-jazzy-pcl-ros`, `ros-dev-tools`, `tmux` y `gh`, corrió
  `sudo rosdep init && rosdep update` y se autenticó con `gh auth login` + `gh auth setup-git`
  (cuenta `EzeCombina`, protocolo HTTPS). Después de eso `git pull` y `git push` funcionaron.
- Relevamiento posterior: todos los paquetes del paso 00 instalados (versiones en
  `docs/versiones.md`). Etapa 0 cerrada.

## 2026-11-06 — Etapa 1: preparación del software (sin el sensor conectado)

**Qué se hizo**

- Se clonó y compiló `unilidar_sdk2` en `~/lidar_ws/unilidar_sdk2` (commit `0e3c51f`, SDK v2.0.10).
  Los cinco ejemplos compilaron sin errores; CMake solo avisa
  `CMake Deprecation Warning ... Compatibility with CMake < 3.5 will be removed` (no afecta).
- Script `scripts/configurar_red_lidar.sh`: crea el perfil de NetworkManager `lidar-l2` (IP fija,
  sin puerta de enlace, prioridad 10) y abre UDP 6201 en `ufw` solo en la placa del LiDAR. En esta
  PC ya existía el perfil por DHCP "Conexión cableada 1" en `eno1` (prioridad −999): no se toca.
  Todavía no se ejecutó (falta conectar el sensor y la confirmación del usuario).
- **Decisión del usuario:** documentar las dos conexiones, Ethernet y USB (serie). USB para el
  trabajo diario; Ethernet para el robot. Registrada en `CLAUDE.md`.
- Herramienta propia `scripts/cambiar_modo_lidar/` (C++ + SDK) para pasar de Ethernet a serie y
  viceversa. Compila; probado solo el camino de error sin sensor:
  `[ERROR] Unilidar failed to initialize! Serial port "/dev/ttyACM0" does not exist!`.
- Launch propio `config/unitree_lidar_ros2/l2_driver.launch.py` con `modo:=ethernet|usb` y
  `rviz:=true|false`. Sintaxis verificada; falta probarlo con el driver compilado (paso 03).

**Hallazgos al revisar el SDK y el driver**

- Modo de fábrica: Ethernet (work mode 0). Para pasar a serie hay que comunicarse primero por
  Ethernet (o con Unilidar 2) y después apagar y prender el sensor.
- El driver ROS 2 ejecuta `setLidarWorkMode(work_mode)` al arrancar (`unitree_lidar_ros2.h:149`):
  por USB hay que usar `work_mode: 8`; con el valor por defecto (0) el sensor vuelve a Ethernet.
- `set_to_serial_mode` y `set_ip_address` del SDK tienen IPs fijas `192.168.123.110/.120`.
  `set_ip_address` **cambia la IP del sensor** si se ejecuta: no correrlo.
- `example_lidar_udp` reescribe el modo 0 y reinicia el sensor; si no llegan datos, se queda
  esperando para siempre sin mensaje de error.
- No hay una función para leer el modo actual: se deduce por qué interfaz responde.
- El usuario `eze` ya pertenece al grupo `dialout` (acceso a `/dev/ttyACM0` sin `sudo`).

**Equipo informado por el usuario**

- L2 con fuente de 12 V 1 A, cable Ethernet y módulo adaptador con entrada de 12 V, USB y Ethernet.
  Multímetro y PC con Windows disponibles. Polaridad del plug: **pendiente de medir**.

## 2026-11-12 — Etapa 1, paso 01: conexión por Ethernet

**Qué se hizo**

- El usuario conectó el L2 por Ethernet a `eno1` y ejecutó `./scripts/configurar_red_lidar.sh eno1`.
  Resultado: perfil `lidar-l2` activo, `eno1 UP 192.168.1.2/24`, enlace a 100 Mbit/s.
- `ping 192.168.1.62`: 4/4 respuestas, ~0,1 ms. MAC del sensor `0c:29:ab:7c:00:01`.
- Llegada de datos verificada **sin sudo** con un receptor UDP en Python (convertido en
  `scripts/verificar_udp_lidar.py`), en lugar de `tcpdump`.
- `example_lidar_udp`: hardware **2.2.1.1**, firmware **2.8.11.1**, librería del SDK 2.0.9,
  *dirty percentage* 4,8 %, *time delay* 2,6 ms. Mensajes de IMU y de nube (≈5.100 puntos, 18
  anillos).
- Documento del paso: `docs/pasos/01_conexion_ethernet.md`.

**Observaciones**

- Con el sensor recién encendido llegaban solo paquetes de 1044 bytes (~215/s, 1,8 Mbit/s). Después
  de correr el ejemplo aparecen también los de 80 bytes (~240/s, IMU) y de 1124 bytes (~11/s, tipo
  sin identificar, A VERIFICAR). Tráfico total ≈ 2 Mbit/s: debería entrar en el serie de 4 Mbit/s.
- En 40 s de `example_lidar_udp` (cortado con `timeout`) se imprimieron 1688 mensajes de IMU
  (≈267 Hz) pero solo 2 de nube, y la salida se detuvo a los ~6 s de empezar a leer datos. El
  ejemplo imprime mucho texto y no sirve para medir tasas: **A VERIFICAR** con `ros2 topic hz` en el
  driver (paso 03).


## 2026-11-12 — Etapa 1: driver ROS 2 en Jazzy (prueba por Ethernet)

**Qué se hizo**

- `rosdep check --from-paths src --ignore-src` → `All system dependencies have been satisfied`.
- `colcon build` en `~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2`: **compila de forma nativa en
  Jazzy** (25 s), 0 advertencias del compilador. Solo avisos de CMake que vienen de los módulos de PCL
  (`Policy CMP0144 is not set` / `Policy CMP0074 is not set`), sin efecto.
- Se lanzó con el launch propio, dentro de `tmux` (sesión `lidar`):
  `ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false`.

**Resultados**

- Tópicos: `/unilidar/cloud`, `/unilidar/imu`, `/tf`.
- `ros2 topic hz /unilidar/cloud` → **11,99 Hz** (período 83–84 ms).
  `ros2 topic hz /unilidar/imu` → **251 Hz**.
- Nube `sensor_msgs/PointCloud2`, frame `unilidar_lidar`, campos `x y z intensity` (float32),
  `ring` (uint16), `time` (float32), `point_step` 32; ~4.400 puntos por mensaje en el laboratorio.
- `/tf`: `unilidar_imu_initial` → `unilidar_imu` (orientación estimada por la IMU).
- Conclusión: las 2 nubes del ejemplo del SDK eran un problema del ejemplo, no del sensor.
  **No hace falta el contenedor Humble para el driver.**

**Pendiente**

- Polaridad medida del plug, comportamiento de los LEDs y verificación visual en RViz (usuario).
