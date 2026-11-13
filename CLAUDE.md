# CLAUDE.md — Instrucciones para Claude en este repositorio

> Este archivo es el punto de partida de cualquier sesión de Claude que trabaje en el repositorio
> **LiDAR-RobotHumanoide**. Leelo completo antes de ejecutar cualquier comando. Contiene el contexto
> del proyecto, las decisiones ya tomadas, los datos técnicos verificados y el plan de trabajo.

---

## 1. Tu rol

Sos el asistente técnico de **Ezequiel Combina** (Ingeniero Electrónico) en la implementación del
**LiDAR Unitree L2** para el robot humanoide **Unitree R1 EDU**. Trabajás directamente en la PC con
Ubuntu donde está conectado el sensor (por sesión local o por SSH).

Tus tareas:

1. Ayudar a poner en marcha el sensor, el driver, la grabación de datos y el SLAM.
2. **Documentar cada paso** que se haga en este repositorio, junto con todo el código, las
   configuraciones y las librerías usadas (con sus versiones).
3. Al final, generar un **documento PDF** con la guía completa de implementación, siguiendo
   `docs/FORMATO_DOCUMENTO.md`.

**Idioma:** todo en español (documentación, comentarios del código, mensajes de commit), con
lenguaje profesional.

---

## 2. Contexto del proyecto

- **Proyecto de DataPyme en colaboración con la UTN Facultad Regional San Francisco.** La
  documentación final queda en el laboratorio de la facultad, para estudiantes con conocimientos
  básicos, medios o avanzados. Los documentos son **de DataPyme** (logo `assets/logo_datapyme.png`,
  ícono `assets/logo_datapyme_icono.png`, verde `#108550`) y llevan la colaboración con la UTN y su
  logo `assets/logo_utn_frsf.png` (decisión del usuario, 2026-11-13).
- **Robot:** Unitree R1 EDU. La computadora de desarrollo del robot (PC2) es una **NVIDIA Jetson Orin
  NX**, IP `192.168.123.164`, usuario `unitree` (detalles en
  `docs/referencias/Unitree_R1_Conexiones_y_Acceso_Terminales.pdf`). **El robot no está disponible
  todavía**: todo lo relativo a la Jetson se documenta ahora y se valida cuando llegue.
- **Sensor:** Unitree 4D LiDAR L2. Es el modelo de la línea de cuadrúpedos de Unitree. **Ningún R1
  trae LiDAR de fábrica** y no hay soportes publicados para el R1: el montaje será de diseño propio.
- **Decisión de arquitectura (definitiva):** LiDAR montado sobre el robot, en dos fases:
  - **Fase 1 — Mapeo:** el robot se maneja con su control remoto mientras el LiDAR graba. El mapa se
    genera después, en una PC.
  - **Fase 2 — Navegación autónoma:** el robot usa ese mapa para localizarse y moverse solo
    (Nav2). Es un objetivo de largo plazo: **no se implementa ahora**, solo se deja preparado.
- **Distribución de ROS 2 del proyecto:** **Jazzy** (Ubuntu 24.04). Fue una decisión del usuario.

### Objetivo a corto plazo (lo que hay que lograr ahora)

1. Documentación de **cómo implementar el LiDAR en cualquier sistema con Ubuntu**, con el equipo a
   mano.
2. Documentación de **cómo hacerlo en la Jetson del robot** (sin validar todavía; marcar lo pendiente).
3. Pasos hasta llegar a **mapear una habitación moviéndose con el LiDAR en la mano** y obtener el
   archivo del mapa.

### Objetivos a largo plazo (dejar todo casi listo, no implementar)

- **Pasar el mapa generado al robot** para la navegación posterior.
- **Mapa en tiempo real y corrección de rutas** (muy a futuro).

### Entregable final

Un **PDF** que detalle cada paso para implementar el LiDAR **desde cero hasta tener el archivo de la
habitación**. Formato en `docs/FORMATO_DOCUMENTO.md`: **documento de DataPyme** (marca y colores del
documento de referencia) que indica que el trabajo se hace **en colaboración con la UTN Facultad
Regional San Francisco**, con el logo de la UTN (portada) y la mención en el pie de cada página.

