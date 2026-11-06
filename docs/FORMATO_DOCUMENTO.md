# Formato del documento PDF final

El documento final sigue el **mismo formato** que la documentación técnica de referencia que entregó
el usuario: la "Documentación Firmware PLC14 v0.0.5", que **no está en este repositorio** porque es un
documento de otra empresa. Este archivo describe ese formato adaptado a la identidad de la **UTN
Facultad Regional San Francisco**.

## Identidad

- **Proyecto colaborativo con la UTN Facultad Regional San Francisco.** Debe figurar en la portada
  y en el pie de página.
- **Logo:** `assets/logo_utn_frsf.png` (614 × 115 px, fondo transparente, letras negras y azules).
  Como tiene letras negras, **siempre va sobre un recuadro blanco**: nunca directo sobre el fondo
  oscuro.
- **Colores** (tomados del logo):
  - Principal (azul marino): `#2A4470`. Para la banda de portada, títulos, encabezados de tabla y el
    pie.
  - Secundario (celeste): `#61A5D8`. Para detalles: líneas finas y viñetas.
  - Texto: gris muy oscuro (`#24242B`). Filas alternas de tablas: gris muy claro (`#F4F6F9`).
- **Tipografía:** sans serif limpia (por ejemplo Open Sans o Noto Sans) para el texto y monoespaciada
  (DejaVu Sans Mono o similar) para comandos y código.

## Página A4 y márgenes

A4 vertical, márgenes de unos 18 mm a los costados. Las páginas interiores tienen encabezado y pie.

## Portada

1. **Banda superior de color principal** que ocupa unos dos tercios de la hoja, a todo el ancho.
2. Centrado dentro de la banda, un **recuadro blanco con el logo de la UTN FRSF**.
3. Debajo, en blanco y centrado:
   - **Título** grande y en negrita (ej. "Implementación del LiDAR Unitree L2");
   - **subtítulo** en tamaño mediano y peso liviano (ej. "Del sensor nuevo al mapa de una
     habitación");
   - una **línea horizontal fina**;
   - una línea descriptiva (ej. "Guía de implementación para el robot humanoide Unitree R1 EDU");
   - **"Versión X.Y.Z"** en negrita.
4. **Zona blanca inferior** con una tabla de metadatos de dos columnas, sin bordes: la etiqueta en
   negrita y en color principal, el valor en texto normal. Filas sugeridas:
   - Proyecto: Programación del robot humanoide Unitree R1 EDU
   - Colaboración: UTN Facultad Regional San Francisco
   - Equipo: Unitree 4D LiDAR L2 · PC con Ubuntu 24.04 + ROS 2 Jazzy
   - Repositorio: github.com/EzeCombina/LiDAR-RobotHumanoide (privado)
   - Autor: Ezequiel Combina
   - Fecha: mes y año
5. **Pie de la portada:** banda fina de color principal, con "UTN · Facultad Regional San Francisco"
   en negrita a la izquierda y "Documentación técnica · Laboratorio" a la derecha, en blanco.

## Páginas interiores

- **Encabezado:** a la izquierda, un cuadrado pequeño (unos 12 mm) con el logo de la UTN sobre
  blanco. Al lado, en gris y tamaño chico: "Título corto · Tema · vX.Y.Z". Debajo, una **línea de
  color principal** a todo el ancho.
- **Pie:** línea fina gris clara; a la izquierda "UTN FRSF" en negrita y color principal; a la
  derecha "Página N".
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
