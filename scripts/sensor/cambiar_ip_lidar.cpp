/* =============================================================================
 * cambiar_ip_lidar.cpp — Cambia la configuración de red del LiDAR Unitree L2
 * -----------------------------------------------------------------------------
 * Qué hace:
 *   El L2 guarda en su memoria su propia IP y la IP de DESTINO, la única
 *   computadora a la que envía los datos por UDP (de fábrica: sensor
 *   192.168.1.62 -> destino 192.168.1.2). Este programa:
 *     1. Valida las IPs nuevas (mismo /24, distintas entre sí y, en la red del
 *        robot 192.168.123.x, fuera de los bloques reservados por Unitree).
 *     2. Se conecta al sensor por Ethernet con la configuración ACTUAL.
 *     3. Confirma la comunicación leyendo la versión de firmware (si no responde
 *        en 10 s, sale sin cambiar nada).
 *     4. Pide confirmación y envía la configuración nueva con
 *        setLidarIpAddressConfig (máscara 255.255.255.0, puerta de enlace
 *        0.0.0.0 y puertos 6101 -> 6201, como el ejemplo set_ip_address del SDK).
 *   Después hay que APAGAR Y PRENDER el sensor para que el cambio tome efecto.
 *   Desde ese momento solo se lo puede ver desde una computadora con la IP de
 *   destino nueva.
 *
 *   Reemplaza al ejemplo set_ip_address del SDK, que trae las IPs fijas
 *   (192.168.123.110 -> 192.168.123.120) escritas en el código.
 *
 *   ESTADO: compilado, NO probado con el sensor (A VERIFICAR, ver
 *   docs/robot/pasos/01_lidar_en_el_robot.md).
 *
 * Cómo se usa:
 *   ./cambiar_ip_lidar <ip_sensor_nueva> <ip_destino_nueva> [ip_sensor_actual] [ip_pc_actual]
 *   (sin las dos últimas, se usa la red de fábrica 192.168.1.62 / 192.168.1.2)
 *
 *   Ejemplos:
 *   Red del robot R1 (destino: la Jetson, 192.168.123.164):
 *     ./cambiar_ip_lidar 192.168.123.62 192.168.123.164
 *   Volver a la red de fábrica, estando en la del robot (la PC con 192.168.123.164
 *   no se puede usar: hay que configurar la PC con la IP de destino actual):
 *     ./cambiar_ip_lidar 192.168.1.62 192.168.1.2 192.168.123.62 192.168.123.164
 *
 *   Opción -y al final: no pide confirmación (para usarlo desde otro script).
 *
 * Compilación: ver el encabezado de CMakeLists.txt de esta carpeta.
 *   El ejecutable queda en scripts/sensor/build/cambiar_ip_lidar.
 * ============================================================================= */

#include <arpa/inet.h>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <unistd.h>

#include "unitree_lidar_sdk.h"

using namespace unilidar_sdk2;

static const unsigned short PUERTO_SENSOR = 6101;
static const unsigned short PUERTO_DESTINO = 6201;

static void uso(const char *prog)
{
    printf("Uso:\n"
           "  %s <ip_sensor_nueva> <ip_destino_nueva> [ip_sensor_actual] [ip_pc_actual] [-y]\n"
           "Ejemplo (robot R1):\n"
           "  %s 192.168.123.62 192.168.123.164\n",
           prog, prog);
}

// Convierte "a.b.c.d" en 4 bytes. Devuelve false si no es una IPv4 válida.
static bool leerIp(const std::string &texto, uint8_t ip[4])
{
    in_addr dir;
    if (inet_pton(AF_INET, texto.c_str(), &dir) != 1)
        return false;
    memcpy(ip, &dir.s_addr, 4);  // s_addr está en orden de red: ip[0] = primer número
    return true;
}

// En la red del robot (192.168.123.x) Unitree usa .161 y .164 y, en otros
// modelos, los bloques .1–.30 y .120–.170 (ver la referencia del R1).
static bool reservadaEnRobot(const uint8_t ip[4])
{
    if (!(ip[0] == 192 && ip[1] == 168 && ip[2] == 123))
        return false;
    return ip[3] <= 30 || (ip[3] >= 120 && ip[3] <= 170);
}

// Espera hasta 'segundos' a que el sensor envíe su versión de firmware.
static bool confirmarComunicacion(UnitreeLidarReader *lector, int segundos)
{
    std::string firmware, hardware;
    auto inicio = std::chrono::steady_clock::now();
    while (!lector->getVersionOfLidarFirmware(firmware))
    {
        lector->runParse();
        if (std::chrono::steady_clock::now() - inicio > std::chrono::seconds(segundos))
            return false;
    }
    lector->getVersionOfLidarHardware(hardware);
    printf("Comunicación confirmada (hardware %s, firmware %s).\n",
           hardware.c_str(), firmware.c_str());
    return true;
}

