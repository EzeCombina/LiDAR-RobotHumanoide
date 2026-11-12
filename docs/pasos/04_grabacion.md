# Paso 04 — Grabación de datos del LiDAR

## Objetivo

Grabar en un archivo la nube de puntos y la IMU del L2 mientras el sensor está quieto o se mueve.
Las grabaciones permiten:

- generar el mapa **después**, en una PC, sin tener que repetir el recorrido (así va a trabajar el
  robot en la fase 1: graba mientras se lo maneja y el mapa se calcula luego);
- probar distintos parámetros del SLAM sobre los mismos datos;
- guardar registros de referencia del sensor.

## Requisitos

- Paso 03 completo: driver corriendo y publicando `/unilidar/cloud` y `/unilidar/imu`.
- Espacio en disco: unos **120 MB por minuto** de grabación.
- Para grabar caminando: la notebook con el sensor conectado y una forma de alimentarlo (ver
  punto 4.3).

> **¿Qué es un *rosbag*?** Es un archivo donde ROS 2 guarda los mensajes de uno o varios tópicos,
> con su hora exacta. Después se puede "reproducir": ROS 2 vuelve a publicar los mensajes como si el
> sensor estuviera conectado. En Jazzy el formato predeterminado es **MCAP** (extensión `.mcap`).
> Cada grabación es una carpeta con el archivo `.mcap` y un `metadata.yaml` con el resumen.

## 1. Grabar con el script del proyecto

Con el driver corriendo (paso 03), en otra terminal (o en otra ventana de `tmux`):

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/grabacion/grabar_lidar.sh <nombre> [segundos] ["descripción"]
```

Ejemplos:

```bash
./scripts/grabacion/grabar_lidar.sh sala_quieta 90 "Sensor en el piso sobre la almohadilla, nadie se mueve"
./scripts/grabacion/grabar_lidar.sh recorrido_mano            # graba hasta cortar con Ctrl+C
```

El script:

1. Verifica que llegan mensajes en `/unilidar/cloud` y `/unilidar/imu` y que quedan al menos 5 GB
   libres.
2. Graba esos dos tópicos en formato MCAP en `bags/<AAAA-MM-DD_HHMM>_<nombre>/` (carpeta del
   repositorio excluida de git). Para grabar en otro disco: `BAGS_DIR=/ruta ./scripts/grabacion/grabar_lidar.sh ...`.
3. Si se indicó una duración, corta solo; si no, se corta con **Ctrl+C** (también se puede cortar
   antes de tiempo con Ctrl+C). En todos los casos cierra el archivo de forma ordenada. La pausa con
   la barra espaciadora de `ros2 bag record` queda desactivada a propósito.
4. Guarda `descripcion.txt` (nombre, horario, descripción, equipo y commit del proyecto) y muestra
   el resumen.

**Salida obtenida** (prueba de 15 s, 2026-11-12):

```text
Grabando /unilidar/cloud /unilidar/imu
Destino: .../bags/2026-11-12_1001_prueba_script  (38 GB libres)
Duración: 15 s
...
Files:             2026-11-12_1001_prueba_script_0.mcap
Bag size:          28.2 MiB
Storage id:        mcap
ROS Distro:        jazzy
Duration:          14.438826328s
Messages:          3792
Topic information: Topic: /unilidar/cloud | Type: sensor_msgs/msg/PointCloud2 | Count: 173 | Serialization Format: cdr
                   Topic: /unilidar/imu | Type: sensor_msgs/msg/Imu | Count: 3619 | Serialization Format: cdr

Tamaño en disco: 29M
```

**Verificación:** `Count` dividido `Duration` debe dar unos 12 mensajes/s para la nube y unos
250/s para la IMU. En la prueba: 173 / 14,44 = 11,98 y 3619 / 14,44 = 250,6 → no se perdieron
mensajes.

### Comando equivalente, sin el script

```bash
ros2 bag record -s mcap -o bags/mi_grabacion --topics /unilidar/cloud /unilidar/imu
```

> En Jazzy, pasar los tópicos sin `--topics` funciona pero muestra el aviso
> `Positional "topics" argument deprecated`.

### Volumen de datos

| Duración | Tamaño aproximado |
|---|---|
| 1 min | 117 MB |
| 10 min | 1,2 GB |
| 30 min | 3,5 GB |

## 2. Revisar y reproducir una grabación

Los comandos de esta sección sirven para **cualquier grabación y cualquier usuario**. Se asume que
el repositorio está en `~/Documentos/LiDAR-RobotHumanoide` (paso 00) y el SDK en
`~/lidar_ws/unilidar_sdk2` (paso 01); si están en otro lugar, cambiar esas rutas.

### 2.1 Ver qué grabaciones hay y su resumen

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ls bags/                                   # lista las grabaciones
cat bags/<carpeta>/descripcion.txt         # qué es cada una
ros2 bag info bags/<carpeta>               # duración, cantidad de mensajes, tamaño
```

