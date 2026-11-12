# Paso 05 — SLAM con Point-LIO: de la grabación al mapa 3D

## Objetivo

Procesar una grabación del L2 (paso 04) con el SLAM **Point-LIO** para obtener un **mapa 3D** del
lugar en un archivo `.pcd`, y verlo en RViz.

> **¿Qué es un SLAM?** *Simultaneous Localization And Mapping*: localización y mapeo simultáneos.
> Cada nube del sensor está expresada respecto del sensor en ese instante; si el sensor se mueve,
> las nubes no se pueden sumar directamente. Point-LIO combina la nube con la IMU y calcula,
> momento a momento, **dónde está el sensor** (su trayectoria). Con eso ubica cada nube en un
> sistema de coordenadas fijo (`camera_init`) y las suma en **un único mapa coherente**.

| | Driver + grabación (pasos 03–04) | Point-LIO (este paso) |
|---|---|---|
| Entrada | El sensor | Nube + IMU (en vivo o desde una grabación) |
| Salida | Nubes sueltas, relativas al sensor | Trayectoria del sensor + mapa 3D (`scans.pcd`) |
| Sensor en movimiento | Las nubes no se pueden juntar | Las junta correctamente |

## Requisitos

- Paso 00 completo (`ros-jazzy-pcl-ros`, `ros-jazzy-pcl-conversions`, `libpcl-dev`,
  `libeigen3-dev`, `rosdep`).
- Una grabación hecha con el paso 04. **No hace falta el sensor conectado.**
- Unos 2 GB de RAM libres por cada 10 millones de puntos del mapa (A VERIFICAR con mapas grandes).

## 1. Descargar y compilar Point-LIO

Se usa el *fork* para ROS 2 `dfloreaa/point_lio_ros2`, que trae la configuración del L2. No
necesita el driver de Livox (esa dependencia está comentada). Se compila en un espacio de trabajo
propio, fuera del repositorio del proyecto:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/lidar_ws/point_lio_ws/src && cd ~/lidar_ws/point_lio_ws/src
git clone https://github.com/dfloreaa/point_lio_ros2.git
cd point_lio_ros2 && git checkout a8e2d0d5090af97ead8dd4fac3d37cf3dbb33ff7   # versión probada
cd ~/lidar_ws/point_lio_ws
rosdep check --from-paths src --ignore-src
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

**Salida esperada:**

```text
All system dependencies have been satisfied
Starting >>> point_lio
--- stderr: point_lio
CMake Warning (dev) at /usr/lib/x86_64-linux-gnu/cmake/pcl/Modules/FindFLANN.cmake:45 (find_package):
  Policy CMP0144 is not set: ...
CMake Warning (dev) at CMakeLists.txt:61 (find_package):
  Policy CMP0148 is not set: The FindPythonInterp and FindPythonLibs modules
  are removed. ...
---
Finished <<< point_lio [52.8s]
Summary: 1 package finished [53.0s]
```

Los avisos de CMake no afectan; el compilador no da advertencias. El autor lo probó en Ubuntu
22.04 + Humble; en este proyecto se verificó que **compila y funciona en Ubuntu 24.04 + Jazzy**
(2026-11-12), sin necesidad de un contenedor con Humble.

> **Dónde guarda el mapa:** Point-LIO escribe `PCD/scans.pcd` dentro de su **carpeta fuente**
> (`~/lidar_ws/point_lio_ws/src/point_lio_ros2/PCD/scans.pcd`), no en `install/`. La ruta queda
> fija al compilar (`ROOT_DIR`). Cada corrida **sobrescribe** el archivo anterior.

## 2. Configuración para el L2

Se usa la configuración que trae el paquete, sin cambios: `config/unilidar_l2.yaml` y
`launch/mapping_unilidar_l2.launch.py`. Los parámetros más importantes:

