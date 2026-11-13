# 10. Procesamiento del mapa: mapa 3D limpio y mapa 2D

El mapa que genera Point-LIO se convierte en los dos productos que va a usar el robot. No hace
falta el sensor.

## 10.1 Mapa 3D limpio

```bash
./scripts/mapas/limpiar_mapa.py mapas/<carpeta_del_mapa>
```

| Paso | Qué hace | Parámetro (defecto) |
|---|---|---|
| Reducción de densidad | Un punto por cubo de 3 cm (Point-LIO repite muchas veces los mismos puntos) | `--voxel 0.03` |
| Puntos sueltos | Quita los puntos mucho más lejos de sus 10 vecinos que el promedio (ruido, reflejos) | `--vecinos 10`, `--sigma 2.0` |
| Nivelación | Busca el **piso** (el plano horizontal más bajo), lo deja horizontal y en **z = 0**, y afina con todos los puntos del piso | `--referencia piso` |
| Alineación | Gira el mapa en planta para que la pared principal quede paralela a un eje | `--sin-alinear` la desactiva |

!!! concepto "RANSAC"
    Para encontrar un plano (el piso, una pared) en una nube con ruido, se eligen 3 puntos al azar,
    se arma el plano que pasa por ellos y se cuentan los puntos cercanos. Se repite cientos de veces
    y se queda el plano que más puntos explica. Después se reajusta con todos sus puntos.

Salida real (habitación del capítulo 9):

```text
1. Reducción a celdas de 3 cm: 1.102.546 -> 350.797 puntos
2. Puntos sueltos quitados: 11.446 (vecinos=10, sigma=2.0) -> quedan 339.351
   plano horizontal a z =   1.96 m, inclinación  1.3°,  8.9 % de los puntos
   plano horizontal a z =  -0.89 m, inclinación  1.9°,  4.7 % de los puntos
   plano horizontal a z =   0.00 m, inclinación  0.6°,  3.4 % de los puntos
...
3. Nivelación con el piso: inclinación corregida 1.9°; piso llevado a z = 0 (desplazamiento +0.88 m)
   Refinamiento con la franja del piso (12.395 puntos): 0.35° adicionales
4. Alineación de paredes: giro de +40.0° alrededor del eje vertical
5. Guardado .../mapa_limpio.pcd: 339.351 puntos, 5.4 MB
   Extensión útil (1 %-99 %): x 3.21 m, y 7.88 m, z -0.06 a 2.85 m
```

El plano a −0,89 m es el piso; el de 0,00 m, la **mesa** donde se apoyó el sensor al empezar (el
origen del mapa es la posición inicial del sensor). Resultado: piso en z = 0, inclinación de 0,3 a
0,8° y un archivo de 5,4 MB en lugar de 34 MB. Se guardan además `trayectoria_limpia.csv`,
`transformacion.txt` (la matriz aplicada, que relaciona las coordenadas de Point-LIO con las del
mapa limpio) y `limpieza.txt`.

!!! importante "Sirve para cualquier mapa que vea el piso"
    El script funciona con cualquier `.pcd`, de cualquier lugar. Para nivelar necesita **ver el
    piso**. Si el plano más bajo no puede ser el piso (tiene más del 5 % de los puntos por debajo),
    no nivela y lo avisa: en ese caso usar `--referencia techo` o `--sin-nivelar`.

Verificación: `./scripts/mapas/analizar_mapa.py mapas/<carpeta>/mapa_limpio.pcd` (inclinación de 1°
o menos), y visualmente:
`./scripts/mapas/ver_mapa.sh mapas/<carpeta>/mapa_limpio.pcd mapas/<carpeta>/trayectoria_limpia.csv`.

## 10.2 Mapa 2D de ocupación para Nav2

```bash
./scripts/mapas/generar_mapa_2d.py mapas/<carpeta_del_mapa>
```

