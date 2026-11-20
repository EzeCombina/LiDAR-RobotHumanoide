# =============================================================================
# navegacion.launch.py — Localización, navegación y obstáculos con el LiDAR L2
# -----------------------------------------------------------------------------
# Qué lanza, según el modo:
#
#   modo:=localizacion   (OBJETIVO 1: reconocer un mapa ya hecho)
#       Point-LIO (odometría) + base_nivelada + pointcloud_to_laserscan
#       + map_server (el mapa 2D) + AMCL (ubica al robot en el mapa).
#   modo:=navegacion     (OBJETIVO 1 + 2: moverse solo por el mapa esquivando)
#       lo anterior + Nav2: planificador, controlador, costmaps con la nube en
#       vivo, comportamientos de recuperación, suavizador de velocidad y
#       collision_monitor. Sale /cmd_vel (velocidades para el robot).
#   modo:=obstaculos     (OBJETIVO 2 sin mapa: ver qué obstáculos detecta)
#       Point-LIO + base_nivelada + un costmap suelto con la nube en vivo.
#
#   fuente:=lidar        datos del L2 (en vivo, o de una grabación con bag:=...)
#   fuente:=simulacion   datos de Gazebo (lo usa scripts/simulacion/simulacion.launch.py):
#                        no lanza Point-LIO ni base_nivelada (Gazebo da la odometría).
#
# Argumentos:
#   mapa:=<carpeta del mapa>   con mapa_2d.yaml (paso 07). Obligatorio salvo en "obstaculos".
#   bag:=<carpeta>             reproduce una grabación en lugar del sensor en vivo
#                              (con --clock: todo usa el tiempo de la grabación).
#   tasa:=1.0                  velocidad de reproducción de la grabación.
#   espera_bag:=6.0            segundos de espera antes de reproducir (arranque de los nodos).
#   montaje:=mano|robot        config/navegacion/montaje_<montaje>.yaml (cómo va el sensor).
#   altura_inicial:=<m>        altura del sensor sobre el piso al arrancar. Por defecto:
#                              robot -> la del montaje; mano con inicio:=mapa -> la del mapa.
#   inicio:=mapa | x,y,yaw     pose inicial para AMCL. "mapa": el punto de partida de la
#                              grabación con la que se hizo el mapa (transformacion.txt).
#   nube:=<tópico>             nube del sensor (por defecto /cloud_registered_body, o
#                              /lidar/points con fuente:=simulacion). filtro_cuerpo.py le
#                              quita los puntos del robot y publica /nube_obstaculos, que
#                              es la que usan AMCL (barrido), los costmaps y el collision_monitor.
#   rviz:=true|false           abrir RViz con config/navegacion/navegacion.rviz.
#
# Ejemplos:
#   # Objetivo 1 con una grabación (sin sensor):
#   ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
#       mapa:=mapas/2026-11-12_1445_habitacion_vertical_rapido \
#       bag:=bags/2026-11-12_1442_habitacion_vertical_rapido
#   # Objetivo 2 con una grabación (persona caminando):
#   ros2 launch scripts/navegacion/navegacion.launch.py modo:=obstaculos \
#       bag:=bags/2026-11-12_1028_persona_caminando altura_inicial:=0.0
#   # Con el sensor en vivo (driver corriendo, sensor APOYADO Y QUIETO al lanzar):
#   ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
#       mapa:=mapas/<carpeta> inicio:=0.0,0.0,0.0 altura_inicial:=0.85
#
# Requisitos: paso R02 (Nav2, pointcloud_to_laserscan) y Point-LIO compilado en
#   ~/lidar_ws/point_lio_ws (otra ubicación: variable POINT_LIO_WS). Hacer source de
#   /opt/ros/jazzy/setup.bash y de ~/lidar_ws/point_lio_ws/install/setup.bash.
# =============================================================================
import math
import os
import tempfile

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch_ros.actions import Node

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
CONFIG = os.path.join(REPO, "config", "navegacion")

NODOS_NAVEGACION = ["controller_server", "planner_server", "behavior_server",
                    "velocity_smoother", "collision_monitor", "bt_navigator"]


def ruta(texto):
    """Rutas relativas a la carpeta del repositorio (o absolutas)."""
    texto = os.path.expanduser(texto)
    return texto if os.path.isabs(texto) else os.path.join(REPO, texto)


