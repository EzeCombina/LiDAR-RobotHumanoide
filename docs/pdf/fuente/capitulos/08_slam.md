# 8. SLAM y generación del mapa 3D

El SLAM **Point-LIO** procesa una grabación y genera el **mapa 3D** del lugar (archivo `.pcd`) y la
**trayectoria** del sensor. No hace falta el sensor conectado.

## 8.1 Descargar y compilar Point-LIO

Se usa la versión para ROS 2 `dfloreaa/point_lio_ros2`, que trae la configuración del L2. Se
compila en un espacio de trabajo propio:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/lidar_ws/point_lio_ws/src && cd ~/lidar_ws/point_lio_ws/src
git clone https://github.com/dfloreaa/point_lio_ros2.git
cd point_lio_ros2 && git checkout a8e2d0d5090af97ead8dd4fac3d37cf3dbb33ff7     # versión probada
cd ~/lidar_ws/point_lio_ws
rosdep check --from-paths src --ignore-src
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

```text
All system dependencies have been satisfied
Starting >>> point_lio
...
Finished <<< point_lio [52.8s]
Summary: 1 package finished [53.0s]
```

Los avisos de CMake (`CMP0144`, `CMP0148`) no afectan.

## 8.2 Configuración para el L2

Se usa la configuración que trae el paquete, sin cambios (`config/unilidar_l2.yaml`). Los
parámetros que más influyen en el uso:

| Parámetro | Valor | Significado |
|---|---|---|
| `lid_topic`, `imu_topic` | `/unilidar/cloud`, `/unilidar/imu` | Tópicos del driver del L2 |
| `blind` | 0,5 m | Descarta puntos a menos de 0,5 m: la mano o el cuerpo de quien lleva el sensor |
| `start_in_aggressive_motion` | false | Hay que **empezar con el sensor quieto** |
| `gravity_align` | true | Alinea el eje Z del mapa con la gravedad medida al empezar, **en cualquier orientación del sensor** |
| `pcd_save_en` | true | Guarda el mapa al cerrar Point-LIO |

!!! importante "Arrancar quieto"
    Point-LIO mide la dirección de la gravedad en los primeros instantes y con eso fija la
    orientación de **todo** el mapa. Si en ese momento el sensor se mueve, el mapa queda
    **inclinado**. En una prueba con el sensor en la mano desde el inicio, el mapa quedó inclinado
    13,5° y el error de cierre fue de 1,06 m. Repitiendo el mismo recorrido con el sensor **apoyado
    y quieto** al empezar, la inclinación bajó a 1,9° y el error de cierre a 10,5 cm.

## 8.3 Generar el mapa de una grabación

Con el driver **detenido**:

```bash
./scripts/mapas/procesar_grabacion.sh bags/<carpeta> [nombre_del_mapa] [--rviz]
```

El script lanza Point-LIO, reproduce la grabación una vez, registra la trayectoria, cierra Point-LIO
(que es cuando guarda el mapa) y deja todo en una carpeta propia. Tarda lo mismo que duró la
grabación. Con `--rviz` se ve cómo se arma el mapa.

```text
Grabación: bags/2026-11-12_1028_persona_caminando
Carpeta del mapa: .../mapas/2026-11-12_1412_persona_caminando

Point-LIO en marcha. Reproduciendo la grabación (tarda lo mismo que duró)...
Reproducción terminada. Deteniendo Point-LIO y guardando el mapa...

Mapa: 2026-11-12_1412_persona_caminando/mapa.pcd
Puntos: 1128052
Tamaño: 35M
Trayectoria: 588 muestras, 59.1 s
Largo del recorrido: 4.45 m
Zona recorrida (x, y, z): 0.06 x 0.11 x 0.02 m
Error de cierre (final vs. inicio): 0.052 m (horizontal 0.052 m, vertical -0.002 m)

Para verlo:    ./scripts/mapas/ver_mapa.sh mapas/2026-11-12_1412_persona_caminando
Para medirlo:  ./scripts/mapas/analizar_mapa.py mapas/2026-11-12_1412_persona_caminando
```

