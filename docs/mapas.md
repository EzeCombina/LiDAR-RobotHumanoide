# Registro de mapas

Los mapas `.pcd` **no se suben a git** por su tamaño (decenas o cientos de MB). Se generan con
`scripts/procesar_grabacion.sh` en `mapas/`; junto a cada uno queda un `.txt` con el resumen (sí se
sube a git). Se pueden regenerar a partir de la grabación de origen (ver `docs/grabaciones.md`).

| Mapa | Grabación de origen | SLAM | Puntos | Tamaño | Observaciones | Dónde está |
|---|---|---|---|---|---|---|
| `2026-11-12_1051_sala_quieta_pointlio.pcd` | `2026-11-12_1016_sala_quieta` | Point-LIO (`a8e2d0d`) | 1.729.416 | 53 MB | Sensor quieto; ~8 × 6 × 2,85 m; desvío de la trayectoria ≤ 15 cm | `mapas/` en `eze-laptop` |
| `2026-11-12_1049_persona_caminando_pointlio.pcd` | `2026-11-12_1028_persona_caminando` | Point-LIO (`a8e2d0d`) | 1.121.515 | 35 MB | Sensor fijo, persona caminando | `mapas/` en `eze-laptop` |
