# Paso R05 — Objetivos 1 y 2 juntos, en simulación (Gazebo)

## Objetivo

Probar de punta a punta, sin el robot, que el sistema:

1. **se ubica en un mapa ya hecho y va solo de un punto a otro** (objetivo 1), y
2. **esquiva un obstáculo que no está en el mapa**, visto con el LiDAR en vivo, y lo **borra**
   cuando desaparece (objetivo 2).

En Gazebo se simula un robot del tamaño aproximado del R1 con un LiDAR de la geometría del L2,
dentro de un mundo hecho **a partir del mapa 2D**. Nav2 y toda la configuración son **los mismos**
que con el sensor real; solo cambian la fuente de la nube y la odometría.

## Requisitos

- Paso R02. La simulación no usa Point-LIO.
- Una PC con aceleración gráfica (el LiDAR de Gazebo renderiza con la GPU; en la PC del laboratorio
  funciona con la gráfica integrada AMD y sin ventana, `--headless-rendering`).

!!! concepto "Qué es y qué no es esta simulación"
    Gazebo calcula la física y simula el LiDAR (los rayos chocan con las paredes del mundo). El
    robot es un **bloque** de 0,25 × 0,40 × 1,45 m que se mueve con las velocidades que pide Nav2
    (`cmd_vel`), como las recibiría la marcha del R1. **No** simula la marcha del humanoide ni el
    cabeceo del torso, y la odometría es exacta (en el robot real la da Point-LIO, probada en R03).

## 1. La sala de prueba

Los mapas tomados en la mano (habitación, oficina) tienen muebles y ruido y casi no dejan zonas
libres con espacio para el robot: con 0,45 m de margen, la habitación deja 0,01 m² libres y la
oficina 0,59 m². Para la simulación se usa una **sala de prueba**: 7 × 5 m, con una pared interior
con una puerta de 1 m, una mesa y un mueble.

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/simulacion/crear_sala_de_prueba.py
./scripts/simulacion/generar_mundo_gazebo.py mapas/sala_de_prueba
```

**Salida obtenida** (2026-11-20):

```text
Sala de prueba: 7.2 x 5.2 m, 164 x 124 celdas -> mapas/sala_de_prueba/mapa_2d.*
Mapa: mapas/sala_de_prueba  (164 x 124 celdas de 0.05 m)
Celdas ocupadas: 1760 -> 9 cajas de 2.0 m de alto
Zona libre apta (margen 0.45 m): 18.57 m²
Inicio:    x=5.275 y=3.375 yaw=-149°
Destino:   x=0.525 y=0.525  (recorrido de unos 7.95 m)
Obstáculo: x=3.075 y=1.925
Escrito: mapas/sala_de_prueba/gazebo/mundo.sdf y puntos.yaml
```

- `crear_sala_de_prueba.py` dibuja el mapa 2D con el **mismo formato** que `generar_mapa_2d.py`
  (paso 07).
- `generar_mundo_gazebo.py` sirve para **cualquier** mapa 2D: junta las celdas ocupadas en
  rectángulos, las levanta a 2 m de alto (`mundo.sdf`) y elige el inicio (lo más lejos posible de
  las paredes), el destino (el punto alcanzable más lejano) y un punto para el obstáculo
  (`puntos.yaml`). Las coordenadas del mundo son las del mapa.

## 2. Lanzar la simulación

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch scripts/simulacion/simulacion.launch.py              # con RViz
ros2 launch scripts/simulacion/simulacion.launch.py gui:=true    # también la ventana de Gazebo
ros2 launch scripts/simulacion/simulacion.launch.py rviz:=false  # por SSH
```

Lanza Gazebo con `mapas/sala_de_prueba/gazebo/mundo.sdf`, el robot
(`config/simulacion/robot_r1_simplificado.sdf`) en el punto de inicio, el puente de tópicos
(`config/simulacion/puente_gz.yaml`), el montaje fijo del LiDAR y `navegacion.launch.py` con
`fuente:=simulacion montaje:=robot`.

| Simulado | Igual que en el robot real |
|---|---|
| LiDAR: 18 anillos de 0 a 90°, 360 puntos por anillo, 10 Hz, 0,5–30 m, ruido de 1 cm | La geometría del L2 |
| Montaje: invertido, 0,20 m delante del torso, a 1,55 m | `config/navegacion/montaje_robot.yaml` (provisorio, A VERIFICAR) |
| Odometría exacta de Gazebo (`odom -> base_footprint`) | En el robot: Point-LIO + `base_nivelada.py` |
| Nube en `/lidar/points`, marco `lidar_sim` | En el robot: `/cloud_registered_body`, marco `body` |

Para mandar al robot a un punto a mano: en RViz, herramienta **Nav2 Goal** (o *2D Goal Pose*),
clic y arrastrar en el destino. Para agregar un obstáculo a mano, con la ventana de Gazebo
(`gui:=true`), menú de formas (cubo) y soltarlo en el camino.

## 3. Prueba automática

