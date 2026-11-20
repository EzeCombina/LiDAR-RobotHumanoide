# 6. Software en la Jetson y grabación con el robot

Todo este capítulo está **pendiente de validar con el robot**.

## 6.1 Primer acceso y relevamiento

Solo comandos de lectura, para saber qué sistema trae la Jetson:

```bash
ssh unitree@192.168.123.164
passwd                                   # cambiar la contraseña de fábrica la primera vez
cat /proc/device-tree/model; echo
cat /etc/nv_tegra_release                # versión de L4T (JetPack)
lsb_release -a
ls /opt/ros                              # ROS instalado
ip -br addr                              # nombre de la interfaz con la .164
df -h ~ ; free -h
docker --version
sudo ufw status                          # firewall
```

Registrar todo en `docs/versiones.md`. Antes de instalar nada, respaldar `~/`, `/etc/netplan`,
`/etc/NetworkManager` y la lista de paquetes (`dpkg --get-selections > paquetes.txt`).

## 6.2 Qué camino seguir

El driver y la grabación necesitan ROS 2. Según el sistema de la Jetson:

| Jetson con | Camino |
|---|---|
| Ubuntu 24.04 | ROS 2 Jazzy nativo, igual que la guía anterior (poco probable) |
| Ubuntu 22.04 | ROS 2 Humble nativo, con los mismos pasos |
| Ubuntu 20.04 (lo más probable) | **Contenedor Docker con Jazzy** (recomendado) o Foxy nativo |

El contenedor deja **las mismas versiones y los mismos scripts** que en la PC y no instala nada en
el sistema de la Jetson. Foxy nativo es la alternativa: el driver del L2 está verificado por Unitree
en 20.04 + Foxy, pero los scripts de grabación del proyecto están hechos para Jazzy.

!!! concepto "¿Qué es un contenedor Docker?"
    Un sistema operativo "dentro" de otro: el contenedor trae su propio Ubuntu 24.04 con Jazzy, pero
    usa el núcleo y la red de la Jetson. Lo que se instala adentro no toca el sistema del robot.

## 6.3 Contenedor con Jazzy

```bash
# En la Jetson (requiere internet; ~1 GB)
docker pull ros:jazzy-ros-base
docker run -d --name lidar --net=host --restart unless-stopped \
    -v ~/LiDAR-RobotHumanoide:/root/LiDAR-RobotHumanoide \
    -v ~/lidar_ws:/root/lidar_ws \
    ros:jazzy-ros-base sleep infinity

# Dentro del contenedor: dependencias y compilación del driver
docker exec -it lidar bash
apt update && apt install -y ros-jazzy-pcl-ros ros-jazzy-pcl-conversions libpcl-dev \
    libeigen3-dev ros-jazzy-rosbag2 ros-jazzy-rosbag2-storage-mcap python3-numpy git tmux
source /opt/ros/jazzy/setup.bash
cd ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2
colcon build
```

- `--net=host`: el contenedor recibe los datos del sensor en la `.164`.
- La compilación usa sola la librería del SDK para `aarch64`.
- El repositorio y el SDK se copian antes desde la PC con `rsync` (la Jetson puede no tener
  internet).

## 6.4 Que los datos no salgan a la red del robot

La nube (unos 2 MB/s) no tiene por qué viajar por la red interna, que también usa la computadora
de movimiento:

```bash
export ROS_DOMAIN_ID=1                          # distinto del dominio 0 de Unitree
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST  # solo procesos de la misma máquina
```

Para ver en vivo desde la PC (RViz), no usar `LOCALHOST` y usar Jazzy en los dos lados: Jazzy y
Foxy no se comunican de forma confiable.

## 6.5 Grabar un mapa con el robot

```bash
# En la Jetson, dentro del contenedor, en tmux
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false \
    lidar_ip:=192.168.123.62 local_ip:=192.168.123.164
# En otra sesión de tmux
BAGS_DIR=~/bags ./scripts/grabacion/grabar_lidar.sh robot_<lugar> "" "Robot con control remoto"
```

El robot camina con su control remoto, en el modo normal de marcha, con el mismo procedimiento de
la guía anterior (quieto al empezar y al terminar, despacio, volver al punto de partida). Después,
en la PC:

```bash
rsync -av --progress unitree@192.168.123.164:~/bags/ ~/Documentos/LiDAR-RobotHumanoide/bags/
./scripts/mapas/procesar_grabacion.sh bags/<carpeta> robot_<lugar>
```

Y los productos del mapa (mapa limpio y mapa 2D) como en la guía anterior. **Un mapa grabado con el
robot es el que mejor va a servir para que el robot se ubique** (capítulo 9).
