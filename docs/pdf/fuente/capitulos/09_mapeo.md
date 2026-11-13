# 9. Mapeo de una habitación

Este capítulo reúne, en orden, todo lo necesario para obtener el mapa de un lugar recorriéndolo
con el sensor en la mano.

## 9.1 Preparación

1. **Conectar** el sensor (Ethernet y fuente) y dejarlo encendido unos minutos: en frío tarda en
   entregar puntos.
2. **Verificar la red:** `ip -br addr show eno1` tiene que mostrar `UP  192.168.1.2/24`.
3. **Lanzar el driver** dentro de tmux (capítulo 6) y verificar con
   `ros2 topic hz /unilidar/cloud` que da unos 12 Hz.
4. **Preparar el lugar:** abrir las puertas que se van a atravesar, despejar el camino y, si es
   posible, que no haya gente moviéndose.
5. **Cables:** la fuente es de pared y los datos van por cable a la notebook. Usar un alargue,
   llevar la notebook encima y dejar el cable con juego para que no se tense al levantar el sensor.

## 9.2 Cómo llevar el sensor

Point-LIO funciona con el sensor en cualquier orientación, siempre que **empiece quieto**. Lo que
cambia es qué parte del lugar queda en el mapa:

| Orientación | Cómo | Queda en el mapa | No queda |
|---|---|---|---|
| **Horizontal** | Cúpula hacia arriba, a la altura de la cabeza o más arriba | Paredes, objetos altos y techo, en 360° | Piso y obstáculos bajos |
| **Vertical** | Cúpula hacia adelante, a la altura del pecho | Piso, obstáculos bajos, paredes y techo de adelante | Lo que queda detrás |

Para el mapa 2D que va a usar el robot hace falta ver el piso y los obstáculos bajos: conviene la
orientación **vertical**. En los dos casos, no tapar la ventana del sensor con la mano ni con el
cable.

## 9.3 Grabar el recorrido

```bash
./scripts/grabacion/grabar_lidar.sh habitacion_vertical "" "Habitación, sensor vertical, inicio y fin en la puerta"
```

1. **Sensor apoyado y quieto 10 s** sobre una mesa, un estante o el piso. Puede estar en otra
   orientación que la de trabajo (por ejemplo, horizontal sobre la mesa): lo importante es que esté
   **quieto**. Recién después, levantarlo.
2. Caminar **despacio** y girar **suave**: los giros bruscos son la causa más común de mapas
   deformados. En las puertas, ir más despacio, porque hay pocas referencias.
3. **Volver al punto de partida**, apoyarlo y dejarlo quieto otros 10 s.
4. **Ctrl+C** y esperar el resumen antes de desconectar nada.

## 9.4 Generar, revisar y ver el mapa

```bash
tmux attach -t lidar                                   # y Ctrl+C: detener el driver
./scripts/grabacion/revisar_grabacion.py bags/<carpeta>  # "grabación completa" y arranque "QUIETO"
./scripts/mapas/procesar_grabacion.sh bags/<carpeta>     # genera mapas/<fecha>_<nombre>/
./scripts/mapas/ver_mapa.sh mapas/<carpeta_del_mapa>     # terminal del escritorio
```

Qué revisar:

- **Error de cierre** de pocos centímetros (si se volvió al punto de partida).
- **Inclinación** de piso y techo de 1–2° como máximo (`analizar_mapa.py`).
- En RViz: paredes simples, sin duplicados; piso paralelo a la grilla; esferas verde y roja juntas.

Si algo falla, repetir la grabación más despacio y arrancando bien quieto.

## 9.5 Resultado obtenido

Habitación recorrida con el sensor vertical, con un recorrido de unos 74 s:

| Dato | Valor |
|---|---|
| Grabación | 74 s, completa, arranque quieto |
| Mapa 3D | 1,10 millones de puntos (34 MB) |
| Error de cierre | **10,5 cm** |
| Inclinación (antes de nivelar) | 1,9° |
| Medidas | unos 3,2 × 7,9 m en planta y 2,85 m de alto |

Las grabaciones y mapas de referencia del proyecto, con sus resultados, están registrados en
`docs/grabaciones.md` y `docs/mapas.md`.
