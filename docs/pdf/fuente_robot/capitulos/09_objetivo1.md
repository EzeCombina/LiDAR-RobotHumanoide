# 9. Objetivo 1: ubicarse en un mapa ya hecho

Se comprueba que, con un **mapa guardado** y los datos del LiDAR, el sistema reconoce el lugar y
sabe dónde está, incluso si arranca con una posición inicial equivocada. Se usa una **grabación
real**, reproducida como si el sensor estuviera en vivo, y se compara la posición que estima AMCL
con la que calculó Point-LIO al hacer el mapa (la "verdad").

## 9.1 Qué hace falta

- Una carpeta de mapa con `mapa_2d.yaml`, `transformacion.txt` y `trayectoria_limpia.csv` (los genera
  la guía anterior, capítulo 10).
- La grabación con la que se hizo ese mapa.

## 9.2 Prueba automática

```bash
./scripts/navegacion/probar_con_grabacion.sh localizacion \
    bags/2026-11-12_1442_habitacion_vertical_rapido \
    mapas/2026-11-12_1445_habitacion_vertical_rapido 68
```

El script arranca todo sin RViz, reproduce la grabación, mide el error y cierra todo al terminar
(unos 2 minutos). La pose y la altura iniciales del sensor salen de `transformacion.txt` (el punto
de partida de la grabación del mapa). Resultados en `resultados/<fecha>_localizacion_<grabación>/`.

```text
Resumen (121 poses de AMCL en 65.9 s)
  incertidumbre final de AMCL: σx=0.329 m  σy=0.277 m  σángulo=14.3°
  error de posición: medio 0.121 m, mediana 0.113 m, máximo 0.217 m, final 0.175 m
  primera vez bajo 0.2 m: a los 0.0 s; después de eso, 98 % del tiempo bajo 0.2 m
```

## 9.3 ¿Reconoce el lugar si arranca mal ubicado?

El caso que importa para el robot. Se le da a AMCL una pose corrida 0,5 m y girada 20° (los dos
últimos argumentos: `x,y,yaw` en m y rad, y la altura del sensor en m):

```bash
./scripts/navegacion/probar_con_grabacion.sh localizacion \
    bags/2026-11-12_1442_habitacion_vertical_rapido \
    mapas/2026-11-12_1445_habitacion_vertical_rapido 68 0.40,-0.30,1.05 0.873
```

```text
  error de posición: medio 0.236 m, mediana 0.158 m, máximo 0.598 m, final 0.117 m
  primera vez bajo 0.2 m: a los 30.7 s; después de eso, 100 % del tiempo bajo 0.2 m (máximo 0.181 m)
```

AMCL **se corrigió solo**: a los 31 s el error bajó de 0,2 m y no volvió a subir.

![Error de posición de AMCL en la habitación, comparado con la trayectoria de Point-LIO](docs/img/robot_localizacion_error.png)

## 9.4 Resultados

| Prueba | Error medio | Bajo 0,2 m |
|---|---|---|
| Habitación, pose inicial correcta | 0,12 m (máximo 0,22 m) | 98 % del tiempo |
| Habitación, pose inicial equivocada (0,5 m y 20°) | 0,18 m máximo, después de corregirse | 100 % desde los 31 s |
| Oficina, pose inicial correcta | **Falla**: AMCL se pierde | — |

Por qué falla en la oficina: el mapa 2D tiene **80 % de zona desconocida** y muchos bordes ruidosos
de escritorios y computadoras dentro de la franja de alturas; el recorrido fue de menos de 1 m² y con
el sensor vertical, que solo ve hacia adelante. Con tan poca información, las partículas se
dispersan. Se espera que mejore con un mapa grabado **con el robot**, con un recorrido amplio.

!!! importante "Falta una prueba"
    La "verdad" es la trayectoria de Point-LIO de la misma grabación del mapa. Falta probar con una
    **grabación nueva** del mismo lugar (otro día, otro recorrido).

## 9.5 Con RViz, o con el sensor en vivo

```bash
# Con la grabación y RViz (en el escritorio)
ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
    mapa:=mapas/2026-11-12_1445_habitacion_vertical_rapido \
    bag:=bags/2026-11-12_1442_habitacion_vertical_rapido
# Con el sensor en vivo (driver corriendo; sensor APOYADO Y QUIETO al lanzar)
ros2 launch scripts/navegacion/navegacion.launch.py modo:=localizacion \
    mapa:=mapas/<carpeta> inicio:=<x>,<y>,<yaw> altura_inicial:=<m>
```

En RViz se ven el mapa, el barrido (rojo), las partículas (verde) y la flecha de la pose. El
barrido tiene que quedar **sobre las paredes** del mapa. Para corregir la pose a mano: herramienta
*2D Pose Estimate*, clic y arrastrar.

| Síntoma | Causa | Solución |
|---|---|---|
| `ya hay procesos de navegación o simulación corriendo` | Quedó abierta otra prueba (dos Point-LIO mezclan datos) | Cerrarla con Ctrl+C |
| El barrido no coincide con las paredes | Altura inicial equivocada: la franja de alturas queda corrida | Medir la altura del sensor al arrancar |
| No llegan poses de AMCL | El sensor no se movió (AMCL publica solo con movimiento) | Moverse; revisar `launch.log` |