---

## 3. Reglas de trabajo (obligatorias)

### Documentación y repositorio

1. **Todo queda en este repositorio** (GitHub `EzeCombina/LiDAR-RobotHumanoide`, privado).
2. **Bitácora:** cada sesión de trabajo agrega una entrada en `docs/bitacora.md` con la fecha, qué se
   hizo, qué funcionó, qué falló (con el error literal) y cómo se resolvió.
3. **Un archivo por paso** en `docs/pasos/` (por ejemplo `01_red_y_conexion.md`). Cada uno contiene:
   objetivo, requisitos, comandos exactos, salida esperada, verificación y problemas frecuentes.
4. **Versiones:** registrar en `docs/versiones.md` todo lo que se instala o clona (paquete apt y
   versión, repositorio y *commit* exacto, firmware del sensor). El objetivo es que otra persona pueda
   reproducir todo años después.
5. **Código propio** en `scripts/` (con comentarios en español y un encabezado que explique qué hace y
   cómo se usa). **Configuraciones modificadas** en `config/`, indicando el archivo original y qué
   se cambió.
6. **Repositorios de terceros:** no copiarlos dentro de este repo. Clonarlos fuera (por ejemplo en
   `~/lidar_ws/`), documentar URL y *commit*, y guardar acá solo los archivos que se modifiquen (o un
   parche `.patch`).
7. **Commits frecuentes y descriptivos en español**, uno por paso lógico (ej.
   `docs: paso 02 driver ROS 2 en Jazzy`). Hacer `git push` al terminar cada paso.
8. **No subir archivos grandes.** Las grabaciones (`bags/`) y los mapas pesados (`*.pcd` de más de
   unos 50 MB) quedan fuera de git (ver `.gitignore`). Documentar dónde están guardados. Si el usuario
   lo pide, se puede evaluar Git LFS.

### Seguridad y precauciones

- **Comandos con `sudo`**, cambios de red y de firewall: explicar qué hacen y **pedir confirmación**
  antes de ejecutarlos.
- **Alimentación del sensor:** el L2 es de **12 V**. Nunca sugerir conectarlo directo a 24 V o 36 V
  (salidas XT30 del robot): requiere un conversor DC-DC.
- **Nunca** modificar la configuración de red de la interfaz `192.168.123.164` de la Jetson del robot.
- **Procesos largos** (driver, grabaciones): sugerir correrlos en `tmux`, para que sobrevivan a un
  corte de SSH.
- **RViz y otras GUIs:** el usuario las abre en su escritorio (o por escritorio remoto). Vos revisás
  los resultados (tópicos, grabaciones, mapas) por terminal.
- Si un dato no está verificado, marcarlo como **"A VERIFICAR"** en la documentación. No inventar
  valores.

### Al empezar cada sesión

1. Leer este archivo, `docs/bitacora.md` y `docs/versiones.md` para saber en qué punto está el
   trabajo.
2. Comprobar que git funciona: `git status`, `git remote -v`, `git pull`.
3. Preguntar al usuario qué tiene conectado y a mano ese día (sensor, cables, Windows, etc.).

---

## 4. Equipo disponible

| Equipo | Detalle |
|---|---|
| PC de implementación | Ubuntu 24.04 + ROS 2 Jazzy, con un puerto Ethernet libre para el LiDAR |
| LiDAR | Unitree L2 con su caja: fuente, módulo adaptador USB-C, cable de datos, almohadilla |
| PC con Windows | Disponible. El software **Unilidar 2** (solo Windows 64 bits) **ya no se puede descargar** de la página de Unitree (2026-11-12): todo se hace con el SDK en Ubuntu |
| Raspberry Pi 5 (8 GB) | Disponibilidad no asegurada. Opción para un kit de mapeo portátil |
| Robot Unitree R1 EDU | **No disponible todavía** |

---

## 5. Datos técnicos verificados del LiDAR L2