int main(int argc, char *argv[])
{
    bool sin_confirmar = false;
    if (argc > 1 && std::string(argv[argc - 1]) == "-y")
    {
        sin_confirmar = true;
        argc--;
    }
    if (argc < 3 || argc > 5)
    {
        uso(argv[0]);
        return 1;
    }

    const std::string sensor_nueva = argv[1];
    const std::string destino_nueva = argv[2];
    const std::string sensor_actual = argc > 3 ? argv[3] : "192.168.1.62";
    const std::string pc_actual = argc > 4 ? argv[4] : "192.168.1.2";

    // --- Validación de la configuración nueva ------------------------------
    LidarIpAddressConfig config;
    memset(&config, 0, sizeof(config));
    if (!leerIp(sensor_nueva, config.lidar_ip) || !leerIp(destino_nueva, config.user_ip))
    {
        printf("ERROR: alguna de las IPs nuevas no es una dirección IPv4 válida.\n");
        return 1;
    }
    if (memcmp(config.lidar_ip, config.user_ip, 3) != 0)
    {
        printf("ERROR: el sensor y el destino tienen que estar en la misma red /24\n"
               "       (los tres primeros números iguales).\n");
        return 1;
    }
    if (config.lidar_ip[3] == config.user_ip[3])
    {
        printf("ERROR: la IP del sensor y la de destino no pueden ser iguales.\n");
        return 1;
    }
    if (config.lidar_ip[3] == 0 || config.lidar_ip[3] == 255 ||
        config.user_ip[3] == 0 || config.user_ip[3] == 255)
    {
        printf("ERROR: .0 y .255 no son direcciones de equipo.\n");
        return 1;
    }
    if (reservadaEnRobot(config.lidar_ip))
    {
        printf("ERROR: %s está en un bloque que Unitree usa en la red del robot\n"
               "       (.1-.30 y .120-.170). Elegir otra IP libre (comprobar con nmap).\n",
               sensor_nueva.c_str());
        return 1;
    }
    config.subnet_mask[0] = 255;
    config.subnet_mask[1] = 255;
    config.subnet_mask[2] = 255;
    config.subnet_mask[3] = 0;
    // Puerta de enlace 0.0.0.0, como el ejemplo del SDK: el sensor solo habla
    // con un equipo de su misma red y no la necesita.
    config.lidar_port = PUERTO_SENSOR;
    config.user_port = PUERTO_DESTINO;

    // --- Conexión con la configuración actual ------------------------------
    printf("Conectando por Ethernet: sensor %s:%u -> PC %s:%u\n", sensor_actual.c_str(),
           PUERTO_SENSOR, pc_actual.c_str(), PUERTO_DESTINO);
    UnitreeLidarReader *lector = createUnitreeLidarReader();
    if (lector->initializeUDP(PUERTO_SENSOR, sensor_actual, PUERTO_DESTINO, pc_actual))
    {
        printf("ERROR: no se pudo abrir el puerto UDP (¿la PC tiene la IP %s?).\n",
               pc_actual.c_str());
        return 1;
    }

    // Igual que los ejemplos del SDK: se arranca la rotación por si el sensor
    // estaba en espera (STANDBY) y no atendía comandos.
    lector->startLidarRotation();
    sleep(1);

    if (!confirmarComunicacion(lector, 10))
    {
        printf("ERROR: el sensor no respondió en 10 s. NO se cambió la red.\n"
               "Revisar alimentación, cable, la IP de la PC y que el sensor esté en modo Ethernet.\n");
        return 1;
    }

    printf("\nConfiguración nueva:\n"
           "  IP del sensor     : %s (puerto %u)\n"
           "  IP de destino     : %s (puerto %u)\n"
           "  Máscara           : 255.255.255.0\n"
           "  Puerta de enlace  : 0.0.0.0\n"
           "Después del cambio, el sensor SOLO envía datos a %s.\n",
           sensor_nueva.c_str(), PUERTO_SENSOR, destino_nueva.c_str(), PUERTO_DESTINO,
           destino_nueva.c_str());

    if (!sin_confirmar)
    {
        printf("¿Aplicar? Escribir SI y Enter: ");
        fflush(stdout);
        std::string respuesta;
        std::getline(std::cin, respuesta);
        if (respuesta != "SI")
        {
            printf("Cancelado. No se cambió nada.\n");
            return 1;
        }
    }

    lector->setLidarIpAddressConfig(config);
    sleep(1);

    printf("Listo. APAGAR Y PRENDER el sensor (desenchufar la fuente unos segundos)\n"
           "para que el cambio tome efecto. Anotar la configuración nueva en una etiqueta\n"
           "pegada al sensor.\n");
    return 0;
}