Usa `mapa_limpio.pcd` (hay que hacer antes el punto 10.1). Arma una grilla de 5 cm vista desde
arriba y clasifica cada celda:

- **Ocupada (negro):** tiene al menos 2 puntos en la **franja de alturas** de 0,10 a 1,80 m sobre
  el piso, donde el robot puede chocar. El piso y lo que está por encima del robot no cuentan.
- **Libre (blanco):** se vio el piso y no hay obstáculos, o pasó por ahí quien llevaba el sensor
  (unos 20 cm alrededor de la trayectoria). Se rellenan huecos chicos.
- **Desconocida (gris):** no se vio.

| Parámetro | Defecto | Significado |
|---|---|---|
| `--resolucion` | 0.05 | Tamaño de celda (m) |
| `--altura-min` / `--altura-max` | 0.10 / 1.80 | Franja de obstáculos (m). `--altura-max` debe ser al menos la altura del robot |
| `--min-puntos` | 2 | Puntos para considerar ocupada una celda |
| `--piso` | 0.05 | Tolerancia del piso (m) |

```text
Grilla: 85 x 180 celdas de 5 cm = 4.25 x 9.00 m
Origen (esquina inferior izquierda): x = -2.497 m, y = -3.800 m
Franja de obstáculos: 0.10 a 1.80 m sobre el piso
Celdas: ocupadas 41.7 %, libres 14.7 %, desconocidas 43.6 %
```

![Mapa 2D de la habitación. Negro: ocupado (paredes y muebles); blanco: libre; gris: desconocido](docs/img/mapa_2d_habitacion_2026-11-12.png)

Las manchas negras dentro de la habitación son **muebles**: hay unos 5 m² de superficies entre 0,7 y
1,0 m de altura (mesas y escritorios). Para un robot, una mesa es un obstáculo.

El script genera `mapa_2d.pgm` (la imagen), `mapa_2d.png` (copia para ver) y `mapa_2d.yaml`:

```yaml
image: mapa_2d.pgm
mode: trinary
resolution: 0.05
origin: [-2.497, -3.800, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

!!! peligro "El umbral free_thresh"
    Nav2 calcula, para cada píxel, `p = (255 − valor) / 255`. Las celdas desconocidas (gris, 205)
    dan p = 0,196. Con `free_thresh: 0.196` quedan **desconocidas**; con un valor mayor (por ejemplo
    0,25) pasarían a ser **libres**, y el robot creería que puede ir por zonas que nunca se vieron.

## 10.3 Verificar el mapa 2D con Nav2

```bash
./scripts/mapas/ver_mapa_2d.sh mapas/<carpeta_del_mapa>       # terminal del escritorio
```

Carga el mapa con `nav2_map_server` (el mismo programa que va a usar el robot), lo activa y lo
muestra en RViz visto desde arriba. A mano:

```bash
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=<ruta completa>/mapa_2d.yaml
ros2 run nav2_util lifecycle_bringup map_server      # en otra terminal: lo activa
rviz2 -d ~/Documentos/LiDAR-RobotHumanoide/config/rviz/ver_mapa_2d.rviz
```

!!! concepto "Nodos con ciclo de vida"
    Los nodos de Nav2 arrancan **inactivos** y solo publican después de pasar por los estados
    *configure* y *activate*. `lifecycle_bringup` hace esas dos transiciones. Sin eso, RViz muestra
    "No map received".

Para comprobar cómo interpreta Nav2 cada celda (con el mapa cargado y activado):

```bash
./scripts/mapas/verificar_mapa_2d.py
```

```text
Mapa en /map: 85 x 180 celdas de 5 cm (4.25 x 9.00 m), origen (-2.497, -3.800), marco 'map'
Nav2 recibe: ocupadas (100) 41.7 %, libres (0) 14.7 %, desconocidas (-1) 43.6 %, otros valores 0.0 %
```

Los porcentajes tienen que ser **iguales** a los de `generar_mapa_2d.py`.
