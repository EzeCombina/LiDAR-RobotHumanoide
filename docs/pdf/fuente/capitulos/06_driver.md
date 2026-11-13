# 6. Driver de ROS 2 y visualización

El **driver** es el nodo de ROS 2 que recibe los datos del sensor y los publica en los tópicos
`/unilidar/cloud` (nube) y `/unilidar/imu` (IMU). Viene dentro del SDK de Unitree.

## 6.1 Compilar el driver

```bash
source /opt/ros/jazzy/setup.bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2
rosdep check --from-paths src --ignore-src      # verifica que no falte nada
colcon build
```

```text
All system dependencies have been satisfied
Starting >>> unitree_lidar_ros2
--- stderr: unitree_lidar_ros2
CMake Warning (dev) at /usr/lib/x86_64-linux-gnu/cmake/pcl/Modules/FindFLANN.cmake:45 (find_package):
  Policy CMP0144 is not set: ...
---
Finished <<< unitree_lidar_ros2 [25.5s]
Summary: 1 package finished [25.8s]
```

Los avisos de CMake vienen de la librería PCL y no afectan.

!!! importante "No mover el paquete"
    El driver busca la librería del SDK con una ruta relativa (tres carpetas hacia arriba). Hay que
    compilarlo en su carpeta original, `~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2`, y no moverlo.
    El README de Unitree dice `unilidar_sdk/...`: la carpeta real se llama `unilidar_sdk2`.

## 6.2 Lanzar el driver

El proyecto tiene su propio archivo de lanzamiento, `config/unitree_lidar_ros2/l2_driver.launch.py`,
basado en el de Unitree, con estas mejoras:

- **`modo:=ethernet`** o **`modo:=usb`**: configura juntos los dos parámetros que dependen de la
  conexión (`initialize_type` y `work_mode`).
- **`lidar_ip:=…`, `local_ip:=…`, `serial_port:=…`**: cambiar direcciones sin editar archivos.
- **`rviz:=false`**: no abrir RViz (por ejemplo, al trabajar por SSH).

Como el driver es un proceso que queda corriendo, conviene lanzarlo dentro de **tmux**:

```bash
tmux new -s lidar
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false
```

```text
[INFO] [unitree_lidar_ros2_node-1]: process started with pid [8192]
[unitree_lidar_ros2_node-1] initialize_type_ = 2
[unitree_lidar_ros2_node-1] [UDPHandler] bind udp port success. port 6201.
```

!!! concepto "tmux"
    `tmux` mantiene la terminal "viva" aunque se cierre la ventana o se corte una conexión SSH.
    Salir dejándolo corriendo: **Ctrl+b**, soltar, y después **d**. Volver: `tmux attach -t lidar`.
    Detener el driver: dentro de tmux, **Ctrl+C**. Si se lanzó en otra terminal y no se sabe en
    cuál: `pkill -INT -f l2_driver.launch.py`.

## 6.3 Verificar los tópicos

En otra terminal (con `source /opt/ros/jazzy/setup.bash`):

```bash
ros2 topic list
ros2 topic hz /unilidar/cloud
ros2 topic hz /unilidar/imu
```

| Tópico | Frecuencia medida | Contenido |
|---|---|---|
| `/unilidar/cloud` | **12,0 Hz** (un mensaje cada 83 ms) | Nube `PointCloud2`, marco `unilidar_lidar`, ~4.400 a 5.100 puntos |
| `/unilidar/imu` | **251 Hz** | IMU, marco `unilidar_imu` |
| `/tf` | — | Orientación estimada por la IMU (`unilidar_imu_initial` → `unilidar_imu`) |

Cada punto de la nube tiene los campos `x`, `y`, `z` (metros), `intensity`, `ring` (anillo, de 0 a
17) y `time` (tiempo del punto dentro del barrido, en segundos), que son los que necesita el SLAM.
Se pueden ver con `ros2 topic echo --once /unilidar/cloud --field fields`.

## 6.4 Ver la nube en RViz

RViz es una ventana gráfica: se abre en una **terminal del escritorio**. Con el driver corriendo:

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
rviz2 -d "$(ros2 pkg prefix unitree_lidar_ros2)/share/unitree_lidar_ros2/view.rviz"
```

`ros2 pkg prefix` devuelve dónde quedó instalado el driver, así el comando funciona en cualquier
PC. La configuración de Unitree muestra la nube coloreada por altura en el marco `unilidar_lidar`.

![Primera nube de puntos del L2 en RViz. El sensor apoyado en el piso ve las paredes alrededor y hacia arriba (laboratorio, 12/11/2026)](docs/img/rviz_primera_nube_2026-11-12.png)

!!! importante "RViz y VS Code instalado como snap"
    Si RViz se lanza desde la terminal integrada de **VS Code instalado como snap**, falla con
    `symbol lookup error: /snap/core20/.../libpthread.so.0: undefined symbol: __libc_pthread_init`.
    La terminal de VS Code agrega variables de entorno propias del snap. Solución: abrir RViz desde
    la terminal de Ubuntu.
