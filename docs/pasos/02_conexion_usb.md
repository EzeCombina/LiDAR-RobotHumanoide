# Paso 02 — Conexión del LiDAR por USB (modo serie)

> **Estado (2026-11-17):** documentado a partir del SDK, del manual y de pruebas parciales.
> **Verificado:** la PC reconoce el adaptador USB sin instalar nada, con los permisos correctos, y
> con el sensor en modo Ethernet no llegan datos por USB. **Pendiente de probar (A VERIFICAR):** el
> cambio de modo, el funcionamiento del driver por USB y la vuelta a Ethernet.

## Objetivo

Usar el LiDAR conectado a la PC por **USB** en lugar de Ethernet, saber cómo pasar de una conexión
a la otra y qué cambia en cada caso.

## ¿Se puede hacer lo mismo por USB que por Ethernet?

**Sí, en principio.** El driver de ROS 2 publica los mismos tópicos (`/unilidar/cloud` y
`/unilidar/imu`) con cualquiera de las dos conexiones. Todo lo que viene después del driver
(RViz, grabación, SLAM, mapas 3D y 2D) **no cambia**. Lo que cambia es la conexión física, la
configuración de la PC, cómo se lanza el driver y algunas herramientas de diagnóstico (punto 7).

Limitaciones a tener en cuenta:

| Tema | Ethernet | USB (serie) |
|---|---|---|
| Velocidad | 100 Mbit/s; el sensor usa unos 2 Mbit/s (medido) | 4 Mbit/s del puerto serie: los ~2 Mbit/s del sensor entran, pero con menos margen (sin pérdidas: A VERIFICAR) |
| Largo del cable | Hasta 100 m | Hasta unos 5 m (límite de USB 2.0) |
| Configuración de la PC | IP fija `192.168.1.2` y firewall (paso 01) | Ninguna: solo permiso de acceso al puerto (grupo `dialout`) |
| Uso en el robot R1 | **Sí**: es la conexión prevista | No |
| Puerto Ethernet de la PC | Queda ocupado por el sensor | Queda libre |

> **Un solo modo a la vez.** El sensor envía los datos **por Ethernet o por USB, nunca por los
> dos**. El modo queda guardado en el sensor (no se pierde al apagarlo) y para cambiarlo hay que
> enviarle una orden **por la conexión que está activa** y después **apagarlo y prenderlo**. De
> fábrica viene en Ethernet. Antes de montar el sensor en el robot, **dejarlo en modo Ethernet**.

## Requisitos

- Paso 01 completo (sensor funcionando por Ethernet y herramientas de `scripts/sensor/` compiladas,
  punto 5 del paso 01).
- El **módulo adaptador** del L2 con su puerto USB-C y un **cable USB-C de datos** (algunos cables
  solo cargan: con esos la PC no ve nada).
- La **fuente de 12 V** conectada siempre: el USB no alimenta al sensor.
- El usuario en el grupo `dialout` (permiso para usar puertos serie):

  ```bash
  id -nG | grep -w dialout          # si no aparece:
  sudo usermod -aG dialout $USER    # y cerrar la sesión de Ubuntu y volver a entrar
  ```

## 1. Reconocer el adaptador USB (verificado)

Al conectar el USB-C del módulo a la PC, Linux lo reconoce solo (no hay que instalar drivers):

```bash
lsusb | grep -i serial
ls -l /dev/serial/by-id/
journalctl -k --since "-5 min" --no-pager | grep -iE "ttyACM|usb .*Product"
```

**Salida obtenida** (2026-11-17):

```text
Bus 001 Device 003: ID 1a86:55d3 QinHeng Electronics USB Single Serial
lrwxrwxrwx 1 root root 13 nov 17 11:10 usb-1a86_USB_Single_Serial_5A2A026354-if00 -> ../../ttyACM0
nov 17 11:10:00 eze-laptop kernel: usb 1-2: Product: USB Single Serial
nov 17 11:10:00 eze-laptop kernel: cdc_acm 1-2:1.0: ttyACM0: USB ACM device
```

- El conversor es un **QinHeng (WCH) `1a86:55d3`** y usa el driver estándar `cdc_acm`.
- El puerto queda como **`/dev/ttyACM0`**. Si hay otros dispositivos serie conectados, puede tomar
  otro número (`ttyACM1`…). Para evitarlo, usar el **nombre fijo**, que incluye el número de serie
  del adaptador:
  `/dev/serial/by-id/usb-1a86_USB_Single_Serial_<número de serie>-if00` (en el adaptador del
  laboratorio: `...5A2A026354-if00`). Todas las herramientas de este paso aceptan el puerto como
  argumento.

## 2. ¿En qué modo está el sensor?

El sensor no tiene una consulta de "modo actual": se averigua viendo **por dónde llegan datos**.
Con la fuente conectada:

