/* =============================================================================
 * cambiar_modo_lidar.cpp — Cambia el modo de comunicación del LiDAR Unitree L2
 * -----------------------------------------------------------------------------
 * Qué hace:
 *   El L2 guarda en su memoria un "modo de trabajo" (work mode). El bit 3 elige
 *   la interfaz de datos: 0 = Ethernet (UDP, valor de fábrica), 1 = serie (USB).
 *   Solo una interfaz está activa a la vez. Este programa:
 *     1. Se conecta al sensor por la interfaz que está activa AHORA.
 *     2. Confirma la comunicación leyendo la versión de firmware (si no responde
 *        en 10 s, sale sin cambiar nada).
 *     3. Envía el nuevo modo: 0 (Ethernet) u 8 (serie). El resto de los bits
 *        quedan en 0 = FOV estándar, 3D, IMU activada, arranque automático.
 *   Después hay que APAGAR Y PRENDER el sensor para que el cambio tome efecto.
 *
 *   Reemplaza a los ejemplos set_to_serial_mode / set_to_udp_mode del SDK, que
 *   traen IPs fijas (192.168.123.110/.120) distintas de las de fábrica.
 *
 * Cómo se usa:
 *   Pasar a serie (USB), conectado hoy por Ethernet:
 *     ./cambiar_modo_lidar serie                       # IPs de fábrica
 *     ./cambiar_modo_lidar serie 192.168.10.62 192.168.10.2   # IPs cambiadas
 *   Volver a Ethernet, conectado hoy por USB:
 *     ./cambiar_modo_lidar ethernet                    # puerto /dev/ttyACM0
 *     ./cambiar_modo_lidar ethernet /dev/ttyACM1
 *
 * Compilación (requiere el SDK clonado en ~/lidar_ws/unilidar_sdk2):
 *   cd scripts/cambiar_modo_lidar && mkdir -p build && cd build
 *   cmake .. && make
 *   (otra ubicación del SDK: cmake -DUNILIDAR_SDK_DIR=/ruta/unitree_lidar_sdk ..)
 *   El ejecutable queda en scripts/cambiar_modo_lidar/build/cambiar_modo_lidar.
 * ============================================================================= */

#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>
#include <unistd.h>

#include "unitree_lidar_sdk.h"

using namespace unilidar_sdk2;

static const uint32_t MODO_ETHERNET = 0;  // todos los bits en 0
static const uint32_t MODO_SERIE = 8;     // bit 3 en 1

static void uso(const char *prog)
{
    printf("Uso:\n"
           "  %s serie    [ip_lidar] [ip_pc]   (conectado hoy por Ethernet)\n"
           "  %s ethernet [puerto_serie]       (conectado hoy por USB)\n",
           prog, prog);
}

// Espera hasta 'segundos' a que el sensor envíe su versión de firmware.
static bool confirmarComunicacion(UnitreeLidarReader *lector, int segundos)
{
    std::string firmware, hardware, sdk;
    auto inicio = std::chrono::steady_clock::now();
    while (!lector->getVersionOfLidarFirmware(firmware))
    {
        lector->runParse();
        if (std::chrono::steady_clock::now() - inicio > std::chrono::seconds(segundos))
            return false;
    }
    lector->getVersionOfLidarHardware(hardware);
    lector->getVersionOfSDK(sdk);
    printf("Comunicación confirmada.\n"
           "  versión de hardware = %s\n"
           "  versión de firmware = %s\n"
           "  versión del SDK     = %s\n",
           hardware.c_str(), firmware.c_str(), sdk.c_str());
    return true;
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        uso(argv[0]);
        return 1;
    }

    const std::string destino = argv[1];
    UnitreeLidarReader *lector = createUnitreeLidarReader();
    uint32_t modo_nuevo;

    if (destino == "serie")
    {
        // Hoy el sensor está en Ethernet: se conecta por UDP.
        std::string ip_lidar = argc > 2 ? argv[2] : "192.168.1.62";
        std::string ip_pc = argc > 3 ? argv[3] : "192.168.1.2";
        printf("Conectando por Ethernet: sensor %s:6101 -> PC %s:6201\n",
               ip_lidar.c_str(), ip_pc.c_str());
        if (lector->initializeUDP(6101, ip_lidar, 6201, ip_pc))
        {
            printf("ERROR: no se pudo abrir el puerto UDP (¿la PC tiene la IP %s?).\n",
                   ip_pc.c_str());
            return 1;
        }
        modo_nuevo = MODO_SERIE;
    }
    else if (destino == "ethernet")
    {
        // Hoy el sensor está en serie: se conecta por el puerto USB.
        std::string puerto = argc > 2 ? argv[2] : "/dev/ttyACM0";
        printf("Conectando por USB: %s a 4000000 baudios\n", puerto.c_str());
        if (lector->initializeSerial(puerto, 4000000))
        {
            printf("ERROR: no se pudo abrir %s (¿está conectado? ¿permisos de dialout?).\n",
                   puerto.c_str());
            return 1;
        }
        modo_nuevo = MODO_ETHERNET;
    }
    else
    {
        uso(argv[0]);
        return 1;
    }

    // Igual que los ejemplos del SDK: se arranca la rotación por si el sensor
    // estaba en espera (STANDBY) y no atendía comandos.
    lector->startLidarRotation();
    sleep(1);

    if (!confirmarComunicacion(lector, 10))
    {
        printf("ERROR: el sensor no respondió en 10 s. NO se cambió el modo.\n"
               "Revisar alimentación, cable y que el sensor esté en el modo de origen.\n");
        return 1;
    }

    printf("Enviando modo de trabajo %u (%s)...\n", modo_nuevo,
           modo_nuevo == MODO_SERIE ? "serie / USB" : "Ethernet / UDP");
    lector->setLidarWorkMode(modo_nuevo);
    sleep(1);

    printf("Listo. APAGAR Y PRENDER el sensor (desenchufar la fuente unos segundos)\n"
           "para que el cambio tome efecto.\n");
    return 0;
}
