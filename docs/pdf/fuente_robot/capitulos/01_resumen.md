# 1. Resumen

Este documento continúa la guía **Implementación del LiDAR Unitree L2** (versión 0.1.2), que
explica cómo usar el sensor en una PC con Ubuntu y obtener el mapa de una habitación. Acá se usa
ese mapa y el LiDAR para que el robot humanoide **Unitree R1 EDU** se mueva solo. Los dos objetivos
de esta etapa:

1. **Reconocer un mapa ya hecho y moverse por él.** El robot recibe el mapa de una zona, se ubica
   en él (aunque arranque sin saber exactamente dónde está) y va de un punto a otro.
2. **Esquivar obstáculos con el LiDAR en tiempo real.** Mientras se mueve, usa la nube del sensor
   en vivo para ver lo que no está en el mapa (una persona, una silla, una caja) y lo rodea.

Es parte del proyecto de **DataPyme** de programación del robot humanoide Unitree R1 EDU, que se
desarrolla en conjunto con la **UTN Facultad Regional San Francisco**.

El robot todavía no está disponible. Por eso todo se implementó y se probó **sin el robot**:

- con **grabaciones reales** del sensor, reproducidas como si estuviera en vivo (capítulos 9 y 10);
- en **simulación** con Gazebo: un robot del tamaño del R1, con un LiDAR como el L2, dentro de un
  mundo hecho a partir de un mapa 2D (capítulo 11).

La conexión con la computadora del robot (capítulos 3 a 6) y el último eslabón, el envío de las
velocidades a la marcha del R1 (capítulo 12), quedan documentados y **pendientes de validar**.

## 1.1 Resultados

| Prueba | Resultado |
|---|---|
| **Objetivo 1** con una grabación real de la habitación | Error medio de posición **0,12 m**; arrancando con una pose equivocada (0,5 m y 20°), **se corrigió solo** en 31 s |
| Objetivo 1 con la grabación de la oficina | **Falla**: con ese mapa (80 % desconocido, recorrido de menos de 1 m²) se pierde |
| **Objetivo 2** con una grabación real (persona caminando) | El costmap ve a la persona (prueba cualitativa) |
| **Objetivos 1 y 2 juntos**, en simulación | **4 de 4** corridas llegaron al destino; esquivaron la caja que apareció en el camino (a 0,68–0,71 m); error de ubicación de **5–6 cm** |
| Puente hacia la marcha del R1 | Límites y parada por falta de órdenes verificados; envío al R1 sin probar |

## 1.2 Para quién es

Para estudiantes y docentes con conocimientos **básicos, medios o avanzados**. Se supone que se
siguió la guía anterior: el sensor funciona en una PC y hay un mapa de un lugar. Los conceptos
nuevos se explican en el capítulo 2 y en recuadros:

!!! concepto "Recuadro de concepto"
    Explicación breve de una idea nueva. Quien ya la conoce puede saltearla sin perder el hilo.

!!! importante "Importante"
    Algo que, si se pasa por alto, hace que el resultado salga mal.

!!! peligro "Peligro"
    Riesgo de dañar el sensor, el robot o a una persona.

Todo dato sin comprobar está marcado **A VERIFICAR**.

## 1.3 Qué hace falta

- La PC y el sensor de la guía anterior, con Point-LIO compilado y al menos un mapa.
- Para las pruebas de este documento: solo la PC (con aceleración gráfica, para la simulación).
- Para el robot: el **Unitree R1 EDU**, un **conversor DC-DC de 24 V a 12 V** de 2 A o más, un
  **switch Ethernet** chico y un soporte para el sensor.

## 1.4 Alcance de esta versión

| Tema | Estado |
|---|---|
| Ubicarse en un mapa guardado (objetivo 1) | Implementado; verificado con grabaciones y en simulación |
| Obstáculos en tiempo real (objetivo 2) | Implementado; verificado en simulación, cualitativo con grabaciones |
| Conexión, red y software en la Jetson del robot | Documentado; **pendiente de validar con el robot** |
| Envío de velocidades al R1 | Programado; **pendiente de probar con el robot** |
| Mapa que se actualiza mientras navega | Trabajo futuro |

!!! nota "Documentación de trabajo"
    El detalle de cada paso está en el repositorio, en `docs/robot/` (pasos R00 a R06), separado de
    la primera etapa (`docs/pasos/`). La bitácora (`docs/bitacora.md`) registra los errores
    encontrados y cómo se resolvieron.
