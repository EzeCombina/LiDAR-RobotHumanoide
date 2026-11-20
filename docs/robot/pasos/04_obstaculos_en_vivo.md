# Paso R04 — Objetivo 2: obstáculos con el LiDAR en tiempo real

## Objetivo

Que el sistema use la **nube del L2 en vivo** para ver lo que **no está en el mapa** (una persona,
una silla movida, una caja) y lo tenga en cuenta para moverse, y que lo **borre** cuando se va.

Este paso explica la configuración y la prueba con grabaciones reales. La prueba completa (el robot
esquiva una caja que aparece en su camino) es en simulación, en R05.

## Requisitos

- Paso R02.
- Para la prueba: las grabaciones `persona_caminando` y `sala_quieta` (primera etapa, paso 04).

!!! concepto "¿Qué es un costmap?"
    Una grilla (celdas de 5 cm) alrededor del robot donde cada celda dice cuánto "cuesta" pasar:
    0 = libre, 100 = obstáculo, valores intermedios = cerca de un obstáculo (zona **inflada**, para
    que el robot no pase rozando). Nav2 usa dos: el **global**, sobre todo el mapa (para planificar
    la ruta), y el **local**, una ventana de 5 × 5 m que se mueve con el robot (para el controlador).
    Los dos reciben la nube en vivo: lo que el LiDAR ve se **marca**, y el espacio que los rayos
    atraviesan sin chocar se **borra**.

## 1. Cómo está configurado

En `config/navegacion/nav2_lidar.yaml`:

| Pieza | Configuración | Por qué |
|---|---|---|
| Fuente de obstáculos | La nube 3D (`/nube_obstaculos`, la del sensor sin el cuerpo) | Ve obstáculos a cualquier altura, no solo en un plano |
| Costmap local | Capa de **vóxeles** (`VoxelLayer`, 16 × 0,125 m = 2 m de alto) | Lleva la cuenta en 3D: una mesa marca aunque sus patas sean finas |
| Costmap global | Capa de obstáculos + el mapa guardado (`static_layer`) | El plan rodea lo nuevo y lo conocido |
| Franja que se marca | 0,10 a 1,80 m sobre el piso (capa) | La misma del mapa 2D; el piso y el techo no son obstáculos |
| Franja que se usa para **borrar** | 0 a 3 m (fuente) | Ver 1.1 |
| Inflado | 0,45 m, caída 4,0; robot de radio 0,26 m | Pasa por puertas de 1 m (**A VERIFICAR** con el R1) |
| `collision_monitor` | Huella proyectada 1,2 s + zona delante que frena al 40 % | Freno de seguridad aunque falle el resto |

### 1.1 Por qué la fuente acepta puntos hasta 3 m

Nav2 filtra la nube **antes** de trazar los rayos. Si la fuente solo acepta 0,10–1,80 m (lo
intuitivo), los rayos que llegan al techo se descartan, y el espacio por donde pasó una persona
**nunca se borra**. Se comprobó con la grabación `persona_caminando`: la mancha que dejaba la
persona crecía y no se limpiaba. La solución estándar: la **fuente** acepta 0 a 3 m (los rayos al
techo borran) y la **capa** marca solo 0,10 a 1,80 m.

### 1.2 Filtro del cuerpo

`scripts/navegacion/filtro_cuerpo.py` quita los puntos que caen dentro de una caja alrededor del
robot (en `base_footprint`) antes de pasar la nube a Nav2. Sin él, el robot se ve a sí mismo como
un obstáculo y el `collision_monitor` lo frena (encontrado en la simulación, R05). La caja está en
`config/navegacion/montaje_robot.yaml` (R1 aproximado, **A VERIFICAR**) y en `montaje_mano.yaml`
(la persona que lleva el sensor).

!!! importante "Zona del collision_monitor: frenar, no detener"
    Una zona fija delante del robot con acción "stop" frena también los **giros**: el robot queda
    trabado mirando una pared, sin poder darse vuelta (encontrado en R05). Por eso la zona baja la
    velocidad al 40 % (`slowdown`) y la parada la decide la **huella proyectada**
    (`FootprintApproach`), que mira hacia dónde se mueve el robot.

