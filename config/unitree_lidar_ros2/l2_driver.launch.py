# =============================================================================
# l2_driver.launch.py — Lanza el driver ROS 2 del LiDAR Unitree L2
# -----------------------------------------------------------------------------
# Archivo original: unilidar_sdk2/unitree_lidar_ros2/src/unitree_lidar_ros2/launch/launch.py
#                   (repositorio unitreerobotics/unilidar_sdk2, commit 0e3c51f)
#
# Cambios respecto del original:
#   1. Argumento "modo" (ethernet | usb) que fija JUNTOS initialize_type y work_mode.
#      El driver ejecuta setLidarWorkMode(work_mode) al arrancar: con el original,
#      usar initialize_type=1 (serie) dejando work_mode=0 devuelve el sensor a modo
#      Ethernet y se corta la conexión USB.
#        ethernet -> initialize_type 2, work_mode 0
#        usb      -> initialize_type 1, work_mode 8
#   2. Argumentos para las IPs y el puerto serie, sin editar el archivo.
#   3. Argumento "rviz" (true | false) para no abrir RViz al trabajar por SSH.
#   4. Comentarios en español. El resto de los parámetros quedan como el original.
#
# Uso (después de compilar el driver y hacer source de su install/setup.bash):
#   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet
#   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=usb
#   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=usb rviz:=false
#   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet \
#       lidar_ip:=192.168.10.62 local_ip:=192.168.10.2
#
# IMPORTANTE: el modo indicado tiene que coincidir con el modo en el que está el
# sensor (ver scripts/cambiar_modo_lidar). Este launch no cambia de interfaz.
# =============================================================================
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# modo -> (initialize_type, work_mode)
MODOS = {
    'ethernet': (2, 0),
    'usb': (1, 8),
}


def crear_driver(context):
    modo = LaunchConfiguration('modo').perform(context)
    if modo not in MODOS:
        raise RuntimeError(f"modo '{modo}' no válido: usar 'ethernet' o 'usb'")
    initialize_type, work_mode = MODOS[modo]

    driver = Node(
        package='unitree_lidar_ros2',
        executable='unitree_lidar_ros2_node',
        name='unitree_lidar_ros2_node',
        output='screen',
        parameters=[{
            # Interfaz de comunicación (fijada por "modo")
            'initialize_type': initialize_type,
            'work_mode': work_mode,

            # Nube de puntos
            'use_system_timestamp': True,
            'range_min': 0.0,
            'range_max': 100.0,
            'cloud_scan_num': 18,

            # Serie (USB)
            'serial_port': LaunchConfiguration('serial_port').perform(context),
            'baudrate': 4000000,

            # Ethernet (UDP)
            'lidar_port': 6101,
            'lidar_ip': LaunchConfiguration('lidar_ip').perform(context),
            'local_port': 6201,
            'local_ip': LaunchConfiguration('local_ip').perform(context),

            # Tópicos y marcos de referencia
            'cloud_frame': 'unilidar_lidar',
            'cloud_topic': 'unilidar/cloud',
            'imu_frame': 'unilidar_imu',
            'imu_topic': 'unilidar/imu',
        }],
    )
    return [driver]


def generate_launch_description():
    rviz_config = os.path.join(
        get_package_share_directory('unitree_lidar_ros2'), 'view.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('modo', default_value='ethernet',
                              description="Interfaz del sensor: 'ethernet' o 'usb'"),
        DeclareLaunchArgument('lidar_ip', default_value='192.168.1.62',
                              description='IP del sensor (modo ethernet)'),
        DeclareLaunchArgument('local_ip', default_value='192.168.1.2',
                              description='IP de la PC en la placa del LiDAR (modo ethernet)'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyACM0',
                              description='Puerto serie del sensor (modo usb)'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Abrir RViz (false al trabajar por SSH)'),

        OpaqueFunction(function=crear_driver),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='log',
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
