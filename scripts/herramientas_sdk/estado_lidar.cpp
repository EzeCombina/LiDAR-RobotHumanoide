/* =============================================================================
 * estado_lidar.cpp — Muestra el estado interno del LiDAR Unitree L2
 * -----------------------------------------------------------------------------
 * Qué hace:
 *   Cada paquete de puntos que envía el L2 trae también su "estado interno"
 *   (estructura LidarInsideState del SDK). Este programa lo lee y muestra, una
 *   vez por segundo:
 *     - sys_rotation_period: motor de baja velocidad (giro horizontal del cabezal)
 *     - com_rotation_period: motor de alta velocidad (espejo, barrido vertical)
 *     - dirty_index: índice de suciedad de la ventana
 *     - packet_lost_up / packet_lost_down: pérdida de paquetes de las placas internas
 *     - apd_temperature, apd_voltage, laser_voltage, imu_temperature
 *   y, además, cuántos paquetes de cada tipo llegaron (puntos, IMU, etc.).
 *   Al final imprime un resumen con mínimo, promedio y máximo.
 *
 *   Son los mismos datos que mostraba el panel "Lidar Info" de Unilidar 2
 *   (programa de Windows que Unitree ya no ofrece para descargar). Sirve para diagnosticar el sensor (por
 *   ejemplo, si hace ruido: ver si los motores giran estables).
 *
 *   El programa SOLO ESCUCHA: no envía ningún comando de configuración, ni de
 *   rotación, ni de reinicio al sensor.
 *
 * Cómo se usa (cerrar antes el driver de ROS 2 u otro programa que use el puerto):
 *   ./estado_lidar udp                         # 10 s, IPs de fábrica
 *   ./estado_lidar udp 30                      # 30 s
 *   ./estado_lidar udp 10 192.168.10.62 192.168.10.2
 *   ./estado_lidar serie                       # 10 s por /dev/ttyACM0
 *   ./estado_lidar serie 20 /dev/ttyACM1
 *
 * Compilación: ver el encabezado de CMakeLists.txt de esta carpeta.
 * ============================================================================= */

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <map>
#include <string>
#include <vector>

#include "unitree_lidar_sdk.h"

using namespace unilidar_sdk2;
using reloj = std::chrono::steady_clock;

// Nombre legible de cada tipo de paquete (valores de unitree_lidar_protocol.h).
static const char *nombreTipo(int tipo)
{
    switch (tipo)
    {
    case LIDAR_ACK_DATA_PACKET_TYPE: return "respuesta (ACK)";
    case LIDAR_POINT_DATA_PACKET_TYPE: return "puntos 3D";
    case LIDAR_2D_POINT_DATA_PACKET_TYPE: return "puntos 2D";
    case LIDAR_IMU_DATA_PACKET_TYPE: return "IMU";
    case LIDAR_VERSION_PACKET_TYPE: return "versión";
    case LIDAR_TIME_STAMP_PACKET_TYPE: return "marca de tiempo";
    case LIDAR_WORK_MODE_CONFIG_PACKET_TYPE: return "config. modo de trabajo";
    case LIDAR_IP_ADDRESS_CONFIG_PACKET_TYPE: return "config. IP";
    case LIDAR_MAC_ADDRESS_CONFIG_PACKET_TYPE: return "config. MAC";
    case LIDAR_COMMAND_PACKET_TYPE: return "comando";
    case LIDAR_PARAM_DATA_PACKET_TYPE: return "parámetros";
    default: return "desconocido";
    }
}

// Acumula valores para calcular mínimo, promedio y máximo.
struct Serie
{
    std::vector<double> v;
    void agregar(double x) { v.push_back(x); }
    double min() const { return v.empty() ? 0 : *std::min_element(v.begin(), v.end()); }
    double max() const { return v.empty() ? 0 : *std::max_element(v.begin(), v.end()); }
    double prom() const
    {
        double s = 0;
        for (double x : v) s += x;
        return v.empty() ? 0 : s / v.size();
    }
};

