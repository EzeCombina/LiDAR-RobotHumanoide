# Paso R02 — Instalación: Nav2, Gazebo y archivos del proyecto

## Objetivo

Dejar instalado, en una PC con Ubuntu 24.04 + ROS 2 Jazzy, todo lo que usan los pasos R03 a R06:
Nav2 (navegación), `pointcloud_to_laserscan`, Gazebo Harmonic (simulación) y su puente con ROS 2.

## Requisitos

- La primera etapa completa: pasos 00 a 07 (`docs/pasos/`). En particular, Point-LIO compilado en
  `~/lidar_ws/point_lio_ws` (paso 05) y al menos un mapa con `mapa_2d.yaml` y
  `trayectoria_limpia.csv` (paso 07).
- Conexión a internet.
- Unos 1,5 GB libres en disco para los paquetes.

## 1. Paquetes

```bash
sudo apt update
sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
    ros-jazzy-pointcloud-to-laserscan \
    ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
    python3-matplotlib python3-scipy python3-pil
```

| Paquete | Para qué |
|---|---|
| `ros-jazzy-navigation2` | Nav2 completo: AMCL (localización), costmaps, planificador NavFn, controlador MPPI, `collision_monitor`, comportamientos de recuperación, `nav2_simple_commander` |
| `ros-jazzy-nav2-bringup` | El archivo de parámetros de referencia (`nav2_params.yaml`) del que sale `config/navegacion/nav2_lidar.yaml` |
| `ros-jazzy-pointcloud-to-laserscan` | Convierte la nube 3D en un barrido 2D para AMCL |
| `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-bridge` | Gazebo Harmonic (lo instalan como dependencia) y el puente de tópicos con ROS 2 |
| `python3-matplotlib` | La figura de la prueba automática en simulación |

Versiones de referencia: `docs/versiones.md`, sección "Etapa del robot".

!!! nota "En la PC del laboratorio"
    Nav2 y Gazebo ya estaban instalados; el 2026-11-20 solo se instaló
    `ros-jazzy-pointcloud-to-laserscan` (2.0.2-3noble.20261105.112224).

## 2. Verificación de la instalación

```bash
source /opt/ros/jazzy/setup.bash
for p in nav2_amcl pointcloud_to_laserscan ros_gz_sim ros_gz_bridge nav2_mppi_controller; do
    echo "$p: $(ros2 pkg prefix $p)"
done
gz sim --version
python3 -c "import nav2_simple_commander, matplotlib, scipy; print('python ok')"
```

**Salida esperada:**

```text
nav2_amcl: /opt/ros/jazzy
pointcloud_to_laserscan: /opt/ros/jazzy
ros_gz_sim: /opt/ros/jazzy
ros_gz_bridge: /opt/ros/jazzy
nav2_mppi_controller: /opt/ros/jazzy
Gazebo Sim, version 8.15.0
python ok
```

Si falta un paquete, `ros2 pkg prefix` responde `Package not found` (salida obtenida el 2026-11-20).

## 3. Archivos del proyecto que se usan

No hay que compilar nada nuevo: los nodos propios son scripts de Python y los lanzamientos se
ejecutan con `ros2 launch <archivo>`.

| Archivo | Qué es |
|---|---|
| `scripts/navegacion/navegacion.launch.py` | Lanzamiento principal (modos `localizacion`, `navegacion`, `obstaculos`) |
| `scripts/navegacion/base_nivelada.py` | Odometría del robot desde Point-LIO (R00, sección 2) |
| `scripts/navegacion/filtro_cuerpo.py` | Quita de la nube los puntos del propio robot |
| `scripts/navegacion/probar_con_grabacion.sh` | Prueba de los objetivos 1 y 2 con una grabación |
| `scripts/navegacion/evaluar_localizacion.py`, `evaluar_obstaculos.py` | Evaluadores de esas pruebas |
| `scripts/navegacion/puente_cmd_vel_r1.py` | Puente hacia la marcha del R1 (R06) |
| `config/navegacion/nav2_lidar.yaml` | Parámetros de Nav2 (encabezado: original y cambios) |
| `config/navegacion/montaje_mano.yaml`, `montaje_robot.yaml` | Montaje del sensor y caja del cuerpo |
| `config/navegacion/navegacion.rviz`, `obstaculos.rviz` | Vistas de RViz |
| `scripts/simulacion/*`, `config/simulacion/*` | Simulación (R05) |

## 4. Entorno de cada terminal

Cada terminal que lance algo de esta etapa necesita:

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/point_lio_ws/install/setup.bash      # Point-LIO (no hace falta en la simulación)
cd ~/Documentos/LiDAR-RobotHumanoide
```

## Verificación final

- [ ] `ros2 pkg prefix` encuentra los cinco paquetes de la sección 2.
- [ ] `gz sim --version` responde 8.x (Harmonic).
- [ ] `ros2 launch scripts/navegacion/navegacion.launch.py --show-args` lista los argumentos.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `Package 'pointcloud_to_laserscan' not found` al lanzar | Falta el paquete | Sección 1 |
| `Package 'point_lio' not found` | No se cargó el entorno de Point-LIO | `source ~/lidar_ws/point_lio_ws/install/setup.bash` |
| `sudo` pide contraseña y no se puede escribir (sesión sin terminal) | Asistente o script sin terminal interactiva | Ejecutar el `apt install` a mano en una terminal |
