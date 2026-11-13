# 3. Materiales y requisitos

## 3.1 El sensor: Unitree 4D LiDAR L2

| Característica | Valor |
|---|---|
| Campo de visión | 360° × 90° (semiesfera por encima de la base); 360° × 96° en modo de ángulo negativo |
| Puntos por segundo | 64.000 (unas 12 nubes por segundo) |
| Distancia de medición | 0,05 a 30 m (con 90 % de reflectividad) |
| IMU | Integrada, unas 250 mediciones por segundo, con los ejes paralelos a los de la nube |
| Alimentación | **12 V DC**, 1 A; 10 W típicos, picos de 13 W mientras se calienta |
| Interfaces de datos | Ethernet (UDP, modo de fábrica) o serie UART por USB (un solo modo activo a la vez) |
| Fijación | 4 tornillos M3 en la base |
| Peso y medidas | 230 g; 75 × 75 × 65 mm |
| Sistema de coordenadas | Origen en el centro de la cara inferior; eje +X opuesto a la salida del cable |

Fuentes: manual oficial del L2 (v1.1) y manual de Unilidar 2 (v1.0), guardados en
`docs/referencias/`.

### Contenido de la caja

- El sensor, con su cable de salida.
- Un **módulo adaptador** con tres conectores: entrada de alimentación (plug DC de 3,5 × 1,35 mm),
  **RJ45** (Ethernet) y **USB-C** (modo serie).
- Una **fuente de 12 V / 1 A**.
- Una **almohadilla de goma** para apoyar el sensor mientras se lo prueba.

!!! peligro "Alimentación: solo 12 V"
    El L2 se alimenta con **12 V**. No conectarlo nunca a 24 V ni a 36 V (por ejemplo, a las
    salidas XT30 del robot R1): para usarlo en el robot hace falta un conversor DC-DC a 12 V.

### Versiones del sensor del laboratorio

| Dato | Valor |
|---|---|
| Hardware | 2.2.1.1 |
| Firmware | 2.8.11.1 |
| Red de fábrica | Sensor `192.168.1.62` → envía los datos a `192.168.1.2`, puertos UDP 6101 → 6201 |

## 3.2 La computadora

Cualquier PC con **Ubuntu 24.04 LTS** y arquitectura x86_64 sirve. Lo importante:

- **Un puerto Ethernet libre**, que queda dedicado al sensor. Internet se usa por Wi-Fi o por
  otra placa.
- **Espacio en disco:** unos 10 GB para el software, más unos **120 MB por minuto** de grabación.
- **Placa de video:** cualquiera que maneje RViz (el visualizador 3D).

PC usada para esta guía:

| Elemento | Valor |
|---|---|
| Procesador / memoria | AMD Ryzen 5 4600H (12 hilos) / 22 GiB |
| Sistema | Ubuntu 24.04.5 LTS, kernel 7.0.0-42 |
| ROS 2 | Jazzy (`ros-jazzy-desktop` 0.11.0) |
| Compilador | gcc 13.3.0, CMake 3.28.3, Python 3.12.3 |

## 3.3 Software

| Componente | Origen | Uso |
|---|---|---|
| **ROS 2 Jazzy** | Paquetes oficiales (apt) | Base de todo: comunicación, RViz, grabación |
| **SDK del L2** (`unilidar_sdk2` v2.0.10) | `github.com/unitreerobotics/unilidar_sdk2` | Librería del sensor, ejemplos y **driver ROS 2** |
| **Point-LIO** (`point_lio_ros2`) | `github.com/dfloreaa/point_lio_ros2` | SLAM: genera el mapa 3D |
| **Nav2 map server** | Paquetes oficiales (apt) | Cargar y verificar el mapa 2D |
| Scripts del proyecto | Repositorio `EzeCombina/LiDAR-RobotHumanoide` | Red, diagnóstico, grabación, mapas |

Las versiones exactas (paquetes y *commits* de cada repositorio) están en el **Anexo B**.

!!! nota "Jazzy y el driver de Unitree"
    Unitree verificó su driver de ROS 2 solo en Ubuntu 20.04 con ROS 2 Foxy, y el autor de
    Point-LIO para ROS 2, en Ubuntu 22.04 con Humble. En este proyecto se comprobó que **ambos
    compilan y funcionan sin cambios en Ubuntu 24.04 con Jazzy**: no hace falta usar contenedores
    ni otra versión de ROS 2.

## 3.4 Software de Windows (Unilidar 2)

Unitree ofrecía un programa para Windows, **Unilidar 2**, para ver la nube y configurar el sensor.
A noviembre de 2026 **ya no se puede descargar** de su página. Todo lo que hacía (ver la nube,
consultar el estado, cambiar de modo) se hace en esta guía con el SDK y herramientas propias en
Ubuntu.