Cada mapa queda en `mapas/<fecha>_<nombre>/`:

| Archivo | Contenido | ¿En git? |
|---|---|---|
| `mapa.pcd` | El mapa 3D | No (pesa decenas de MB) |
| `resumen.txt` | Datos del mapa y de la trayectoria | Sí |
| `trayectoria.csv` | Posición estimada del sensor cada 0,1 s | Sí |
| `pointlio.log` | Registro de Point-LIO | No |

**Indicadores de calidad** del resumen:

- **Zona recorrida:** tiene que parecerse a lo que se caminó. (En el ejemplo, el sensor estaba
  fijo: 6 × 11 cm.)
- **Error de cierre:** distancia entre la posición final y la inicial. Si se terminó en el punto
  de partida, debería ser de pocos centímetros. Con el sensor quieto da 5 a 9 cm.
- **Largo del recorrido:** solo orientativo; incluye el pequeño temblor de la estimación.

## 8.4 Lo mismo, a mano

Con el driver detenido, en tres terminales con el entorno cargado
(`source /opt/ros/jazzy/setup.bash` y `source ~/lidar_ws/point_lio_ws/install/setup.bash`):

1. **Terminal 1**: `ros2 launch point_lio mapping_unilidar_l2.launch.py rviz:=false` y esperar el
   mensaje `... file opened`.
2. **Terminal 2** (opcional): `./scripts/mapas/registrar_trayectoria.py /tmp/trayectoria.csv`.
3. **Terminal 3**: `ros2 bag play bags/<carpeta>`.
4. Al terminar la reproducción: **Ctrl+C en la terminal 2** (muestra el resumen de la trayectoria)
   y después **Ctrl+C en la terminal 1**. Point-LIO guarda el mapa en
   `~/lidar_ws/point_lio_ws/src/point_lio_ros2/PCD/scans.pcd`.
5. Copiar el mapa con un nombre propio, porque la próxima corrida lo **sobrescribe**:

```bash
CARPETA=mapas/$(date +%Y-%m-%d_%H%M)_<nombre>
mkdir -p $CARPETA
cp ~/lidar_ws/point_lio_ws/src/point_lio_ros2/PCD/scans.pcd $CARPETA/mapa.pcd
cp /tmp/trayectoria.csv $CARPETA/trayectoria.csv
```

## 8.5 Ver y medir el mapa

Desde una terminal del escritorio:

```bash
./scripts/mapas/ver_mapa.sh mapas/<carpeta_del_mapa>
```

Muestra el mapa en RViz y el **recorrido** del sensor: línea blanca, con una **esfera verde** en la
partida y una **roja** en la llegada. Que las paredes crucen la grilla en diagonal es normal (los
ejes los fija la dirección del sensor al empezar); lo que no es normal es que el piso no sea
paralelo a la grilla.

Para ver las medidas con números:

```bash
./scripts/mapas/analizar_mapa.py mapas/<carpeta_del_mapa>
```

```text
  eje   mínimo   máximo  |  útil (1 %-99 %)   extensión útil
   x    -3.57     5.68  |   -3.35 a   3.47     6.82 m
...
  Planos principales (muestra de 40000 puntos):
    plano horizontal a z =  1.95 m: inclinación  1.9° (20 % de los puntos)
...
Trayectoria: 720 muestras, 72.5 s
  error de cierre: 0.105 m (horizontal 0.105 m, vertical +0.006 m)
```

La **extensión útil** son las medidas aproximadas del lugar. La **inclinación** de los planos
horizontales (piso y techo) indica si el mapa quedó nivelado: tiene que ser de 1 a 2° como máximo.
Si es mayor, la causa más común es haber arrancado con el sensor en movimiento. El capítulo 10
explica cómo nivelar el mapa.
