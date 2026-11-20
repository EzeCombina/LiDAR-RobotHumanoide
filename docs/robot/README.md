# Etapa del robot: el L2 en el R1 y la navegación autónoma

Documentación de trabajo de la segunda etapa del proyecto, **separada** de la primera
(`docs/pasos/`, implementación del sensor en Ubuntu y mapas). El PDF de esta etapa se genera desde
`docs/pdf/fuente_robot/`.

## Objetivos de esta etapa

1. **Objetivo 1 — Reconocer un mapa ya hecho y moverse por él.** El robot recibe el mapa de una zona
   (el que produce la guía de la primera etapa), se ubica en él y va de un punto a otro.
2. **Objetivo 2 — Esquivar obstáculos con el LiDAR en tiempo real.** Mientras se mueve solo, usa la
   nube del L2 en vivo para ver lo que no está en el mapa (personas, sillas, cajas) y lo rodea.

Lo previo que habilita los dos: montar el sensor en el robot y conectarlo a su computadora (R01).

## Pasos

| Paso | Archivo | Estado (2026-11-20) |
|---|---|---|
| R00 | [00_arquitectura.md](pasos/00_arquitectura.md) — piezas, marcos de referencia y flujo de datos | Implementado |
| R01 | [01_lidar_en_el_robot.md](pasos/01_lidar_en_el_robot.md) — conexión, alimentación, red y software en la Jetson | Documentado, **pendiente de validar con el robot** |
| R02 | [02_instalacion_navegacion.md](pasos/02_instalacion_navegacion.md) — Nav2, Gazebo y archivos del proyecto | Verificado en la PC |
| R03 | [03_localizacion_en_mapa.md](pasos/03_localizacion_en_mapa.md) — **objetivo 1** con grabaciones reales | Verificado con grabaciones (habitación); falla en la oficina |
| R04 | [04_obstaculos_en_vivo.md](pasos/04_obstaculos_en_vivo.md) — **objetivo 2**: costmap con la nube en vivo | Verificado con grabaciones (cualitativo) y en simulación |
| R05 | [05_simulacion_gazebo.md](pasos/05_simulacion_gazebo.md) — **objetivos 1 y 2 juntos** en Gazebo | Verificado (4 de 4 corridas) |
| R06 | [06_puente_robot.md](pasos/06_puente_robot.md) — velocidades de Nav2 hacia la marcha del R1 | Límites y watchdog verificados; envío al R1 **pendiente** |

## Qué falta para el robot real

- Validar R01 (red, alimentación, software en la Jetson) y diseñar el soporte del sensor.
- Medir el montaje real (CAD) y cargarlo en `config/navegacion/montaje_robot.yaml`.
- Grabar un mapa **con el robot** (el sensor montado ve el piso y los muebles de forma más pareja
  que en la mano).
- Probar el puente R06 con el SDK de Unitree, primero con el robot en su soporte.

## Archivos de esta etapa

| Carpeta | Contenido |
|---|---|
| `scripts/navegacion/` | Nodos y launch de navegación, pruebas con grabaciones, puente al robot |
| `scripts/simulacion/` | Sala de prueba, mundo de Gazebo, launch y prueba automática |
| `config/navegacion/` | Parámetros de Nav2, montajes del sensor, configuraciones de RViz |
| `config/simulacion/` | Robot simplificado (SDF) y puente Gazebo ↔ ROS 2 |
| `mapas/sala_de_prueba/` | Mapa 2D y mundo de Gazebo de la sala de prueba |
| `resultados/` | Resultados de las pruebas (una carpeta por prueba) |
