# =============================================================================
# simulacion.launch.py — Robot simulado en Gazebo con Nav2 y el LiDAR simulado
# -----------------------------------------------------------------------------
# Qué lanza:
#   1. Gazebo (servidor, sin ventana) con el mundo <mapa>/gazebo/mundo.sdf
#      (generar_mundo_gazebo.py). Con gui:=true abre también la ventana.
#   2. El robot simplificado (config/simulacion/robot_r1_simplificado.sdf) en el
#      punto "inicio" de <mapa>/gazebo/puntos.yaml.
#   3. El puente Gazebo <-> ROS 2 (config/simulacion/puente_gz.yaml): reloj, nube
#      /lidar/points, odometría /odom y /tf, y /cmd_vel hacia el robot.
#   4. La transformada fija base_footprint -> lidar_sim (montaje del sensor:
#      0,20 m adelante, 1,55 m de alto, invertido).
#   5. scripts/navegacion/navegacion.launch.py con fuente:=simulacion: el MISMO
#      Nav2 (AMCL, costmaps con la nube, planificador, controlador,
#      collision_monitor) que se usa con el sensor real.
#
# Argumentos:
#   mapa:=mapas/sala_de_prueba   carpeta del mapa (con mapa_2d.yaml y gazebo/)
#   modo:=navegacion             localizacion | navegacion
#   gui:=false                   abrir la ventana de Gazebo
#   rviz:=true                   abrir RViz
#
# Requisitos: paso R02 (Nav2, ros_gz, pointcloud_to_laserscan) y el mundo generado:
#   ./scripts/simulacion/crear_sala_de_prueba.py
#   ./scripts/simulacion/generar_mundo_gazebo.py mapas/sala_de_prueba
#
# Cómo se usa:
#   ros2 launch scripts/simulacion/simulacion.launch.py
#   ros2 launch scripts/simulacion/simulacion.launch.py gui:=true
#   ros2 launch scripts/simulacion/simulacion.launch.py rviz:=false    # por SSH
#   Después: en RViz, "Nav2 Goal" para mandar al robot a un punto, o la prueba
#   automática: ./scripts/simulacion/probar_navegacion_sim.py
# =============================================================================
import os

import yaml
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription,
                            OpaqueFunction, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
ROBOT = os.path.join(REPO, "config", "simulacion", "robot_r1_simplificado.sdf")
PUENTE = os.path.join(REPO, "config", "simulacion", "puente_gz.yaml")
# Montaje del LiDAR en el robot simulado (igual que en robot_r1_simplificado.sdf)
LIDAR_XYZ_RPY = ["0.20", "0.0", "1.55", "3.14159265", "0.0", "0.0"]


def crear(context):
    c = context.launch_configurations
    mapa = c["mapa"] if os.path.isabs(c["mapa"]) else os.path.join(REPO, c["mapa"])
    mundo = os.path.join(mapa, "gazebo", "mundo.sdf")
    archivo_puntos = os.path.join(mapa, "gazebo", "puntos.yaml")
    for f in (mundo, archivo_puntos):
        if not os.path.isfile(f):
            raise RuntimeError(f"no existe {f}: correr scripts/simulacion/generar_mundo_gazebo.py {c['mapa']}")
    inicio = yaml.safe_load(open(archivo_puntos))["inicio"]
    st = {"use_sim_time": True}

    acciones = [
        # Servidor de Gazebo sin ventana (-s); el LiDAR necesita renderizar: --headless-rendering
        ExecuteProcess(cmd=["gz", "sim", "-r", "-s", "--headless-rendering", mundo], output="screen"),
        Node(package="ros_gz_bridge", executable="parameter_bridge", name="puente_gz", output="screen",
             parameters=[{"config_file": PUENTE, "use_sim_time": True}]),
        Node(package="tf2_ros", executable="static_transform_publisher", name="montaje_lidar_sim",
             arguments=["--x", LIDAR_XYZ_RPY[0], "--y", LIDAR_XYZ_RPY[1], "--z", LIDAR_XYZ_RPY[2],
                        "--roll", LIDAR_XYZ_RPY[3], "--pitch", LIDAR_XYZ_RPY[4], "--yaw", LIDAR_XYZ_RPY[5],
                        "--frame-id", "base_footprint", "--child-frame-id", "lidar_sim"],
             parameters=[st]),
        # Robot en el punto de inicio (espera a que arranque Gazebo)
        TimerAction(period=4.0, actions=[Node(
            package="ros_gz_sim", executable="create", output="screen",
            arguments=["-world", "gemelo", "-file", ROBOT, "-name", "r1",
                       "-x", str(inicio["x"]), "-y", str(inicio["y"]), "-z", "0.0",
                       "-Y", str(inicio["yaw"])])]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(REPO, "scripts", "navegacion", "navegacion.launch.py")),
            launch_arguments={"modo": c["modo"], "fuente": "simulacion", "mapa": mapa, "montaje": "robot",
                              "inicio": f"{inicio['x']},{inicio['y']},{inicio['yaw']}",
                              "rviz": c["rviz"]}.items()),
    ]
    if c["gui"] == "true":
        acciones.append(ExecuteProcess(cmd=["gz", "sim", "-g"], output="log"))
    print(f"[simulacion.launch] mundo={mundo} inicio=({inicio['x']}, {inicio['y']}, {inicio['yaw']})")
    return acciones


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("mapa", default_value="mapas/sala_de_prueba"),
        DeclareLaunchArgument("modo", default_value="navegacion"),
        DeclareLaunchArgument("gui", default_value="false"),
        DeclareLaunchArgument("rviz", default_value="true"),
        OpaqueFunction(function=crear),
    ])