| Parámetro | Valor | Significado |
|---|---|---|
| `lid_topic` / `imu_topic` | `/unilidar/cloud` / `/unilidar/imu` | Tópicos del driver del L2 |
| `lidar_type` / `scan_line` | 5 / 18 | Formato de nube de Unitree, 18 anillos |
| `timestamp_unit` | 0 | El campo `time` de cada punto está en segundos |
| `blind` | 0,5 m | Descarta puntos a menos de 0,5 m (la mano o el cuerpo de quien lleva el sensor) |
| `start_in_aggressive_motion` | false | Hay que **empezar con el sensor quieto**: la IMU se inicializa en reposo |
| `gravity_align` | true | El eje Z del mapa se alinea con la gravedad medida al inicio, **cualquiera sea la orientación del sensor** |
| `acc_norm` | 9,81 | La IMU entrega la aceleración en m/s² |
| `extrinsic_T` / `extrinsic_R` | `[0.007698, 0.014655, -0.00667]` / identidad | Posición de la IMU respecto de la nube (de fábrica, no se estima: `extrinsic_est_en: false`) |
| `pcd_save_en` / `interval` | true / -1 | Guarda **todo** el mapa en un único archivo al cerrar |
| `filter_size_map` (launch) | 0,1 m | Resolución del mapa interno de Point-LIO |

## 3. Procesar una grabación con el script del proyecto

El script `scripts/procesar_grabacion.sh` hace todo el proceso: verifica que no haya otra fuente de
datos activa, lanza Point-LIO, reproduce la grabación **una vez**, cierra Point-LIO correctamente
(que es cuando guarda el mapa) y copia el resultado a `mapas/` con un nombre propio.

**Con el driver del sensor detenido:**

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/procesar_grabacion.sh bags/<carpeta> [nombre_del_mapa] [--rviz]
```

- `nombre_del_mapa` es opcional (por defecto, el nombre de la grabación).
- `--rviz` abre la ventana de Point-LIO para ver cómo se arma el mapa (desde una terminal del
  escritorio).
- Tarda lo mismo que duró la grabación, más unos segundos.

**Salida obtenida** (grabación `persona_caminando`, 60 s):

```text
Grabación: bags/2026-11-12_1028_persona_caminando
Mapa de salida: .../mapas/2026-11-12_1049_persona_caminando_pointlio.pcd

Point-LIO en marcha. Reproduciendo la grabación (tarda lo mismo que duró)...
Reproducción terminada. Deteniendo Point-LIO y guardando el mapa...

Mapa: 2026-11-12_1049_persona_caminando_pointlio.pcd
Generado: 2026-11-12 10:50:52 en eze-laptop
Grabación de origen: bags/2026-11-12_1028_persona_caminando
SLAM: Point-LIO (point_lio_ros2), config/unilidar_l2.yaml + mapping_unilidar_l2.launch.py
Puntos: 1121515
Tamaño: 35M

Para verlo: ./scripts/ver_mapa.sh .../mapas/2026-11-12_1049_persona_caminando_pointlio.pcd
```

En `mapas/` quedan tres archivos por mapa: el `.pcd` (fuera de git), el `.txt` con el resumen (se
sube a git) y el `.log` de Point-LIO (fuera de git).

### Hacerlo a mano (dos terminales)

```bash
# Terminal 1: Point-LIO
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/point_lio_ws/install/setup.bash
ros2 launch point_lio mapping_unilidar_l2.launch.py rviz:=false   # o rviz:=true

# Terminal 2: reproducir la grabación
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 bag play bags/<carpeta>
```

Cuando termina la reproducción, **Ctrl+C en la terminal 1**: Point-LIO guarda
`~/lidar_ws/point_lio_ws/src/point_lio_ros2/PCD/scans.pcd`. Copiarlo con un nombre descriptivo
antes de la próxima corrida.

**Salida esperada de Point-LIO al recibir los primeros datos:**

```text
[pointlio_mapping-1] lidar_type: 5
[pointlio_mapping-1] ~~~~/home/<usuario>/lidar_ws/point_lio_ws/src/point_lio_ros2/ file opened
[pointlio_mapping-1] first lidar time1.79449e+09
[pointlio_mapping-1] [INFO] [...] [laserMapping]: IMU Initializing: 1.0 %
[pointlio_mapping-1] [WARN] [...] [laserMapping]: Reset ImuProcess
[pointlio_mapping-1] [INFO] [...] [laserMapping]: IMU Initializing: 100.0 %
```

Tópicos que publica Point-LIO: `/cloud_registered` (nube actual ubicada en el mapa), `/Laser_map`,
`/aft_mapped_to_init` (posición estimada del sensor, `nav_msgs/Odometry`), `/path` (trayectoria) y
`/tf`.

## 4. Ver el mapa

Desde una terminal del escritorio de Ubuntu:

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/ver_mapa.sh mapas/<archivo>.pcd
```