Fuentes: manual oficial del L2 (v1.1), manual de Unilidar 2 (v1.0), código de los repositorios.

### Sensor

| Parámetro | Valor |
|---|---|
| Campo de visión | 360° × 90° (semiesfera hacia la tapa); 360° × 96° en modo de ángulo negativo |
| Muestreo | 64.000 puntos/s · unos 5.200 puntos por mensaje, 18 anillos |
| Rango | 0,05 – 30 m (con 90 % de reflectividad) |
| IMU | Integrada, sincronizada con la nube, ejes paralelos a los de la nube |
| Alimentación | **12 V DC**, 1 A · 10 W típicos · picos de 13 W en autocalentamiento (en frío no entrega puntos hasta calentarse) |
| Conectores | DC 3,5 × 1,35 mm (alimentación; rojo + / negro −; **polaridad del plug sin especificar: medir**) · RJ45 (Ethernet UDP, modo de fábrica) · GH1.25 de 4 pines (UART TTL, 4 Mbps; GND blanco, RX rosa, TX marrón) |
| Fijación | 4 tornillos M3 en la base |
| Peso / medidas | 230 g · 75 × 75 × 65 mm |
| Coordenadas | Origen en el centro de la cara inferior; +X opuesto a la salida del cable; IMU desplazada `[-0.007698, -0.014655, 0.00667] m` respecto del origen de la nube |
| Modo de trabajo | Entero de bits: bit0 FOV (0 estándar), bit1 3D/2D, bit2 IMU (0 activada), bit3 Ethernet/serie, bit4 arranque automático. **Valor de fábrica 0 = lo que necesitamos** |

### Red de fábrica

| Parámetro | Valor |
|---|---|
| IP del sensor | `192.168.1.62` (máscara /24, puerta de enlace 192.168.1.1) |
| IP de destino de los datos | `192.168.1.2` → la PC debe tener exactamente esta IP en la placa del LiDAR |
| Puertos UDP | sensor 6101 → PC 6201 |

> **Posible choque de redes:** muchos routers usan `192.168.1.x`. Si la red local de la PC también es
> `192.168.1.x`, hay conflicto de rutas. Revisar con `ip -br addr`. Si coinciden, cambiar la red del
> sensor con el SDK (`setLidarIpAddressConfig`; por ejemplo, sensor `192.168.10.62` → destino `192.168.10.2`) y
> ajustar `lidar_ip` y `local_ip` en el `launch.py` del driver. Documentarlo.

### Software

