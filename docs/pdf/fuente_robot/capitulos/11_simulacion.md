# 11. Los dos objetivos juntos, en simulación

En Gazebo, un robot del tamaño aproximado del R1, con un LiDAR de la geometría del L2, recibe un
mapa, se ubica en él, va solo hasta un destino y **esquiva una caja que aparece en su camino** y que
no está en el mapa.

!!! concepto "Qué es y qué no es esta simulación"
    El robot es un **bloque** de 0,25 × 0,40 × 1,45 m que se mueve con las mismas órdenes de
    velocidad que recibiría la marcha del R1. **No** simula la marcha del humanoide ni el cabeceo del
    torso, y la odometría es exacta (en el robot real la da Point-LIO, probada en el capítulo 9). El
    LiDAR simulado tiene 18 anillos de 0 a 90°, 360 puntos por anillo, 10 Hz y 1 cm de ruido, y va
    montado invertido, 0,20 m por delante del torso, a 1,55 m (como el capítulo 4.4).

## 11.1 La sala de prueba y su mundo

Los mapas tomados en la mano tienen muebles y ruido y casi no dejan espacio libre para el robot. Para
la simulación se usa una **sala de prueba** de 7 × 5 m, con una pared interior con una puerta de 1 m,
una mesa y un mueble:

```bash
./scripts/simulacion/crear_sala_de_prueba.py
./scripts/simulacion/generar_mundo_gazebo.py mapas/sala_de_prueba
```

```text
Sala de prueba: 7.2 x 5.2 m, 164 x 124 celdas -> mapas/sala_de_prueba/mapa_2d.*
Celdas ocupadas: 1760 -> 9 cajas de 2.0 m de alto
Zona libre apta (margen 0.45 m): 18.57 m²
Inicio:    x=5.275 y=3.375 yaw=-149°
Destino:   x=0.525 y=0.525  (recorrido de unos 7.95 m)
```

`generar_mundo_gazebo.py` sirve para **cualquier** mapa 2D (el de la guía anterior o uno grabado
con el robot): levanta las celdas ocupadas como paredes de 2 m y elige el inicio, el destino y un
punto para el obstáculo. Las coordenadas del mundo son las mismas que las del mapa.

## 11.2 Lanzar la simulación

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 launch scripts/simulacion/simulacion.launch.py              # con RViz
ros2 launch scripts/simulacion/simulacion.launch.py gui:=true    # también la ventana de Gazebo
```

Se lanzan Gazebo, el robot en el punto de inicio, el puente de tópicos entre Gazebo y ROS 2 y la
**misma** navegación que con el sensor real. En RViz, con la herramienta *2D Goal Pose* (clic y
arrastrar) se manda al robot a cualquier punto del mapa.

## 11.3 Prueba automática

Con la simulación corriendo, en otra terminal:

```bash
./scripts/simulacion/probar_navegacion_sim.py
```

La prueba manda al robot del inicio al destino y compara todo el tiempo la pose de AMCL con la
**real** de Gazebo. Cuando el robot recorrió 1,5 m, hace aparecer una caja de 0,4 × 0,4 × 0,8 m
**sobre el camino planificado**, 1,3 m por delante. Cuando el robot la dejó atrás, la quita y
comprueba que el costmap la borró.

```text
[  5.9 s] Caja puesta en x=2.94 y=2.94 (1.3 m por delante, sobre el plan)
[  9.9 s] Plan nuevo: pasa a 0.68 m del centro de la caja
[ 11.8 s] Caja quitada (el robot está a 0.99 m); costmap global en la caja: 100
[ 16.9 s] 5 s después: costmap global en la caja: 69
Resultado: LLEGÓ en 26.5 s (reloj de la PC); recorrido real 6.90 m
OBJETIVO 1 — error de posición: medio 0.051 m, máximo 0.118 m
OBJETIVO 2 — distancia mínima robot-caja (centros): 0.68 m (choque si < 0.40 m)
```

![Prueba en simulación: plan inicial, caja que aparece, plan nuevo, recorrido real y estimación de AMCL](docs/img/robot_simulacion_recorrido.png)

## 11.4 Resultados de cuatro corridas

| Corrida | Resultado | Recorrido | Error medio (máx.) de AMCL | Distancia a la caja | Costmap al quitarla |
|---|---|---|---|---|---|
| 1 | Llegó | 7,54 m | 0,056 m (0,154 m) | 0,70 m | 100 → 0 |
| 2 | Llegó | 6,85 m | 0,053 m (0,119 m) | 0,71 m | 100 → 84 |
| 3 | Llegó | 7,46 m | 0,059 m (0,178 m) | 0,70 m | 100 → 0 |
| 4 | Llegó | 6,90 m | 0,051 m (0,118 m) | 0,68 m | 100 → 69 |

Hay choque si la distancia entre centros es menor que 0,40 m. En el costmap, un valor menor que 99
quiere decir **sin obstáculo**: solo queda el inflado de las paredes cercanas.

## 11.5 Lo que encontró la simulación

| Problema | Causa | Solución |
|---|---|---|
| El robot no se movía | El LiDAR veía el propio cuerpo y el monitor de colisiones lo frenaba | `filtro_cuerpo.py` |
| Se detenía antes de la puerta | Radio y zona inflada demasiado grandes para una puerta de 1 m | Radio 0,26 m, inflado 0,45 m |
| Llegaba pero no terminaba | Una zona de parada fija le impedía girar frente a la pared | Zona que frena al 40 % |
| El controlador no llegaba a 20 Hz | Gazebo y Nav2 en la misma PC | Controlador a 10 Hz |

Todos son problemas que también hubiera tenido el robot real: la simulación los encontró sin riesgo.
