# LiDAR-RobotHumanoide

Implementación del **LiDAR Unitree 4D L2** para el robot humanoide **Unitree R1 EDU**: puesta en
marcha del sensor, grabación de datos, SLAM y mapeo de ambientes, con vistas a la navegación autónoma
del robot.

**Proyecto colaborativo con la UTN Facultad Regional San Francisco.**

<img src="assets/logo_utn_frsf.png" alt="UTN Facultad Regional San Francisco" width="320">

## Objetivos

**Corto plazo**
- Documentar cómo implementar el LiDAR en cualquier sistema con Ubuntu.
- Documentar cómo hacerlo en la computadora del robot (NVIDIA Jetson Orin NX).
- Llegar a mapear una habitación moviéndose con el LiDAR y obtener el archivo del mapa.

**Largo plazo**
- Pasar el mapa generado al robot para la navegación.
- Mapa en tiempo real y corrección de rutas.

**Entregable:** un documento PDF con la guía completa desde cero, para el laboratorio de la facultad.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `CLAUDE.md` | Contexto e instrucciones para las sesiones de trabajo con Claude |
| `docs/pasos/` | Un documento por paso de la implementación |
| `docs/bitacora.md` | Registro de cada sesión de trabajo |
| `docs/versiones.md` | Versiones de todo lo instalado o clonado |
| `docs/FORMATO_DOCUMENTO.md` | Formato del PDF final |
| `docs/referencias/` | Documentación de referencia del proyecto |
| `docs/pdf/` | Fuente y salida del documento PDF final |
| `scripts/` | Scripts propios |
| `config/` | Configuraciones propias o modificadas |
| `mapas/` | Mapas livianos de ejemplo (los pesados quedan fuera de git) |
| `bags/` | Grabaciones (fuera de git) |
| `assets/` | Logo e imágenes |

## Equipo

- Unitree 4D LiDAR L2
- PC con Ubuntu 24.04 + ROS 2 Jazzy
- Robot Unitree R1 EDU (Jetson Orin NX)

## Estado

En curso. Ver `docs/bitacora.md`.
