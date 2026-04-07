#!/usr/bin/env python3
"""Pipeline de análisis para Entregable.

Lee la base de datos original desde el CSV bruto y crea un archivo enriquecido
con columnas adicionales para análisis exploratorio. Genera CSV, SQLite, Markdown y PDFs.
"""

from __future__ import annotations

import csv
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------

def install_package(package: str, import_name: str | None = None) -> bool:
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        log(f"Intentando instalar {package}...")
        try:
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True, timeout=90, check=True,
            )
            log(f"{package} instalado correctamente")
            return True
        except Exception as e:
            log(f"Error instalando {package}: {e}")
            return False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {message}")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def must_exist(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} no existe: {path}")


def parse_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def create_insolation_class(pl_eqt: float | None) -> str:
    if pl_eqt is None:
        return "unknown"
    if pl_eqt <= 250:
        return "cold"
    if pl_eqt <= 500:
        return "temperate"
    if pl_eqt <= 1000:
        return "hot"
    return "extreme"


def build_analysis_rows(raw_csv: Path) -> tuple[list[dict[str, Any]], list[str]]:
    log(f"Cargando datos originales desde {raw_csv}")
    rows: list[dict[str, Any]] = []
    with raw_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        output_fields = list(fieldnames) + [
            "disc_decade",
            "pl_density_earth",
            "insolation_class",
        ]

        for row in reader:
            disc_year   = parse_int(row.get("disc_year", ""))
            pl_bmasse   = parse_float(row.get("pl_bmasse", ""))
            pl_rade     = parse_float(row.get("pl_rade", ""))
            pl_eqt      = parse_float(row.get("pl_eqt", ""))

            disc_decade = disc_year // 10 * 10 if disc_year is not None else ""
            pl_density_earth = (
                pl_bmasse / (pl_rade ** 3)
                if pl_bmasse is not None and pl_rade is not None and pl_rade != 0
                else ""
            )
            insolation_class = create_insolation_class(pl_eqt)

            row["disc_decade"]       = disc_decade
            row["pl_density_earth"]  = (
                f"{pl_density_earth:.6f}" if isinstance(pl_density_earth, float) else ""
            )
            row["insolation_class"]  = insolation_class
            rows.append(row)

    return rows, output_fields


# ---------------------------------------------------------------------------
# Export: CSV
# ---------------------------------------------------------------------------

def export_analysis_csv(
    rows: list[dict[str, Any]], fieldnames: list[str], out_csv: Path
) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    log(f"Exportando análisis enriquecido a {out_csv}")
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log("Exportación CSV completada")


# ---------------------------------------------------------------------------
# Export: SQLite
# ---------------------------------------------------------------------------

def export_analysis_sqlite(
    rows: list[dict[str, Any]], fieldnames: list[str], out_db: Path
) -> None:
    out_db.parent.mkdir(parents=True, exist_ok=True)
    log(f"Exportando análisis a SQLite: {out_db}")
    con = sqlite3.connect(str(out_db))
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS analysis_planet")
    field_defs   = ", ".join(f'"{f}" TEXT' for f in fieldnames)
    placeholders = ", ".join("?" * len(fieldnames))
    cur.execute(f"CREATE TABLE analysis_planet ({field_defs})")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_disc_decade      ON analysis_planet (disc_decade)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_insolation_class ON analysis_planet (insolation_class)")
    for row in rows:
        values = [row.get(f, "") for f in fieldnames]
        cur.execute(f"INSERT INTO analysis_planet VALUES ({placeholders})", values)
    con.commit()
    con.close()
    log(f"SQLite database creada con {len(rows)} filas")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_analysis_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_rows        = len(rows)
    rows_with_decade  = sum(1 for r in rows if r.get("disc_decade") not in (None, ""))
    densities = [
        float(r["pl_density_earth"])
        for r in rows
        if r.get("pl_density_earth") not in (None, "")
    ]
    avg_density = sum(densities) / len(densities) if densities else 0.0
    min_density = min(densities) if densities else 0.0
    max_density = max(densities) if densities else 0.0
    cold_count      = sum(1 for r in rows if r.get("insolation_class") == "cold")
    temperate_count = sum(1 for r in rows if r.get("insolation_class") == "temperate")
    hot_count       = sum(1 for r in rows if r.get("insolation_class") == "hot")
    extreme_count   = sum(1 for r in rows if r.get("insolation_class") == "extreme")
    unknown_count   = sum(1 for r in rows if r.get("insolation_class") == "unknown")

    return {
        "total_rows":        total_rows,
        "rows_with_decade":  rows_with_decade,
        "avg_density":       avg_density,
        "min_density":       min_density,
        "max_density":       max_density,
        "cold_count":        cold_count,
        "temperate_count":   temperate_count,
        "hot_count":         hot_count,
        "extreme_count":     extreme_count,
        "unknown_count":     unknown_count,
    }