| Prueba | Si el sensor está en Ethernet | Si está en USB |
|---|---|---|
| `./scripts/red/verificar_udp_lidar.py` (cable Ethernet conectado y red del paso 01) | Recibe paquetes | `No llegó ningún paquete` |
| `./scripts/sensor/build/estado_lidar serie 5` (USB conectado) | `Serial port timeout` y ningún paquete | Muestra el estado del sensor |

**Salida obtenida** por USB con el sensor en modo Ethernet (2026-11-17):

```text
[WARNING] Serial port timeout!
[WARNING] Serial port timeout!

Paquetes recibidos por tipo:

No llegó ningún paquete de puntos: no hay estado para mostrar.
```

## 3. Pasar de Ethernet a USB

**Conexiones necesarias: fuente + cable Ethernet + USB-C**, las tres a la vez (la orden viaja por
Ethernet, que es el modo activo).

1. Detener el driver y cualquier programa que use el sensor.
2. Verificar que el sensor responde por Ethernet (`ping 192.168.1.62`).
3. Enviar el cambio de modo:

   ```bash
   cd ~/Documentos/LiDAR-RobotHumanoide
   ./scripts/sensor/build/cambiar_modo_lidar serie
   ```

   Salida esperada (según el programa; A VERIFICAR con el sensor):

   ```text
   Conectando por Ethernet: sensor 192.168.1.62:6101 -> PC 192.168.1.2:6201
   Comunicación confirmada.
     versión de hardware = 2.2.1.1
     versión de firmware = 2.8.11.1
     versión del SDK     = 2.0.9
   Enviando modo de trabajo 8 (serie / USB)...
   Listo. APAGAR Y PRENDER el sensor (desenchufar la fuente unos segundos)
   para que el cambio tome efecto.
   ```

   Si el sensor no responde en 10 s, el programa sale **sin cambiar nada**.
4. **Apagar y prender** el sensor: desenchufar la fuente unos segundos y volver a enchufarla.
5. Verificar con el punto 2: ahora los datos llegan por USB y no por Ethernet. Desde acá se puede
   desconectar el cable Ethernet.

> **Qué hace `cambiar_modo_lidar`:** se conecta por la interfaz activa, confirma la comunicación
> leyendo la versión de firmware y envía el modo de trabajo nuevo: **8** = serie/USB (bit 3 en 1)
> o **0** = Ethernet. Los demás bits quedan en 0 (campo de visión estándar, 3D, IMU activada,
> arranque automático). Los ejemplos `set_to_serial_mode` y `set_ip_address` del SDK **no** sirven
> para esto: tienen fijas IPs de otra red (`192.168.123.110`/`.120`) y el segundo cambia la IP del
> sensor.

**Alternativa con el driver de ROS 2** (A VERIFICAR): el driver envía al sensor el modo indicado en
su parámetro `work_mode` al arrancar. Conectado por Ethernet:

```bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
ros2 run unitree_lidar_ros2 unitree_lidar_ros2_node --ros-args -p initialize_type:=2 -p work_mode:=8
```

Esperar unos segundos, cortar con Ctrl+C y apagar y prender el sensor.

## 4. Usar el sensor por USB

**Conexiones: fuente + USB-C.** No hace falta configurar la red.

Lanzar el driver con `modo:=usb` (en lugar de `modo:=ethernet`):

```bash
tmux new -s lidar
source /opt/ros/jazzy/setup.bash
source ~/lidar_ws/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
cd ~/Documentos/LiDAR-RobotHumanoide
ros2 launch config/unitree_lidar_ros2/l2_driver.launch.py modo:=usb rviz:=false
# con el nombre fijo del puerto:
#   ... modo:=usb serial_port:=/dev/serial/by-id/usb-1a86_USB_Single_Serial_<serie>-if00
```

Verificar que publica como por Ethernet (A VERIFICAR: unos 12 Hz y 250 Hz):

```bash
ros2 topic hz /unilidar/cloud
ros2 topic hz /unilidar/imu
```

Desde acá, **todo sigue igual que por Ethernet**: RViz (paso 03), grabación (paso 04), SLAM
(paso 05), mapeo (paso 06) y productos del mapa (paso 07), con los mismos comandos.

> **Trampa del driver original:** el `launch.py` de Unitree trae `work_mode: 0`. Si se lo usa por
> USB (`initialize_type: 1`) sin cambiar también `work_mode` a 8, el driver le ordena al sensor
> volver a Ethernet y se corta la conexión USB. El launch del proyecto (`modo:=usb`) fija los dos
> valores juntos.

## 5. Volver de USB a Ethernet

**Conexiones necesarias: fuente + USB-C** (la orden viaja por USB). Conviene conectar también el
cable Ethernet para verificar al final.

```bash
./scripts/sensor/build/cambiar_modo_lidar ethernet                 # usa /dev/ttyACM0
./scripts/sensor/build/cambiar_modo_lidar ethernet /dev/serial/by-id/usb-1a86_USB_Single_Serial_<serie>-if00
```

