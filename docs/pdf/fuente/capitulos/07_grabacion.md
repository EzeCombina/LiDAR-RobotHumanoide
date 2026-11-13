# 7. Grabación de datos

Grabar permite generar el mapa **después**, en la PC, sin repetir el recorrido. Así va a trabajar el
robot: graba mientras se lo maneja y el mapa se calcula luego.

## 7.1 Grabar

Con el driver corriendo (capítulo 6), en otra terminal:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/grabacion/grabar_lidar.sh <nombre> [segundos] ["descripción"]
```

- **`<nombre>`:** letras, números y guiones bajos (por ejemplo `laboratorio_vuelta1`).
- **`segundos`:** opcional. Sin duración, graba hasta cortar con **Ctrl+C**. Para dar una
  descripción sin duración, dejar la duración vacía: `""`.
- **`"descripción"`:** opcional; queda guardada junto a la grabación.

Ejemplo:

```bash
./scripts/grabacion/grabar_lidar.sh sala_quieta 90 "Sensor en el piso, nadie se mueve"
```

El script:

1. **Verifica** que lleguen mensajes de la nube y de la IMU y que queden al menos 5 GB libres.
2. **Graba** `/unilidar/cloud` y `/unilidar/imu` en formato MCAP en `bags/<fecha>_<hora>_<nombre>/`.
3. **Vigila** que sigan llegando datos: si pasan más de 1,5 s sin nubes (un cable que se soltó),
   avisa en pantalla con un pitido cada 2 s.
4. **Corta** al cumplirse la duración o con Ctrl+C, cerrando el archivo de forma ordenada.
5. Guarda un `descripcion.txt` y muestra el resumen.

```text
Files:             2026-11-12_1001_prueba_script_0.mcap
Bag size:          28.2 MiB
Storage id:        mcap
Duration:          14.438826328s
Messages:          3792
Topic information: Topic: /unilidar/cloud | Type: sensor_msgs/msg/PointCloud2 | Count: 173 | ...
                   Topic: /unilidar/imu | Type: sensor_msgs/msg/Imu | Count: 3619 | ...
```

Comprobación rápida: 173 nubes / 14,44 s = 12 por segundo, y 3619 IMU / 14,44 s = 250 por segundo:
no se perdieron mensajes.

!!! importante "Terminar bien una grabación"
    Después del Ctrl+C, **esperar a que aparezca el resumen** (`Files:`, `Duration:`, `Messages:`)
    antes de desconectar el sensor. Si se lo desconecta antes, la grabación queda abierta sin datos.
    En ese caso la terminal empieza a pitar con el aviso `NO LLEGAN DATOS DEL LiDAR`.

**Lo mismo, a mano** (sin controles ni aviso):

```bash
ros2 bag record -s mcap -o bags/mi_grabacion --topics /unilidar/cloud /unilidar/imu
```

| Duración | Tamaño aproximado |
|---|---|
| 1 minuto | 117 MB |
| 10 minutos | 1,2 GB |

Las grabaciones **no se suben a git** (la carpeta `bags/` está excluida). Cada grabación útil se
anota en `docs/grabaciones.md`.

## 7.2 Revisar una grabación

```bash
./scripts/grabacion/revisar_grabacion.py bags/<carpeta>
```

Revisa tres cosas:

- **Huecos:** intervalos entre mensajes mayores a 3 veces el normal.
- **Corte al final:** si el sensor dejó de enviar datos antes de que se cortara la grabación.
- **Arranque:** si el sensor estaba **quieto** en los primeros 4 s. Es importante para el SLAM
  (capítulo 8).

Ejemplo real, una grabación completa y con arranque quieto:

```text
/unilidar/cloud
  mensajes: 874 en 72.78 s -> 12.01 por segundo
  intervalo medio: 83.4 ms | máximo: 88.5 ms
  sin huecos
...
Duración de la grabación (descripcion.txt): 74 s | último dato a los 74 s (14:43:58)

Resultado: grabación completa

Arranque (primeros 4 s de IMU, 1005 muestras):
  aceleración media [m/s²]: x=0.07 y=-0.09 z=8.95 (módulo 8.95)
  gravedad sobre el eje z del sensor, a 0.7° de ese eje
  desvío del giróscopo [rad/s]: x=0.051 y=0.040 z=0.050 -> QUIETO (límite 0.1 rad/s)
```

Y una grabación en la que se desconectó el sensor creyendo que ya se había cortado:

```text
Duración de la grabación (descripcion.txt): 271 s | último dato a los 16 s (14:32:48)
  ATENCIÓN: no llegaron datos durante los últimos 255 s. El sensor dejó de enviar datos (¿cable desconectado o sin alimentación?).
Resultado: GRABACIÓN INCOMPLETA: revisar los avisos de arriba
```

## 7.3 Ver una grabación en RViz

No hace falta el sensor, pero **el driver tiene que estar detenido** (si no, se mezclan los datos en
vivo con los grabados).

!!! nota "Ver el lugar más completo"
    Cada nube cubre solo una parte del barrido. En RViz, dentro de *PointCloud2*, subir
    **Decay Time** de 1 a 10: se acumulan los últimos 10 segundos de puntos. Sirve solo con el
    sensor quieto; si se movió, los puntos acumulados quedan corridos. Para eso está el SLAM.

En dos terminales del escritorio:

```bash
# Terminal 1: reproducir (--loop la repite hasta Ctrl+C; --rate 0.5 la hace más lenta)
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 bag play bags/<carpeta> --loop

# Terminal 2: RViz
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
rviz2 -d "$(ros2 pkg prefix unitree_lidar_ros2)/share/unitree_lidar_ros2/view.rviz"
```
