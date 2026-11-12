# Registro de mapas

Los mapas `.pcd` **no se suben a git** por su tamaño (decenas o cientos de MB). Se generan con
`scripts/procesar_grabacion.sh` en `mapas/`; junto a cada uno queda un `.txt` con el resumen (sí se
sube a git). Se pueden regenerar a partir de la grabación de origen (ver `docs/grabaciones.md`).

| Mapa | Grabación de origen | SLAM | Puntos | Tamaño | Observaciones | Dónde está |
|---|---|---|---|---|---|---|
| `2026-11-12_1051_sala_quieta_pointlio.pcd` | `2026-11-12_1016_sala_quieta` | Point-LIO (`a8e2d0d`) | 1.729.416 | 53 MB | Sensor quieto; ~8 × 6 × 2,85 m; desvío de la trayectoria ≤ 15 cm | `mapas/` en `eze-laptop` |
| `2026-11-12_1049_persona_caminando_pointlio.pcd` | `2026-11-12_1028_persona_caminando` | Point-LIO (`a8e2d0d`) | 1.121.515 | 35 MB | Sensor fijo, persona caminando | `mapas/` en `eze-laptop` |
| `2026-11-12_1339_departamento_vertical_pointlio.pcd` | `2026-11-12_1333_departamento_vertical` | Point-LIO (`a8e2d0d`) | 2.247.488 | 69 MB | Zona recorrida estimada 1,11 × 0,65 m, largo 12,4 m, **error de cierre 1,06 m**; mapa ~8 × 4,4 m. En evaluación: ¿recorrido corto o el SLAM no siguió el movimiento? | `mapas/` en `eze-laptop` |
