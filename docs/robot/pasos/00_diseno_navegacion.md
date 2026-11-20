# Navegación autónoma del R1 con el mapa del L2 (diseño, no implementado)

> **DOCUMENTO DE DISEÑO.** Nada de esto está implementado ni probado (2026-11-20). Describe cómo se
> piensa usar el mapa que genera la guía (pasos 04–07) para que el robot se ubique y se mueva solo
> (Fase 2 del proyecto), y qué decisiones quedan abiertas. Requiere el robot y el paso 09
> validado.

## Objetivo

Dejar definido el camino desde "tengo el mapa de la habitación" hasta "el robot va solo de un punto
a otro del mapa", para que el trabajo futuro empiece con las decisiones ya pensadas.

## 1. Qué hay hoy y qué falta

| Pieza | Estado |
|---|---|
| Mapa 3D limpio y nivelado (`mapa_limpio.pcd`) | Hecho (paso 07) |
| Mapa 2D de ocupación para Nav2 (`mapa_2d.pgm` + `mapa_2d.yaml`) | Hecho y verificado con `nav2_map_server` (paso 07) |
| SLAM en vivo (Point-LIO en tiempo real) | Probado en la PC con el sensor en la mano (paso 05, sección 7) |
| L2 montado y grabando en el robot | Documentado, sin validar (paso 09) |
| Transformada sensor → cuerpo del robot | Falta: sale del diseño del soporte |
| Localización sobre el mapa guardado | Falta (sección 4) |
| Planificación de rutas (Nav2) | Falta (sección 5) |
| Puente de velocidades Nav2 → robot | Falta (sección 6) |

## 2. Llevar el mapa al robot

Se copian los productos de la carpeta del mapa a la computadora que va a navegar (la Jetson o la
PC, ver sección 7):

```bash
rsync -av mapas/<carpeta>/mapa_2d.pgm mapas/<carpeta>/mapa_2d.yaml mapas/<carpeta>/mapa_limpio.pcd \
    unitree@192.168.123.164:~/mapas/<carpeta>/
```

| Archivo | Para qué |
|---|---|
| `mapa_2d.pgm` + `mapa_2d.yaml` | Mapa para AMCL y los planificadores de Nav2 (`nav2_map_server`) |
| `mapa_limpio.pcd` | Localización 3D (alternativa de la sección 4.2) y simulación |
| `transformacion.txt` | Rotación y traslación que se aplicaron al nivelar: relaciona el mapa limpio con el mapa original de Point-LIO |

!!! concepto "El origen del mapa"
    El mapa 2D tiene su origen (`origin` en el `.yaml`) en la esquina inferior izquierda de la
    imagen, expresado en el marco `map`. El marco `map` es el del mapa limpio: piso en z = 0 y
    paredes alineadas con los ejes. El robot tiene que arrancar sabiendo, aunque sea
    aproximadamente, dónde está en ese marco (sección 4).

## 3. Marcos de referencia (frames)

Convención estándar de ROS (REP 105), que es la que espera Nav2:

```text
map ──► odom ──► base_link ──► unilidar_lidar ──► unilidar_imu
 │        │          │                │
 │        │          │                └─ fija: sale del manual del L2 (IMU desplazada
 │        │          │                   [-0.007698, -0.014655, 0.00667] m)
 │        │          └─ fija: sale del CAD del soporte (dónde y cómo está montado el sensor)
 │        └─ continua, sin saltos: odometría (Point-LIO)
 └─ con saltos chicos: corrección de la localización (AMCL o NDT)
```

| Marco | Qué es | Quién lo publica |
|---|---|---|
| `map` | Marco fijo del mapa guardado | — |
| `odom` | Marco de la odometría: continuo, pero acumula deriva | — |
| `base_link` | Cuerpo del robot: centro entre los pies, sobre el piso, +X hacia adelante | — |
| `map → odom` | Corrige la deriva de la odometría | AMCL (o el localizador 3D) |
| `odom → base_link` | Movimiento del robot | Point-LIO + transformada fija del soporte |
| `base_link → unilidar_lidar` | Montaje del sensor | `static_transform_publisher` con los valores del CAD |

