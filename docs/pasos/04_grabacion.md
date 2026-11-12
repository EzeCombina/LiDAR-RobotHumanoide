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
./scripts/grabar_lidar.sh <nombre> [segundos] ["descripción"]
```

Ejemplos:

```bash
./scripts/grabar_lidar.sh sala_quieta 90 "Sensor en el piso sobre la almohadilla, nadie se mueve"
./scripts/grabar_lidar.sh recorrido_mano            # graba hasta cortar con Ctrl+C
```

El script:

1. Verifica que llegan mensajes en `/unilidar/cloud` y `/unilidar/imu` y que quedan al menos 5 GB
   libres.
2. Graba esos dos tópicos en formato MCAP en `bags/<AAAA-MM-DD_HHMM>_<nombre>/` (carpeta del
   repositorio excluida de git). Para grabar en otro disco: `BAGS_DIR=/ruta ./scripts/grabar_lidar.sh ...`.
3. Si se indicó una duración, corta solo; si no, se corta con **Ctrl+C**. En ambos casos cierra el
   archivo de forma ordenada.
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

```bash
ros2 bag info bags/<carpeta>
```

Para verla en RViz, **primero detener el driver** (si no, se mezclan los datos en vivo con los
grabados) y después:

```bash
ros2 bag play bags/<carpeta>
```

y abrir RViz como en el paso 03, punto 4.

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
3. Llevar el sensor **con la cúpula hacia arriba** y por encima del cuerpo en lo posible: el L2 mide
   la semiesfera superior, y el cuerpo tapa parte de la vista hacia abajo.
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
| La grabación tiene menos mensajes de los esperados | Disco lento o PC muy cargada | Cerrar RViz y otros programas mientras se graba |
| En RViz se ven dos nubes superpuestas al reproducir | El driver sigue corriendo | Detener el driver antes de `ros2 bag play` |