## 2. Prueba con grabaciones: ver el costmap en vivo

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/point_lio_ws/install/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/navegacion/probar_con_grabacion.sh obstaculos bags/2026-11-12_1028_persona_caminando 0.05 50
./scripts/navegacion/probar_con_grabacion.sh obstaculos bags/2026-11-12_1016_sala_quieta 0.05 50
```

(argumentos: grabación, altura del sensor sobre el piso —estaba apoyado en el piso: 0,05 m— y
segundos a evaluar). Lanza el modo `obstaculos` (un costmap suelto de 8 × 8 m, sin mapa) y corre
`evaluar_obstaculos.py`, que cada segundo cuenta las celdas ocupadas, nuevas y liberadas, separa el
**fondo** (lo ocupado el 80 % del tiempo o más: paredes, muebles) y mide el **grupo dinámico más
grande** (celdas vecinas ocupadas que no son fondo). Guarda una imagen del costmap cada 10 s.

**Salida obtenida** (2026-11-20, resumida):

```text
persona_caminando:
Grupo dinámico más grande por segundo (celdas):
  33 40 41 33 43 41 40 46 37 36 33 19 33 48 32 33 39 45 33 35 30 37 27 31 34 35 36 37 43 50
  34 35 36 23 42 77 115 116 180 249 291 346 412 421 436 464 444 494 501 482 479
  mediana 40, máximo 501
sala_quieta (control: el mismo lugar, sin nadie moviéndose):
  10 15 10 18 13 10 10 11 12 20 9 22 19 16 16 18 16 12 13 15 17 14 16 15 15 20 24 22 18 28
  17 32 38 27 29 26 21 30 27 35 45 33 27 25 40 38 48 41 36 37 42
  mediana 20, máximo 48
```

### 2.1 Qué dicen estos números

- **Primeros 35 s:** con la persona, el grupo dinámico más grande ronda las 30–50 celdas (≈ 0,1 m²,
  el tamaño de una persona vista desde arriba); en la sala quieta, 10–20 (ruido del sensor en los
  bordes de los muebles). El costmap **ve a la persona**.
- **Después de los 35 s**, con la persona aparece una zona dinámica grande (hasta 500 celdas,
  ≈ 1,25 m²). **A CONFIRMAR** qué pasó en la escena (la descripción de la grabación quedó vacía):
  puede ser una puerta abierta, un objeto movido o la persona quieta cerca del sensor.
- Es una prueba **cualitativa**: no se sabe con exactitud dónde estuvo la persona. La prueba con
  verdad conocida (una caja que aparece y desaparece en un lugar exacto) es la de R05.

## 3. Hacerlo a mano, con RViz

```bash
ros2 launch scripts/navegacion/navegacion.launch.py modo:=obstaculos \
    bag:=bags/2026-11-12_1028_persona_caminando altura_inicial:=0.05
```

RViz abre `config/navegacion/obstaculos.rviz`: el costmap (`/obstaculos/costmap`), la nube del
sensor y los vóxeles marcados (`/obstaculos/voxel_marked_cloud`, cubos rojos). Con el sensor en
vivo, lo mismo sin `bag:=` y con el sensor apoyado y quieto al lanzar: al pasar una mano o una
persona delante del sensor, aparecen celdas negras que se borran cuando se va.

## Verificación final

- [ ] `probar_con_grabacion.sh obstaculos` termina con "Errores en el launch.log: ninguno" y genera
      imágenes en `resultados/<fecha>_obstaculos_<grabación>/costmap/`.
- [ ] Con la persona, el grupo dinámico más grande es mayor que en la sala quieta.
- [ ] En RViz, un obstáculo nuevo aparece y desaparece al sacarlo (con el sensor en vivo, A VERIFICAR).

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| Lo que pasó por delante del sensor queda marcado para siempre | La fuente filtra la nube hasta 1,80 m: los rayos al techo no borran | 1.1: fuente 0–3 m, capa 0,10–1,80 m |
| `Failed to activate costmap because transform from base_footprint to odom did not become available` | El costmap arrancó antes que la odometría | El launch ya espera (`initial_transform_timeout` 60 s; con grabación, los gestores arrancan después de la reproducción) |
| El robot se ve a sí mismo como obstáculo | Faltan o están mal las medidas de la caja del cuerpo | Ajustar `filtro_cuerpo.caja` en el montaje |
| No sale ninguna nube de `filtro_cuerpo.py` (0 mensajes en `/nube_obstaculos`) | Una versión anterior esperaba las transformadas dentro del callback y se colgaba con el reloj de la grabación | Usar la versión actual (no espera: toma la transformada más reciente) |
