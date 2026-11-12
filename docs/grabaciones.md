# Registro de grabaciones

Las grabaciones (`rosbag2`, formato MCAP) **no se suben a git** por su tamaño. Este archivo indica
qué grabaciones existen y dónde están guardadas. Cada grabación tiene además un `descripcion.txt` en
su carpeta (lo genera `scripts/grabacion/grabar_lidar.sh`).

Ubicación por defecto: `bags/` dentro del repositorio, en la PC `eze-laptop`.

| Carpeta | Fecha | Duración | Tamaño | Tópicos | Descripción | Dónde está |
|---|---|---|---|---|---|---|
| `2026-11-12_1016_sala_quieta` | 2026-11-12 10:16 | 89,45 s | 184 MB | cloud 1071 (11,97/s), imu 22409 (250,5/s) | Grabación de referencia 1, sensor quieto (detalle de la escena: A CONFIRMAR; en `descripcion.txt` quedó "...") | `bags/` en `eze-laptop` |
| `2026-11-12_1028_persona_caminando` | 2026-11-12 10:28 | 59,47 s | 123 MB | cloud 712 (11,97/s), imu 14882 (250,2/s) | Grabación de referencia 2, sensor fijo con una persona caminando alrededor (detalle de la escena: A CONFIRMAR; en `descripcion.txt` quedó "...") | `bags/` en `eze-laptop` |
| `2026-11-12_1333_departamento_vertical` | 2026-11-12 13:33 | 135,10 s | 243 MB | cloud 1621 (12,0/s, intervalo máx. 84,5 ms), imu 33884 (250,8/s) | Recorrido con el sensor **vertical**, cúpula hacia adelante, en una habitación del departamento del usuario (confirmado: no se salió de la habitación) | `bags/` en `eze-laptop` |
