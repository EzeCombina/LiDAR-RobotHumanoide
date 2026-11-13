# 1. Resumen

Esta guía explica, paso por paso, cómo poner en marcha el **LiDAR Unitree 4D L2** en una
computadora con **Ubuntu 24.04 y ROS 2 Jazzy**, desde el sensor recién sacado de la caja hasta
obtener el **mapa de una habitación**: un mapa 3D (nube de puntos) y un mapa 2D listo para el
sistema de navegación del robot.

Es parte del proyecto de **DataPyme** de programación del robot humanoide **Unitree R1 EDU**,
que se desarrolla en conjunto con la **UTN Facultad Regional San Francisco**. El LiDAR se va a montar sobre el
robot para que pueda mapear el lugar donde trabaja y, más adelante, navegar solo. Este documento
cubre la primera parte: aprender a usar el sensor y a generar mapas, llevándolo en la mano.

## 1.1 Qué se logra

- **Sensor funcionando en Ubuntu:** red configurada, datos verificados y diagnóstico del estado
  interno del sensor (motores, temperaturas, tensiones).
- **Driver de ROS 2** del sensor compilado y funcionando en Jazzy, con la nube de puntos en RViz.
- **Grabación** de los datos del sensor con controles automáticos (cortes de datos, arranque
  quieto).
- **Mapa 3D** del lugar con el SLAM Point-LIO, a partir de una grabación.
- **Productos para el robot:** mapa 3D limpio y nivelado, y **mapa 2D de ocupación** en el formato
  de Nav2.

Resultado obtenido con una habitación recorrida con el sensor en la mano: mapa de unos
3,2 × 7,9 m, con un **error de cierre de 10,5 cm** (diferencia entre el punto de llegada y el de
partida, que eran el mismo) y piso nivelado a menos de 1°.

## 1.2 Para quién es

Para estudiantes y docentes del laboratorio con conocimientos **básicos, medios o avanzados**. No
hace falta saber ROS 2 de antemano: los conceptos nuevos se explican en recuadros como este:

!!! concepto "Recuadro de concepto"
    Explicación breve de una idea nueva. Quien ya la conoce puede saltearla sin perder el hilo.

Los otros recuadros que aparecen en la guía:

!!! nota "Nota"
    Datos útiles, aclaraciones o dónde encontrar algo.

!!! importante "Importante"
    Algo que, si se pasa por alto, hace que el resultado salga mal.

!!! peligro "Peligro"
    Riesgo de dañar el sensor, la computadora o el robot.

## 1.3 Qué hace falta

- El **LiDAR Unitree L2** con su fuente de 12 V, el módulo adaptador y un cable Ethernet.
- Una **PC con Ubuntu 24.04** con un puerto Ethernet libre (capítulo 3).
- Conexión a internet para instalar el software, y acceso al repositorio del proyecto.
- Unas horas para la instalación y las primeras pruebas.

Todo el software propio del proyecto (scripts, configuraciones y documentación) está en el
repositorio `github.com/EzeCombina/LiDAR-RobotHumanoide`. Cada capítulo indica qué script usar y,
además, **cómo hacer lo mismo a mano**, para entender qué hace cada herramienta.

## 1.4 Alcance de esta versión

| Tema | Estado |
|---|---|
| Implementación en una PC con Ubuntu, conexión por **Ethernet** | Completo y verificado |
| Mapeo de una habitación con el sensor en la mano | Completo y verificado |
| Mapa 3D limpio y mapa 2D para Nav2 | Completo y verificado |
| Conexión por **USB** (modo serie del sensor) | Pendiente: herramientas listas, sin probar |
| Implementación en la **Jetson** del robot R1 | Próximo documento |
| Navegación autónoma, mapa en tiempo real, simulación en Gazebo | Próximo documento |

!!! nota "Dónde encontrar más detalle"
    La documentación de trabajo del proyecto está en el repositorio: `docs/pasos/` (un documento
    por paso), `docs/bitacora.md` (registro de cada sesión, con los errores encontrados y cómo se
    resolvieron) y `docs/versiones.md` (versiones exactas de todo lo usado).