def print_summary(stats: dict[str, Any]) -> None:
    log("Resumen de análisis")
    print(f"  Total filas:                       {stats['total_rows']:,}")
    print(f"  Filas con década de descubrimiento:{stats['rows_with_decade']:,}")
    print(f"  Densidad media relativa (Earth):   {stats['avg_density']:.6f}")
    print(f"  Densidad mínima:                   {stats['min_density']:.6f}")
    print(f"  Densidad máxima:                   {stats['max_density']:.6f}")
    print(f"  Planetas fríos:                    {stats['cold_count']:,}")
    print(f"  Planetas templados:                {stats['temperate_count']:,}")
    print(f"  Planetas calientes:                {stats['hot_count']:,}")
    print(f"  Planetas extremos:                 {stats['extreme_count']:,}")
    print(f"  Temperatura desconocida:           {stats['unknown_count']:,}")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_markdown_report(
    stats: dict[str, Any], output_md: Path, output_csv: Path, output_db: Path
) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    log(f"Generando reporte Markdown: {output_md}")
    timestamp = datetime.now(timezone.utc).isoformat()
    report = f"""# Reporte de Análisis Exoplanetario — Pipeline Entregable

**Fecha de generación:** {timestamp}

## Resumen Ejecutivo

Este reporte documenta el análisis enriquecido del dataset de exoplanetas de la NASA,
con tres columnas adicionales calculadas para análisis profundo.

## Columnas Añadidas

1. **disc_decade**: Década de descubrimiento (agrupación 10 años)
   - Calculada como: `(disc_year // 10) * 10`
   - Facilita análisis histórico por períodos

2. **pl_density_earth**: Densidad del planeta relativa a la Tierra
   - Calculada como: `pl_bmasse / (pl_rade ^ 3)`
   - Métrica física para caracterización planetaria

3. **insolation_class**: Clasificación de temperatura de equilibrio
   - Categorías: cold (<=250 K), temperate (250-500 K), hot (500-1000 K), extreme (>1000 K)
   - Basada en `pl_eqt` (temperatura de equilibrio del planeta)

## Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| Total de filas procesadas | {stats['total_rows']:,} |
| Filas con década de descubrimiento | {stats['rows_with_decade']:,} |
| Densidad media (Earth) | {stats['avg_density']:.6f} |
| Densidad mínima | {stats['min_density']:.6f} |
| Densidad máxima | {stats['max_density']:.6f} |

## Distribución por Clase de Insolación

| Clase | Cantidad | Porcentaje |
|-------|----------|-----------|
| Fríos (<=250 K) | {stats['cold_count']:,} | {100*stats['cold_count']/stats['total_rows']:.2f}% |
| Templados (250-500 K) | {stats['temperate_count']:,} | {100*stats['temperate_count']/stats['total_rows']:.2f}% |
| Calientes (500-1000 K) | {stats['hot_count']:,} | {100*stats['hot_count']/stats['total_rows']:.2f}% |
| Extremos (>1000 K) | {stats['extreme_count']:,} | {100*stats['extreme_count']/stats['total_rows']:.2f}% |
| Desconocidos | {stats['unknown_count']:,} | {100*stats['unknown_count']/stats['total_rows']:.2f}% |

## Archivos Generados

- **CSV**: `{output_csv.name}` — Datos completos con columnas enriquecidas
- **Base de datos**: `{output_db.name}` — Índices optimizados para consultas rápidas
- **Reporte**: Este documento

## Notas Técnicas

- Valores nulos: Se preservan como campos vacíos en el CSV e índices en SQLite
- Precisión numérica: 6 decimales para densidades
- Encoding: UTF-8 para todos los archivos
- Índices SQLite: `disc_decade`, `insolation_class` para consultas optimizadas

---
*Generado automáticamente por pipeline.py*
"""
    with output_md.open("w", encoding="utf-8") as f:
        f.write(report)
    log("Reporte Markdown generado")


# ---------------------------------------------------------------------------
# PDF helpers — reportlab
# ---------------------------------------------------------------------------

# Color palette
_NAVY   = (0.10, 0.18, 0.35)   # dark header bg
_STEEL  = (0.24, 0.44, 0.70)   # accent
_LIGHT  = (0.93, 0.95, 0.98)   # alternating row
_WHITE  = (1.00, 1.00, 1.00)
_BLACK  = (0.10, 0.10, 0.10)
_GRAY   = (0.50, 0.50, 0.50)