!!! importante "Point-LIO no publica base_link"
    Point-LIO publica la posición del **sensor** (marcos `camera_init → aft_mapped` por defecto,
    configurables con `odom_header_frame_id` y `odom_child_frame_id`). Para Nav2 hace falta la
    posición del **cuerpo**: un nodo chico tiene que combinar la odometría del sensor con la
    transformada fija del soporte y publicar `odom → base_link`. Point-LIO también tiene un modo
    `odom_only` (solo odometría, tópico `/odom_corrected`) que sirve para esto.

La transformada `base_link → unilidar_lidar` se mide en el CAD del soporte: posición del centro de
la cara inferior del L2 (origen de su nube) respecto de `base_link`, y su orientación (+X del
sensor opuesto a la salida del cable). Un error de pocos grados en esa orientación tuerce el mapa
2D proyectado.

## 4. Localización: dónde está el robot en el mapa

### 4.1 Opción recomendada: Point-LIO + AMCL sobre el mapa 2D

1. **Point-LIO en vivo** da la odometría (`odom → base_link`), a 10 Hz o más, con poca deriva.
2. **`pointcloud_to_laserscan`** convierte la nube 3D en un barrido 2D "falso" (como un LiDAR
   plano) tomando los puntos de la misma franja de alturas que el mapa 2D (0,10–1,80 m).
3. **AMCL** (Nav2) compara ese barrido con `mapa_2d.pgm` y publica `map → odom`.

!!! importante "El torso del bípedo cabecea"
    Al caminar, el torso del R1 se inclina hacia adelante y atrás. Si el barrido 2D se calcula en
    el marco del sensor, cuando el torso se inclina el barrido "toca" el piso o el techo y AMCL ve
    paredes donde no hay. El barrido tiene que calcularse en un marco **nivelado con la gravedad y
    a altura constante** (por ejemplo `base_footprint`: la proyección de `base_link` sobre el piso,
    sin inclinación). La inclinación sale de la IMU del L2 (Point-LIO ya la estima).

Ventaja: Nav2 trae todo (AMCL, `map_server`, `pointcloud_to_laserscan`), está muy probado y el
mapa 2D ya está verificado. Desventaja: pierde la información 3D (mesas, estantes por encima de la
franja).

### 4.2 Alternativa: localización 3D por registro (NDT o ICP)

Se compara cada nube del sensor con `mapa_limpio.pcd` completo (registro NDT o ICP, por ejemplo con
PCL) y se publica `map → odom`. Más robusta en lugares con muebles y desniveles, pero más pesada de
calcular y sin un paquete "oficial" de Nav2: habría que elegir uno de la comunidad o escribirlo.
Evaluarla si AMCL resulta poco confiable.

### 4.3 Posición inicial

AMCL necesita una estimación inicial: se marca en RViz con **2D Pose Estimate** o se arranca
siempre desde un punto conocido (por ejemplo, el punto de partida de la grabación, que es el
origen del mapa de Point-LIO antes de limpiar: ver `transformacion.txt`).

## 5. Planificación de rutas (Nav2)

Con la localización funcionando, Nav2 se configura con:

- **Costmap global** sobre `mapa_2d` (capas `static_layer` + `inflation_layer`). El radio de
  inflado sale del ancho del robot (A VERIFICAR: medida del R1).
- **Costmap local** con la nube en vivo del L2 (`obstacle_layer` o `voxel_layer` sobre
  `/unilidar/cloud`): ve obstáculos nuevos que no están en el mapa (personas, sillas movidas).
- **Planificador global** (por ejemplo `NavFn` o `Smac 2D`) y **controlador local** (por ejemplo
  `Regulated Pure Pursuit`, que limita la velocidad cerca de obstáculos y en curvas).
- **Velocidades máximas bajas** para las primeras pruebas (por ejemplo 0,2 m/s y 0,3 rad/s,
  A VERIFICAR con el robot).

Salida de Nav2: el tópico `cmd_vel` (velocidad lineal `vx`, `vy` y angular `vyaw` deseadas).

## 6. Puente cmd_vel → robot

El R1 no entiende `cmd_vel`. Su control de marcha de alto nivel se usa con el SDK de Unitree
(`unitree_sdk2` en C++ o `unitree_sdk2_python`): cliente `LocoClient` con `Move(vx, vy, vyaw)`
y `StopMove()` (A VERIFICAR los nombres y el comportamiento en el R1; la referencia del R1 menciona
`unitree_sdk2py.r1.loco.r1_loco_client.LocoClient`).

