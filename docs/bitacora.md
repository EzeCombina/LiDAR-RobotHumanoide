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

## 2026-11-12 — Observación: ruido fuerte del sensor al girar

- El usuario informa que el L2 hace un **ruido raro y bastante fuerte al girar**, que no parece
  normal.
- No existe una calibración a cargo del usuario: la API del SDK no tiene ninguna función de
  calibración (solo modo, IP/MAC, rotación, reinicio, sincronización de tiempo y suciedad). Si
  Unilidar 2 ofrece algo así: A VERIFICAR.
- Medición de 10 s con la IMU del sensor (driver por Ethernet, 251 Hz): desvío de la aceleración
  [1,47; 1,13; 2,37] m/s², pico a pico [9,9; 9,1; 13,8] m/s², desvío del giróscopo
  [0,43; 0,35; 0,24] rad/s, |g| medio 8,35 m/s². Frecuencias dominantes: X e Y por debajo de
  0,5 Hz (indica que el sensor se estaba moviendo o manipulando), Z en 8,7 Hz con 4,4 y 17,5 Hz.
  **No concluyente**: no se sabe si estaba quieto y no hay un valor de referencia de un L2 sano.
- Driver detenido. Se recomienda dejar el sensor sin alimentación hasta caracterizar el ruido.
  No se pasa a modo USB hasta resolverlo.

### Segunda medición, con el sensor quieto (2026-11-12)

Sensor en el piso, sobre su almohadilla, sin tocar. Driver por Ethernet. Script nuevo
`scripts/medir_vibracion_imu.py`, 20 s, 5017 muestras a 251 Hz. Datos crudos en
`docs/mediciones/imu_reposo_2026-11-12.csv`.

| Magnitud | x | y | z |
|---|---|---|---|
| Aceleración media [m/s²] | 0,012 | 0,119 | 7,818 |
| Aceleración, desvío [m/s²] | 0,336 | 0,416 | **1,706** |
| Aceleración, pico a pico [m/s²] | 2,61 | 3,04 | **9,18** |
| Velocidad angular, desvío [rad/s] | 0,064 | 0,036 | 0,040 |
| Frecuencias dominantes [Hz] | 23,3 / 14,5 / 78,6 | 23,3 / 14,5 | **8,7** / 13,1 |

- El giróscopo casi en cero confirma que el sensor estaba quieto: la medición es válida.
- **Vibración vertical fuerte**: 9,2 m/s² pico a pico en Z, dominante en 8,7 Hz. El módulo
  instantáneo de la aceleración va de 2,66 a 11,59 m/s² (mediana 8,00).
- **Módulo medio de la aceleración 7,82 m/s²**, cuando en reposo debería ser ≈ 9,81 m/s²
  (≈ 20 % menos). Puede ser un error de la IMU o un efecto de la vibración: A VERIFICAR.
- No hay una medición de un L2 sano para comparar. Los datos son coherentes con el ruido que
  escucha el usuario. Si no se corrige, podría afectar al SLAM (Point-LIO usa la IMU): A VERIFICAR.
- Recomendación: consultar al vendedor o al soporte de Unitree con un video con sonido y esta
  medición antes de seguir usando el sensor por períodos largos.

## 2026-11-12 — Software Unilidar 2 y manuales oficiales

- Se descargaron de `https://www.unitree.com/download/L2` el manual del L2 (v1.1, 2024.10) y el de
  Unilidar 2 (v1.0, 2024.11). Quedan en `docs/referencias/`.
- **Unilidar 2 solo funciona en Windows de 64 bits** (lo dicen los dos manuales). Se ejecuta como
  administrador. En la página de descargas, leída de forma automática, no aparece el instalador:
  el usuario tiene que verificarlo desde el navegador.
- La página también ofrece dos grabaciones de ejemplo (`L2 Indoor/Park Point Cloud Data.bag`,
  formato ROS 1) y el SLAM oficial `unitreerobotics/point_lio_unilidar` v2.0.2. Sirven para probar
  el SLAM sin el sensor.
- Datos del manual útiles para el diagnóstico del ruido: el L2 tiene **dos motores**, uno de alta
  velocidad (espejo, barrido vertical, **216 Hz**) y uno de baja velocidad (cabezal, barrido
  horizontal, **5,55 Hz**). Unilidar 2 muestra sus velocidades (`sys_rotation_period`,
  `com_rotation_period`), las temperaturas del APD y de la IMU, las tensiones del APD y del láser y
  la pérdida de paquetes.
