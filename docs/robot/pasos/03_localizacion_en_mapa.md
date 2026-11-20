# Paso R03 — Objetivo 1: ubicarse en un mapa ya hecho

## Objetivo

Comprobar que, con un **mapa guardado** (el de la primera etapa) y los datos del LiDAR, el sistema
**reconoce el lugar y sabe dónde está**, incluso si arranca con una posición inicial equivocada. Es
la mitad del objetivo 1; la otra mitad (moverse por el mapa) se prueba en R05.

Se prueba **sin el sensor y sin el robot**: se reproduce una grabación real como si el sensor
estuviera en vivo, y se compara la posición que estima el sistema con la que calculó Point-LIO al
hacer el mapa.

## Requisitos

- Paso R02.
- Una carpeta de mapa con `mapa_2d.yaml` (paso 07), `transformacion.txt` y `trayectoria_limpia.csv`
  (los genera `limpiar_mapa.py`), y la grabación con la que se hizo ese mapa.

!!! concepto "¿Qué es AMCL?"
    *Adaptive Monte Carlo Localization*. Reparte cientos de "partículas" (posibles posiciones del
    robot) sobre el mapa. Cada vez que el robot se mueve, las desplaza según la odometría y les da
    más peso a las que explican mejor lo que ve el LiDAR (las paredes que mide coinciden con las del
    mapa). Con el tiempo, las partículas se juntan en la posición real. Publica esa posición en
    `/amcl_pose` y la corrección `map -> odom`.

## 1. Cómo funciona

1. **Point-LIO** calcula el movimiento del sensor (odometría) con la nube y la IMU.
2. **`base_nivelada.py`** lo convierte en la pose del robot sobre el piso (`base_footprint`).
3. **`filtro_cuerpo.py`** quita de la nube los puntos de quien lleva el sensor (o del robot).
4. **`pointcloud_to_laserscan`** toma de la nube los puntos entre 0,10 y 1,80 m de altura (la misma
   franja del mapa 2D) y arma un barrido 2D en `base_footprint`, que no se inclina.
5. **AMCL** compara ese barrido con el mapa 2D y estima la posición.

## 2. Prueba automática con una grabación

```bash
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/point_lio_ws/install/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/navegacion/probar_con_grabacion.sh localizacion \
    bags/2026-11-12_1442_habitacion_vertical_rapido \
    mapas/2026-11-12_1445_habitacion_vertical_rapido 68
```

El script lanza todo sin RViz, reproduce la grabación, corre `evaluar_localizacion.py` y cierra
todo al terminar (unos 2 minutos). Resultados en `resultados/<fecha>_localizacion_<grabación>/`:
`launch.log`, `evaluacion.txt`, `error.csv` y `descripcion.txt`.

**Salida obtenida** (2026-11-20, resumida):

```text
[navegacion.launch] modo=localizacion fuente=lidar nube=/cloud_registered_body sim_time=True
  altura_inicial=0.873 inicio=(0.000, 0.000, 40.0°) ...
Escuchando /amcl_pose ... (Ctrl+C para terminar)
  t=   0.0 s  x=  0.000  y=  0.000  σxy=0.000 m
  t=   9.9 s  x=  0.283  y= -0.380  σxy=0.119 m
  ...
Resumen (121 poses de AMCL en 65.9 s)
  incertidumbre final de AMCL: σx=0.329 m  σy=0.277 m  σángulo=14.3°
  error de posición: medio 0.121 m, mediana 0.113 m, máximo 0.217 m, final 0.175 m
  primera vez bajo 0.2 m: a los 0.0 s; después de eso, 98 % del tiempo bajo 0.2 m (máximo 0.217 m)
```

La **pose inicial** (`inicio=mapa`, valor por defecto) es el punto de partida de la grabación con
la que se hizo el mapa, leído de `transformacion.txt`; la **altura inicial** del sensor sobre el
piso (0,873 m: estaba apoyado sobre un mueble) sale del mismo archivo.

### 2.1 Arrancar con una pose equivocada: ¿reconoce el lugar?

El caso que importa para el robot: no saber con exactitud dónde arranca. Se le da a AMCL una pose
corrida 0,5 m y girada 20°:

```bash
./scripts/navegacion/probar_con_grabacion.sh localizacion \
    bags/2026-11-12_1442_habitacion_vertical_rapido \
    mapas/2026-11-12_1445_habitacion_vertical_rapido 68 0.40,-0.30,1.05 0.873
```

(los dos últimos argumentos: pose `x,y,yaw` en m y rad, y altura inicial del sensor en m).

**Salida obtenida** (2026-11-20):

```text
Resumen (131 poses de AMCL en 66.9 s)
  incertidumbre final de AMCL: σx=0.270 m  σy=0.270 m  σángulo=14.0°
  error de posición: medio 0.236 m, mediana 0.158 m, máximo 0.598 m, final 0.117 m
  primera vez bajo 0.2 m: a los 30.7 s; después de eso, 100 % del tiempo bajo 0.2 m (máximo 0.181 m)
```

AMCL **se corrigió solo**: a los 31 s el error bajó de 0,2 m y no volvió a subir.

