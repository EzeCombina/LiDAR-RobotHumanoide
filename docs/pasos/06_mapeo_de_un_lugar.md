# Paso 06 — Mapear un lugar: procedimiento completo

## Objetivo

Obtener el **mapa 3D** (`.pcd`) de una habitación, un departamento o un laboratorio recorriéndolo
con el LiDAR en la mano. Este documento reúne, en orden, todo lo necesario. El detalle de cada parte
está en los pasos 01 a 05.

```
1. Preparar   →   2. Grabar recorriendo   →   3. Generar el mapa   →   4. Ver y revisar   →   5. Registrar
(sensor + driver)    (grabar_lidar.sh)        (procesar_grabacion.sh)  (ver_mapa.sh)          (docs/)
```

## Requisitos

- Pasos 00 a 05 completos una vez en la PC: ROS 2 Jazzy, SDK y driver compilados, red configurada
  (`lidar-l2`), Point-LIO compilado.
- Notebook con el sensor conectado por Ethernet, fuente de 12 V y un **alargue** (o una fuente
  portátil de 12 V, A VERIFICAR).
- Unos 120 MB libres por minuto de recorrido.

## 1. Preparar

1. Conectar el sensor: cable Ethernet a la placa configurada (`eno1` en la PC del laboratorio) y
   fuente de 12 V al módulo adaptador. Dejarlo **encendido unos minutos** antes de grabar (en frío
   tarda en entregar puntos).
2. Lanzar el driver dentro de `tmux`:

   ```bash
   tmux new -s lidar
   source /opt/ros/jazzy/setup.bash
   source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
   cd ~/Documentos/LiDAR-RobotHumanoide
   ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false
   ```

   Salir de `tmux` sin cortar el driver: **Ctrl+b**, después **d**.
3. Comprobar que publica (unos 12 Hz):

   ```bash
   source /opt/ros/jazzy/setup.bash
   ros2 topic hz /unilidar/cloud
   ```

4. Preparar el lugar: abrir las puertas que se van a atravesar, despejar el camino y, si es
   posible, que no haya gente moviéndose.