- El SDK recibe esos mismos datos de estado dentro de cada paquete de puntos (`LidarInsideState`
  en `unitree_lidar_protocol.h`), así que también se pueden leer desde Ubuntu.
- Diferencia entre manuales: el de Unilidar 2 dice que el modo de ángulo negativo (NEGA) viene
  activado de fábrica; el del L2 y el README del SDK dicen que no. A VERIFICAR en Unilidar 2.

## 2026-11-12 — Renumeración de pasos y herramienta `estado_lidar`

- El usuario descargó de la página de Unitree `unilidar_sdk2-2.0.10.zip`: es **idéntico** al clon
  (commit `0e3c51f` = tag `v2.0.10`). No incluye el programa Unilidar 2. El manual de Unilidar 2
  descargado es el mismo que ya estaba en `docs/referencias/`.
- **Renumeración de los pasos** (decisión del usuario): 01 primera prueba con Unilidar 2 en Windows
  (nuevo, `01_prueba_unilidar2_windows.md`, pendiente de validar), 02 Ethernet (antes 01,
  `02_conexion_ethernet.md`), 03 USB, 04 driver ROS 2. Referencias actualizadas en `CLAUDE.md`,
  paso 00, `versiones.md` y `configurar_red_lidar.sh` (que además apuntaba a un archivo
  inexistente, `01_red_y_conexion.md`). Las entradas anteriores de esta bitácora conservan la
  numeración vieja.
- Las herramientas en C++ pasan a `scripts/herramientas_sdk/`: `cambiar_modo_lidar` y la nueva
  **`estado_lidar`**, que lee el estado interno (`LidarInsideState`) de cada paquete de puntos:
  velocidades de los dos motores, suciedad, pérdida de paquetes, temperaturas y tensiones, más un
  conteo de paquetes por tipo. Solo escucha, no envía comandos. Compila sin advertencias; falta
  probarla con el sensor conectado.

## 2026-11-12 — Se descarta Unilidar 2; se vuelve a la numeración anterior

- El usuario verificó que **Unilidar 2 ya no se puede descargar** de la página de Unitree. Se
  elimina el paso de prueba en Windows y se vuelve a la numeración anterior: **01 Ethernet**
  (`01_conexion_ethernet.md`), **02 USB**, **03 driver ROS 2**. Referencias actualizadas en
  `CLAUDE.md`, paso 00, `versiones.md` y `configurar_red_lidar.sh`.
- Todo lo que dependía de Unilidar 2 pasa al SDK en Ubuntu: cambio de modo con
  `cambiar_modo_lidar`, diagnóstico con `estado_lidar` y, si hiciera falta, cambio de IP con
  `setLidarIpAddressConfig` (procedimiento A VERIFICAR; se usa para el choque de redes y para la red
  del robot).
- El manual de Unilidar 2 se conserva en `docs/referencias/` porque describe los campos de estado
  del sensor (unidades de los motores, temperaturas, tensiones).

## 2026-11-12 — Estado de los motores con `estado_lidar`

- Sensor conectado por Ethernet, apoyado en la almohadilla, en el piso. `estado_lidar udp 15` y
  luego `udp 20` (con unos minutos de funcionamiento, guardado en
  `docs/mediciones/estado_lidar_2026-11-12.txt`).
- **Motores estables:** `sys_rotation_period` 4.616–4.629 (≈ 4.621) y `com_rotation_period`
  229.384–232.396 (≈ 230.100). Interpretados como períodos en µs: **espejo 216,4 Hz** (coincide
  con los 216 Hz del manual) y **cabezal 4,35 Hz** (el manual dice 5,55 Hz: A VERIFICAR). Las
  unidades y la asignación sys/com contradicen al manual de Unilidar 2, que habla de r/min y asigna
  `sys` al motor horizontal.
- Sin pérdida de paquetes internos. APD 38,7 → 41,5 °C y 148 → 152 V (sube con la temperatura),
  láser 49,7 V, IMU ≈ 60,5 °C (calefaccionada), `dirty_index` promedio ≈ 5.
- Paquetes por tipo: puntos 3D 216/s, IMU 251/s, ACK ≈ 1/s, 1 de versión, 1 de parámetros. La
  librería del SDK intercambia mensajes con el sensor al conectarse aunque el programa no llame a
  funciones de configuración: se corrigió el texto de `estado_lidar` que decía "solo escucha".
  Los paquetes de 1124 bytes (~11/s) vistos con `verificar_udp_lidar.py` siguen sin identificar:
  el SDK no los reporta con ningún tipo conocido (A VERIFICAR).