Diseño del nodo puente (a escribir):

1. Se suscribe a `cmd_vel`.
2. **Limita** las velocidades a los máximos configurados (nunca envía más que eso).
3. Llama a `Move(vx, vy, vyaw)` a frecuencia fija (por ejemplo 10–20 Hz).
4. **Watchdog:** si no llega un `cmd_vel` en, por ejemplo, 0,5 s (Nav2 se cayó, se cortó la red),
   llama a `StopMove()`.
5. Al cerrarse (Ctrl+C), llama a `StopMove()`.
6. Solo usa la marcha de alto nivel: **nunca** los tópicos de bajo nivel (`rt/lowcmd`,
   `rt/arm_sdk`). La referencia del R1 documenta que el control de brazos puede bloquear la
   locomoción.

!!! peligro "Pruebas seguras"
    Primeras pruebas con el robot en su soporte o con una persona con el control remoto en la mano
    lista para detenerlo, parada de emergencia externa cableada, área despejada y velocidades
    mínimas. Nunca controlar la marcha por Wi-Fi sin el watchdog.

El SDK de Unitree usa DDS directamente (dominio 0) y no depende de la distribución de ROS: el puente
puede ser un nodo ROS 2 que, además, inicializa el SDK. **A VERIFICAR** que el SDK y ROS 2 convivan
en el mismo proceso (ambos usan CycloneDDS; puede hacer falta separarlos en dos procesos).

## 7. ¿Dónde se procesa? Decisión abierta

| Opción | A favor | En contra |
|---|---|---|
| **Todo a bordo** (Jetson) | No depende de la red; latencia mínima | Carga de la Jetson (Point-LIO en `aarch64` compila con un solo hilo, `MP_PROC_NUM=1`); instalar Nav2 en la Jetson |
| **PC por Wi-Fi** | Más potencia; ya está todo instalado | La nube viaja por Wi-Fi (~2 MB/s); latencia y cortes; requiere el watchdog sí o sí |
| **Mixto** | Driver, Point-LIO y puente a bordo; Nav2 en la PC | Dos máquinas con la misma distribución de ROS |

Recomendación inicial: **todo a bordo**, con la PC solo para mirar en RViz. Decidirlo midiendo la
carga de la Jetson con Point-LIO en vivo.

## 8. Mapa en tiempo real y corrección de rutas (muy a futuro)

- **Mapa actualizado mientras navega:** SLAM en línea en lugar del mapa fijo. Point-LIO ya hace
  el mapa 3D en vivo; para 2D, `slam_toolbox` sobre el barrido nivelado de la sección 4.1.
- **Corrección de rutas:** el costmap local de Nav2 con la nube en vivo (sección 5) ya permite
  esquivar obstáculos nuevos y replanificar. Es el primer paso, y no requiere SLAM en línea.

## 9. Gemelo digital en Gazebo (opcional)

Una copia virtual de la habitación para probar Nav2 en simulación antes de usar el robot:

1. Malla 3D desde `mapa_limpio.pcd` (reconstrucción de superficie, por ejemplo Poisson con
   Open3D), exportada a `.dae` o `.stl`.
2. Mundo SDF de Gazebo con esa malla como objeto estático.
3. Modelo del robot (URDF del R1, `r1_description`, A VERIFICAR) con un LiDAR simulado de
   parámetros parecidos al L2 (18 anillos, 360° × 90°).

No reemplaza la localización real: sirve para probar configuraciones de Nav2 sin riesgo.

## 10. Orden de trabajo propuesto

1. Validar el paso 09 (L2 grabando en el robot) y diseñar el soporte → transformada
   `base_link → unilidar_lidar`.
2. Mapa de un lugar grabado **con el robot** (paso 09, sección 5).
3. Point-LIO en vivo a bordo + nodo `odom → base_link`; medir la carga de la Jetson.
4. `pointcloud_to_laserscan` nivelado + AMCL; comprobar en RViz que el robot se ubica bien.
5. Puente `cmd_vel` con watchdog, probado primero con velocidades enviadas a mano
   (`ros2 topic pub`) y el robot en el soporte.
6. Nav2 completo, con velocidades mínimas.
7. Opcional: gemelo en Gazebo para probar configuraciones.
