# 10. Objetivo 2: obstáculos con el LiDAR en tiempo real

El sistema usa la **nube del L2 en vivo** para ver lo que no está en el mapa y tenerlo en cuenta al
moverse, y lo **borra** cuando se va. Este capítulo explica la configuración y una prueba con
grabaciones reales; la prueba completa, con un obstáculo que aparece en un lugar conocido, está en
el capítulo 11.

## 10.1 Configuración

| Pieza | Configuración | Por qué |
|---|---|---|
| Fuente de obstáculos | La nube 3D sin el cuerpo del robot (`/nube_obstaculos`) | Ve obstáculos a cualquier altura |
| Costmap local (5 × 5 m, se mueve con el robot) | Capa de vóxeles: guarda la ocupación en 3D, hasta 2 m de alto | Una mesa se marca aunque sus patas sean finas |
| Costmap global (todo el mapa) | Mapa guardado + capa de obstáculos | El plan rodea lo nuevo y lo conocido |
| Franja que se **marca** | 0,10 a 1,80 m sobre el piso | La misma del mapa 2D: el piso y el techo no son obstáculos |
| Franja que se usa para **borrar** | 0 a 3 m | Ver el recuadro |
| Monitor de colisiones | Huella del robot proyectada 1,2 s hacia adelante; zona delante que frena al 40 % | Freno de seguridad aunque falle el resto |

!!! importante "Para borrar hay que dejar pasar los rayos al techo"
    Nav2 filtra la nube **antes** de trazar los rayos. Si la nube se filtra a 0,10–1,80 m (lo
    intuitivo), los rayos que llegan al techo se descartan y el espacio por donde pasó una persona
    **nunca se borra**: se comprobó con la grabación `persona_caminando`. La solución estándar: la
    fuente acepta 0 a 3 m (los rayos al techo borran) y la capa marca solo de 0,10 a 1,80 m.

## 10.2 Prueba con grabaciones

```bash
./scripts/navegacion/probar_con_grabacion.sh obstaculos bags/2026-11-12_1028_persona_caminando 0.05 50
./scripts/navegacion/probar_con_grabacion.sh obstaculos bags/2026-11-12_1016_sala_quieta 0.05 50
```

(argumentos: grabación, altura del sensor sobre el piso y segundos a evaluar). Se lanza un costmap
suelto de 8 × 8 m, sin mapa, y el evaluador separa el **fondo** (lo que está ocupado el 80 % del
tiempo o más: paredes y muebles) de lo **dinámico**, y mide el grupo dinámico más grande de cada
segundo. La sala quieta (el mismo lugar, sin nadie moviéndose) es el control.

| Grabación | Grupo dinámico más grande (primeros 35 s) |
|---|---|
| Persona caminando | 30 a 50 celdas (≈ 0,1 m², el tamaño de una persona vista desde arriba) |
| Sala quieta (control) | 10 a 20 celdas (ruido del sensor en los bordes de los muebles) |

El costmap **ve a la persona**. Después de los 35 s, con la persona aparece una zona dinámica grande
(hasta 1,25 m²) que no se sabe qué fue (**A CONFIRMAR**: la descripción de la grabación quedó vacía).
Es una prueba **cualitativa**, porque no se sabe con exactitud dónde estuvo la persona.

## 10.3 Verlo en RViz

```bash
ros2 launch scripts/navegacion/navegacion.launch.py modo:=obstaculos \
    bag:=bags/2026-11-12_1028_persona_caminando altura_inicial:=0.05
```

RViz muestra el costmap, la nube del sensor y los vóxeles marcados (cubos rojos). Con el sensor en
vivo es igual, sin `bag:=` y con el sensor apoyado y quieto al lanzar: una mano o una persona
delante del sensor aparece como celdas negras, que se borran cuando se va.
