#!/usr/bin/env python3
# =============================================================================
# generar_pdf.py — Genera el documento PDF del proyecto
# -----------------------------------------------------------------------------
# Qué hace:
#   1. Lee los datos del documento (docs/pdf/fuente/documento.yaml): título,
#      versión, fecha, tabla de la portada.
#   2. Convierte a HTML cada capítulo escrito en Markdown
#      (docs/pdf/fuente/capitulos/*.md, en orden alfabético del nombre).
#   3. Arma la portada, el índice ("Contenido", con los títulos # y ## de cada
#      capítulo) y el encabezado de cada capítulo.
#   4. Aplica el diseño (docs/pdf/fuente/estilos.css, formato de
#      docs/FORMATO_DOCUMENTO.md) y genera el PDF con WeasyPrint en
#      docs/pdf/salida/<archivo_salida del yaml>.
#
#   Markdown admitido (además del común): tablas, bloques ```código```, y
#   recuadros de aviso con la extensión "admonition":
#       !!! concepto "¿Qué es un tópico?"
#           Texto del recuadro (sangrado 4 espacios).
#   Tipos: concepto, nota, importante, peligro.
#   Imágenes: ![Epígrafe](docs/img/archivo.png) — la ruta es desde la carpeta del
#   repositorio; se muestran como figura con el texto entre corchetes de epígrafe.
#
# Requisitos: weasyprint, python3-markdown, python3-yaml (sudo apt install -y
#             weasyprint python3-markdown). Fuentes Open Sans y DejaVu Sans Mono.
#
# Cómo se usa (desde cualquier carpeta):
#   ./scripts/documentacion/generar_pdf.py
#   ./scripts/documentacion/generar_pdf.py --html     # guarda también el HTML intermedio
# =============================================================================
import argparse
import html
import os
import re
import sys

import markdown
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FUENTE = os.path.join(REPO, "docs", "pdf", "fuente")
SALIDA = os.path.join(REPO, "docs", "pdf", "salida")
# Documento de DataPyme (logo e ícono, como la referencia), en colaboración con la UTN FRSF.
LOGO = os.path.join(REPO, "assets", "logo_datapyme.png")
ICONO = os.path.join(REPO, "assets", "logo_datapyme_icono.png")
LOGO_UTN = os.path.join(REPO, "assets", "logo_utn_frsf.png")


def slug(texto, usados):
    """Identificador para enlazar un título desde el índice."""
    base = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-") or "seccion"
    s, i = base, 2
    while s in usados:
        s, i = f"{base}-{i}", i + 1
    usados.add(s)
    return s


def capitulo_a_html(texto_md, usados):
    """Markdown -> HTML; agrega ids a h1/h2 y devuelve (html, [(nivel, título, id)])."""
    cuerpo = markdown.markdown(
        texto_md, extensions=["tables", "fenced_code", "admonition", "attr_list", "sane_lists", "md_in_html"])
    titulos = []

    def poner_id(m):
        nivel, contenido = m.group(1), m.group(2)
        plano = html.unescape(re.sub(r"<[^>]+>", "", contenido))
        ident = slug(plano, usados)
        titulos.append((int(nivel), plano, ident))
        return f'<h{nivel} id="{ident}">{contenido}</h{nivel}>'

    cuerpo = re.sub(r"<h([12])>(.*?)</h\1>", poner_id, cuerpo, flags=re.S)
    # Imagen sola en un párrafo -> figura con epígrafe.
    cuerpo = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)"\s*/?></p>',
                    lambda m: f'<figure><img src="{m.group(2)}" alt="{m.group(1)}"/>'
                              f'<figcaption>{m.group(1)}</figcaption></figure>', cuerpo)
    return cuerpo, titulos


def portada(d):
    filas = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in d["metadatos"])
    return f"""
<section class="portada">
  <div class="banda">
    <div class="logo"><img src="file://{LOGO}" alt="DataPyme"/></div>
    <h1 class="titulo-portada">{html.escape(d['titulo'])}</h1>
    <div class="subtitulo">{html.escape(d['subtitulo'])}</div>
    <hr/>
    <div class="descripcion">{html.escape(d['descripcion'])}</div>
    <div class="version">Versión {html.escape(str(d['version']))}</div>
  </div>
  <table class="metadatos">{filas}</table>
  <div class="colaboracion"><span>Proyecto realizado en colaboración con la<br/>
    <b>UTN Facultad Regional San Francisco</b></span>
    <img src="file://{LOGO_UTN}" alt="UTN Facultad Regional San Francisco"/></div>
  <div class="pie"><b>DataPyme</b><span>Documentación técnica · En colaboración con la UTN FRSF</span></div>
</section>"""


def indice(titulos, encabezado):
    items = []
    for nivel, texto, ident in titulos:
        clase = "cap" if nivel == 1 else "sub"
        items.append(f'<li class="{clase}"><a href="#{ident}">{html.escape(texto)}</a></li>')
    return f'<section class="indice">{encabezado}<h1>Contenido</h1><ul>{"".join(items)}</ul></section>'


def main():
    p = argparse.ArgumentParser(description="Genera el PDF del proyecto.")
    p.add_argument("--html", action="store_true", help="guarda también el HTML intermedio")
    a = p.parse_args()

    d = yaml.safe_load(open(os.path.join(FUENTE, "documento.yaml")))
    carpeta_cap = os.path.join(FUENTE, "capitulos")
    archivos = sorted(f for f in os.listdir(carpeta_cap) if f.endswith(".md"))
    if not archivos:
        print(f"ERROR: no hay capítulos en {carpeta_cap}")
        sys.exit(1)

    def encabezado(tema):
        return (f'<div class="encabezado"><img src="file://{ICONO}" alt=""/>'
                f'<span>{html.escape(d["titulo_corto"])} · {html.escape(tema)} · v{d["version"]}</span></div>')

    usados, todos, secciones = set(), [], []
    for nombre in archivos:
        cuerpo, titulos = capitulo_a_html(open(os.path.join(carpeta_cap, nombre)).read(), usados)
        cap = next((t for n, t, _ in titulos if n == 1), "")
        secciones.append(f'<section class="capitulo">{encabezado(cap)}{cuerpo}</section>')
        todos += titulos
        print(f"  capítulo: {nombre}  ({cap})")

    documento = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"/><title>{html.escape(d['titulo'])}</title>
<link rel="stylesheet" href="file://{os.path.join(FUENTE, 'estilos.css')}"/></head>
<body>{portada(d)}{indice(todos, encabezado("Contenido"))}{''.join(secciones)}</body></html>"""

    os.makedirs(SALIDA, exist_ok=True)
    if a.html:
        with open(os.path.join(SALIDA, "documento_intermedio.html"), "w") as f:
            f.write(documento)
    from weasyprint import HTML  # se importa acá: tarda unos segundos en cargar
    ruta = os.path.join(SALIDA, d["archivo_salida"])
    pdf = HTML(string=documento, base_url=REPO).write_pdf(ruta)  # noqa: F841
    from weasyprint import __version__ as v
    print(f"PDF generado: {ruta} ({os.path.getsize(ruta) / 1e6:.1f} MB, WeasyPrint {v})")


if __name__ == "__main__":
    main()
