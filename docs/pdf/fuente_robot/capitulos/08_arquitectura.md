# 8. Cómo funciona: piezas y flujo de datos

```text
 L2 (driver) ─► nube + IMU ─► Point-LIO ─► odometría ─► base_nivelada.py ─► odom → base_footprint
                                  │
                                  └─► nube del sensor ─► filtro_cuerpo.py ─► /nube_obstaculos
                                                                                   │
        ┌──────────────────────────────────────────┬───────────────────────────────┤
        ▼                                          ▼                               ▼
 pointcloud_to_laserscan ─► barrido 2D      costmaps de Nav2               monitor de colisiones
        │                                   (obstáculos en vivo)           (freno de seguridad)
        ▼                                          │                               ▲
 mapa 2D ─► AMCL ─► map → odom          planificador + controlador ─► velocidades ─┘
 (OBJETIVO 1)                           (OBJETIVO 2)                               │
                                                                                   ▼
                                                     puente_cmd_vel_r1.py ─► marcha del R1
```

- **Objetivo 1** (izquierda): AMCL compara el barrido 2D con el mapa guardado y corrige la deriva
  de la odometría. Así el robot sabe dónde está en el mapa.
- **Objetivo 2** (derecha): la nube en vivo entra a los costmaps (lo nuevo se marca y el
  planificador lo rodea) y al monitor de colisiones (frena si algo se cruza, aunque falle el resto).
- En la **simulación**, Gazebo reemplaza al L2, a Point-LIO y a `base_nivelada.py`; todo lo demás
  es igual.

## 8.1 Piezas propias del proyecto

| Pieza | Qué hace |
|---|---|
| `base_nivelada.py` | Convierte la pose del **sensor** (Point-LIO) en la pose del **robot** sobre el piso, sin inclinación (`base_footprint`), usando el montaje del sensor. También deja el piso en z = 0 en el marco `odom` |
| `filtro_cuerpo.py` | Quita de la nube los puntos que caen dentro de la caja del propio robot (o de la persona que lleva el sensor). Sin él, el robot se ve a sí mismo como un obstáculo y no se mueve |
| `navegacion.launch.py` | Arranca todo según el modo: `localizacion` (objetivo 1), `navegacion` (1 + 2) u `obstaculos` (2, sin mapa). Con `bag:=<grabación>`, reproduce una grabación en lugar del sensor |
| `nav2_lidar.yaml` | Parámetros de Nav2 (anexo A) |
| `puente_cmd_vel_r1.py` | Velocidades de Nav2 hacia la marcha del R1, con límites y parada automática |

## 8.2 Decisiones y por qué

| Decisión | Motivo |
|---|---|
| Odometría con Point-LIO | El R1 no publica su odometría a ROS; Point-LIO ya funciona con el L2 |
| Localización con AMCL sobre el **mapa 2D** | Viene con Nav2, está muy probado y el mapa 2D ya está verificado. Alternativa futura: localización 3D sobre el `.pcd` |
| Obstáculos con la **nube 3D** (no con un barrido 2D) | Ve mesas y estantes a cualquier altura entre 0,10 y 1,80 m |
| Velocidades bajas: 0,30 m/s y 0,6 rad/s | Robot humanoide y primeras pruebas (**A VERIFICAR** con el R1) |
| Radio del robot 0,26 m, inflado 0,45 m | Del tamaño del modelo simulado; pasa por puertas de 1 m (**A VERIFICAR** con el R1) |

!!! importante "Tres ajustes que encontraron las pruebas"
    1. Ruido de odometría de AMCL en 0,05 (Nav2 trae 0,2, pensado para ruedas que patinan): el
       error medio bajó de 0,26 a 0,12 m (capítulo 9).
    2. La nube que usan los costmaps acepta puntos de 0 a 3 m para **borrar** y marca solo de 0,10 a
       1,80 m; si no, lo que pasa por delante del sensor queda marcado para siempre (capítulo 10).
    3. El monitor de colisiones **frena** al 40 % delante del robot en lugar de detenerlo: una zona
       de parada fija también impide girar, y el robot queda trabado mirando una pared (capítulo 11).