`<carpeta>` es el nombre que aparece en `ls bags/`, por ejemplo `2026-11-12_1016_sala_quieta`.

Para comprobar que la grabación **no tiene huecos** (por ejemplo, por un corte del cable de red
mientras se grababa):

```bash
./scripts/grabacion/revisar_grabacion.py bags/<carpeta>
```

**Salida obtenida** (recorrido del departamento, 2026-11-12):

```text
Grabación: bags/2026-11-12_1333_departamento_vertical (formato mcap)

/unilidar/cloud
  mensajes: 1621 en 135.04 s -> 12.00 por segundo
  intervalo medio: 83.4 ms | máximo: 84.5 ms
  sin huecos

/unilidar/imu
  mensajes: 33884 en 135.10 s -> 250.81 por segundo
  intervalo medio: 4.0 ms | máximo: 9.8 ms
  sin huecos

Resultado: grabación completa
```

Al final, el script revisa el **arranque**: si el sensor estaba quieto en los primeros 4 s, que es
cuando Point-LIO mide la gravedad para nivelar el mapa. Ejemplo real de una grabación que arrancó
con el sensor en la mano:

```text
Arranque (primeros 4 s de IMU, 1001 muestras):
  aceleración media [m/s²]: x=9.08 y=-2.91 z=1.53 (módulo 9.66)
  gravedad sobre el eje x del sensor, a 19.9° de ese eje
  desvío del giróscopo [rad/s]: x=0.242 y=0.305 z=0.139 -> EN MOVIMIENTO (límite 0.1 rad/s)
  ATENCIÓN: el sensor se movía al empezar. El mapa puede quedar inclinado;
  conviene repetir la grabación arrancando con el sensor apoyado y quieto.
```

Con el sensor apoyado (`sala_quieta`) da `0.087 / 0.081 / 0.006 rad/s -> QUIETO`.

Se considera hueco un intervalo mayor a 3 veces el normal. Si aparecen huecos, conviene repetir la
grabación: el SLAM puede perderse en esos momentos.

### 2.2 Verla en RViz

1. **Detener el driver** si está corriendo (Ctrl+C en su terminal, o `tmux attach -t lidar` y
   Ctrl+C). Si no, se mezclan los datos en vivo con los grabados. Para ver una grabación **no hace
   falta tener el sensor conectado**.
2. Abrir **dos terminales del escritorio de Ubuntu** (no la terminal integrada de VS Code, ver el
   paso 03, problemas frecuentes).

**Terminal 1 — reproducir la grabación:**

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 bag play bags/<carpeta> --loop
```

`--loop` repite la grabación en bucle hasta cortarla con **Ctrl+C**. Sin `--loop`, se reproduce una
sola vez. Para reproducir más lento o más rápido: `--rate 0.5` (mitad de velocidad) o `--rate 2`.

**Terminal 2 — RViz:**

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
rviz2 -d "$(ros2 pkg prefix unitree_lidar_ros2)/share/unitree_lidar_ros2/view.rviz"
```

`ros2 pkg prefix unitree_lidar_ros2` devuelve la carpeta donde quedó instalado el driver, así el
comando funciona en cualquier PC sin escribir la ruta completa. Se usa la misma configuración de
RViz del driver (paso 03): marco fijo `unilidar_lidar` y nube de `/unilidar/cloud`.

**Resultado esperado:** se ve la nube igual que en vivo. En `sala_quieta`, la nube no se mueve.

> **Ver la habitación más completa:** cada mensaje de la nube cubre solo una parte del barrido. En el
> panel *Displays* de RViz, dentro de *PointCloud2*, subir **Decay Time** de `1` a `10`: RViz
> acumula los últimos 10 segundos de puntos y la habitación se ve mucho más densa. Esto sirve
> **solo con el sensor quieto**; si se movió, los puntos acumulados quedan "corridos" (para eso está
> el SLAM, etapa siguiente).

3. Al terminar, Ctrl+C en ambas terminales. Para volver a usar el sensor en vivo, relanzar el driver
   (paso 03).

## 3. Registro de las grabaciones

Las grabaciones no se suben a git. Cada grabación útil se anota en `docs/grabaciones.md` con su
nombre, fecha, duración, tamaño, descripción y dónde está guardada.

## 4. Grabaciones de referencia

Antes de mapear una habitación conviene tener tres grabaciones cortas para probar el SLAM y conocer
el comportamiento del sensor:

| # | Nombre | Duración | Cómo se hace | Para qué sirve |
|---|---|---|---|---|
| 1 | `sala_quieta` | 90 s | Sensor en el piso sobre su almohadilla. Nadie se mueve en el lugar | Ruido del sensor en reposo; el SLAM no debe "moverse" |
| 2 | `persona_caminando` | 60 s | Sensor fijo; una persona camina alrededor, a 1–3 m | Cómo afectan los objetos en movimiento |
| 3 | `recorrido_mano` | 1–3 min | Sensor en la mano, recorriendo el lugar (punto 4.2) | Primera prueba real de SLAM |

