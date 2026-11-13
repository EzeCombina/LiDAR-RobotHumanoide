# Anexo A. Parámetros

## A.1 Launch del driver (`config/unitree_lidar_ros2/l2_driver.launch.py`)

| Argumento | Defecto | Significado |
|---|---|---|
| `modo` | `ethernet` | `ethernet` (`initialize_type` 2, `work_mode` 0) o `usb` (`initialize_type` 1, `work_mode` 8) |
| `lidar_ip` | `192.168.1.62` | IP del sensor (modo Ethernet) |
| `local_ip` | `192.168.1.2` | IP de la PC en la placa del sensor |
| `serial_port` | `/dev/ttyACM0` | Puerto serie (modo USB) |
| `rviz` | `true` | Abrir RViz |

Parámetros fijos del driver: `cloud_topic` `unilidar/cloud` (marco `unilidar_lidar`), `imu_topic`
`unilidar/imu` (marco `unilidar_imu`), puertos UDP 6101 → 6201, `baudrate` 4000000,
`cloud_scan_num` 18, `range_min` 0, `range_max` 100 m, `use_system_timestamp` true.

## A.2 Point-LIO (`config/unilidar_l2.yaml` y `mapping_unilidar_l2.launch.py`)

| Parámetro | Valor | Significado |
|---|---|---|
| `lidar_type` / `scan_line` | 5 / 18 | Formato de nube de Unitree, 18 anillos |
| `timestamp_unit` | 0 | Tiempo de cada punto en segundos |
| `blind` | 0,5 m | Distancia mínima de los puntos usados |
| `imu_en` / `acc_norm` | true / 9,81 | Usa la IMU; aceleración en m/s² |
| `start_in_aggressive_motion` | false | Arranque con el sensor quieto |
| `gravity_align` | true | Alinea el mapa con la gravedad inicial |
| `extrinsic_est_en` | false | No estima la posición IMU–LiDAR (usa la de fábrica) |
| `extrinsic_T` | `[0.007698, 0.014655, -0.00667]` | Posición de la IMU respecto de la nube (m) |
| `filter_size_surf` / `filter_size_map` | 0,1 / 0,1 m | Resolución de la nube procesada y del mapa interno |
| `pcd_save_en` / `interval` | true / −1 | Guarda todo el mapa en un único archivo al cerrar |

## A.3 Scripts del proyecto

| Script | Argumentos y opciones |
|---|---|
| `red/configurar_red_lidar.sh` | `<placa> [ip/máscara]` (defecto `192.168.1.2/24`) |
| `red/verificar_udp_lidar.py` | `--ip`, `--puerto` (6201), `--segundos` (5) |
| `sensor/build/estado_lidar` | `udp [segundos] [ip_lidar] [ip_pc]` o `serie [segundos] [puerto]` |
| `sensor/build/cambiar_modo_lidar` | `serie [ip_lidar] [ip_pc]` o `ethernet [puerto]` |
| `sensor/medir_vibracion_imu.py` | `--segundos` (15), `--csv <archivo>`, `--topico` |
| `grabacion/grabar_lidar.sh` | `<nombre> [segundos] ["descripción"]`; variable `BAGS_DIR` |
| `grabacion/revisar_grabacion.py` | `<carpeta_de_la_grabación>` |
| `mapas/procesar_grabacion.sh` | `<carpeta_de_la_grabación> [nombre] [--rviz]`; variable `POINT_LIO_WS` |
| `mapas/ver_mapa.sh` | `<carpeta_del_mapa ó .pcd> [trayectoria.csv]` |
| `mapas/analizar_mapa.py` | `<carpeta_del_mapa ó .pcd> [trayectoria.csv]` |
| `mapas/limpiar_mapa.py` | `--voxel` (0,03), `--vecinos` (10), `--sigma` (2,0), `--referencia piso\|techo`, `--sin-nivelar`, `--sin-alinear`, `--salida` |
| `mapas/generar_mapa_2d.py` | `--resolucion` (0,05), `--altura-min` (0,10), `--altura-max` (1,80), `--piso` (0,05), `--min-puntos` (2), `--cerrar` (2), `--margen` (0,5) |
| `mapas/ver_mapa_2d.sh` | `<carpeta_del_mapa ó mapa_2d.yaml>` |

Las rutas son relativas a `scripts/`. Cada script explica su uso en el encabezado del archivo.
