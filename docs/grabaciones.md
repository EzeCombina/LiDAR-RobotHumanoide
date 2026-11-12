# Registro de grabaciones

Las grabaciones (`rosbag2`, formato MCAP) **no se suben a git** por su tamaño. Este archivo indica
qué grabaciones existen y dónde están guardadas. Cada grabación tiene además un `descripcion.txt` en
su carpeta (lo genera `scripts/grabar_lidar.sh`).

Ubicación por defecto: `bags/` dentro del repositorio, en la PC `eze-laptop`.

| Carpeta | Fecha | Duración | Tamaño | Tópicos | Descripción | Dónde está |
|---|---|---|---|---|---|---|
| `2026-11-12_1016_sala_quieta` | 2026-11-12 10:16 | 89,45 s | 184 MB | cloud 1071 (11,97/s), imu 22409 (250,5/s) | Grabación de referencia 1, sensor quieto (detalle de la escena: A CONFIRMAR; en `descripcion.txt` quedó "...") | `bags/` en `eze-laptop` |
