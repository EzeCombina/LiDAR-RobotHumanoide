# Formato del documento PDF final

El documento final sigue el **mismo formato y la misma identidad** que la documentación técnica de
referencia: `docs/referencias/formato/Referencia_formato_Documentacion_Firmware_PLC14_v0.0.5.pdf`.
**Es un documento de DataPyme**, con sus colores y su logo, hecho **en colaboración con la UTN
Facultad Regional San Francisco**, que figura con su logo (decisión del usuario, 2026-11-13).
Del documento de referencia se toman el diseño y la marca; **no** su contenido (textos del firmware
del PLC).

## Identidad

- **Marca:** DataPyme.
  - Logo de portada: `assets/logo_datapyme.png` (cuadrado verde con el símbolo y "DataPyme" en
    blanco), extraído del PDF de referencia. Va directo sobre la banda verde de la portada.
  - Ícono del encabezado: `assets/logo_datapyme_icono.png` (cuadrado verde redondeado con el
    símbolo en blanco), extraído del PDF de referencia.
- **Colaboración con la UTN FRSF:** tiene que figurar en la portada y en el pie de página.
  - Portada: en la zona blanca, debajo de la tabla de datos, "Proyecto realizado en colaboración
    con la **UTN Facultad Regional San Francisco**" y el logo `assets/logo_utn_frsf.png`. Como el
    logo de la UTN tiene letras negras, **siempre va sobre fondo blanco**.
  - Pie de las páginas interiores (centro): "En colaboración con la UTN Facultad Regional San
    Francisco". Pie de la portada (derecha): "Documentación técnica · En colaboración con la UTN
    FRSF".
- **Colores** (los del documento de referencia):
  - Principal (verde DataPyme): `#108550`. Banda de portada, títulos, encabezados de tabla, línea
    del encabezado y pie.
  - Secundario (verde claro): `#4FB585`. Detalles: viñetas y recuadros de concepto.
  - Texto: gris muy oscuro (`#24242B`). Filas alternas de tablas: gris muy claro (`#F4F6F9`).
- **Tipografía:** sans serif limpia (Open Sans) para el texto y monoespaciada (DejaVu Sans Mono)
  para comandos y código.

## Página A4 y márgenes

A4 vertical, márgenes de unos 18 mm a los costados. Las páginas interiores tienen encabezado y pie.

## Portada

1. **Banda superior de color principal** que ocupa unos dos tercios de la hoja, a todo el ancho.
2. Centrado dentro de la banda, el **logo de DataPyme**.
3. Debajo, en blanco y centrado:
   - **Título** grande y en negrita (ej. "Implementación del LiDAR Unitree L2");
   - **subtítulo** en tamaño mediano y peso liviano (ej. "Del sensor nuevo al mapa de una
     habitación");
   - una **línea horizontal fina**;
   - una línea descriptiva (ej. "Guía de implementación para el robot humanoide Unitree R1 EDU");
   - **"Versión X.Y.Z"** en negrita.
4. **Zona blanca inferior** con una tabla de metadatos de dos columnas, sin bordes: la etiqueta en
   negrita y en color principal, el valor en texto normal. Debajo, la colaboración con la UTN y su
   logo (ver "Identidad"). Filas sugeridas:
   - Proyecto: Programación del robot humanoide Unitree R1 EDU
   - Colaboración: UTN Facultad Regional San Francisco
   - Equipo: Unitree 4D LiDAR L2 · PC con Ubuntu 24.04 + ROS 2 Jazzy
   - Repositorio: github.com/EzeCombina/LiDAR-RobotHumanoide (privado)
   - Autor: Ezequiel Combina
   - Fecha: mes y año
5. **Pie de la portada:** banda fina de color principal, con "DataPyme" en negrita a la izquierda y
   "Documentación técnica · En colaboración con la UTN FRSF" a la derecha, en blanco.

## Páginas interiores

- **Encabezado:** a la izquierda, el ícono de DataPyme (unos 8 mm). Al lado, en gris y tamaño
  chico: "Título corto · Tema · vX.Y.Z". Debajo, una **línea de color principal** a todo el ancho.
- **Pie:** línea fina gris clara; a la izquierda "DataPyme" en negrita y color principal; al centro
  "En colaboración con la UTN Facultad Regional San Francisco" en gris; a la derecha "Página N".
- **Títulos de capítulo (h1):** grandes, en negrita y color principal (ej. "1. Resumen"). Cada
  capítulo empieza en página nueva.
- **Subtítulos (h2):** medianos, en negrita y color principal (ej. "2.1 Conexión de red").
- **Texto:** unos 10 pt, interlineado cómodo.
- **Listas:** viñetas simples, con la frase clave en negrita al principio.

## Índice ("Contenido")

Página propia después de la portada, con el título "Contenido". Capítulos en negrita con líneas de
puntos hasta el número de página. Subsecciones en texto normal más chico, sangradas, también con
puntos. Los anexos al final ("Anexo A. …").

## Tablas

- Encabezado con **fondo de color principal y texto blanco en negrita**.
- Filas con línea separadora fina y fondo alterno gris muy claro.
- Primera columna en negrita cuando es la "clave" (parámetro, síntoma, archivo).
- Nombres de archivos, comandos, parámetros e IPs en **monoespaciada y en color principal**.

## Recuadros de aviso

Recuadro de fondo suave con una **barra vertical gruesa a la izquierda** y un título en negrita:

| Tipo | Uso | Fondo / barra / título |
|---|---|---|
| Importante | Advertencias generales | ámbar claro / ámbar oscuro |
| Peligro | Riesgo de dañar el equipo (tensión, polaridad) o el robot | rosado claro / rojo |
| Nota o "Dónde encontrar…" | Datos útiles, aclaraciones | azul muy claro / color principal |
| Concepto | Explicación breve para principiantes (qué es un tópico, una nube de puntos, SLAM) | celeste muy claro / color secundario |

## Bloques de código y salidas

Recuadro de **fondo gris muy claro con borde fino**, letra monoespaciada chica. Para salidas de
consola, mostrarlas tal cual, en el orden en que aparecen.

## Estructura sugerida del contenido

1. Resumen (qué se logra, para quién es, qué hace falta)
2. Conceptos básicos (LiDAR, nube de puntos, IMU, ROS 2, tópicos, bags, SLAM, mapas 2D y 3D)
3. Materiales y requisitos (hardware y software, con versiones)
4. Instalación del entorno
5. Conexión y puesta en marcha del sensor
6. Driver de ROS 2 y visualización
7. Grabación de datos
8. SLAM y generación del mapa 3D
9. Mapeo de una habitación (procedimiento de recorrido)
10. Procesamiento del mapa: limpieza, mapa 2D, mundo de Gazebo
11. Implementación en la Jetson del robot (pendiente de validar)
12. Problemas frecuentes
13. Trabajo futuro: el mapa en el robot, navegación, mapa en tiempo real
- Anexo A. Parámetros (launch, yaml)
- Anexo B. Versiones de todo lo usado
- Anexo C. Archivos del repositorio
- Anexo D. Referencias
