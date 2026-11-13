# Anexo C. Archivos del repositorio

Repositorio: `github.com/EzeCombina/LiDAR-RobotHumanoide`.

| Carpeta o archivo | Contenido |
|---|---|
| `README.md` | Presentación del proyecto, tabla de pasos y uso rápido |
| `docs/pasos/` | Un documento por paso (00 a 07), con comandos, salidas y problemas frecuentes |
| `docs/bitacora.md` | Registro de cada sesión de trabajo: qué se hizo, qué falló y cómo se resolvió |
| `docs/versiones.md` | Versiones exactas de todo lo instalado o descargado |
| `docs/grabaciones.md`, `docs/mapas.md` | Registro de grabaciones y mapas, y dónde están guardados |
| `docs/mediciones/` | Mediciones del sensor (vibración, estado interno) |
| `docs/referencias/` | Manuales oficiales del L2 y de Unilidar 2 |
| `docs/pdf/` | Fuente de este documento (`fuente/`) y el PDF (`salida/`) |
| `config/unitree_lidar_ros2/l2_driver.launch.py` | Launch del driver con `modo:=ethernet\|usb` |
| `config/rviz/` | Configuraciones de RViz para ver mapas 3D (`ver_mapa.rviz`) y 2D (`ver_mapa_2d.rviz`) |
| `scripts/sistema/` | `relevar_sistema.sh`: relevamiento del software instalado |
| `scripts/red/` | `configurar_red_lidar.sh`, `verificar_udp_lidar.py` |
| `scripts/sensor/` | Herramientas en C++ (`estado_lidar`, `cambiar_modo_lidar`) y `medir_vibracion_imu.py` |
| `scripts/grabacion/` | `grabar_lidar.sh`, `vigilar_datos.py`, `revisar_grabacion.py` |
| `scripts/mapas/` | `procesar_grabacion.sh`, `registrar_trayectoria.py`, `ver_mapa.sh`, `publicar_trayectoria.py`, `analizar_mapa.py`, `limpiar_mapa.py`, `generar_mapa_2d.py`, `ver_mapa_2d.sh`, `verificar_mapa_2d.py` |
| `scripts/documentacion/generar_pdf.py` | Genera este documento |
| `bags/` | Grabaciones (fuera de git) |
| `mapas/<fecha>_<nombre>/` | Un mapa por carpeta: `mapa.pcd` y `mapa_limpio.pcd` (fuera de git), resúmenes, trayectorias y mapa 2D |

Fuera del repositorio, en `~/lidar_ws/`: el SDK de Unitree (`unilidar_sdk2`, con el driver
compilado) y Point-LIO (`point_lio_ws`).

## C.1 Regenerar este documento

```bash
./scripts/documentacion/generar_pdf.py
```

Lee `docs/pdf/fuente/documento.yaml` (título, versión, fecha), los capítulos de
`docs/pdf/fuente/capitulos/` y los estilos de `docs/pdf/fuente/estilos.css`, y genera el PDF en
`docs/pdf/salida/`. Requiere `weasyprint` y `python3-markdown`.
