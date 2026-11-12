# Registro de mapas

Cada mapa está en su propia carpeta, `mapas/<fecha>_<nombre>/`, generada con
`scripts/mapas/procesar_grabacion.sh`:

| Archivo | Contenido | En git |
|---|---|---|
| `mapa.pcd` | Mapa 3D (decenas o cientos de MB) | No |
| `resumen.txt` | Datos del mapa y de la trayectoria (error de cierre) | Sí |
| `trayectoria.csv` | Posición estimada del sensor cada 0,1 s | Sí |
| `pointlio.log` | Registro de Point-LIO | No |

Los `.pcd` se pueden regenerar a partir de la grabación de origen (ver `docs/grabaciones.md`).
SLAM de todos los mapas: Point-LIO `dfloreaa/point_lio_ros2` commit `a8e2d0d`.

| Carpeta | Grabación de origen | Puntos | Tamaño | Cierre | Inclinación piso/techo | Observaciones | Dónde está |
|---|---|---|---|---|---|---|---|
| `2026-11-12_1413_sala_quieta` | `2026-11-12_1016_sala_quieta` | 1.735.865 | 53 MB | 8,6 cm | 0,7–0,9° | Sensor quieto, horizontal, en el piso; ~8 × 6 × 2,85 m | `mapas/` en `eze-laptop` |
| `2026-11-12_1412_persona_caminando` | `2026-11-12_1028_persona_caminando` | 1.128.052 | 35 MB | 5,2 cm | — | Sensor fijo, persona caminando alrededor | `mapas/` en `eze-laptop` |
| `2026-11-12_1339_departamento_vertical` | `2026-11-12_1333_departamento_vertical` | 2.247.488 | 69 MB | 1,06 m | **13,5–15,4°** | Sensor vertical en la mano, una sola habitación (confirmado). Mapa "bastante bueno" según el usuario, pero **inclinado**: arranque con el sensor en movimiento. Altura entre planos 2,75 m. Pendiente: si se volvió al punto de partida | `mapas/` en `eze-laptop` |
| `2026-11-12_1403_departamento_vertical` | `2026-11-12_1333_departamento_vertical` | 2.247.073 | 69 MB | 0,83 m | — | Segunda corrida de la misma grabación (la hizo el usuario con `--rviz`). El cierre varía entre corridas (0,83 m contra 1,06 m) | `mapas/` en `eze-laptop` |
| `2026-11-12_1445_habitacion_vertical_rapido` | `2026-11-12_1442_habitacion_vertical_rapido` | 1.102.546 | 34 MB | **10,5 cm** | 2,1–2,9° | Arranque apoyado y quieto: confirma que la inclinación anterior se debía al arranque en la mano. Zona recorrida 1,77 × 1,55 × 1,00 m; extensión útil 6,8 × 6,6 × 3,0 m | `mapas/` en `eze-laptop` |

> Los mapas anteriores a la reorganización (`2026-11-12_1049_persona_caminando_pointlio.pcd` y
> `2026-11-12_1051_sala_quieta_pointlio.pcd`, sin trayectoria) se borraron y se reemplazaron por
> las carpetas `1412` y `1413`, generadas de las mismas grabaciones.
