# 5. Red del sensor para el robot

El sensor guarda en su memoria **su propia IP** y la **IP de destino**: la única computadora a la
que envía los datos. Para el robot se cambian a `192.168.123.62` → `192.168.123.164`.

Todo este capítulo **se puede hacer sin el robot**, con el sensor y la PC de la guía anterior.

## 5.1 La herramienta `cambiar_ip_lidar`

El SDK trae un ejemplo (`set_ip_address`) con las IPs escritas en el código y sin controles. El
proyecto tiene su propia herramienta, `scripts/sensor/cambiar_ip_lidar`, que:

1. Recibe las IPs nuevas como argumentos y las valida: misma red, distintas entre sí y, si es la
   red del robot, fuera de los bloques reservados (capítulo 3).
2. Se conecta al sensor con su red **actual** y confirma que responde (si no, sale sin cambiar nada).
3. Muestra la configuración nueva y pide escribir `SI` antes de enviarla.

Se compila junto con las otras herramientas del sensor (guía anterior, capítulo 5):

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor
mkdir -p build && cd build
cmake .. && make
```

Los controles de los argumentos están verificados (no tocan el sensor):

```text
$ ./cambiar_ip_lidar 192.168.123.150 192.168.123.164
ERROR: 192.168.123.150 está en un bloque que Unitree usa en la red del robot
       (.1-.30 y .120-.170). Elegir otra IP libre (comprobar con nmap).
$ ./cambiar_ip_lidar 192.168.123.62 192.168.124.164
ERROR: el sensor y el destino tienen que estar en la misma red /24
```

!!! importante "No probada con el sensor"
    La herramienta compila y valida bien las IPs, pero todavía no cambió la red de un sensor real.
    El ensayo de la sección 5.2 es la prueba pendiente.

## 5.2 Ensayo en la PC, sin el robot (A VERIFICAR)

La PC hace de "Jetson": se le pone la IP `192.168.123.164` en su placa del LiDAR. Es una IP de la
**PC**, así que no hay riesgo para el robot; hacerlo lejos del robot, porque dos equipos con la
misma IP en la misma red chocan.

**Paso 1.** Con el sensor en la red de fábrica y el driver detenido, cambiar su red:

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor/build
./cambiar_ip_lidar 192.168.123.62 192.168.123.164
```

```text
Conectando por Ethernet: sensor 192.168.1.62:6101 -> PC 192.168.1.2:6201
Comunicación confirmada (hardware 2.2.1.1, firmware 2.8.11.1).
Configuración nueva:
  IP del sensor     : 192.168.123.62 (puerto 6101)
  IP de destino     : 192.168.123.164 (puerto 6201)
...
¿Aplicar? Escribir SI y Enter: SI
```

**Paso 2.** **Apagar y prender** el sensor (desenchufar la fuente unos segundos).

**Paso 3.** Cambiar la IP de la PC con el script de la guía anterior (pide `sudo` solo para el
firewall):

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/red/configurar_red_lidar.sh eno1 192.168.123.164/24
```

**Paso 4.** Verificar y lanzar el driver con las IPs nuevas:

```bash
ping -c 3 192.168.123.62
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=ethernet rviz:=false \
    lidar_ip:=192.168.123.62 local_ip:=192.168.123.164
ros2 topic hz /unilidar/cloud        # en otra terminal: unos 10 Hz
```

**Paso 5.** Si el sensor va al robot, dejarlo así y **pegarle una etiqueta** con la red nueva.

## 5.3 Volver a la red de fábrica

La PC tiene que estar con la IP de destino **actual** del sensor para poder hablarle:

```bash
cd ~/Documentos/LiDAR-RobotHumanoide/scripts/sensor/build
./cambiar_ip_lidar 192.168.1.62 192.168.1.2 192.168.123.62 192.168.123.164
# apagar y prender el sensor
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/red/configurar_red_lidar.sh eno1          # la PC vuelve a 192.168.1.2/24
ping -c 3 192.168.1.62
```

!!! nota "Si no se sabe qué red tiene el sensor"
    Conectarlo directo a la PC y mirar qué paquetes envía: `sudo tcpdump -i eno1 -n -c 5`. La IP
    de origen es la del sensor y la de destino es la que tiene que tener la PC.