### 4.1 Antes de grabar

- Dejar el sensor encendido unos minutos: en frío tarda en entregar puntos.
- Abrir puertas y despejar el camino si se va a caminar.
- Verificar el espacio libre (el script lo controla).

### 4.2 Procedimiento para grabar caminando

1. Iniciar la grabación con el sensor **quieto de 5 a 10 s** en el punto de partida (la IMU se
   inicializa con el sensor en reposo).
2. Caminar **despacio** y hacer los giros **suaves**. Los giros bruscos son la causa más común de
   mapas deformados.
3. Llevar el sensor **horizontal, con la cúpula hacia arriba**, a la altura de la cabeza o un poco
   más arriba (brazo levantado o un palo corto). El L2 mide solo la **semiesfera que está por encima
   de su base** (360° × 90°): no ve el piso ni lo que está más abajo que él. Si se lo lleva a la
   altura del pecho, la cabeza de quien lo lleva tapa una parte de la vista.

   > **Limitación para mapas de robots:** con el sensor horizontal, los obstáculos que estén por
   > debajo de su altura (sillas, mesas bajas, cajas) no quedan en el mapa: solo se ven paredes,
   > objetos altos y techo. Alcanza para probar el SLAM. Para el mapa que va a usar el robot habrá
   > que decidir la altura e inclinación del sensor junto con el diseño del soporte (etapa 3):
   > A VERIFICAR.
4. No tapar el sensor con la mano ni con cables.
5. **Terminar en el mismo punto de partida** y quedarse quieto otros 5 a 10 s. Volver al inicio
   permite comprobar si el mapa "cierra".
6. Cortar con Ctrl+C (o esperar la duración indicada).

### 4.3 Alimentación y cables al caminar

El sensor se alimenta con la fuente de 12 V de pared, y los datos van por el cable Ethernet hasta la
notebook. Para la primera prueba alcanza con un **alargue** para la fuente y llevar la notebook
encima. Para recorridos más largos hará falta una fuente portátil de **12 V** (por ejemplo, una
batería con salida regulada de 12 V y al menos 1,5 A): **A VERIFICAR** al diseñar el montaje de
mano (etapa 3). Nunca conectar el sensor a 24 V o 36 V directamente.

## Verificación final

- [ ] `grabar_lidar.sh` termina mostrando el resumen y crea `descripcion.txt`.
- [ ] La tasa de mensajes de la grabación coincide con la del driver (12 Hz y 250 Hz).
- [ ] La grabación se reproduce con `ros2 bag play` y se ve en RViz.
- [ ] La grabación quedó anotada en `docs/grabaciones.md`.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: no llegan mensajes en /unilidar/cloud. ¿Está corriendo el driver?` | El driver no está en marcha o no recibe datos | Paso 03 |
| `ERROR: no se encuentra 'ros2'` | No se cargó el entorno de ROS 2 | `source /opt/ros/jazzy/setup.bash` |
| `ERROR: la grabación no se cerró correctamente (falta metadata.yaml)` | La grabación se interrumpió de golpe (corte de luz, terminal cerrada) | Intentar `ros2 bag reindex bags/<carpeta>` (A VERIFICAR con MCAP); para evitarlo, grabar dentro de `tmux` |
| La grabación con duración no termina nunca y no se crea la carpeta en `bags/` (versión del script anterior al 2026-11-12 10:15) | `timeout` deja a `ros2 bag record` en segundo plano; al intentar leer el teclado, el sistema lo congela (estado `T` en `ps`) | Actualizar el script (usa `timeout --foreground` y `< /dev/null`). Para destrabar: Ctrl+C no alcanza; cerrar la terminal o `kill` del proceso |
| `ERROR: no llegan mensajes en /unilidar/cloud` aunque el driver esté corriendo | Se cortó el enlace Ethernet (cable flojo o sensor sin alimentación) | Ver el paso 01, problemas frecuentes: diagnóstico de cortes de red |
| `revisar_grabacion.py` informa huecos | Corte de red o PC sobrecargada durante la grabación | Revisar cables y repetir la grabación |
| La grabación tiene menos mensajes de los esperados | Disco lento o PC muy cargada | Cerrar RViz y otros programas mientras se graba |
| `ERROR: no llegan mensajes en /unilidar/cloud` justo después de ver una grabación | Se detuvo el driver para reproducir la grabación | Relanzar el driver (paso 03) y cerrar antes cualquier `ros2 bag play` |
| La grabación nueva es idéntica a una anterior | Quedó abierto un `ros2 bag play` y el script grabó la reproducción en lugar del sensor | Cerrar el `ros2 bag play` (Ctrl+C) antes de grabar; con el driver detenido, el script avisa que no llegan mensajes |
| En RViz se ven dos nubes superpuestas al reproducir | El driver sigue corriendo | Detener el driver antes de `ros2 bag play` |
