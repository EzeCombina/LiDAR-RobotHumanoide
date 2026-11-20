# Paso R00 — Arquitectura: piezas, marcos de referencia y flujo de datos

## Objetivo

Explicar cómo se conectan las piezas que permiten al robot (1) **ubicarse en un mapa ya hecho y
moverse por él** y (2) **esquivar obstáculos con el LiDAR en tiempo real**, antes de entrar en los
pasos R02–R06, que las instalan y las prueban.

Todo lo de este documento está **implementado y probado en la PC** (con grabaciones reales y en
simulación, 2026-11-20). Lo único sin probar es el último eslabón: el envío de velocidades al R1
real (R06).

## 1. Flujo de datos

```text
                 L2 (driver) ─► /unilidar/cloud, /unilidar/imu
                                       │
                                       ▼
                             Point-LIO (odometría)
                     /aft_mapped_to_init      /cloud_registered_body
                              │                       │
                              ▼                       ▼
                       base_nivelada.py         filtro_cuerpo.py ─► /nube_obstaculos
                 odom -> base_footprint, /odom        │
                              │          ┌────────────┼──────────────────────┐
                              │          ▼            ▼                      ▼
                              │  pointcloud_to_  costmaps de Nav2      collision_monitor
                              │  laserscan        (obstáculos en vivo)  (freno de seguridad)
                              │     /scan              │                      ▲
                              │       ▼                ▼                      │
     mapa_2d.pgm/.yaml ─► map_server ─► AMCL    planificador + controlador ───┘
                                     map -> odom          /cmd_vel_nav ─► velocity_smoother
                                                                                 │
                                         /cmd_vel ◄── collision_monitor ◄────────┘
                                             │
                                             ▼
                              puente_cmd_vel_r1.py ─► LocoClient.Move (marcha del R1)
```

- **Objetivo 1** = la parte izquierda: el mapa guardado + AMCL, que compara el barrido 2D con el
  mapa y corrige la deriva de la odometría (`map -> odom`).
- **Objetivo 2** = la parte derecha: la nube en vivo entra a los costmaps (lo que no está en el mapa
  se marca como obstáculo y el planificador lo rodea) y al `collision_monitor` (frena si algo se
  cruza, aunque falle el resto).

En la simulación (R05), Gazebo reemplaza al L2, a Point-LIO y a `base_nivelada.py` (da la nube y
la odometría del robot simulado); todo lo demás es **lo mismo**.

## 2. Marcos de referencia (frames)

```text
map ─(AMCL)─► odom ─(base_nivelada, fija)─► pointlio_odom ─(Point-LIO)─► body
               │
               └─(base_nivelada)─► base_footprint
```

| Marco | Qué es | Quién lo publica |
|---|---|---|
| `map` | Marco del mapa guardado (el del mapa limpio del paso 07: piso en z = 0) | — |
| `odom` | Marco de la odometría, con el piso en z = 0 | — |
| `pointlio_odom` | Marco fijo de Point-LIO: donde arrancó el sensor, eje z con la gravedad | `base_nivelada.py` (`odom -> pointlio_odom`, sube el origen a la altura inicial del sensor) |
| `body` | El sensor (IMU del L2); marco de `/cloud_registered_body` | Point-LIO |
| `base_footprint` | El robot sobre el piso, **sin inclinación** (solo gira alrededor de la vertical) | `base_nivelada.py` |

Por qué `base_footprint` es **nivelado**: al caminar, el torso de un bípedo cabecea. Si el barrido
2D para AMCL se calculara en un marco que cabecea, "tocaría" el piso o el techo y AMCL vería paredes
donde no hay. `base_nivelada.py` toma la pose del sensor, le aplica el montaje (dónde va el sensor
en el robot, `config/navegacion/montaje_*.yaml`) y publica solo la posición en el plano y el giro.

## 3. Piezas propias del proyecto

