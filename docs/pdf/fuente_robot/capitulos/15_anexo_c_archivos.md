# Anexo C. Archivos de esta etapa

Repositorio: `github.com/EzeCombina/LiDAR-RobotHumanoide`. Esta etapa está separada de la primera.

| Carpeta o archivo | Contenido |
|---|---|
| `docs/robot/` | Documentación de trabajo: `README.md` y los pasos R00 a R06 |
| `docs/pdf/fuente_robot/` | Fuente de este documento |
| `scripts/navegacion/navegacion.launch.py` | Lanzamiento: modos `localizacion`, `navegacion`, `obstaculos` |
| `scripts/navegacion/base_nivelada.py` | Odometría del robot desde Point-LIO |
| `scripts/navegacion/filtro_cuerpo.py` | Quita de la nube los puntos del propio robot |
| `scripts/navegacion/probar_con_grabacion.sh` | Pruebas con grabaciones |
| `scripts/navegacion/evaluar_localizacion.py`, `evaluar_obstaculos.py` | Evaluadores |
| `scripts/navegacion/puente_cmd_vel_r1.py` | Puente hacia la marcha del R1 |
| `scripts/simulacion/crear_sala_de_prueba.py` | Mapa 2D de la sala de prueba |
| `scripts/simulacion/generar_mundo_gazebo.py` | Mundo de Gazebo desde un mapa 2D |
| `scripts/simulacion/simulacion.launch.py`, `probar_navegacion_sim.py` | Simulación y prueba automática |
| `scripts/sensor/cambiar_ip_lidar.cpp` | Cambia la red del sensor (capítulo 5) |
| `config/navegacion/` | Parámetros de Nav2, montajes, configuraciones de RViz |
| `config/simulacion/` | Robot simplificado y puente Gazebo ↔ ROS 2 |
| `mapas/sala_de_prueba/` | Mapa 2D y mundo de la sala de prueba |
| `resultados/` | Resultados de las pruebas: una carpeta por prueba |
