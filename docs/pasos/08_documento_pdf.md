# Paso 08 — Documento PDF de la guía

## Objetivo

Generar (y regenerar después de cada cambio) el documento PDF con la guía completa del proyecto,
con el formato de `docs/FORMATO_DOCUMENTO.md`: portada con el logo de la UTN FRSF, índice con
números de página, encabezado y pie en cada página, tablas y recuadros de aviso.

## Requisitos

```bash
sudo apt install -y weasyprint python3-markdown
```

| Paquete | Para qué |
|---|---|
| `weasyprint` | Convierte HTML + CSS en PDF. A diferencia de un navegador, maneja bien los encabezados y pies de página con número de página y el índice con números de página reales (CSS *paged media*) |
| `python3-markdown` | Convierte los capítulos, escritos en Markdown, a HTML |

Fuentes tipográficas: Open Sans (paquete `fonts-open-sans`) y DejaVu Sans Mono (viene con Ubuntu).

## 1. Generar el PDF

```bash
cd ~/Documentos/LiDAR-RobotHumanoide
./scripts/documentacion/generar_pdf.py
```

**Salida obtenida** (2026-11-13):

```text
  capítulo: 01_resumen.md  (1. Resumen)
  capítulo: 02_conceptos.md  (2. Conceptos básicos)
  ...
  capítulo: 15_anexo_d_referencias.md  (Anexo D. Referencias)
PDF generado: .../docs/pdf/salida/Guia_LiDAR_L2_v0.1.0.pdf (0.7 MB, WeasyPrint 61.1)
```

Tarda unos segundos. Con `--html` guarda además el HTML intermedio
(`docs/pdf/salida/documento_intermedio.html`), útil para revisar problemas de diseño.

## 2. Cómo está armado

| Archivo | Contenido |
|---|---|
| `docs/pdf/fuente/documento.yaml` | Título, subtítulo, **versión**, fecha, tabla de la portada y nombre del PDF |
| `docs/pdf/fuente/capitulos/*.md` | Un archivo por capítulo o anexo, en el orden de su nombre (`01_…`, `02_…`) |
| `docs/pdf/fuente/estilos.css` | Diseño (colores, tipografías, portada, tablas, recuadros) |
| `assets/logo_utn_frsf.png` | Logo de la portada |
| `assets/logo_utn_emblema.png` | Emblema de la UTN para el encabezado: recorte del logo (columnas 0–72, filas 7–90) ampliado y centrado en un cuadrado |
| `scripts/documentacion/generar_pdf.py` | Arma portada + índice + capítulos y genera el PDF |
| `docs/pdf/salida/` | El PDF generado (se sube a git) |

El script:

1. Lee `documento.yaml`.
2. Convierte cada capítulo de Markdown a HTML, numera los títulos `#` y `##` para el índice y
   convierte cada imagen sola en una figura con epígrafe.
3. Arma la portada, el índice ("Contenido") y el encabezado de cada capítulo
   ("LiDAR Unitree L2 · <capítulo> · v<versión>").
4. Aplica `estilos.css` y genera el PDF con WeasyPrint.

## 3. Cómo editar el contenido

- **Títulos:** `# 5. Título del capítulo` (cada capítulo empieza en página nueva) y
  `## 5.1 Subtítulo`. La numeración se escribe a mano. Los anexos: `# Anexo A. …`.
- **Recuadros de aviso:**

  ```text
  !!! concepto "¿Qué es un tópico?"
      Texto del recuadro, sangrado con 4 espacios.
  ```

  Tipos: `concepto` (celeste), `nota` (azul), `importante` (ámbar), `peligro` (rojo). Dejar una
  línea en blanco antes del `!!!`.
- **Imágenes:** `![Epígrafe](docs/img/archivo.png)` en un párrafo propio; la ruta es desde la
  carpeta del repositorio. Se muestran con 80 mm de alto.
- **Tablas, código y listas:** Markdown común (tablas con `|`, bloques con tres comillas
  invertidas).
- **Nueva versión:** cambiar `version`, `fecha` y `archivo_salida` en `documento.yaml` y regenerar.

## 4. Verificación

Revisar el PDF página por página (o convertirlo a imágenes con
`pdftoppm -r 40 -png docs/pdf/salida/<archivo>.pdf /tmp/pagina`):

- [ ] El índice tiene todos los capítulos y los números de página coinciden.
- [ ] No hay páginas casi vacías ni tablas o bloques de código cortados.
- [ ] Las figuras y los recuadros se ven completos.

Contenido de la versión 0.1.0: 40 páginas; capítulos 1 a 11 (objetivo de corto plazo:
implementación en Ubuntu y mapa de una habitación) y anexos A a D. La Jetson del robot y la
navegación van en un documento posterior.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'markdown'` o `'weasyprint'` | Faltan los paquetes | `sudo apt install -y weasyprint python3-markdown` |
| Un recuadro aparece como texto con `!!!` | Falta la línea en blanco antes, o el texto no está sangrado 4 espacios | Corregir el Markdown |
| Una figura deja un espacio en blanco al final de la página anterior | No entra en el espacio que queda y pasa a la página siguiente (normal) | Si molesta, mover la figura o reordenar el texto |
| Tipografía distinta de Open Sans | Falta la fuente | `sudo apt install -y fonts-open-sans` |