## 2. Grabar el recorrido

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/grabacion/grabar_lidar.sh <nombre> "" "<descripción del recorrido>"
```

- `<nombre>`: letras, números y guiones bajos, por ejemplo `departamento_horizontal`.
- `""`: sin duración fija; se corta con **Ctrl+C** al terminar.
- `<descripción>`: dónde, cómo se llevó el sensor y cualquier detalle útil.

Ejemplo:

```bash
./scripts/grabacion/grabar_lidar.sh departamento_horizontal "" "Departamento completo, sensor horizontal sobre la cabeza, inicio y fin en la puerta de entrada"
```

### Cómo hacer el recorrido

1. **Apoyado y quieto 5 a 10 s** en el punto de partida antes de moverse: dejar el sensor sobre
   una mesa, un estante o el piso, **en la misma orientación** con la que se lo va a llevar, y
   recién después levantarlo. Point-LIO mide la gravedad en ese momento y con eso nivela todo el
   mapa; sostenerlo en la mano no alcanza (el pulso lo mueve y el mapa queda inclinado, ver
   paso 05, punto 6).
2. Caminar **despacio** y girar **suave**. Los giros bruscos son la causa más común de mapas
   deformados.
3. Pasar por todos los ambientes. En las puertas, ir despacio: hay pocas referencias.
4. **Volver al punto de partida** y quedarse quieto otros 5 a 10 s. Si el mapa "cierra" (la
   llegada coincide con la partida), el recorrido salió bien.
5. **Ctrl+C** para terminar y **esperar a que aparezca el resumen** (`Files:`, `Duration:`,
   `Messages:` …) antes de desconectar el sensor. Si se desconecta antes, la grabación queda
   abierta sin datos; en ese caso la terminal empieza a pitar con el aviso
   `NO LLEGAN DATOS DEL LiDAR` (paso 04, punto 1.1).

### Cómo llevar el sensor

Point-LIO funciona con el sensor en cualquier orientación, siempre que empiece quieto. Lo que
cambia es qué parte del lugar queda en el mapa (paso 05, punto 6):

| Orientación | Cómo | Queda en el mapa | No queda |
|---|---|---|---|
| **Horizontal** | Cúpula hacia arriba, a la altura de la cabeza o más arriba | Paredes, objetos altos, techo, 360° | Piso y obstáculos bajos |
| **Vertical** | Cúpula hacia adelante, a la altura del pecho | Piso, obstáculos bajos, paredes y techo de adelante | Lo que queda detrás |

En ambos casos: no tapar la ventana con la mano ni con el cable. El cuerpo de quien lo lleva queda
filtrado si está a menos de 0,5 m del sensor (`blind`).

> **Resultado (2026-11-12):** recorrido de una habitación con el sensor **vertical**, arrancando
> apoyado y quieto: error de cierre 10,5 cm, inclinación 2–3°, mapa validado visualmente
> (`mapas/2026-11-12_1445_habitacion_vertical_rapido`). La comparación con el sensor horizontal en
> el mismo recorrido sigue pendiente.

> **Prueba sugerida:** hacer el **mismo recorrido dos veces**, una con el sensor horizontal y otra
> vertical (`<lugar>_horizontal` y `<lugar>_vertical`), y comparar los mapas. Sirve para elegir la
> orientación y como dato para el montaje en el robot. Resultado: **pendiente** (A VERIFICAR).

## 3. Generar el mapa

1. **Detener el driver** (no tiene que haber nada publicando `/unilidar/cloud`):

   ```bash
   tmux attach -t lidar     # y Ctrl+C
   ```

   Si el driver se lanzó en otra terminal y no se sabe en cuál:

   ```bash
   pkill -INT -f l2_driver.launch.py     # equivale a Ctrl+C en esa terminal
   source /opt/ros/jazzy/setup.bash
   ros2 topic hz /unilidar/cloud         # no debe mostrar datos (cortar con Ctrl+C)
   ```

   Desde acá ya no hace falta el sensor: se puede desconectar.
2. (Opcional) Comprobar que la grabación no tiene huecos:

   ```bash
   ./scripts/grabacion/revisar_grabacion.py bags/<carpeta>
   ```

3. Procesar la grabación:

   ```bash
   cd ~/Documentos/LiDAR-RobotHumanoide
   ls bags/                                          # buscar la carpeta de la grabación
   ./scripts/mapas/procesar_grabacion.sh bags/<carpeta>    # agregar --rviz para ver cómo se arma
   ```

   Tarda lo mismo que duró la grabación. Al final muestra el nombre del mapa, la cantidad de puntos
   y el tamaño. El mapa queda en la carpeta `mapas/<fecha>_<nombre>/` (`mapa.pcd`, `resumen.txt`,
   `trayectoria.csv` y `pointlio.log`).

## 4. Ver y revisar el mapa

Desde una terminal del escritorio de Ubuntu:

```bash
./scripts/mapas/ver_mapa.sh mapas/<fecha>_<nombre>
```

Primero, los números del resumen que muestra `procesar_grabacion.sh` (también en
`mapas/<fecha>_<nombre>/resumen.txt`):

- [ ] **Zona recorrida** parecida a lo que se caminó.
- [ ] **Error de cierre** de pocos centímetros (si se terminó en el punto de partida).
- [ ] **Piso y techo nivelados:** en `analizar_mapa.py`, inclinación de los planos horizontales de
      1–2° como máximo.

Para ver las medidas del mapa y la trayectoria cada 10 s:

```bash
./scripts/mapas/analizar_mapa.py mapas/<fecha>_<nombre>
```

La **extensión útil** de cada eje debe parecerse a las medidas reales del lugar.

Después, en RViz:

- [ ] Las paredes se ven **rectas y simples**, no duplicadas ni "fantasmas" corridos.
- [ ] El piso (o el techo) es **plano** y paralelo a la grilla. Que las paredes crucen la grilla en
      diagonal es normal (depende de hacia dónde apuntaba el sensor al empezar).
- [ ] El recorrido (línea blanca) es coherente con lo que se caminó; la esfera verde (partida) y la
      roja (llegada) están juntas si se terminó en el punto de partida.
- [ ] Los ambientes están en la posición correcta entre sí; las medidas son razonables (se pueden
      medir distancias con la herramienta *Measure* de RViz).
- [ ] La zona de llegada coincide con la de partida.

Si algo falla, repetir la grabación más despacio, con giros más suaves y empezando bien quieto.

## 5. Registrar

- Anotar la grabación en `docs/grabaciones.md` y el mapa en `docs/mapas.md`.
- Agregar una entrada en `docs/bitacora.md` con el resultado y los problemas.
- `git add` de la carpeta del mapa (solo se suben `resumen.txt` y `trayectoria.csv`) y de los
  documentos; commit y push. Los `.pcd` y las
  grabaciones **no** se suben (están en `.gitignore`).

## Resumen de comandos

```bash
# 1. Driver (en tmux)
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false
# 2. Grabar (Ctrl+C al terminar)
./scripts/grabacion/grabar_lidar.sh <nombre> "" "<descripción>"
# 3. Detener el driver y generar el mapa
./scripts/mapas/procesar_grabacion.sh bags/<carpeta>
# 4. Ver el mapa (terminal del escritorio)
./scripts/mapas/ver_mapa.sh mapas/<fecha>_<nombre>
```

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: no llegan mensajes en /unilidar/cloud` al grabar | El driver no está corriendo | Punto 1 |
| `ERROR: ya hay algo publicando /unilidar/cloud` al procesar | El driver sigue corriendo | Detenerlo (punto 3) |
| Paredes duplicadas o mapa torcido | Giros bruscos, inicio en movimiento, ambiente con pocas referencias | Repetir más despacio; empezar y terminar quieto |
| El mapa no tiene piso ni muebles bajos | Sensor horizontal: no ve por debajo de su base | Probar con el sensor vertical o inclinado |
| `revisar_grabacion.py`: `GRABACIÓN INCOMPLETA` (no llegaron datos durante los últimos N s) | Se desconectó el sensor o un cable antes de cortar la grabación | Repetir; cortar con Ctrl+C y esperar el resumen antes de desconectar |
| Pitidos y `NO LLEGAN DATOS DEL LiDAR` durante la grabación | Cable Ethernet o alimentación sueltos | Revisar las conexiones; dejar el cable con juego para que no se tense al levantar el sensor |
| Se corta la alimentación al caminar | El cable de la fuente no alcanza | Alargue o fuente portátil de 12 V |
| Más problemas | — | Ver los pasos 01 a 05 |
