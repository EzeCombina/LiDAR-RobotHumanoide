# 11. Problemas frecuentes

Los problemas encontrados durante el desarrollo, con el mensaje de error literal cuando lo hay.

## 11.1 Instalación y repositorio

| Síntoma | Causa | Solución |
|---|---|---|
| `fatal: could not read Username for 'https://github.com'` | No hay credenciales de GitHub | `gh auth login` y `gh auth setup-git` (capítulo 4.4) |
| `E: Unable to locate package ros-jazzy-desktop` | Falta el repositorio de ROS 2 o un `apt update` | Repetir el capítulo 4.2 |
| `apt update`: `Conflicting values set for option Signed-By` | El repositorio de ROS 2 se agregó dos veces, con el método viejo (`ros2.list`) y el nuevo | `sudo rm /etc/apt/sources.list.d/ros2.list` y `sudo apt update` |
| `ros2: orden no encontrada` | La terminal no cargó ROS 2 | `source /opt/ros/jazzy/setup.bash` o abrir una terminal nueva |
| `sudo rosdep init`: `ERROR: default sources list file already exists` | Ya estaba inicializado | Ignorarlo y correr `rosdep update` |

## 11.2 Red y sensor

| Síntoma | Causa | Solución |
|---|---|---|
| `ping 192.168.1.62` sin respuesta; `eno1` en `DOWN` | Sin enlace: cable, alimentación o placa equivocada | Revisar fuente y cable; `cat /sys/class/net/eno1/carrier` debe dar `1` |
| `ping` responde pero no llegan datos | Firewall, o la PC no tiene exactamente `192.168.1.2` | `ip -br addr`; regla de `ufw` del capítulo 5.2 |
| `[Errno 98] Address already in use` | Otro programa usa el puerto 6201 (driver, ejemplo, `estado_lidar`) | Cerrarlo antes |
| `example_lidar_udp` no muestra nada | Espera datos sin límite de tiempo: no llegan | Verificar con `verificar_udp_lidar.py` |
| El sensor gira pero hay pocos puntos | Arranque en frío | Esperar unos minutos |
| El sensor dejó de responder en `192.168.1.62` | Se ejecutó `set_ip_address`, o está en modo serie | Probar `ping 192.168.123.110`; ver capítulo 5.7 |
| Ruido fuerte al girar | Ver la observación del capítulo 5.6 | Medir con `medir_vibracion_imu.py` y `estado_lidar` |

**Cuándo se cortó el enlace.** Si en algún momento dejan de llegar datos:

```bash
ip -br addr show eno1                       # debe decir UP y 192.168.1.2/24
journalctl -k --since "-30 min" --no-pager | grep -i "eno1"
```

```text
nov 12 14:32:48 eze-laptop kernel: r8169 0000:03:00.0 eno1: Link is Down
```

`Link is Down` indica que se perdió el enlace físico (cable suelto o sensor sin alimentación). Al
reconectar, la red se reconfigura sola y el driver vuelve a recibir datos sin reiniciarlo.

## 11.3 Driver y RViz

| Síntoma | Causa | Solución |
|---|---|---|
| `rviz2: symbol lookup error: /snap/core20/... undefined symbol: __libc_pthread_init` | RViz lanzado desde la terminal de VS Code instalado como snap | Abrirlo desde la terminal de Ubuntu |
| `PackageNotFoundError: "package 'unitree_lidar_ros2' not found` | Falta cargar el entorno del driver | `source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash` |
| Error al compilar: no encuentra `libunilidar_sdk2.a` | Se movió el paquete del driver | Compilarlo en su carpeta original |
| En RViz: `Fixed Frame [...] does not exist` | El marco fijo no coincide | *Global Options → Fixed Frame*: `unilidar_lidar` (nube) o `map` (mapas) |
| Por USB, se corta la conexión al lanzar el driver | Se usó el modo serie con `work_mode: 0` | Usar `modo:=usb` del launch del proyecto |

## 11.4 Grabación

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: no llegan mensajes en /unilidar/cloud. ¿Está corriendo el driver?` | El driver no está corriendo, o se cortó el enlace | Lanzar el driver; revisar la red (11.2) |
| Pitidos y `NO LLEGAN DATOS DEL LiDAR` durante la grabación | Cable suelto, o se desconectó el sensor sin cortar la grabación | Revisar conexiones; si ya se terminó, Ctrl+C y esperar el resumen |
| `revisar_grabacion.py`: `GRABACIÓN INCOMPLETA` | Se cortaron los datos antes de terminar la grabación | Repetir la grabación |
| `revisar_grabacion.py`: arranque `EN MOVIMIENTO` | El sensor no estaba quieto al empezar | Repetir arrancando con el sensor apoyado |
| En RViz se ven dos nubes al reproducir | El driver sigue corriendo | Detenerlo antes de `ros2 bag play` |

## 11.5 SLAM y mapas

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: ya hay algo publicando /unilidar/cloud` | El driver o un `ros2 bag play` siguen abiertos | Detenerlos antes de procesar |
| Mapa inclinado (planos horizontales de más de 2°) | Se arrancó con el sensor en movimiento | Repetir arrancando quieto; o nivelar con `limpiar_mapa.py` |
| Paredes duplicadas o mapa torcido | Giros bruscos o pocas referencias | Repetir más despacio |
| El mapa no tiene piso ni muebles bajos | Sensor horizontal | Grabar con el sensor vertical |
| `limpiar_mapa.py`: `Nivelación: NO se hace. ... no es el piso` | El mapa no ve el piso | `--referencia techo`, o grabar con el sensor vertical |
| El mapa 2D sale casi todo gris | No se ve el piso o el mapa no se niveló | Revisar `limpieza.txt` y la orientación del sensor |
| RViz: "No map received" (mapa 2D) | El servidor de mapas no se activó | `ros2 run nav2_util lifecycle_bringup map_server` |
| `verificar_mapa_2d.py`: porcentajes distintos u "otros valores" | Umbrales del `.yaml` modificados | `occupied_thresh: 0.65`, `free_thresh: 0.196` |