Salida esperada: `Conectando por USB: /dev/ttyACM0 a 4000000 baudios`, `Comunicación confirmada.`,
las versiones y `Enviando modo de trabajo 0 (Ethernet / UDP)...` (A VERIFICAR). Después, **apagar y
prender** el sensor y verificar con el punto 2.

**Alternativa con el SDK** (A VERIFICAR): el ejemplo oficial `set_to_udp_mode` se conecta por
`/dev/ttyACM0` y envía el modo 0, así que sirve tal cual:

```bash
~/lidar_ws/unilidar_sdk2/unitree_lidar_sdk/bin/set_to_udp_mode
```

## 6. Diagnóstico por USB

| Herramienta | Por Ethernet | Por USB |
|---|---|---|
| ¿Llegan datos? | `./scripts/red/verificar_udp_lidar.py` | `./scripts/sensor/build/estado_lidar serie 5 [puerto]` |
| Estado interno (motores, temperaturas) | `estado_lidar udp 20` | `estado_lidar serie 20 [puerto]` |
| Ejemplo del SDK | `example_lidar_udp` | `example_lidar_serial` (usa `/dev/ttyACM0`; envía el modo 8, que es el que ya tiene) |
| ¿Se cortó la conexión? | `journalctl -k \| grep eno1` (`Link is Down`) | `ls /dev/ttyACM0` y `journalctl -k \| grep -i ttyACM` (al desconectar desaparece el puerto) |
| Aviso durante la grabación | `vigilar_datos.py` (igual para las dos) | `vigilar_datos.py` (igual para las dos) |

## 7. Resumen: qué cambia entre Ethernet y USB

| Qué | Ethernet | USB |
|---|---|---|
| Conexiones | Fuente + cable Ethernet | Fuente + USB-C |
| Modo guardado en el sensor | 0 | 8 |
| Configuración de la PC | `configurar_red_lidar.sh <placa>` (IP `192.168.1.2`, firewall) | Usuario en `dialout` |
| Lanzar el driver | `l2_driver.launch.py modo:=ethernet` | `l2_driver.launch.py modo:=usb [serial_port:=…]` |
| Herramientas de diagnóstico | Ver punto 6 | Ver punto 6 |
| Grabación, SLAM, mapas, RViz | Sin cambios | Sin cambios |
| Pasar a la otra conexión | `cambiar_modo_lidar serie` + apagar y prender | `cambiar_modo_lidar ethernet` + apagar y prender |

## Verificación final (A VERIFICAR)

- [ ] Con el sensor en USB, `estado_lidar serie 5` muestra el estado y `verificar_udp_lidar.py`
      no recibe nada.
- [ ] `ros2 topic hz /unilidar/cloud` da unos 12 Hz por USB, igual que por Ethernet.
- [ ] Una grabación por USB pasa `revisar_grabacion.py` sin huecos.
- [ ] El sensor vuelve a Ethernet con `cambiar_modo_lidar ethernet`.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| No aparece `/dev/ttyACM0` ni nada nuevo en `lsusb` | Cable USB-C no conectado o de solo carga | Probar con un cable de datos |
| `Permission denied` al abrir `/dev/ttyACM0` | El usuario no está en `dialout` | `sudo usermod -aG dialout $USER` y volver a iniciar sesión |
| `[WARNING] Serial port timeout!` y ningún paquete | El sensor está en modo Ethernet, o sin alimentación | Punto 2; pasar a USB con el punto 3 |
| `cambiar_modo_lidar`: `ERROR: el sensor no respondió en 10 s. NO se cambió el modo.` | Se intentó por la conexión que no está activa | Usar la otra conexión (punto 2) |
| `ERROR: no se pudo abrir el puerto UDP (¿la PC tiene la IP 192.168.1.2?)` al pasar a USB | El cable Ethernet no está conectado o la red no está configurada | Conectar el Ethernet (la orden viaja por ahí) |
| Al lanzar el driver por USB se corta la conexión | Se usó el launch original con `work_mode: 0` | Usar `modo:=usb` del launch del proyecto; si el sensor volvió a Ethernet, repetir el punto 3 |
| El puerto aparece como `ttyACM1` u otro número | Hay otros dispositivos serie conectados | Usar el nombre fijo de `/dev/serial/by-id/` |
| Fallas en los primeros segundos después de conectar el USB | **ModemManager** revisa el puerto al conectarlo (en el registro: `couldn't check support for device ... not supported by any plugin`) | Esperar unos segundos después de conectar. Si molesta, excluir el adaptador con una regla de udev (`ENV{ID_MM_DEVICE_IGNORE}="1"`; A VERIFICAR) |
| `Device or resource busy` | Otro programa usa el puerto (driver, `estado_lidar`) | Cerrarlo antes |
