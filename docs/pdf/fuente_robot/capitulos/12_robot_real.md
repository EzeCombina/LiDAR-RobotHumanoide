# 12. Con el robot real

Todo este capítulo está **pendiente de probar con el robot**.

## 12.1 Puente hacia la marcha del R1

Nav2 pide velocidades en el tópico `/cmd_vel`. El R1 no entiende ROS: su marcha se maneja con el SDK
de Unitree (`LocoClient.Move` y `LocoClient.StopMove`). `scripts/navegacion/puente_cmd_vel_r1.py`:

1. **Limita** cada velocidad (por defecto −0,10 a 0,30 m/s hacia adelante, ±0,10 m/s de costado y
   ±0,60 rad/s de giro), aunque Nav2 pida más.
2. Envía la última orden a 20 Hz.
3. **Parada automática (watchdog):** si no llega una orden en 0,5 s (Nav2 se colgó, se cortó la red),
   detiene el robot con `StopMove()`.
4. Al cerrarse, detiene el robot.
5. Solo usa la marcha de alto nivel, nunca el control de bajo nivel ni el de los brazos.

Probado en modo simulado, sin el robot:

```bash
./scripts/navegacion/puente_cmd_vel_r1.py --simular &
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.8, y: -0.5}, angular: {z: 2.0}}"      # cortar con Ctrl+C a los 4 s
```

```text
[simulado] Move(vx=+0.30 m/s, vy=-0.10 m/s, vyaw=+0.60 rad/s)
[WARN] [puente_cmd_vel_r1]: WATCHDOG: sin /cmd_vel hace más de 0.5 s -> StopMove()
[simulado] StopMove()
```

Se pidió 0,8, −0,5 y 2,0; se enviaron los límites. Al cortar las órdenes, se detuvo.

**A VERIFICAR** con el robot: el nombre del módulo del SDK para el R1
(`unitree_sdk2py.r1.loco.r1_loco_client.LocoClient`, según la documentación disponible), los
argumentos de `Move` y si el SDK y ROS 2 pueden funcionar en el mismo programa.

## 12.2 Navegar con el robot

```bash
# En la Jetson: driver corriendo (capítulo 6) y el robot PARADO Y QUIETO al lanzar
ros2 launch scripts/navegacion/navegacion.launch.py modo:=navegacion montaje:=robot \
    mapa:=mapas/<carpeta> inicio:=<x>,<y>,<yaw> rviz:=false
# En otra terminal
./scripts/navegacion/puente_cmd_vel_r1.py --interfaz <interfaz con 192.168.123.x> --vx-max 0.15 --wz-max 0.3
```

!!! peligro "Primeras pruebas"
    Robot en su soporte o con una persona con el control remoto en la mano, lista para detenerlo;
    parada de emergencia externa cableada; área despejada y velocidades mínimas. Nunca mover el
    robot por Wi-Fi sin la parada automática.

Orden sugerido:

1. Robot en el soporte, patas libres: órdenes a mano (`ros2 topic pub`) muy lentas; comprobar el
   sentido de cada eje y que se detiene al cortar las órdenes.
2. Robot en el piso, con el control remoto en la mano: órdenes a mano.
3. Navegación completa con velocidades mínimas, en un lugar despejado y **mapeado con el robot**.

## 12.3 Lista de verificación

| Tema | Qué verificar |
|---|---|
| Jetson | Modelo, JetPack, Ubuntu, ROS, Docker, espacio en disco |
| Red | Nombre de la interfaz con la `.164`; IPs libres (`nmap -sn`); firewall |
| Alimentación | Conector y polaridad del XT30; salida del conversor medida antes de enchufar |
| Conexión | Switch con el sensor y la PC a la vez; datos del sensor en la Jetson |
| Montaje | Soporte terminado; posición y orientación medidas y cargadas en `montaje_robot.yaml`; caja del cuerpo |
| Navegación | Mapa grabado con el robot; AMCL ubicado; puente probado en el soporte |

## 12.4 Trabajo futuro

- **Mapa que se actualiza mientras navega** (SLAM en línea). Hoy, la corrección de rutas ya funciona
  con el costmap en vivo, sin necesidad de un SLAM en línea.
- **Localización 3D** sobre el `.pcd`, si AMCL resulta poco confiable en lugares con muchos muebles.
- Decidir si todo corre **a bordo** (Jetson) o en una PC por Wi-Fi: medir la carga de Point-LIO y
  Nav2 en la Jetson.
