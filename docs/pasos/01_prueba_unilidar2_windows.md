# Paso 01 — Primera prueba del sensor con Unilidar 2 (Windows)

> **Estado:** redactado a partir del *Unilidar 2 User Manual* v1.0 (2024.11). **Pendiente de
> validar** con el equipo del laboratorio: completar los valores y las capturas marcadas como
> A VERIFICAR.

## Objetivo

Comprobar que el LiDAR L2 funciona **antes de instalar nada en Ubuntu**, con el programa oficial de
Unitree. Al terminar se sabe que:

- el sensor enciende, gira y entrega una nube de puntos coherente con el lugar;
- los motores, las temperaturas y las tensiones internas están en valores normales;
- se conocen las versiones de hardware y firmware y la configuración de fábrica.

Si algo falla en este paso, el problema es del sensor, del cable o de la fuente, no de Linux ni de
ROS 2.

## Requisitos

- PC con **Windows de 64 bits** (Unilidar 2 no existe para Linux ni para Mac). El manual recomienda
  una placa de video con buen rendimiento por la visualización 3D.
- Programa **Unilidar 2**. Según el manual del L2, se descarga desde
  `https://www.unitree.com/download`. **A VERIFICAR:** en la página del L2 consultada el
  2026-11-12 no aparecía el instalador; si no está, pedirlo al vendedor o al soporte de Unitree.
- LiDAR L2 con su módulo adaptador, fuente de 12 V / 1 A y cable Ethernet.
- La **almohadilla de goma** incluida en la caja.
- Multímetro (para la polaridad de la fuente, ver paso 02, punto 1.1).

> **¿Qué es un LiDAR?** Un sensor que mide distancias con pulsos de luz láser. El L2 tiene dos
> motores: uno de **alta velocidad** que hace girar un espejo (barrido vertical, 216 Hz según el
> manual) y uno de **baja velocidad** que hace girar todo el cabezal (barrido horizontal, 5,55 Hz).
> Así cubre una semiesfera de 360° × 90° y mide 64.000 puntos por segundo.

## 1. Preparar el sensor

1. Medir la polaridad de la fuente antes de conectarla (paso 02, punto 1.1).
2. Apoyar el L2 sobre la **almohadilla de goma**, y la almohadilla sobre una superficie **plana y
   firme**. El manual lo pide expresamente para que el sensor funcione estable.
3. Conectar el cable Ethernet del módulo adaptador a la PC con Windows y la fuente al módulo. El
   sensor arranca y gira solo.

## 2. Configurar la red en Windows

El sensor envía sus datos a la IP `192.168.1.2`. La placa Ethernet de Windows tiene que tener esa
dirección:

1. *Configuración* → *Red e Internet* → *Ethernet* → *Asignación de IP* → *Editar* → *Manual*.
2. Activar IPv4 y completar:
   - Dirección IP: `192.168.1.2`
   - Máscara de subred: `255.255.255.0` (longitud de prefijo 24)
   - Puerta de enlace: `192.168.1.1` (es lo que indica el manual; dejarla vacía no impide recibir
     los datos y evita que Windows intente salir a internet por esa placa — A VERIFICAR)
3. Guardar.

> Si el Wi-Fi de esa PC también está en una red `192.168.1.x`, hay choque de redes (ver paso 02).

La primera vez que se abre Unilidar 2, el firewall de Windows puede preguntar si se permite el
acceso a la red: **permitirlo**, o los datos no van a llegar (A VERIFICAR).

## 3. Conectarse con Unilidar 2

1. Ejecutar `Unilidar 2.exe` **como administrador** (clic derecho → *Ejecutar como
   administrador*), como indica el manual del L2.
2. En el recuadro superior izquierdo:
   - seleccionar **UDPMode**;
   - *Select UDP IP*: `192.168.1.2`;
   - *Select UDP Port*: `6201`;
   - clic en **Open UDP Port**. El campo *LIDAR IP Port* debe mostrar `192.168.1.62:6101`.
3. La nube de puntos aparece en la parte derecha. Rueda del mouse: acercar y alejar. Botón
   izquierdo o flechas del teclado: girar la vista.

**Resultado esperado:** se reconocen las paredes, el piso y los objetos del lugar.

Captura: **A VERIFICAR** (guardar en `docs/pasos/img/01_unilidar2_nube.png`).

## 4. Revisar el estado del sensor

### 4.1 Versiones (pestaña *Version*)

Clic en **GetVersion**. Si aparecen los datos, la comunicación es correcta.

