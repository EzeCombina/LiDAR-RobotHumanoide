# Anexo A. Parámetros principales

Todos en `config/navegacion/nav2_lidar.yaml` (salvo los indicados). Los marcados **ROBOT** dependen
del R1 real y se ajustan al probarlo.

## A.1 Localización (AMCL)

| Parámetro | Valor | Original de Nav2 | Motivo |
|---|---|---|---|
| `alpha1` a `alpha5` | 0,05 | 0,2 | Point-LIO es mucho más exacta que una odometría de ruedas |
| `robot_model_type` | `OmniMotionModel` | `DifferentialMotionModel` | El R1 puede caminar de costado |
| `min_particles` / `max_particles` | 600 / 3000 | 500 / 2000 | Más partículas para corregir una pose inicial mala |
| `update_min_d` / `update_min_a` | 0,10 m / 0,15 rad | 0,25 m / 0,2 rad | Actualiza más seguido (robot lento) |
| `laser_max_range` / `laser_min_range` | 20 m / 0,3 m | 100 m / sin mínimo | Rango útil del L2 en interiores |

## A.2 Barrido para AMCL (`pointcloud_to_laserscan`, en el launch)

| Parámetro | Valor |
|---|---|
| Marco | `base_footprint` (sin inclinación) |
| Alturas | 0,10 a 1,80 m (como el mapa 2D) |
| Resolución angular | 0,5° en 360° |
| Rango | 0,3 a 30 m |

## A.3 Obstáculos (costmaps y monitor de colisiones)

| Parámetro | Valor | Motivo |
|---|---|---|
| Fuente | `/nube_obstaculos`, tipo `PointCloud2` | Nube 3D sin el cuerpo |
| Alturas de la fuente | 0 a 3 m | Los rayos al techo borran |
| Alturas que se marcan (capa) | 0,10 a 1,80 m | Como el mapa 2D |
| Vóxeles (costmap local) | 16 × 0,125 m | 2 m de alto |
| Alcance para marcar / borrar | 5 m / 6 m | |
| `robot_radius` | 0,26 m **ROBOT** | Modelo simulado de 0,25 × 0,40 m |
| `inflation_radius` / `cost_scaling_factor` | 0,45 m / 4,0 | Pasa por puertas de 1 m |
| Zona lenta del monitor | 0,30–0,55 m delante, ±0,25 m, 40 % **ROBOT** | Frena sin impedir girar |
| Huella proyectada | 1,2 s | Detiene antes de chocar |

## A.4 Movimiento

| Parámetro | Valor |
|---|---|
| Velocidad hacia adelante / atrás / de costado | 0,30 / 0,10 / 0,10 m/s **ROBOT** |
| Giro | 0,60 rad/s **ROBOT** |
| Controlador | MPPI, 10 Hz, horizonte de 4 s (40 pasos de 0,1 s) |
| Planificador | NavFn, sin cruzar zonas desconocidas |
| Tolerancia de llegada | 0,25 m y 0,35 rad |

## A.5 Montaje del sensor (`config/navegacion/montaje_*.yaml`)

| Montaje | Posición en el robot | Orientación | Caja del cuerpo (m) |
|---|---|---|---|
| `mano` | el propio sensor | — | ±0,25 × ±0,25 × −0,05 a 2,00 |
| `robot` | 0,20 m adelante, 1,55 m de alto **ROBOT** | invertido (roll 180°) **ROBOT** | −0,20 a 0,20 × ±0,28 × −0,05 a 1,70 **ROBOT** |
