# 7. Instalación de la navegación

Para los capítulos 8 a 12, en una PC con Ubuntu 24.04 + ROS 2 Jazzy, con la guía anterior
completa (Point-LIO compilado en `~/lidar_ws/point_lio_ws` y al menos un mapa).

## 7.1 Paquetes

```bash
sudo apt update
sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
    ros-jazzy-pointcloud-to-laserscan \
    ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
    python3-matplotlib python3-scipy python3-pil
```

| Paquete | Para qué |
|---|---|
| `ros-jazzy-navigation2` | Nav2 completo: AMCL, costmaps, planificador, controlador, monitor de colisiones |
| `ros-jazzy-nav2-bringup` | Los parámetros de referencia de los que salen los del proyecto |
| `ros-jazzy-pointcloud-to-laserscan` | Convierte la nube 3D en un barrido 2D para AMCL |
| `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-bridge` | Gazebo Harmonic y el puente de tópicos con ROS 2 |
| `python3-matplotlib` | La figura de la prueba en simulación |

## 7.2 Verificación

```bash
source /opt/ros/jazzy/setup.bash
for p in nav2_amcl pointcloud_to_laserscan ros_gz_sim ros_gz_bridge nav2_mppi_controller; do
    echo "$p: $(ros2 pkg prefix $p)"
done
gz sim --version
```

```text
nav2_amcl: /opt/ros/jazzy
pointcloud_to_laserscan: /opt/ros/jazzy
ros_gz_sim: /opt/ros/jazzy
ros_gz_bridge: /opt/ros/jazzy
nav2_mppi_controller: /opt/ros/jazzy
Gazebo Sim, version 8.15.0
```

## 7.3 Archivos del proyecto

No hay que compilar nada nuevo: los nodos propios son programas de Python y los lanzamientos se
ejecutan con `ros2 launch <archivo>`. Cada terminal necesita:

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/point_lio_ws/install/setup.bash      # Point-LIO (no hace falta en la simulación)
cd ~/Documentos/LiDAR-RobotHumanoide
```

| Archivo | Qué es |
|---|---|
| `scripts/navegacion/navegacion.launch.py` | Lanzamiento principal: modos `localizacion`, `navegacion` y `obstaculos` |
| `config/navegacion/nav2_lidar.yaml` | Parámetros de Nav2; su encabezado dice de qué archivo original sale y qué se cambió |
| `config/navegacion/montaje_mano.yaml`, `montaje_robot.yaml` | Dónde va el sensor y qué caja ocupa el cuerpo |
| `scripts/navegacion/probar_con_grabacion.sh` | Pruebas de los objetivos 1 y 2 con una grabación |
| `scripts/simulacion/simulacion.launch.py`, `probar_navegacion_sim.py` | Simulación y prueba automática |
| `scripts/navegacion/puente_cmd_vel_r1.py` | Puente hacia la marcha del R1 |

Lista completa en el anexo C; versiones en el anexo B.