| Campo | Valor esperado (sensor del laboratorio, leído con el SDK en el paso 02) |
|---|---|
| HW_Version | 2.2.1.1 |
| SW_Version | 2.8.11.1 |
| Name / Data | A VERIFICAR |

### 4.2 Estado interno (pestaña *Lidar Info*)

| Campo | Significado (según el manual) | Valor medido |
|---|---|---|
| `sys_rotation_period` | Velocidad del motor de baja velocidad (horizontal) | A VERIFICAR |
| `com_rotation_period` | Velocidad del motor de alta velocidad (espejo) | A VERIFICAR |
| `dirty_index` | Índice de suciedad de la ventana | A VERIFICAR |
| `packet_lost_up` / `packet_lost_down` | Pérdida de paquetes de las placas internas | A VERIFICAR |
| `apd_temperature` | Temperatura del fotodetector (APD), en °C | A VERIFICAR |
| `apd_voltage` | Tensión del APD, en V | A VERIFICAR |
| `laser_voltage` | Tensión del emisor láser, en V | A VERIFICAR |
| `imu_temperature` | Temperatura de la IMU | A VERIFICAR |

> El manual dice que las velocidades están en revoluciones por minuto, pero los nombres de los
> campos dicen *period* (período). Las unidades reales se verifican comparando con
> `estado_lidar` (paso 02). A VERIFICAR.

Los mismos datos se pueden leer desde Ubuntu con la herramienta del proyecto
`scripts/herramientas_sdk/estado_lidar` (paso 02).

### 4.3 IMU

En la parte inferior izquierda se ven el cuaternión (Q1–Q4), la aceleración (ACC1–ACC3) y la
velocidad angular (GYRO1–GYRO3). Con el sensor quieto:

- la aceleración total debe ser de unos 9,8 m/s² (la gravedad), casi toda en el eje Z;
- la velocidad angular debe estar cerca de 0.

### 4.4 Configuración de fábrica (pestañas *Work Mode* y *Config Setting*)

Clic en **Synchronous** para leer la configuración actual del sensor y anotarla:

| Parámetro | Valor de fábrica según los manuales | Valor leído |
|---|---|---|
| ENET/UART Select | ENET | A VERIFICAR |
| Work Mode (Normal / NEGA) | **Contradicción:** el manual de Unilidar 2 dice NEGA; el del L2 y el SDK dicen modo normal | A VERIFICAR |
| 3D/2D Mode | 3D | A VERIFICAR |
| Power On mode | SELF START | A VERIFICAR |
| Gray Enable | Gray ON | A VERIFICAR |
| IP del sensor / destino | `192.168.1.62` → `192.168.1.2`, puertos 6101 → 6201 | A VERIFICAR |

> **No tocar `SetMode`, `Change` ni `Restore Factory Defaults` en esta prueba.** Esos botones
> guardan cambios en el sensor. En particular, pasar a **UART** deja al sensor sin datos por
> Ethernet (el cambio de modo se explica en el paso 03).

## Verificación final

- [ ] La nube de puntos se ve y coincide con el lugar.
- [ ] *GetVersion* responde con las versiones de hardware y firmware.
- [ ] *Lidar Info* muestra valores estables (anotarlos en la tabla 4.2).
- [ ] Con el sensor quieto, la IMU marca unos 9,8 m/s² y una velocidad angular cercana a 0.
- [ ] El sensor no hace ruidos anormales (raspado, golpeteo, traqueteo).

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| No aparece la nube después de *Open UDP Port* | La placa de Windows no tiene la IP `192.168.1.2`, o el firewall bloquea | Revisar la IP (`ipconfig` en una consola) y permitir Unilidar 2 en el firewall |
| *GetVersion* no responde | Sin comunicación | Revisar cables y fuente; el manual pide una fuente de 12 V / 1 A |
| El sensor no aparece por Ethernet | Está en modo serie (UART) | Conectarse por USB (*SerialMode*, puerto COM) y volver a ENET |
| No se recuerda la IP del sensor | Se cambió antes | Conectarse por USB y usar *Restore Factory Defaults* (manual de Unilidar 2) |
| El sensor dejó de girar después de un golpe o de frenarlo con la mano | Estado de interferencia | Se recupera solo al soltarlo; si no, reiniciarlo |
| Ruido fuerte o vibración al girar | Posible problema mecánico | Ver la bitácora del 2026-11-12; medir el estado de los motores y consultar al soporte de Unitree |
