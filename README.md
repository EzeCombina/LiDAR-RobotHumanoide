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
| `docs/grabaciones.md`, `docs/mapas.md` | Registro de grabaciones y mapas, y dónde están guardados |
| `docs/FORMATO_DOCUMENTO.md` | Formato del PDF final |
| `docs/referencias/` | Documentación de referencia del proyecto |
| `docs/pdf/` | Fuente y salida del documento PDF final |
| `scripts/` | Scripts propios, por función: `sistema/`, `red/`, `sensor/` (herramientas C++ del SDK y diagnóstico), `grabacion/`, `mapas/` |
| `config/` | Configuraciones propias o modificadas |
| `mapas/` | Una carpeta por mapa (`mapa.pcd` fuera de git; `resumen.txt` y `trayectoria.csv` en git) |
| `bags/` | Grabaciones (fuera de git) |
| `assets/` | Logo e imágenes |

## Equipo

- Unitree 4D LiDAR L2
- PC con Ubuntu 24.04 + ROS 2 Jazzy
- Robot Unitree R1 EDU (Jetson Orin NX)

## Guía de pasos

| Paso | Documento | Estado |
|---|---|---|
| 00 | [Preparación del entorno](docs/pasos/00_preparacion_entorno.md) | Completo |
| 01 | [Conexión por Ethernet](docs/pasos/01_conexion_ethernet.md) | Completo |
| 02 | Conexión por USB | Pendiente |
| 03 | [Driver ROS 2 y RViz](docs/pasos/03_driver_ros2.md) | Completo (Ethernet) |
| 04 | [Grabación de datos](docs/pasos/04_grabacion.md) | Completo |
| 05 | [SLAM con Point-LIO](docs/pasos/05_slam_pointlio.md) | Completo |
| 06 | [Mapear un lugar: procedimiento completo](docs/pasos/06_mapeo_de_un_lugar.md) | Validado con una habitación (2026-11-12) |

## Uso rápido: de un recorrido a un mapa

Con todo instalado (pasos 00 a 05), desde la carpeta del repositorio:

```bash
# 1. Driver del sensor (dentro de tmux)
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false
# 2. Grabar el recorrido (Ctrl+C al volver al punto de partida)
./scripts/grabacion/grabar_lidar.sh <nombre> "" "<descripción>"
# 3. Detener el driver y generar el mapa 3D
./scripts/mapas/procesar_grabacion.sh bags/<carpeta>
# 4. Ver el mapa en RViz (terminal del escritorio)
./scripts/mapas/ver_mapa.sh mapas/<fecha>_<nombre>
```

Detalle en [docs/pasos/06_mapeo_de_un_lugar.md](docs/pasos/06_mapeo_de_un_lugar.md).

## Estado

En curso. Ver `docs/bitacora.md`.