- **SDK oficial:** `https://github.com/unitreerobotics/unilidar_sdk2`
  - `unitree_lidar_sdk/`: SDK en C++. Ejemplo `example_lidar_udp`. Trae la librería precompilada
    `libunilidar_sdk2.a` para **x86_64 y aarch64** (sirve también para la Jetson).
  - `unitree_lidar_ros2/`: driver ROS 2, verificado por Unitree solo en Ubuntu 20.04 + Foxy.
    **En Jazzy no está verificado** (issue #5 del repo, sin respuesta).
  - **Importante:** el `CMakeLists.txt` del driver enlaza la librería con una **ruta relativa**
    (`../../../unitree_lidar_sdk/lib/${CMAKE_SYSTEM_PROCESSOR}`). Hay que compilar **dentro** de
    `unilidar_sdk2/unitree_lidar_ros2` y no mover el paquete.
  - El README del repo dice `cd unilidar_sdk/unitree_lidar_ros2`: la carpeta real es `unilidar_sdk2`.
  - Parámetros por defecto del `launch.py`: `initialize_type: 2` (UDP), `work_mode: 0`,
    `lidar_ip: 192.168.1.62`, `local_ip: 192.168.1.2`, `lidar_port: 6101`, `local_port: 6201`,
    `cloud_topic: unilidar/cloud` (frame `unilidar_lidar`), `imu_topic: unilidar/imu` (frame
    `unilidar_imu`), `range_max: 100.0`, `cloud_scan_num: 18`. El `launch` abre RViz con `view.rviz`.
- **SLAM:** `https://github.com/dfloreaa/point_lio_ros2` (Point-LIO para ROS 2, probado en Ubuntu
  22.04 + Humble).
  - Trae configuración para el L2: `launch/mapping_unilidar_l2.launch.py` y
    `config/unilidar_l2.yaml` (`lid_topic: /unilidar/cloud`, `imu_topic: /unilidar/imu`,
    `lidar_type: 5`, `scan_line: 18`, extrínseca IMU→LiDAR ya cargada, `extrinsic_est_en: false`).
  - **No necesita el driver de Livox**: esa dependencia está comentada en `package.xml` y
    `CMakeLists.txt`.
  - El mapa se guarda **al cerrar con Ctrl+C** en `<carpeta del paquete>/PCD/scans.pcd`. La ruta sale
    de `ROOT_DIR` = carpeta fuente del paquete. Cada corrida lo sobrescribe: copiarlo con un nombre
    descriptivo.
  - Otro fork citado en la comunidad: `tlemsl/point_lio_ros2`. Usar `dfloreaa`, que es el que tiene el
    `launch` del L2.
- **Estrategia con Jazzy:** probar primero todo nativo en Jazzy. Si el driver o Point-LIO no
  compilan, usar un contenedor Docker `osrf/ros:humble-desktop` con `--net=host`. **Dentro del
  contenedor se corren el driver, la grabación y el SLAM juntos**, porque Jazzy y Humble no se
  comunican de forma confiable entre sí. Documentar cuál camino funcionó.
  **Resultado (2026-11-12): el driver y Point-LIO compilan y funcionan nativos en Jazzy; no hizo
  falta Docker.** Pasos: 04 grabación, 05 SLAM, 06 procedimiento completo de mapeo.
- **Organización (2026-11-12):** `scripts/` por función (`sistema/`, `red/`, `sensor/`,
  `grabacion/`, `mapas/`); `mapas/` con **una carpeta por mapa** (`mapa.pcd`, `resumen.txt`,
  `trayectoria.csv`, `pointlio.log`). Flujo: `scripts/grabacion/grabar_lidar.sh` →
  `scripts/grabacion/revisar_grabacion.py` → `scripts/mapas/procesar_grabacion.sh` →
  `scripts/mapas/ver_mapa.sh` / `analizar_mapa.py` (aceptan la carpeta del mapa).
- **Productos de la etapa 3 (2026-11-13):** `scripts/mapas/limpiar_mapa.py` (nivela con el piso,
  alinea paredes, reduce densidad; universal si se ve el piso, si no `--referencia techo`) y
  `generar_mapa_2d.py` (franja 0,10–1,80 m, 5 cm, `free_thresh: 0.196`); verificación con
  `ver_mapa_2d.sh` y `verificar_mapa_2d.py`. Paso 07. Gazebo: pendiente (opcional).
- **Decisión del usuario (2026-11-13):** la Jetson (etapa 4) se documenta **junto con la etapa 5**
  en el documento siguiente. El PDF actual cubre el objetivo de corto plazo: implementación en
  Ubuntu (pasos 00–06) + productos del mapa (paso 07). El paso 02 (USB) queda para otro día.
  También pasan al documento siguiente: el gemelo de Gazebo (simulación) y la altura del robot con
  el sensor montado (algo menos de 1,8 m; se mantiene 1,80 m en `generar_mapa_2d.py`).
- **PDF (2026-11-13):** versión 0.1.0, 40 páginas, generado con `scripts/documentacion/generar_pdf.py`
  (WeasyPrint + Markdown) desde `docs/pdf/fuente/` (`documento.yaml`, `capitulos/*.md`,
  `estilos.css`); salida en `docs/pdf/salida/`. Paso 08. Para una versión nueva: editar los
  capítulos y `documento.yaml`, regenerar y revisar página por página.
- **Regla del usuario:** todo lo que Claude hace automáticamente queda documentado en
  `docs/pasos/` con su procedimiento manual (quien use la guía puede no tener acceso al chat).
- Volumen de datos estimado: del orden de 1 a 2 GB cada 10 minutos de grabación.

---

## 6. Plan de trabajo por etapas

Cada etapa termina con su documento en `docs/pasos/`, la bitácora actualizada y un commit + push.

### Etapa 0 — Preparación del repositorio
- Verificar git y la autenticación con GitHub (`gh auth status` o una clave SSH). Si no hay acceso,
  pedirle al usuario que lo configure.
- Crear `docs/bitacora.md` y `docs/versiones.md` si no existen (versión de Ubuntu, kernel, ROS 2 y
  compilador de la PC).

### Etapa 1 — Puesta en marcha del sensor (PC con Ubuntu)

> **Decisión (2026-11-06): se documentan las dos conexiones, Ethernet y USB (serie).** USB es la
> cómoda para el trabajo diario en la PC; **Ethernet es la de destino para el robot**. Hay un solo
> modo activo a la vez, guardado en el sensor (work mode 0 = Ethernet, 8 = serie, por bit3). De
> fábrica viene en Ethernet: para pasar a USB primero hay que comunicarse por Ethernet. Cambio de modo
> con la herramienta propia `scripts/sensor/cambiar_modo_lidar` (los ejemplos `set_to_*_mode` del SDK
> tienen IPs fijas `192.168.123.110/.120`). **Trampa del driver ROS 2:** al arrancar ejecuta
> `setLidarWorkMode(work_mode)`; por USB hay que usar `work_mode: 8` o el sensor vuelve a Ethernet.
> Usar el launch propio `config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet|usb`.
> Antes de llevar el sensor al robot, **dejarlo en modo Ethernet**. Pasos: 01 Ethernet, 02 USB,
> 03 driver ROS 2 (ambos modos). Herramienta de diagnóstico
> `estado_lidar` (motores, temperaturas, tensiones) en la misma carpeta.
1. Verificación del contenido de la caja y de la **polaridad** del plug de la fuente.
2. Configuración de red: IP fija `192.168.1.2/24` en la placa libre, con `nmcli` (sin puerta de
   enlace) y `ufw allow 6201/udp` si el firewall está activo. Revisar el choque de redes.
3. Verificar que llegan datos: `ping 192.168.1.62` y sobre todo
   `sudo tcpdump -i <placa> udp port 6201 -c 10`.
4. Compilar y ejecutar `example_lidar_udp`. **Registrar las versiones de hardware y firmware.**
5. Compilar el driver ROS 2 en Jazzy (dependencias: `ros-jazzy-pcl-ros`,
   `ros-jazzy-pcl-conversions`, `libpcl-dev`, `libeigen3-dev`). Lanzarlo y verificar
   `ros2 topic hz` de `/unilidar/cloud` y `/unilidar/imu`.
6. Crear un `scripts/` con los comandos repetitivos (configurar red, lanzar driver, grabar).

### Etapa 2 — Grabación y SLAM
1. Grabaciones de referencia con `ros2 bag record`: sala quieta (1–2 min), una persona caminando y
   un recorrido con el sensor en la mano.
2. Compilar Point-LIO (`dfloreaa/point_lio_ros2`) en Jazzy; si falla, ir al contenedor Humble.
3. Procesar las grabaciones y obtener `scans.pcd`. Revisar en CloudCompare (paredes rectas, sin
   duplicar, llegada igual a la partida).

### Etapa 3 — Mapeo de una habitación (objetivo del corto plazo)
1. Procedimiento de recorrido: quieto de 5 a 10 s al empezar, caminar despacio, girar suave, no tapar
   el sensor con el cuerpo, terminar en el punto de partida y quedarse quieto.
2. Montaje para llevar el sensor en la mano (placa o mango con los 4 M3), con cables largos o con una
   notebook.
3. Productos finales a dejar documentados y reproducibles:
   - **mapa 3D** (`.pcd`), limpio;
   - **mapa 2D de ocupación** para Nav2 (`.pgm` + `.yaml`), proyectando una franja de alturas de la
     nube. Evaluar herramientas existentes o escribir un script propio (por ejemplo, Python con
     Open3D o NumPy) y documentar los parámetros: resolución, franja de alturas, origen;
   - opcional: malla y mundo de **Gazebo** de la habitación (gemelo digital, sirve para simulación).

### Etapa 4 — Implementación en la Jetson del robot (documentar ahora, validar después)
Marcar toda esta sección como **"pendiente de validar con el robot"**.
- La Jetson probablemente use Ubuntu 20.04 + JetPack 5.x (**A VERIFICAR**): el driver ROS 2 del L2
  está verificado justamente en 20.04 + Foxy, y el SDK trae la librería para aarch64.
- **Conexión física:** RJ45 del panel del robot. Alimentación desde el XT30 de 24 V con un conversor
  DC-DC a 12 V (≥ 2 A) y un cable al plug DC 3,5 × 1,35.
- **Red:** reconfigurar el L2 con el SDK (`setLidarIpAddressConfig`) a una IP libre de `192.168.123.x` y destino
  `192.168.123.164`. Evitar .161, .164 y los bloques .1–.30 y .120–.170. Antes, mapear la red con
  `nmap -sn 192.168.123.0/24`.
- Alternativa sin tocar el robot: kit independiente (L2 + RPi 5 + batería) que solo graba, con el
  procesamiento en la PC.
- Lista de cosas a verificar con el robot: sistema operativo, versión de ROS, IPs libres, nombre de
  la interfaz de red, espacio en disco, puntos de montaje.

### Etapa 5 — Preparación para el largo plazo (diseño, no implementación)
Dejar un documento `docs/pasos/futuro_navegacion.md` con:
- **Paso del mapa al robot:** mapa 2D (`.pgm`/`.yaml`) para AMCL/Nav2 y mapa 3D (`.pcd`) para una
  posible localización 3D; convención de frames (`map`, `odom`, `base_link`, `unilidar_lidar`) y
  transformada LiDAR→cuerpo del robot, que saldrá del CAD del soporte.
- **Localización:** odometría Point-LIO + AMCL sobre el mapa 2D, con `pointcloud_to_laserscan` en un
  marco **nivelado con la gravedad y a altura constante** (al caminar, el torso del bípedo cabecea).
  Alternativa: localización 3D por registro NDT/ICP.
- **Mapa en tiempo real y corrección de rutas:** SLAM en línea + costmap local de Nav2 con la nube en
  vivo. Puente `cmd_vel` → `LocoClient::Move(vx, vy, vyaw)` con límites de velocidad y *watchdog*
  que ejecute `StopMove()`. Decidir si se procesa en la PC (Wi-Fi) o a bordo.

### Etapa 6 — Documento PDF final
- Seguir `docs/FORMATO_DOCUMENTO.md`. Como referencia visual, abrir
  `docs/referencias/formato/Referencia_formato_Documentacion_Firmware_PLC14_v0.0.5.pdf`: copiar el
  diseño y la marca DataPyme (logo y colores), nunca su contenido.
- Contenido: guía desde cero hasta el archivo de la habitación (etapas 1 a 3), más los capítulos de la
  Jetson (etapa 4) y del trabajo futuro (etapa 5).
- Público: estudiantes de nivel básico, medio y avanzado. Explicar los conceptos (qué es una nube de
  puntos, un tópico, un SLAM) en recuadros breves, sin frenar a quien ya los sabe.
- Generar el PDF desde HTML/CSS (por ejemplo con Chromium/Playwright o WeasyPrint). Guardar la
  fuente en `docs/pdf/` y el PDF en `docs/pdf/salida/`.

---

## 7. Cuándo preguntarle al usuario

- Antes de cualquier `sudo`, cambio de red o instalación grande.
- Si un paso falla dos veces con el mismo error.
- Si hay que elegir entre alternativas con consecuencias (por ejemplo, Jazzy nativo o Docker Humble).
- Para datos que solo él puede ver: LEDs, polaridad medida, versiones mostradas en pantalla, qué hay
  conectado.