| Pieza | Archivo | Qué hace |
|---|---|---|
| Base nivelada | `scripts/navegacion/base_nivelada.py` | Odometría Point-LIO → `odom -> base_footprint` y `/odom` |
| Filtro del cuerpo | `scripts/navegacion/filtro_cuerpo.py` | Quita de la nube los puntos del propio robot (o de quien lleva el sensor) |
| Lanzamiento | `scripts/navegacion/navegacion.launch.py` | Modos `localizacion`, `navegacion` y `obstaculos`, con el sensor o una grabación |
| Parámetros de Nav2 | `config/navegacion/nav2_lidar.yaml` | Basado en el `nav2_params.yaml` de Jazzy; cambios documentados en su encabezado |
| Montajes | `config/navegacion/montaje_mano.yaml`, `montaje_robot.yaml` | Dónde va el sensor y la caja del cuerpo |
| Pruebas con grabaciones | `scripts/navegacion/probar_con_grabacion.sh`, `evaluar_localizacion.py`, `evaluar_obstaculos.py` | Objetivos 1 y 2 sin sensor |
| Simulación | `scripts/simulacion/*` y `config/simulacion/*` | Sala de prueba, mundo, robot simplificado, prueba automática |
| Puente al robot | `scripts/navegacion/puente_cmd_vel_r1.py` | `/cmd_vel` → `LocoClient.Move`, con límites y watchdog |

## 4. Decisiones tomadas y por qué

| Decisión | Motivo |
|---|---|
| Odometría con **Point-LIO** (no con las patas del robot) | El R1 no publica odometría a ROS; Point-LIO ya funciona con el L2 (guía anterior) |
| Localización con **AMCL sobre el mapa 2D** | Viene con Nav2, muy probado, y el mapa 2D ya está verificado (paso 07). Alternativa futura: localización 3D (NDT/ICP) sobre el `.pcd` |
| Ruido de odometría de AMCL `alpha` = 0,05 (Nav2 trae 0,2) | Con 0,2 el error medio fue 0,26 m; con 0,05, 0,12 m (R03). El 0,2 es para ruedas que patinan |
| Obstáculos con la **nube 3D** en los costmaps (no con un barrido 2D) | Ve mesas y estantes a cualquier altura de la franja 0,10–1,80 m |
| La **fuente** de la nube acepta 0–3 m y la **capa** marca 0,10–1,80 m | Si la fuente filtra a 1,80 m, los rayos al techo se descartan y lo que pasó por delante queda marcado para siempre (encontrado en R04) |
| **Filtro del cuerpo** antes de Nav2 | El LiDAR ve el propio robot; sin el filtro, el `collision_monitor` lo frena siempre (encontrado en R05) |
| Zona de `collision_monitor` que **frena al 40 %**, no "stop" | Una zona de parada fija frena también los giros y el robot queda trabado mirando una pared (encontrado en R05) |
| Sensor **invertido** (cúpula abajo) y **adelantado** 0,20 m | El L2 ve una semiesfera hacia la cúpula: derecho no ve nada por debajo de su altura. Invertido sobre la cabeza, el propio cuerpo le tapa el piso cercano; adelantado, ve el piso de adelante. Provisorio: **A VERIFICAR** con el soporte real |
| Velocidades bajas (0,30 m/s, 0,6 rad/s) | Humanoide; primeras pruebas. **A VERIFICAR** con el R1 |

## 5. Trabajo futuro (no implementado)

- **Mapa en tiempo real** mientras navega (SLAM en línea): Point-LIO ya arma el mapa 3D en vivo;
  para 2D, `slam_toolbox` sobre el mismo barrido nivelado. Hoy la corrección de rutas ya funciona
  con el costmap local (R04), sin necesitar SLAM en línea.
- **Localización 3D** por registro (NDT/ICP) contra `mapa_limpio.pcd`, si AMCL resulta poco
  confiable en lugares con muchos muebles (como la oficina, R03).
- **Procesamiento a bordo** (Jetson) o en la PC por Wi-Fi: decisión abierta; medir la carga de
  Point-LIO + Nav2 en la Jetson (en `aarch64` Point-LIO compila con un solo hilo, `MP_PROC_NUM=1`).