![Error de posición de AMCL en la habitación, frente a la trayectoria de Point-LIO](docs/img/robot_localizacion_error.png)

### 2.2 Resultados

| Prueba | Error medio | Error máximo | Tiempo bajo 0,2 m |
|---|---|---|---|
| Habitación, pose inicial correcta | 0,12 m | 0,22 m | 98 % |
| Habitación, pose inicial equivocada (0,5 m, 20°) | 0,24 m (0,18 m máx. después de converger) | 0,60 m (al principio) | 100 % desde los 31 s |
| Oficina, pose inicial correcta | **falla**: AMCL diverge (error final de decenas de metros) | — | 4 % |

!!! importante "La prueba usa la misma grabación del mapa"
    La referencia ("verdad") es la trayectoria que calculó Point-LIO con esa misma grabación, así
    que es la mejor prueba posible sin otra fuente de posición. **Falta** probar con una grabación
    nueva del mismo lugar (otro día, otro recorrido): la grabación `2026-11-12_1432` de la habitación
    está incompleta y no sirve. Pendiente para la próxima sesión con el sensor.

### 2.3 Por qué falla en la oficina

- El mapa 2D de la oficina tiene **80 % de zona desconocida** y muchos bordes ruidosos de escritorios
  y computadoras dentro de la franja de alturas.
- El recorrido fue corto (zona de 0,8 × 1,1 m) y con el sensor vertical, que solo ve hacia adelante.
- Con poca información que compare bien, las partículas se dispersan y AMCL se pierde.

Se espera mejorar con un mapa grabado **con el robot** (sensor montado, recorrido amplio) o con
localización 3D (R00, trabajo futuro). Antes de agregar el filtro del cuerpo, la oficina daba un
desvío casi fijo de unos 0,38 m (error medio 0,38 m, máximo 0,54 m); con la configuración final,
diverge. En los dos casos, el resultado no sirve para navegar.

!!! nota "Ajuste que más mejoró la localización"
    El ruido de odometría de AMCL (`alpha1` a `alpha5`). Nav2 trae 0,2, pensado para ruedas que
    patinan. Con 0,2, en la habitación el error medio fue 0,26 m y la incertidumbre crecía; con 0,05
    (Point-LIO es mucho más exacta), 0,12 m.

## 3. Hacerlo a mano (lo mismo que hace el script)

Terminal 1 — todo el sistema con RViz (en el escritorio):

```bash
ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
    mapa:=mapas/2026-11-12_1445_habitacion_vertical_rapido \
    bag:=bags/2026-11-12_1442_habitacion_vertical_rapido
```

Con `bag:=...` el launch reproduce la grabación a los 6 s (`espera_bag`) con `--clock` (todo usa
el tiempo de la grabación) y activa AMCL 5 s después. En RViz se ven el mapa, el barrido rojo
(`/scan`), las partículas verdes y la flecha de la pose de AMCL; el barrido tiene que quedar
**sobre las paredes** del mapa.

Terminal 2 — el evaluador:

```bash
./scripts/navegacion/evaluar_localizacion.py --mapa mapas/2026-11-12_1445_habitacion_vertical_rapido \
    --duracion 68 --ros-args -p use_sim_time:=true
```

Para probar una pose equivocada, en RViz: herramienta **2D Pose Estimate**, clic y arrastrar en otro
lugar del mapa.

## 4. Con el sensor en vivo (A VERIFICAR)

Con el driver corriendo (paso 03) y el sensor **apoyado y quieto** al lanzar:

```bash
ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
    mapa:=mapas/<carpeta> inicio:=<x>,<y>,<yaw> altura_inicial:=<m>
```

`inicio` es dónde está el sensor en el mapa (si no se sabe, uno aproximado y corregirlo en RViz con
*2D Pose Estimate*). `altura_inicial` es la altura del sensor sobre el piso al lanzar. Después,
caminar despacio por el lugar.

## Verificación final

- [ ] `probar_con_grabacion.sh localizacion` termina con "Errores en el launch.log: ninguno".
- [ ] Con la pose correcta, error medio de 0,15 m o menos.
- [ ] Con la pose equivocada, aparece "primera vez bajo 0.2 m" y después se mantiene bajo 0,2 m.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ERROR: ya hay procesos de navegación o simulación corriendo` | Quedó abierta otra prueba (dos Point-LIO mezclan datos) | Cerrarla con Ctrl+C; si no responde, `pkill -f pointlio_mapping` y `pkill -f "ros2 bag play"` |
| `indicar altura_inicial:=<m>` | Pose inicial a mano sin altura | Agregar la altura del sensor sobre el piso |
| "No llegaron suficientes poses de AMCL" | El sensor no se movió (AMCL publica solo al moverse) o el sistema no arrancó | Revisar `launch.log`; esperar más (`--inactividad`) |
| Error medio alto y que crece | Mapa pobre (mucho desconocido o ruido), o recorrido corto | Ver 2.3 |
| El barrido no coincide con las paredes en RViz | Altura inicial equivocada (la franja 0,10–1,80 m queda corrida) | Medir la altura real del sensor al arrancar |