def pose_de_partida_del_mapa(carpeta):
    """(x, y, yaw, altura) del punto de partida de la grabación del mapa, en el marco
    del mapa limpio. Sale de transformacion.txt (limpiar_mapa.py): el origen de
    Point-LIO (0, 0, 0) llevado al mapa limpio."""
    archivo = os.path.join(carpeta, "transformacion.txt")
    if not os.path.isfile(archivo):
        raise RuntimeError(f"no existe {archivo}: indicar inicio:=x,y,yaw y altura_inicial:=...")
    filas = [list(map(float, l.split())) for l in open(archivo) if l.strip() and not l.startswith("#")]
    return filas[0][3], filas[1][3], math.atan2(filas[1][0], filas[0][0]), filas[2][3]


def poner_parametro(datos, clave, valor):
    """Pone clave=valor en todos los bloques ros__parameters (recursivo)."""
    if isinstance(datos, dict):
        if "ros__parameters" in datos:
            datos["ros__parameters"][clave] = valor
        for v in datos.values():
            poner_parametro(v, clave, valor)


def cambiar_topico_nube(datos, topico):
    """Reemplaza el tópico de todas las fuentes de obstáculos llamadas "nube"."""
    if isinstance(datos, dict):
        for k, v in datos.items():
            if k == "nube" and isinstance(v, dict) and "topic" in v:
                v["topic"] = topico
            else:
                cambiar_topico_nube(v, topico)


