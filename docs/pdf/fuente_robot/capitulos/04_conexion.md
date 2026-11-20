# 4. Conexión física

```text
 L2 ──RJ45──► switch ──► RJ45 del panel ──► red interna ──► Jetson (192.168.123.164)
                 │
                 └──► PC (solo para arrancar y detener la grabación)

 L2 ◄── plug DC 12 V ◄── conversor DC-DC 24 → 12 V ◄── XT30 de 24 V del panel
```

## 4.1 Alimentación

!!! peligro "El L2 es de 12 V"
    Las salidas XT30 del robot son de **24 V y 36 V**. Conectar el sensor directo **lo daña**.
    Siempre a través de un conversor DC-DC.

!!! concepto "¿Qué es un conversor DC-DC?"
    Un circuito que transforma una tensión continua en otra: acá, los 24 V del robot en los 12 V
    del sensor. Se elige por la tensión de entrada, la de salida y la corriente máxima que puede
    entregar.

- Desde el XT30 de **24 V / 3 A**, un conversor **24 V → 12 V de 2 A o más**. El sensor consume
  1 A típico, con picos de 13 W mientras se calienta.
- Salida del conversor a un plug **DC 3,5 × 1,35 mm**, con la misma polaridad que se midió en la
  fuente original del sensor (guía anterior, capítulo 5).
- **Medir con el multímetro la salida del conversor antes de enchufar el sensor.**
- Si el switch es de 12 V, puede alimentarse del mismo conversor (sumar su consumo).
- Conector y polaridad del XT30: **A VERIFICAR** con el robot.

## 4.2 Datos: un solo RJ45

El panel tiene **un solo RJ45**. Lo necesita el sensor y también la PC, para entrar a la Jetson.

| Opción | Cómo | Estado |
|---|---|---|
| **A. Switch chico (recomendada)** | Switch de 5 puertos sobre el robot: panel, sensor y un puerto libre para la PC | **A VERIFICAR** |
| B. Wi-Fi de la Jetson | Sensor en el RJ45 y PC por Wi-Fi | **A VERIFICAR** (no se sabe si la Jetson tiene Wi-Fi propio) |
| C. Sensor por USB | Sensor en modo serie (guía anterior, punto 5.7) al USB-C del panel | **A VERIFICAR** (no se sabe si ese USB-C va a la Jetson) |

Con la opción A, la PC solo se conecta para arrancar y detener la grabación: durante el recorrido
se desenchufa, porque todo corre en `tmux` en la Jetson.

!!! importante "Switch, no router"
    Un switch **no administrable** solo reparte el tráfico: no tiene IP ni DHCP y no cambia la red
    del robot. Un **router** sí: su DHCP interrumpiría la red interna.

## 4.3 Conectar la PC y mapear la red

La PC necesita una IP fija en la red del robot. Se crea un perfil aparte, llamado `r1`, sin
puerta de enlace (el perfil `lidar-l2` de la guía anterior queda como está). Cambiar `eno1` por el
nombre de la placa de la PC:

```bash
sudo nmcli connection add type ethernet ifname eno1 con-name r1 \
    ipv4.method manual ipv4.addresses 192.168.123.51/24
sudo nmcli connection up r1
ping -c 3 192.168.123.164
```

Después, ver qué equipos hay en la red, para confirmar que la IP elegida para el sensor está libre:

```bash
sudo apt install -y nmap
nmap -sn 192.168.123.0/24
```

`nmap -sn` solo pregunta qué IPs responden; no modifica nada. Para quitar el perfil de la PC:
`sudo nmcli connection delete r1`.

## 4.4 Dónde y cómo montar el sensor (A VERIFICAR)

El L2 ve una **semiesfera hacia su cúpula** (360° × 90°). Eso decide el montaje:

| Montaje | Ve | Sirve para |
|---|---|---|
| Derecho (cúpula arriba) sobre la cabeza | Paredes y techo; **nada por debajo de su altura** | Mapear; **no** para esquivar obstáculos bajos |
| Invertido (cúpula abajo) sobre la cabeza | Piso y obstáculos alrededor, pero el propio cuerpo le tapa el piso cercano | Parcial |
| **Invertido y adelantado** 0,20 m respecto del torso | Piso y obstáculos delante y a los costados | **Navegar** (propuesta provisoria) |

La propuesta provisoria es la tercera, a unos 1,55 m del piso. Así están configurados el robot
(`config/navegacion/montaje_robot.yaml`) y la simulación (capítulo 11). Cuando exista el soporte,
se miden en el CAD la posición y la orientación reales y se reemplazan esos valores.