def _rl_styles():
    """Return a dict of ReportLab ParagraphStyles."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib import colors

    navy  = colors.Color(*_NAVY)
    steel = colors.Color(*_STEEL)
    black = colors.Color(*_BLACK)
    gray  = colors.Color(*_GRAY)

    base = dict(fontName="Helvetica", fontSize=10, leading=14, textColor=black)

    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18,
                              leading=22, textColor=navy, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13,
                              leading=17, textColor=steel, spaceBefore=10, spaceAfter=4),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11,
                              leading=15, textColor=black, spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", **base, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", **base, leftIndent=14,
                                 bulletIndent=4, spaceAfter=2),
        "code": ParagraphStyle("code", fontName="Courier", fontSize=9,
                               leading=12, textColor=black,
                               backColor=colors.Color(0.95, 0.95, 0.95),
                               leftIndent=8, spaceAfter=4),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8,
                                leading=10, textColor=gray),
        "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique",
                                  fontSize=9, leading=12, textColor=gray,
                                  alignment=TA_CENTER, spaceAfter=6),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9,
                             leading=11, textColor=colors.white,
                             alignment=TA_CENTER),
        "td": ParagraphStyle("td", fontName="Helvetica", fontSize=9,
                             leading=11, textColor=black, alignment=TA_LEFT),
        "td_r": ParagraphStyle("td_r", fontName="Helvetica", fontSize=9,
                               leading=11, textColor=black, alignment=TA_RIGHT),
    }


def _add_page_number(canvas, doc):
    """Draw page number footer on every page."""
    from reportlab.lib.units import mm
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(*_GRAY)
    page_num = f"Página {doc.page}"
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, 10 * mm, page_num)
    canvas.drawString(15 * mm, 10 * mm, "Análisis Exoplanetario — NASA Dataset")
    canvas.setStrokeColorRGB(*_STEEL)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 13 * mm, doc.pagesize[0] - 15 * mm, 13 * mm)
    canvas.restoreState()


def create_pdf_from_markdown(md_path: Path, pdf_path: Path) -> None:
    """Convert the Markdown report to a polished PDF using ReportLab."""
    log(f"Generando PDF de reporte desde Markdown: {pdf_path}")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )

    styles = _rl_styles()
    navy   = colors.Color(*_NAVY)
    steel  = colors.Color(*_STEEL)
    light  = colors.Color(*_LIGHT)
    white  = colors.Color(*_WHITE)

    # --- parse markdown into flowables ---
    story: list = []

    with md_path.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Collect table blocks separately
    i = 0
    while i < len(lines):
        line = lines[i]

        # H1
        if line.startswith("# "):
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(line[2:], styles["h1"]))
            story.append(HRFlowable(width="100%", thickness=1.5,
                                    color=steel, spaceAfter=4))
            i += 1

        # H2
        elif line.startswith("## "):
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(line[3:], styles["h2"]))
            i += 1

        # H3
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["h3"]))
            i += 1

        # Horizontal rule
        elif line.strip() in ("---", "***", "___"):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.Color(*_GRAY), spaceAfter=4))
            i += 1

        # Markdown table — collect all rows until blank / non-table line
        elif line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            # Remove separator row (---|---...)
            data_rows = [
                l for l in table_lines
                if not set(l.replace("|", "").replace(" ", "")).issubset({"-", ":"})
            ]
            if data_rows:
                parsed = []
                for tl in data_rows:
                    cells = [c.strip() for c in tl.strip().strip("|").split("|")]
                    parsed.append(cells)

                # Build ReportLab table
                col_count = max(len(r) for r in parsed)
                # Normalise row lengths
                for r in parsed:
                    while len(r) < col_count:
                        r.append("")

                # Convert header row to Paragraph objects
                header = [Paragraph(c, styles["th"]) for c in parsed[0]]
                body_rows = []
                for idx, r in enumerate(parsed[1:]):
                    # Right-align cells that look numeric
                    row_cells = []
                    for c in r:
                        clean = c.replace(",", "").replace("%", "").replace(".", "", 1)
                        st = styles["td_r"] if clean.lstrip("-").isdigit() else styles["td"]
                        row_cells.append(Paragraph(c, st))
                    body_rows.append(row_cells)

                available_w = A4[0] - 30 * mm
                col_w = available_w / col_count

                tbl = Table([header] + body_rows,
                            colWidths=[col_w] * col_count,
                            repeatRows=1)

                ts = TableStyle([
                    # Header
                    ("BACKGROUND",  (0, 0), (-1, 0), navy),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), white),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, 0), 9),
                    ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
                    ("TOPPADDING",  (0, 0), (-1, 0), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    # Body rows — alternating
                    ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE",    (0, 1), (-1, -1), 9),
                    ("TOPPADDING",  (0, 1), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, light]),
                    # Grid
                    ("GRID",        (0, 0), (-1, -1), 0.4, colors.Color(0.75, 0.80, 0.88)),
                    ("BOX",         (0, 0), (-1, -1), 0.8, steel),
                    ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
                ])
                tbl.setStyle(ts)
                story.append(KeepTogether([tbl, Spacer(1, 4 * mm)]))

        # Numbered / bullet list item
        elif line.strip().startswith(("- ", "* ", "+ ")) or (
            len(line) > 2 and line[0].isdigit() and line[1] in ".)"
        ):
            text = line.strip().lstrip("-*+0123456789.) ").strip()
            # Bold key if line starts with **...**
            text = _md_inline(text)
            story.append(Paragraph(f"• {text}", styles["bullet"]))
            i += 1

        # Inline code / bold bold line (key: value pattern)
        elif line.strip().startswith("**") or "`" in line:
            story.append(Paragraph(_md_inline(line.strip()), styles["body"]))
            i += 1

        # Blank line
        elif line.strip() == "":
            story.append(Spacer(1, 2 * mm))
            i += 1

        # Regular paragraph
        else:
            story.append(Paragraph(_md_inline(line.strip()), styles["body"]))
            i += 1

    # --- build PDF ---
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Reporte Análisis Exoplanetario",
        author="pipeline.py",
    )
    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    log(f"PDF de reporte creado: {pdf_path.name}")


def _md_inline(text: str) -> str:
    """Convert basic Markdown inline syntax to ReportLab XML.

    Rules applied in order:
    1. Escape bare & and < that are NOT part of already-converted tags.
    2. Extract inline-code spans first (protect their content from further subs).
    3. Bold (**text**) — must come before single-star italic.
    4. Italic (*text*) — only single stars, NOT underscores inside words.
    5. Re-inject code spans.
    """
    import re

    # --- 1. protect XML special chars that aren't our own tags ---
    # Escape & that aren't already an entity
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", text)
    # Escape < that don't start a known RL tag
    text = re.sub(r"<(?!/?(?:b|i|u|br|super|sub|font|para)\b)", "&lt;", text)

    # --- 2. pull out `code` spans so underscores inside them are safe ---
    code_spans: list[str] = []
    def _stash_code(m: re.Match) -> str:
        idx = len(code_spans)
        # Escape any XML specials inside the code literal
        inner = m.group(1).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        code_spans.append(f'<font name="Courier" size="9">{inner}</font>')
        return f"\x00CODE{idx}\x00"

    text = re.sub(r"`(.+?)`", _stash_code, text)

    # --- 3. bold: **text** (must precede single-star) ---
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # --- 4. italic: *text* (single stars only, not underscores) ---
    # Use a negative look-behind/ahead so we don't match ** leftovers
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)

    # NOTE: We intentionally do NOT convert _word_ → <i>word</i> because
    # column names like disc_decade, pl_density_earth contain underscores
    # that must be rendered literally.

    # --- 5. restore code spans ---
    for idx, span in enumerate(code_spans):
        text = text.replace(f"\x00CODE{idx}\x00", span)

    return text


def create_pdf_from_csv(csv_path: Path, pdf_path: Path, max_rows: int = 200) -> None:
    """Convert CSV data to a nicely formatted PDF table using ReportLab."""
    log(f"Generando PDF de datos desde CSV: {pdf_path}")

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )

    styles   = _rl_styles()
    navy     = colors.Color(*_NAVY)
    steel    = colors.Color(*_STEEL)
    light    = colors.Color(*_LIGHT)
    white    = colors.Color(*_WHITE)
    page_sz  = landscape(A4)
    avail_w  = page_sz[0] - 20 * mm   # usable width

    with csv_path.open("r", encoding="utf-8") as f:
        reader  = csv.reader(f)
        header  = next(reader)
        all_rows = list(reader)

    truncated   = len(all_rows) > max_rows
    sample_rows = all_rows[:max_rows]

    # --- choose which columns to show (prioritise informative ones) ---
    PRIORITY_COLS = [
        "pl_name", "hostname", "disc_year", "disc_decade", "discoverymethod",
        "pl_orbper", "pl_rade", "pl_bmasse", "pl_eqt",
        "pl_density_earth", "insolation_class",
    ]
    col_indices = []
    col_names   = []
    for col in PRIORITY_COLS:
        if col in header:
            col_indices.append(header.index(col))
            col_names.append(col)

    # Fallback: just take first 12 columns
    if not col_indices:
        col_indices = list(range(min(12, len(header))))
        col_names   = header[:12]

    # Compute column widths — wider for text cols, narrower for numeric
    WIDE_COLS  = {"pl_name", "hostname", "discoverymethod"}
    EXTRA_COLS = {"insolation_class"}
    unit = avail_w / (len(col_names) + 4)  # base unit
    col_widths = []
    for c in col_names:
        if c in WIDE_COLS:
            col_widths.append(unit * 2.2)
        elif c in EXTRA_COLS:
            col_widths.append(unit * 1.5)
        else:
            col_widths.append(unit * 0.95)

    # Scale to fill available width exactly
    total = sum(col_widths)
    col_widths = [w * avail_w / total for w in col_widths]

    # --- build table data ---
    header_row = [Paragraph(c, styles["th"]) for c in col_names]
    body = []
    for r in sample_rows:
        cells = []
        for idx, col in zip(col_indices, col_names):
            val = r[idx] if idx < len(r) else ""
            # right-align numeric-looking cells
            clean = val.replace(".", "", 1).replace("-", "", 1)
            st = styles["td_r"] if clean.isdigit() else styles["td"]
            cells.append(Paragraph(val, st))
        body.append(cells)

    tbl = Table([header_row] + body, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), navy),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        # Body
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, light]),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.Color(0.78, 0.83, 0.90)),
        ("BOX",           (0, 0), (-1, -1), 0.8, steel),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])
    tbl.setStyle(ts)

    # --- assemble story ---
    story = [
        Paragraph("Dataset de Exoplanetas — NASA (selección de columnas)", styles["h1"]),
        HRFlowable(width="100%", thickness=1.5, color=steel, spaceAfter=3),
        Paragraph(
            f"Mostrando {len(sample_rows):,} de {len(all_rows):,} filas  •  "
            f"{len(col_names)} columnas seleccionadas  •  "
            f"Generado {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["small"],
        ),
        Spacer(1, 4 * mm),
        tbl,
    ]
    if truncated:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            f"Nota: se muestran las primeras {max_rows} filas. "
            f"El dataset completo contiene {len(all_rows):,} filas.",
            styles["caption"],
        ))

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    def _footer(canvas, doc):
        from reportlab.lib.units import mm
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColorRGB(*_GRAY)
        canvas.drawRightString(
            doc.pagesize[0] - 10 * mm, 8 * mm, f"Página {doc.page}"
        )
        canvas.drawString(10 * mm, 8 * mm, "Análisis Exoplanetario — NASA Dataset")
        canvas.setStrokeColorRGB(*_STEEL)
        canvas.setLineWidth(0.4)
        canvas.line(10 * mm, 11 * mm, doc.pagesize[0] - 10 * mm, 11 * mm)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=page_sz,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Dataset Exoplanetas NASA",
        author="pipeline.py",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    log(f"PDF de datos creado: {pdf_path.name}")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup_existing_pdfs(data_dir: Path) -> None:
    log("Eliminando PDFs previos si existen...")
    for pdf_file in ["analysis_enhanced.pdf", "analysis_report.pdf"]:
        p = data_dir / pdf_file
        if p.exists():
            os.remove(p)
            log(f"PDF eliminado: {pdf_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    reportlab_ok = install_package("reportlab")

    deliverable_dir = Path(__file__).resolve().parent
    project_root    = deliverable_dir.parent

    raw_csv = (
        project_root
        / "data"
        / "raw"
        / "pscomppars.csv"
    )
    must_exist(raw_csv, "CSV original")

    data_dir      = deliverable_dir / "pipeline_results"
    output_csv    = data_dir / "analysis_enhanced.csv"
    output_db     = data_dir / "analysis_exoplanets.db"
    output_md     = data_dir / "analysis_report.md"
    output_csv_pdf = data_dir / "analysis_enhanced.pdf"
    output_md_pdf  = data_dir / "analysis_report.pdf"

    cleanup_existing_pdfs(data_dir)

    rows, fieldnames = build_analysis_rows(raw_csv)
    export_analysis_csv(rows, fieldnames, output_csv)
    export_analysis_sqlite(rows, fieldnames, output_db)
    stats = compute_analysis_stats(rows)
    print_summary(stats)
    generate_markdown_report(stats, output_md, output_csv, output_db)

    if reportlab_ok:
        create_pdf_from_csv(output_csv, output_csv_pdf)
        create_pdf_from_markdown(output_md, output_md_pdf)
    else:
        log("reportlab no disponible — PDFs no generados. Instala con: pip install reportlab")


if __name__ == "__main__":
    main()
