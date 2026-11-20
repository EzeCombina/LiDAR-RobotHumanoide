# Paso R06 — Puente hacia la marcha del R1 (cmd_vel → LocoClient)

## Objetivo

Llevar las velocidades que calcula Nav2 (`/cmd_vel`) a la marcha de alto nivel del R1, con límites
de velocidad y un **watchdog** que detiene el robot si dejan de llegar órdenes.

**Estado (2026-11-20):** límites y watchdog **verificados** en modo simulado. El envío al R1 real
está **sin probar**: los nombres del SDK de Unitree para el R1 son **A VERIFICAR**.

## Requisitos

- Paso R02. Para el robot real: `unitree_sdk2_python` instalado en la máquina que corre el puente
  (A VERIFICAR la instalación en la Jetson) y el robot en modo de marcha normal.

## 1. Qué hace

`scripts/navegacion/puente_cmd_vel_r1.py`:

1. Recibe `/cmd_vel` (velocidad hacia adelante `linear.x`, de costado `linear.y` y de giro
   `angular.z`) y **limita** cada una: por defecto −0,10 a 0,30 m/s, ±0,10 m/s y ±0,60 rad/s.
2. Envía la última orden a 20 Hz con `LocoClient.Move(vx, vy, vyaw)`.
3. **Watchdog:** si no llega un `/cmd_vel` en 0,5 s, llama a `StopMove()` y no vuelve a mover el
   robot hasta que lleguen órdenes nuevas.
4. Al cerrarse (Ctrl+C o error), llama a `StopMove()`.
5. Usa solo la marcha de **alto nivel**; nunca el control de bajo nivel (`rt/lowcmd`) ni el de
   brazos (`rt/arm_sdk`, que según la referencia del R1 puede bloquear la locomoción).

## 2. Prueba sin el robot (modo simulado)

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/navegacion/puente_cmd_vel_r1.py --simular &
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.8, y: -0.5}, angular: {z: 2.0}}"      # cortar con Ctrl+C a los 4 s
```

**Salida obtenida** (2026-11-20):

```text
[INFO] [puente_cmd_vel_r1]: límites: vx -0.1..0.3 m/s, |vy| <= 0.1 m/s, |wz| <= 0.6 rad/s; watchdog 0.5 s; SIMULADO
[simulado] Move(vx=+0.30 m/s, vy=-0.10 m/s, vyaw=+0.60 rad/s)
[simulado] Move(vx=+0.30 m/s, vy=-0.10 m/s, vyaw=+0.60 rad/s)
[simulado] Move(vx=+0.30 m/s, vy=-0.10 m/s, vyaw=+0.60 rad/s)
[simulado] Move(vx=+0.30 m/s, vy=-0.10 m/s, vyaw=+0.60 rad/s)
[WARN] [puente_cmd_vel_r1]: WATCHDOG: sin /cmd_vel hace más de 0.5 s -> StopMove()
[simulado] StopMove()
```

Se pidió 0,8 m/s, −0,5 m/s y 2,0 rad/s: el puente envió 0,30, −0,10 y 0,60 (los límites). Al cortar
las órdenes, el watchdog detuvo el robot. (En modo simulado escribe como mucho una línea por
segundo, aunque envíe a 20 Hz.)

## 3. Con el robot (A VERIFICAR)

!!! peligro "Primeras pruebas"
    Robot en su soporte o con una persona con el control remoto en la mano, lista para detenerlo;
    parada de emergencia externa cableada; área despejada; velocidades mínimas. Nunca mover el
    robot por Wi-Fi sin el watchdog.

```bash
# En la Jetson (o en la PC conectada por cable a la red del robot)
./scripts/navegacion/puente_cmd_vel_r1.py --interfaz <interfaz con 192.168.123.x> --vx-max 0.15 --wz-max 0.3
# Primera prueba: órdenes a mano, unos segundos
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}"
```

Orden sugerido:

1. Robot en el soporte, patas libres: órdenes a mano muy lentas; comprobar el sentido de cada eje y
   que el watchdog lo detiene al cortar `ros2 topic pub`.
2. Robot en el piso, con el control remoto en la mano: órdenes a mano.
3. Nav2 completo (R01, sección 6) con velocidades mínimas, en un lugar despejado y mapeado con el
   robot.

Puntos **A VERIFICAR** con el robot:

- Módulo y clase del SDK para el R1 (`unitree_sdk2py.r1.loco.r1_loco_client.LocoClient` según la
  referencia) y si `Move`/`StopMove` tienen esos nombres y argumentos.
- Si el SDK (usa su propio CycloneDDS, dominio 0) y ROS 2 pueden convivir en el mismo proceso. Si
  no, separar: un proceso ROS 2 que reenvía las órdenes por un canal simple a otro proceso con el SDK.
- Las velocidades máximas reales de la marcha del R1 y su respuesta (retardo) a las órdenes.

## Verificación final

- [ ] En modo simulado, los valores enviados respetan los límites.
- [ ] El watchdog escribe `StopMove()` a los 0,5 s de cortar las órdenes.
- [ ] (Robot) El robot se detiene al cortar las órdenes y al cerrar el puente.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: unitree_sdk2py` | SDK de Unitree no instalado | Instalar `unitree_sdk2_python` (A VERIFICAR el procedimiento en la Jetson) o usar `--simular` |
| El robot no responde | Interfaz equivocada o robot fuera del modo de marcha | Revisar `--interfaz` (la que tiene la red 192.168.123.x) y el modo del robot |