- **Relación con el ruido:** en la medición de vibración del eje Z (`imu_reposo_2026-11-12.csv`),
  ≈ 59 % de la energía está en **8,70–8,80 Hz = 2,00 × la rotación del cabezal**, con armónicos en
  13,1 Hz (×3,0) y 18,9 Hz (×4,35). La vibración vertical está sincronizada con el giro del cabezal
  (dos golpes por vuelta). En X e Y dominan 23,3 y 14,5 Hz, que no son armónicos del cabezal ni el
  alias del espejo (34,4 Hz con la IMU a 250,8 Hz). Hipótesis: desbalance, juego o roce en el
  conjunto que gira. No se puede confirmar sin un L2 de referencia; dato útil para el soporte de
  Unitree.
- Driver relanzado en `tmux` (sesión `lidar`, `modo:=ethernet rviz:=false`): `/unilidar/cloud` a
  12,01 Hz.

## 2026-11-12 — Primera nube en RViz y documento del driver

- El usuario abrió RViz con `view.rviz` del SDK mientras el driver corría en `tmux`: la nube se ve
  bien y se reconoce el lugar. Captura en `docs/img/rviz_primera_nube_2026-11-12.png`.
- **Falló** el primer intento desde la terminal integrada de VS Code:
  `rviz2: symbol lookup error: /snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0: undefined symbol: __libc_pthread_init, version GLIBC_PRIVATE`.
  Causa: VS Code está instalado como snap (`code` 278, classic) y su terminal hereda `GTK_PATH`,
  `GTK_EXE_PREFIX`, `GIO_MODULE_DIR`, `GTK_IM_MODULE_FILE`, `LOCPATH` y `SNAP`. **Se resolvió**
  abriendo RViz desde la terminal de Ubuntu. Quitar esas variables con `env -u` queda A VERIFICAR
  (con `rviz2 --help` sin ventana el error no se reproduce).
- Documento del paso: `docs/pasos/03_driver_ros2.md` (Ethernet completo; USB pendiente del paso 02).

## 2026-11-12 — Etapa 2: grabación (paso 04)

- Por decisión del usuario (cable USB corto), se posterga el paso 02 (USB) y se pasa a la grabación.
- Script `scripts/grabar_lidar.sh <nombre> [segundos] ["descripción"]`: controla entorno, tópicos y
  espacio; graba `/unilidar/cloud` y `/unilidar/imu` en MCAP en `bags/<fecha>_<nombre>/`; corta con
  `timeout -s INT` (Jazzy no tiene opción de duración en `ros2 bag record`) y escribe
  `descripcion.txt`.
- Prueba de 15 s: 173 nubes (11,98/s) y 3619 IMU (250,6/s) en 14,44 s, **sin pérdidas**;
  28,2 MiB → **~117 MB/min**. Aviso corregido:
  `[WARN] [ros2bag]: Positional "topics" argument deprecated. Please use optional "--topics" argument instead.`
  (se pasó a `--topics`; prueba de 5 s sin aviso). Las grabaciones de prueba se borraron.
- `bags/` está excluida de git (verificado con `git check-ignore`). Nuevo registro
  `docs/grabaciones.md` para anotar cada grabación útil y dónde está.
- Documento del paso: `docs/pasos/04_grabacion.md`, con el procedimiento de las tres grabaciones de
  referencia (`sala_quieta`, `persona_caminando`, `recorrido_mano`).

### Falla del script de grabación desde la terminal del usuario (2026-11-12)

- El usuario corrió `./scripts/grabar_lidar.sh sala_quieta 90 ...` en su terminal: pasados los
  90 s no terminaba y no se había creado la carpeta de la grabación. `ps` mostró
  `ros2 bag record` en estado **`Tl` (detenido)** desde el inicio, en un grupo de procesos distinto
  del de primer plano de la terminal.
- Causa: `timeout` (sin `--foreground`) ejecuta el comando en segundo plano; `ros2 bag record`
  intenta leer el teclado (pausa con la barra espaciadora) y el sistema lo congela (SIGTTIN). En las
  pruebas de Claude no apareció porque no había terminal ("stdin is not a terminal device. Keyboard
  handling disabled.").
- Solución: `timeout --foreground -s INT`, entrada `< /dev/null` para `ros2 bag record` y
  `trap ':' INT` en lugar de `trap '' INT` (una señal ignorada se hereda a los procesos hijos).
- Verificado con una terminal simulada (`script -qec`): la versión anterior se cuelga (código 124);
  la nueva termina sola con duración, se corta con Ctrl+C sin duración y también se corta antes de
  tiempo con Ctrl+C. Los procesos trabados se cerraron; las grabaciones de prueba se borraron.
