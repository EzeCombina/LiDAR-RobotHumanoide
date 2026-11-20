# 2. Conceptos básicos

## 2.1 Odometría y localización

Para moverse solo, el robot necesita saber **dónde está**. Hay dos formas de calcularlo, que se
usan juntas:

- **Odometría:** sumar el movimiento desde que arrancó. En este proyecto la calcula **Point-LIO**
  (el mismo SLAM de la guía anterior) con la nube y la IMU del L2. Es precisa a corto plazo, pero
  los pequeños errores se acumulan (**deriva**) y no sabe dónde está el robot en el mapa guardado.
- **Localización:** comparar lo que ve el sensor con el **mapa guardado** para saber dónde está en
  ese mapa. La hace **AMCL**, que además corrige la deriva de la odometría.

!!! concepto "¿Qué es AMCL?"
    *Adaptive Monte Carlo Localization*. Reparte cientos de "partículas" (posibles posiciones del
    robot) sobre el mapa. Cuando el robot se mueve, las desplaza según la odometría y les da más
    peso a las que mejor explican lo que ve el LiDAR (las paredes que mide coinciden con las del
    mapa). Con el tiempo, las partículas se juntan en la posición real.

## 2.2 Marcos de referencia

Cada posición se expresa respecto de un **marco** (sistema de coordenadas). Los que usa este
documento:

| Marco | Qué es |
|---|---|
| `map` | El del mapa guardado: piso en z = 0, paredes alineadas con los ejes |
| `odom` | El de la odometría: arranca donde arrancó el robot y acumula deriva |
| `base_footprint` | El robot, sobre el piso y **sin inclinación**: solo gira alrededor de la vertical |
| `body` | El sensor (su IMU) |

AMCL publica la relación `map → odom`, que corrige la deriva; la odometría publica
`odom → base_footprint`. Juntas dicen dónde está el robot en el mapa.

!!! concepto "¿Por qué un marco sin inclinación?"
    Al caminar, el torso de un robot bípedo cabecea. Si las mediciones se calcularan en un marco que
    se inclina, el sensor "vería" el piso o el techo como si fueran paredes. `base_footprint` toma
    solo la posición en el plano y el giro, y descarta la inclinación.

## 2.3 Nav2 y los costmaps

**Nav2** (*Navigation 2*) es el sistema de navegación de ROS 2. Sus partes principales:

| Parte | Qué hace |
|---|---|
| Servidor de mapas | Carga el mapa 2D (`mapa_2d.pgm` + `.yaml`, el de la guía anterior) |
| AMCL | Localización (2.1) |
| Planificador | Calcula el camino desde donde está el robot hasta el destino |
| Controlador | Sigue el camino y calcula las velocidades (`cmd_vel`) a cada instante |
| Costmaps | Grillas que dicen por dónde se puede pasar |
| Monitor de colisiones | Freno de seguridad: reduce la velocidad o detiene si algo se cruza |

!!! concepto "¿Qué es un costmap?"
    Una grilla de celdas de 5 cm donde cada celda dice cuánto "cuesta" pasar: 0 = libre,
    100 = obstáculo, valores intermedios = cerca de un obstáculo (zona **inflada**, para no pasar
    rozando). Recibe la nube del LiDAR en vivo: lo que el sensor ve se **marca** y el espacio que
    los rayos atraviesan sin chocar se **borra**. Así aparece lo nuevo y desaparece lo que se fue.

## 2.4 Simulación

**Gazebo** es un simulador de robots: calcula la física y simula sensores (los rayos del LiDAR
chocan con las paredes del mundo virtual). Permite probar la navegación completa en la PC, sin
riesgo para el robot ni para las personas. En la simulación, Gazebo reemplaza al sensor y a la
odometría; Nav2 y su configuración son **los mismos** que se usan con el sensor real.
