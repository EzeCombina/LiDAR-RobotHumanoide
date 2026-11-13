# 2. Conceptos básicos

Este capítulo reúne las ideas que se usan en toda la guía. Quien ya trabajó con LiDAR y ROS 2
puede pasar directamente al capítulo 3.

## 2.1 LiDAR

Un **LiDAR** (*Light Detection And Ranging*) mide distancias con pulsos de luz láser: emite un
pulso, lo recibe reflejado y calcula la distancia por el tiempo que tardó en volver. Para medir en
muchas direcciones, mueve el haz.

El **L2** tiene dos motores:

- uno de **alta velocidad** que hace girar un espejo y barre en vertical (216 veces por segundo);
- uno de **baja velocidad** que hace girar todo el cabezal y barre en horizontal.

Así cubre una **semiesfera de 360° × 90°** por encima de su base y mide unos **64.000 puntos por
segundo**, de 5 cm a 30 m de distancia.

!!! importante "El L2 solo ve hacia arriba de su base"
    Apoyado horizontal, con la cúpula hacia arriba, ve paredes y techo pero **no ve el piso** ni
    nada que esté más abajo que él. Esto influye en cómo conviene llevarlo para mapear
    (capítulo 9).

## 2.2 Nube de puntos

Cada medición del LiDAR es un **punto** con coordenadas X, Y, Z (en metros) y una intensidad
(cuánta luz volvió). El conjunto de puntos de un barrido se llama **nube de puntos**. El L2 entrega
unas 12 nubes por segundo, de unos 4.000 a 5.000 puntos cada una.

Las coordenadas de cada nube están expresadas **respecto del sensor en ese instante**: el punto
(0, 0, 0) es el centro de la base del sensor.

## 2.3 IMU

El L2 trae una **IMU** (*Inertial Measurement Unit*, unidad de medición inercial): un acelerómetro
y un giróscopo que miden cómo se mueve el sensor, unas 250 veces por segundo. Con el sensor quieto,
el acelerómetro mide la **gravedad** (unos 9,8 m/s²), y eso indica hacia dónde está "abajo".

## 2.4 ROS 2: nodos, tópicos y mensajes

**ROS 2** (*Robot Operating System 2*) no es un sistema operativo: es un conjunto de librerías y
herramientas para que distintos programas de un robot intercambien datos.

- Un **nodo** es un programa (por ejemplo, el driver del LiDAR).
- Un **tópico** es un canal con nombre por el que un nodo **publica** mensajes y otros nodos los
  **reciben** (se **suscriben**). El driver del L2 publica la nube en `/unilidar/cloud` y la IMU en
  `/unilidar/imu`.
- Un **mensaje** tiene un tipo fijo: la nube es `sensor_msgs/PointCloud2` y la IMU,
  `sensor_msgs/Imu`.
- Cada versión de ROS 2 se llama **distribución** (Foxy, Humble, **Jazzy**…) y corresponde a una
  versión de Ubuntu. Esta guía usa **Jazzy** con **Ubuntu 24.04**.

**RViz** es el visualizador 3D de ROS 2: se suscribe a los tópicos y los dibuja.

## 2.5 Marcos de referencia

Cada dato indica en qué sistema de coordenadas (**marco**, *frame*) está expresado. La nube del L2
está en el marco `unilidar_lidar` y los mapas, en el marco `map`. ROS 2 publica las relaciones entre
marcos en el tópico `/tf`.

## 2.6 Grabaciones (rosbag)

Un **rosbag** es un archivo donde ROS 2 guarda los mensajes de uno o varios tópicos, con su hora
exacta. Después se puede **reproducir**: ROS 2 vuelve a publicar los mensajes como si el sensor
estuviera conectado. En Jazzy el formato es **MCAP** (`.mcap`). Grabar permite generar el mapa
después, en la PC, y repetir el procesamiento con otros parámetros sin volver a recorrer el lugar.

## 2.7 SLAM

Si el sensor se mueve, las nubes no se pueden sumar directamente: cada una está expresada respecto
del sensor en su propio instante. Un **SLAM** (*Simultaneous Localization And Mapping*,
localización y mapeo simultáneos) calcula **dónde está el sensor** en cada momento (su
**trayectoria**) y, con eso, ubica todas las nubes en un mismo sistema de coordenadas y las suma en
un **único mapa**.

Esta guía usa **Point-LIO**, un SLAM que combina la nube del LiDAR con la IMU (*LiDAR-Inertial
Odometry*).

## 2.8 Mapas 3D y 2D

- **Mapa 3D:** la nube de puntos de todo el lugar, en un archivo `.pcd` (*Point Cloud Data*). Sirve
  para ver el lugar, medirlo y, en el futuro, para ubicar al robot en 3D.
- **Mapa 2D de ocupación:** una grilla vista desde arriba, como una hoja cuadriculada, donde cada
  celda está **ocupada** (negro), **libre** (blanco) o **desconocida** (gris). Se guarda como una
  imagen (`.pgm`) más un archivo con la escala (`.yaml`). Es el formato que usa **Nav2**, el
  sistema de navegación de ROS 2, para que el robot se ubique y planifique sus recorridos.