El script publica el `.pcd` en `/cloud_pcd` con `pcd_to_pointcloud` (de `pcl_ros`, ya instalado) y
abre RViz con `config/rviz/ver_mapa.rviz` (marco fijo `map`, colores por altura). Al cerrar RViz
se detiene todo.

## 5. Resultados de las grabaciones de referencia (2026-11-12)

| Grabación | Puntos del mapa | Tamaño | Observaciones |
|---|---|---|---|
| `sala_quieta` (90 s) | 1.729.416 | 53 MB | Mapa de ~8 × 6 m en planta y 2,85 m de alto (de 0 a 2,85 m: el sensor estaba en el piso y solo ve hacia arriba) |
| `persona_caminando` (60 s) | 1.121.515 | 35 MB | — |

**Prueba de estabilidad con el sensor quieto (`sala_quieta`):** se registró la posición estimada por
Point-LIO (`/aft_mapped_to_init`) durante toda la grabación. Como el sensor no se movió, debería
quedar en cero:

| Medida | Resultado |
|---|---|
| Variación en altura (Z) | ±2 cm |
| Desplazamiento horizontal | ~9 cm en los primeros segundos, después estable |
| Desplazamiento máximo respecto del inicio | 15 cm |

Es aceptable para una primera prueba, pero mayor de lo esperable. Posibles causas, **A VERIFICAR**:
la vibración del sensor (bitácora del 2026-11-12) y que la IMU de este sensor mide en reposo una
aceleración media de 7,8 m/s² en lugar de 9,8 m/s².

> La cantidad de puntos varía levemente entre corridas de la misma grabación (por ejemplo, 1.729.416
> y 1.735.865), porque depende de los tiempos de reproducción. Es normal.

## 6. Orientación del sensor al grabar

Gracias a `gravity_align: true`, Point-LIO funciona con el sensor en **cualquier orientación**
(horizontal, inclinado o vertical), siempre que **empiece quieto** para medir la gravedad. Lo que
cambia es qué parte del lugar ve el sensor:

| Orientación | Ve | No ve |
|---|---|---|
| Horizontal, cúpula hacia arriba | 360° alrededor: paredes, objetos altos, techo | Piso y obstáculos por debajo del sensor |
| Vertical, cúpula hacia adelante | Lo que está adelante: piso, paredes, obstáculos bajos y techo | Todo lo que está detrás |
| Inclinado (intermedio) | Parte del piso adelante y casi todo alrededor | Una parte del piso detrás |

Comparación en la práctica: **pendiente de prueba** (A VERIFICAR).

## Verificación final

- [ ] `colcon build` termina con `1 package finished`.
- [ ] `procesar_grabacion.sh` termina mostrando el resumen del mapa.
- [ ] `ver_mapa.sh` muestra el mapa y se reconoce el lugar.
- [ ] Con una grabación con el sensor quieto, el mapa no aparece duplicado ni "corrido".

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: ya hay algo publicando /unilidar/cloud` | El driver o un `ros2 bag play` siguen abiertos | Detenerlos antes de procesar |
| `ERROR: ya hay un Point-LIO corriendo` | Quedó un Point-LIO abierto | Cerrarlo (Ctrl+C en su terminal) |
| No se crea `scans.pcd` | Point-LIO se cerró de golpe (no con Ctrl+C) o nunca recibió datos | Cerrar siempre con Ctrl+C; revisar el `.log` |
| El mapa se ve duplicado o torcido | Movimientos bruscos, inicio con el sensor en movimiento o pocas superficies de referencia | Repetir la grabación siguiendo el procedimiento del paso 04 |
| El `scans.pcd` de una corrida tiene datos de otra | Point-LIO sobrescribe siempre el mismo archivo | Usar el script, que copia el mapa con nombre propio |
| `PackageNotFoundError: "package 'point_lio' not found` | No se cargó el entorno de Point-LIO | `source ~/lidar_ws/point_lio_ws/install/setup.bash` |