static void uso(const char *p)
{
    printf("Uso:\n"
           "  %s udp   [segundos] [ip_lidar] [ip_pc]\n"
           "  %s serie [segundos] [puerto_serie]\n", p, p);
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        uso(argv[0]);
        return 1;
    }
    const std::string via = argv[1];
    const int segundos = argc > 2 ? std::stoi(argv[2]) : 10;

    UnitreeLidarReader *lector = createUnitreeLidarReader();
    int error;
    if (via == "udp")
    {
        std::string ip_lidar = argc > 3 ? argv[3] : "192.168.1.62";
        std::string ip_pc = argc > 4 ? argv[4] : "192.168.1.2";
        printf("Conectando por Ethernet: sensor %s:6101 -> PC %s:6201\n",
               ip_lidar.c_str(), ip_pc.c_str());
        error = lector->initializeUDP(6101, ip_lidar, 6201, ip_pc);
    }
    else if (via == "serie")
    {
        std::string puerto = argc > 3 ? argv[3] : "/dev/ttyACM0";
        printf("Conectando por USB: %s a 4000000 baudios\n", puerto.c_str());
        error = lector->initializeSerial(puerto, 4000000);
    }
    else
    {
        uso(argv[0]);
        return 1;
    }
    if (error)
    {
        printf("ERROR: no se pudo abrir la conexión.\n");
        return 1;
    }

    printf("Escuchando %d s (solo lectura, no se envían comandos)...\n\n", segundos);
    printf("seg | sys_rot | com_rot | dirty  | lost_up | lost_dn | T_apd | V_apd  | V_laser | T_imu | paq. puntos\n");

    std::map<int, long> tipos_total;
    Serie s_sys, s_com, s_dirty, s_lup, s_ldn, s_tapd, s_vapd, s_vlas, s_timu;
    long puntos_seg = 0;
    int seg = 0;
    auto inicio = reloj::now();
    auto proximo = inicio + std::chrono::seconds(1);
    LidarInsideState ultimo{};
    bool hay_estado = false;

    while (reloj::now() - inicio < std::chrono::seconds(segundos))
    {
        int tipo = lector->runParse();
        if (tipo > 0)
        {
            tipos_total[tipo]++;
            if (tipo == LIDAR_POINT_DATA_PACKET_TYPE)
            {
                const LidarInsideState &e = lector->getLidarPointDataPacket().data.state;
                ultimo = e;
                hay_estado = true;
                puntos_seg++;
                s_sys.agregar(e.sys_rotation_period);
                s_com.agregar(e.com_rotation_period);
                s_dirty.agregar(e.dirty_index);
                s_lup.agregar(e.packet_lost_up);
                s_ldn.agregar(e.packet_lost_down);
                s_tapd.agregar(e.apd_temperature);
                s_vapd.agregar(e.apd_voltage);
                s_vlas.agregar(e.laser_voltage);
                s_timu.agregar(e.imu_temperature);
            }
        }
        if (reloj::now() >= proximo)
        {
            if (hay_estado)
                printf("%3d | %7u | %7u | %6.3f | %7.3f | %7.3f | %5.1f | %6.2f | %7.2f | %5.1f | %ld\n",
                       seg, ultimo.sys_rotation_period, ultimo.com_rotation_period,
                       ultimo.dirty_index, ultimo.packet_lost_up, ultimo.packet_lost_down,
                       ultimo.apd_temperature, ultimo.apd_voltage, ultimo.laser_voltage,
                       ultimo.imu_temperature, puntos_seg);
            else
                printf("%3d | (todavía no llegaron paquetes de puntos)\n", seg);
            puntos_seg = 0;
            seg++;
            proximo += std::chrono::seconds(1);
        }
    }

    printf("\nPaquetes recibidos por tipo:\n");
    for (const auto &t : tipos_total)
        printf("  %5d  %-24s %8ld  (%.1f por segundo)\n", t.first, nombreTipo(t.first),
               t.second, (double)t.second / segundos);

    if (s_sys.v.empty())
    {
        printf("\nNo llegó ningún paquete de puntos: no hay estado para mostrar.\n");
        return 2;
    }

    printf("\nResumen del estado (%zu paquetes de puntos):\n", s_sys.v.size());
    printf("  %-20s %12s %12s %12s\n", "", "mínimo", "promedio", "máximo");
    auto fila = [](const char *n, const Serie &s) {
        printf("  %-20s %12.3f %12.3f %12.3f\n", n, s.min(), s.prom(), s.max());
    };
    fila("sys_rotation_period", s_sys);
    fila("com_rotation_period", s_com);
    fila("dirty_index", s_dirty);
    fila("packet_lost_up", s_lup);
    fila("packet_lost_down", s_ldn);
    fila("apd_temperature", s_tapd);
    fila("apd_voltage", s_vapd);
    fila("laser_voltage", s_vlas);
    fila("imu_temperature", s_timu);
    return 0;
}