def crear(context):
    a = {n: context.launch_configurations[n] for n in (
        "modo", "fuente", "mapa", "bag", "tasa", "espera_bag", "montaje",
        "altura_inicial", "inicio", "nube", "rviz")}
    modo, fuente = a["modo"], a["fuente"]
    if modo not in ("localizacion", "navegacion", "obstaculos"):
        raise RuntimeError("modo debe ser localizacion, navegacion u obstaculos")
    if fuente not in ("lidar", "simulacion"):
        raise RuntimeError("fuente debe ser lidar o simulacion")
    bag = ruta(a["bag"]) if a["bag"] else ""
    sim_time = bool(bag) or fuente == "simulacion"
    nube = a["nube"] or ("/lidar/points" if fuente == "simulacion" else "/cloud_registered_body")
    carpeta_mapa = ruta(a["mapa"]) if a["mapa"] else ""
    if modo != "obstaculos" and not os.path.isfile(os.path.join(carpeta_mapa, "mapa_2d.yaml")):
        raise RuntimeError(f"no existe {carpeta_mapa}/mapa_2d.yaml (argumento mapa:=<carpeta>)")

    # --- Montaje del sensor, altura inicial y pose inicial -------------------
    montaje = yaml.safe_load(open(os.path.join(CONFIG, f"montaje_{a['montaje']}.yaml")))
    p_montaje = montaje["base_nivelada"]["ros__parameters"]
    if a["inicio"] == "mapa":
        if modo == "obstaculos":
            x0 = y0 = yaw0 = 0.0
            h_mapa = None
        else:
            x0, y0, yaw0, h_mapa = pose_de_partida_del_mapa(carpeta_mapa)
    else:
        x0, y0, yaw0 = [float(v) for v in a["inicio"].split(",")]
        h_mapa = None
    if fuente == "simulacion":
        altura = 0.0   # Gazebo publica la odometría sobre el piso: no se usa
    elif a["altura_inicial"]:
        altura = float(a["altura_inicial"])
    elif a["montaje"] == "robot":
        altura = float(p_montaje["montaje_xyz"][2])
    elif h_mapa is not None:
        altura = h_mapa
    else:
        raise RuntimeError("indicar altura_inicial:=<m> (altura del sensor sobre el piso al arrancar)")

    # --- Parámetros de Nav2 (copia con los valores de esta corrida) ----------
    params = yaml.safe_load(open(os.path.join(CONFIG, "nav2_lidar.yaml")))
    poner_parametro(params, "use_sim_time", sim_time)
    cambiar_topico_nube(params, "/nube_obstaculos")   # la nube sin el cuerpo del robot
    params["amcl"]["ros__parameters"]["initial_pose"] = {"x": x0, "y": y0, "z": 0.0, "yaw": yaw0}
    if carpeta_mapa and modo != "obstaculos":
        params["map_server"]["ros__parameters"]["yaml_filename"] = os.path.join(carpeta_mapa, "mapa_2d.yaml")
    archivo_params = os.path.join(tempfile.mkdtemp(prefix="nav2_lidar_"), "nav2_lidar.yaml")
    with open(archivo_params, "w") as f:
        yaml.safe_dump(params, f)

    acciones = []
    st = {"use_sim_time": sim_time}
    # Con una grabación, los gestores de ciclo de vida se activan cuando la
    # reproducción ya empezó y Point-LIO publica la odometría (si no, los
    # costmaps no encuentran las transformadas y no se activan).
    demora_gestores = float(a["espera_bag"]) + 5.0 if bag else 0.0

    def gestor(nombre, nodos):
        nodo = Node(package="nav2_lifecycle_manager", executable="lifecycle_manager", name=nombre,
                    output="screen", parameters=[st, {"autostart": True, "node_names": nodos,
                                                      # Con grabación (tiempo simulado) el "bond"
                                                      # (latido) llega tarde: se desactiva.
                                                      "bond_timeout": 0.0 if bag else 4.0}])
        return TimerAction(period=demora_gestores, actions=[nodo]) if demora_gestores else nodo

    # --- Odometría con el LiDAR (Point-LIO + base nivelada) -------------------
    if fuente == "lidar":
        acciones.append(Node(
            package="point_lio", executable="pointlio_mapping", name="laserMapping", output="screen",
            parameters=[
                os.path.join(os.environ.get("POINT_LIO_WS", os.path.expanduser("~/lidar_ws/point_lio_ws")),
                             "src", "point_lio_ros2", "config", "unilidar_l2.yaml"),
                {   # Igual que mapping_unilidar_l2.launch.py de Point-LIO ...
                    "use_imu_as_input": False, "prop_at_freq_of_imu": True, "check_satu": True,
                    "init_map_size": 10, "point_filter_num": 1, "space_down_sample": True,
                    "filter_size_surf": 0.1, "filter_size_map": 0.1, "cube_side_length": 1000.0,
                    "runtime_pos_log_enable": False,
                    # ... más los cambios para navegar:
                    "odom_header_frame_id": "pointlio_odom",   # marco fijo de Point-LIO
                    "odom_child_frame_id": "body",             # = marco de /cloud_registered_body
                    "publish.scan_bodyframe_pub_en": True,     # nube centrada en el sensor
                    "pcd_save.pcd_save_en": False,             # no sobrescribir PCD/scans.pcd
                    "use_sim_time": sim_time,
                }]))
        acciones.append(ExecuteProcess(
            cmd=["python3", os.path.join(REPO, "scripts", "navegacion", "base_nivelada.py"), "--ros-args",
                 "--params-file", os.path.join(CONFIG, f"montaje_{a['montaje']}.yaml"),
                 "-p", f"altura_inicial:={altura}", "-p", f"use_sim_time:={str(sim_time).lower()}"],
            output="screen"))

    # --- Filtro del cuerpo: quita de la nube los puntos del propio robot -------
    caja = montaje.get("filtro_cuerpo", {}).get("ros__parameters", {}).get("caja")
    acciones.append(ExecuteProcess(
        cmd=["python3", os.path.join(REPO, "scripts", "navegacion", "filtro_cuerpo.py"), "--ros-args",
             "-p", f"entrada:={nube}", "-p", "salida:=/nube_obstaculos",
             "-p", f"use_sim_time:={str(sim_time).lower()}"]
            + (["-p", f"caja:={caja}"] if caja else []),
        output="screen"))

    # --- Barrido 2D nivelado para AMCL -----------------------------------------
    if modo != "obstaculos":
        acciones.append(Node(
            package="pointcloud_to_laserscan", executable="pointcloud_to_laserscan_node",
            name="nube_a_barrido", output="screen",
            remappings=[("cloud_in", "/nube_obstaculos"), ("scan", "/scan")],
            parameters=[{
                "target_frame": "base_footprint",   # nivelado: no cabecea con el robot
                "transform_tolerance": 0.2,
                "min_height": 0.10, "max_height": 1.80,   # misma franja que el mapa 2D
                "angle_min": -math.pi, "angle_max": math.pi, "angle_increment": math.radians(0.5),
                "scan_time": 0.1, "range_min": 0.3, "range_max": 30.0,
                "use_inf": True, "use_sim_time": sim_time,
            }]))

    # --- Localización en el mapa (OBJETIVO 1) --------------------------------
    if modo in ("localizacion", "navegacion"):
        acciones += [
            Node(package="nav2_map_server", executable="map_server", name="map_server",
                 output="screen", parameters=[archivo_params]),
            Node(package="nav2_amcl", executable="amcl", name="amcl", output="screen",
                 parameters=[archivo_params]),
            gestor("lifecycle_manager_localization", ["map_server", "amcl"]),
        ]

    # --- Navegación con obstáculos en vivo (OBJETIVO 2) ----------------------
    if modo == "navegacion":
        acciones += [
            Node(package="nav2_controller", executable="controller_server", output="screen",
                 parameters=[archivo_params], remappings=[("cmd_vel", "cmd_vel_nav")]),
            Node(package="nav2_planner", executable="planner_server", name="planner_server",
                 output="screen", parameters=[archivo_params]),
            Node(package="nav2_behaviors", executable="behavior_server", name="behavior_server",
                 output="screen", parameters=[archivo_params], remappings=[("cmd_vel", "cmd_vel_nav")]),
            Node(package="nav2_velocity_smoother", executable="velocity_smoother", name="velocity_smoother",
                 output="screen", parameters=[archivo_params], remappings=[("cmd_vel", "cmd_vel_nav")]),
            Node(package="nav2_collision_monitor", executable="collision_monitor", name="collision_monitor",
                 output="screen", parameters=[archivo_params]),
            Node(package="nav2_bt_navigator", executable="bt_navigator", name="bt_navigator",
                 output="screen", parameters=[archivo_params]),
            gestor("lifecycle_manager_navigation", NODOS_NAVEGACION),
        ]

    # --- Solo obstáculos, sin mapa (OBJETIVO 2) ------------------------------
    if modo == "obstaculos":
        acciones += [
            Node(package="nav2_costmap_2d", executable="nav2_costmap_2d", name="costmap",
                 namespace="obstaculos", output="screen", parameters=[archivo_params]),
            gestor("lifecycle_manager_costmap", ["obstaculos/costmap"]),
        ]

    # --- RViz y grabación ----------------------------------------------------
    if a["rviz"] == "true":
        acciones.append(Node(
            package="rviz2", executable="rviz2", name="rviz2", output="log",
            arguments=["-d", os.path.join(CONFIG, "obstaculos.rviz" if modo == "obstaculos" else "navegacion.rviz")],
            parameters=[st]))
    if bag:
        acciones.append(TimerAction(period=float(a["espera_bag"]), actions=[ExecuteProcess(
            cmd=["ros2", "bag", "play", bag, "--clock", "-r", a["tasa"]], output="screen")]))

    resumen = (f"[navegacion.launch] modo={modo} fuente={fuente} nube={nube} sim_time={sim_time} "
               f"altura_inicial={altura:.3f} inicio=({x0:.3f}, {y0:.3f}, {math.degrees(yaw0):.1f}°) "
               f"parametros={archivo_params}")
    print(resumen)
    return acciones


def generate_launch_description():
    argumentos = [
        ("modo", "navegacion", "localizacion | navegacion | obstaculos"),
        ("fuente", "lidar", "lidar | simulacion"),
        ("mapa", "", "carpeta del mapa (con mapa_2d.yaml)"),
        ("bag", "", "carpeta de una grabación para reproducir"),
        ("tasa", "1.0", "velocidad de reproducción de la grabación"),
        ("espera_bag", "6.0", "segundos antes de reproducir la grabación"),
        ("montaje", "mano", "mano | robot (config/navegacion/montaje_*.yaml)"),
        ("altura_inicial", "", "altura del sensor sobre el piso al arrancar, en m"),
        ("inicio", "mapa", "pose inicial: mapa | x,y,yaw"),
        ("nube", "", "tópico de la nube de obstáculos"),
        ("rviz", "true", "abrir RViz"),
    ]
    return LaunchDescription(
        [DeclareLaunchArgument(n, default_value=v, description=d) for n, v, d in argumentos]
        + [OpaqueFunction(function=crear)])