Con la simulación corriendo, en otra terminal:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/simulacion/probar_navegacion_sim.py
```

1. Manda al robot del inicio al destino.
2. Compara todo el tiempo la pose de AMCL con la pose **real** del robot en Gazebo (objetivo 1).
3. Cuando el robot recorrió 1,5 m, hace aparecer una **caja de 0,4 × 0,4 × 0,8 m** sobre el plan,
   1,3 m por delante del robot. La caja **no está en el mapa**: solo la ve el LiDAR (objetivo 2).
4. Cuando el robot la dejó atrás, la quita y comprueba, 5 s después, que el costmap global la borró.
5. Guarda `resumen.txt`, `recorrido.csv` y `recorrido.png` en
   `resultados/<fecha>_simulacion_sala_de_prueba/`.

**Salida obtenida** (2026-11-20, corrida final):

```text
[  5.9 s] Caja puesta en x=2.94 y=2.94 (1.3 m por delante, sobre el plan)
[  9.9 s] Plan nuevo: pasa a 0.68 m del centro de la caja
[ 11.8 s] Caja quitada (el robot está a 0.99 m); costmap global en la caja: 100
[ 16.9 s] 5 s después: costmap global en la caja: 69
Resultado: LLEGÓ en 26.5 s (reloj de la PC); recorrido real 6.90 m
Distancia final al destino: 0.23 m (tolerancia de Nav2: 0,25 m)
OBJETIVO 1 — Ubicarse en el mapa (AMCL frente a la pose real)
  error de posición: medio 0.051 m, máximo 0.118 m, final 0.050 m
  error de orientación: medio 2.3°, máximo 10.2°
OBJETIVO 2 — Esquivar con el LiDAR en vivo
  caja de 0.4 m puesta en (2.94, 2.94), sobre el plan
  el plan nuevo pasa a 0.68 m del centro de la caja
  distancia mínima robot-caja (centros): 0.68 m (choque si < 0.40 m ...)
  costmap global en la huella de la caja (valor máximo): 100 con la caja -> 69 5 s después de quitarla
```

![Prueba en simulación: plan inicial, caja que aparece, plan nuevo, recorrido real y estimación de AMCL](docs/img/robot_simulacion_recorrido.png)

### 3.1 Resultados de cuatro corridas

| Corrida | Resultado | Recorrido | Error medio (máx.) de AMCL | Distancia mínima a la caja | Costmap al quitar la caja |
|---|---|---|---|---|---|
| 1 | Llegó | 7,54 m | 0,056 m (0,154 m) | 0,70 m | 100 → 0 |
| 2 | Llegó | 6,85 m | 0,053 m (0,119 m) | 0,71 m | 100 → 84 |
| 3 | Llegó | 7,46 m | 0,059 m (0,178 m) | 0,70 m | 100 → 0 |
| 4 (final) | Llegó | 6,90 m | 0,051 m (0,118 m) | 0,68 m | 100 → 69 |

Hay choque si la distancia entre centros es menor que 0,40 m. Un valor menor que 99 en el costmap
quiere decir **sin obstáculo**: solo queda el inflado de las paredes cercanas. La caja cae en un
lugar algo distinto en cada corrida porque depende de por dónde va el plan en ese momento.

### 3.2 Problemas que encontró la simulación (ya resueltos)

| Problema | Causa | Solución |
|---|---|---|
| El robot no se movía | El LiDAR veía el propio cuerpo del robot y el `collision_monitor` lo frenaba | `filtro_cuerpo.py` (R04, 1.2) |
| Se detenía antes de la puerta de 1 m | Radio 0,30 m + inflado 0,55 m: el paso quedaba muy justo | Radio 0,26 m, inflado 0,45 m (A VERIFICAR con el R1) |
| Llegaba a 0,18 m del destino pero no terminaba | La zona "stop" del `collision_monitor` le impedía girar frente a la pared | Zona que frena al 40 % (R04, 1.2) |
| El controlador no llegaba a 20 Hz | Gazebo y Nav2 en la misma PC | Controlador a 10 Hz (`model_dt` 0,1) |
| AMCL saltaba a (0, 0) al empezar la prueba | `BasicNavigator` publica (0, 0, 0) si no recibe una pose inicial | La prueba le pasa la pose de inicio |

## Verificación final

- [ ] `generar_mundo_gazebo.py mapas/sala_de_prueba` escribe `mundo.sdf` y `puntos.yaml`.
- [ ] Con la simulación corriendo, `ros2 topic hz /scan` da unos 10 Hz.
- [ ] `probar_navegacion_sim.py` termina con "Resultado: LLEGÓ", el plan nuevo pasa a más de 0,4 m
      de la caja y el costmap la borra (menos de 99) al quitarla.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `no existe .../gazebo/mundo.sdf` | No se generó el mundo | Sección 1 |
| El LiDAR no publica (`/lidar/points` vacío) | Sin aceleración gráfica para el renderizado sin ventana | Probar con `gui:=true` en el escritorio; revisar los controladores de video |
| AMCL con errores de metros | Quedó corriendo un Gazebo anterior (dos simulaciones a la vez) | Cerrar todo: `pkill -f "gz sim"` y volver a lanzar |
| `XML Element[gz_frame_id] ... not defined in SDF` (aviso) | Elemento nuevo de Gazebo Harmonic que la versión del formato SDF no conoce | No afecta: el marco `lidar_sim` se aplica igual |
