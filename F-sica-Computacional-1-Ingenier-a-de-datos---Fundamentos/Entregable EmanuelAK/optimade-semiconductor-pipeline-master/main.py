"""
pipeline.py — Semiconductor Alloy Discovery Pipeline
Arquitectura medallón Bronze → Silver → Gold sobre Materials Project API.
Incluye: trazabilidad SHA-256, quality gates, SQL limpieza, JOINs M:N,
EXPLAIN ANALYZE, star-schema Gold, filtros físicos + toxicidad/escasez,
scores DFT reales, reporte PDF.
"""

import os, json, time, hashlib, re
from datetime import datetime

import pandas as pd
import numpy as np
import duckdb
from dotenv import load_dotenv
from mp_api.client import MPRester

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from plots_annex import generate_all_plots

import requests
r = requests.get("https://api.materialsproject.org/heartbeat")
print(r.status_code, r.json())

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("MP_API_KEY")
if not API_KEY:
    raise ValueError("MP_API_KEY not found in .env")

# ── Paths ─────────────────────────────────────────────────────────────────────
P = {
    "raw":           "data/raw/materials_raw.json",
    "bronze":        "data/bronze/materials_bronze.parquet",
    "silver":        "data/silver/materials_silver.parquet",
    "gold":          "data/gold/top_semiconductors.parquet",
    "csv_bronze":    "data/bronze/materials_bronze.csv",
    "csv_silver":    "data/silver/materials_silver_enriched.csv",
    "csv_candidates":"data/gold/top_semiconductor_candidates.csv",
    "csv_alloy_cand":"data/gold/alloy_candidates.csv",
    "csv_best":      "data/gold/best_semiconductor_alloys.csv",
    "csv_elements":  "data/gold/elements_analysis.csv",
    "evidence":      "artifacts/evidence/raw_evidence.json",
    "quality":       "artifacts/quality/silver_quality.csv",
    "explain":       "artifacts/explain/gold_explain.txt",
    "report":        "artifacts/reports/semiconductor_report.pdf",
}

DIRS = [
    "data/raw", "data/bronze", "data/silver", "data/gold",
    "artifacts/evidence", "artifacts/timings",
    "artifacts/quality", "artifacts/explain", "artifacts/reports",
]

# ── Physical constants ────────────────────────────────────────────────────────
SQ_EG   = 1.34          # Shockley-Queisser optimal band gap (eV)
SI_EG   = 1.12          # Silicon reference (eV)
N_MID   = 3.25          # Ideal refractive index midpoint
N_HW    = 0.75          # Half-width of ideal n range [2.5, 4.0]
BM_IDEAL = 130.0        # Ideal bulk modulus (GPa)

# ── Exclusion lists (filter 3 new criteria) ───────────────────────────────────
# 1. Toxic / radioactive elements (RoHS + safety)
TOXIC   = {"Hg", "Be", "Tl", "Pb", "Th", "U", "Po", "Ra", "Ac", "Pu"}

# 2. Critically scarce / rare-earth elements (supply chain risk)
#    Pt : platinum-group metal, ~5 ppb crustal abundance, ~$30k/kg
#    Y  : yttrium, classified as critical mineral by EU/US DoE
#    Cs : cesium, byproduct of Li mining, very limited global supply
SCARCE  = {
    "Ho", "Er", "Tm", "Tb", "Sm", "Nd", "Pr", "Ce", "Eu",
    "Gd", "Dy", "La", "Lu", "Yb", "Os", "Ir", "Re", "Ru", "Rh",
    "Pt", "Y", "Cs",
}

# 3. Penalty multiplier for purely theoretical materials (not yet synthesised)
THEORETICAL_PENALTY = 0.90

# ── Column manifests ──────────────────────────────────────────────────────────
SILVER_COLS = [
    "material_id", "formula", "chemsys",
    "band_gap", "cbm", "vbm", "efermi", "is_gap_direct",
    "n", "e_total", "e_ionic", "e_electronic",
    "bulk_modulus_vrh", "shear_modulus_vrh",
    "universal_anisotropy", "homogeneous_poisson",
    "energy_above_hull", "formation_energy_per_atom",
    "equilibrium_reaction_energy_per_atom",
    "density", "volume", "nsites", "nelements",
    "elements", "elements_clean", "crystal_system", "theoretical",
    "is_magnetic", "total_magnetization", "ordering",
    "weighted_work_function", "is_stable",
    "contains_toxic", "contains_scarce",
    "band_gap_score_sq", "band_gap_score_si",
    "stability_score", "dielectric_score", "mechanical_score",
    "magnetic_score", "direct_gap_bonus", "semiconductor_score",
]

GOLD_COLS = [
    "material_id", "formula", "nelements", "elements", "elements_clean",
    "crystal_system", "band_gap", "is_gap_direct",
    "n", "e_total", "e_electronic",
    "bulk_modulus_vrh", "shear_modulus_vrh",
    "energy_above_hull", "formation_energy_per_atom",
    "density", "is_stable", "is_magnetic", "total_magnetization",
    "weighted_work_function", "theoretical",
    "contains_toxic", "contains_scarce",
    "band_gap_score_sq", "band_gap_score_si",
    "stability_score", "dielectric_score", "mechanical_score",
    "magnetic_score", "direct_gap_bonus", "semiconductor_score",
]

# ── Utilities ─────────────────────────────────────────────────────────────────
def ensure_dirs():
    for d in DIRS:
        os.makedirs(d, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def timing(stage, secs):
    with open(f"artifacts/timings/{stage}.txt", "w", encoding="utf-8") as f:
        f.write(f"{stage}: {secs:.2f}s\n")

def to_csv(df, path, cols=None):
    out = df[[c for c in cols if c in df.columns]] if cols else df
    out.to_csv(path, index=False)
    print(f"  -> {path}  ({len(out)} rows × {len(out.columns)} cols)")

def gauss(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def parse_elements(s):
    """
    Robustly extract element symbols from any serialised list format:
      Python list str : "['Si', 'O']"   → comma-separated
      numpy array str : "['Si' 'O']"    → space-separated (NO commas)
      plain string    : "Si, O"         → comma-separated
    Returns a set of clean symbol strings.
    """
    raw = str(s).strip("[]").replace("'", "").replace('"', "")
    # Use regex to extract only valid element symbols (1-2 capital+lower letters)
    return {m for m in re.findall(r'[A-Z][a-z]?', raw)}

# ── RAW extraction ────────────────────────────────────────────────────────────
def extract_raw():
    print("\n[RAW] Querying Materials Project...")
    t0 = time.time()
    records = []

    MP_FIELDS = [
        "material_id", "formula_pretty", "chemsys",
        "band_gap", "cbm", "vbm", "efermi", "is_gap_direct",
        "n", "e_total", "e_ionic", "e_electronic",
        "bulk_modulus", "shear_modulus",
        "universal_anisotropy", "homogeneous_poisson",
        "energy_above_hull", "formation_energy_per_atom",
        "equilibrium_reaction_energy_per_atom",
        "density", "density_atomic", "volume", "nsites",
        "elements", "nelements", "symmetry", "theoretical",
        "is_magnetic", "total_magnetization", "ordering",
        "weighted_work_function", "is_stable",
    ]

    def _f(v):  return float(v) if v is not None else None
    def _i(v):  return int(v)   if v is not None else None
    def _b(v):  return bool(v)
    def _bm(d): return _f(d.get("vrh")) if isinstance(d, dict) else None

    with MPRester(API_KEY) as mpr:
        for doc in mpr.materials.summary.search(
            band_gap=(0.1, 4.0), is_metal=False,
            fields=MP_FIELDS, chunk_size=1000,
        ):
            try:
                records.append({
                    "material_id":   str(doc.material_id),
                    "formula":       doc.formula_pretty,
                    "chemsys":       str(doc.chemsys) if doc.chemsys else None,
                    "band_gap":      _f(doc.band_gap),
                    "cbm":           _f(doc.cbm),
                    "vbm":           _f(doc.vbm),
                    "efermi":        _f(doc.efermi),
                    "is_gap_direct": _b(doc.is_gap_direct) if doc.is_gap_direct is not None else None,
                    "n":             _f(doc.n),
                    "e_total":       _f(doc.e_total),
                    "e_ionic":       _f(doc.e_ionic),
                    "e_electronic":  _f(doc.e_electronic),
                    "bulk_modulus_vrh":    _bm(doc.bulk_modulus),
                    "shear_modulus_vrh":   _bm(doc.shear_modulus),
                    "universal_anisotropy":_f(doc.universal_anisotropy),
                    "homogeneous_poisson": _f(doc.homogeneous_poisson),
                    "energy_above_hull":   _f(doc.energy_above_hull),
                    "formation_energy_per_atom": _f(doc.formation_energy_per_atom),
                    "equilibrium_reaction_energy_per_atom": _f(
                        doc.equilibrium_reaction_energy_per_atom),
                    "density":       _f(doc.density),
                    "density_atomic":_f(doc.density_atomic),
                    "volume":        _f(doc.volume),
                    "nsites":        _i(doc.nsites),
                    "nelements":     _i(doc.nelements),
                    "elements":      [str(e) for e in doc.elements] if doc.elements else [],
                    "crystal_system":str(doc.symmetry.crystal_system) if doc.symmetry else None,
                    "theoretical":   _b(doc.theoretical),
                    "is_magnetic":   _b(doc.is_magnetic),
                    "total_magnetization": _f(doc.total_magnetization),
                    "ordering":      str(doc.ordering) if doc.ordering else None,
                    "weighted_work_function": _f(doc.weighted_work_function),
                    "is_stable":     _b(doc.is_stable),
                })
            except Exception as e:
                print(f"  skip: {e}")

    with open(P["raw"], "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    json.dump({
        "timestamp": str(datetime.now()),
        "records":   len(records),
        "sha256":    sha256(P["raw"]),
    }, open(P["evidence"], "w", encoding="utf-8"), indent=2)

    timing("raw_extract", time.time() - t0)
    print(f"[RAW] {len(records)} materials  ({time.time()-t0:.1f}s)")

# ── BRONZE ────────────────────────────────────────────────────────────────────
def bronze_layer():
    print("\n[BRONZE] Loading raw → parquet + CSV...")
    t0 = time.time()
    df = pd.DataFrame(json.load(open(P["raw"], encoding="utf-8")))
    df.to_parquet(P["bronze"])
    to_csv(df, P["csv_bronze"])
    timing("bronze", time.time() - t0)
    print(f"[BRONZE] {len(df)} rows")

# ── SILVER ────────────────────────────────────────────────────────────────────
def silver_layer():
    """
    SQL-style cleaning + enrichment (run via DuckDB for reproducibility):
      1. Dedup + drop nulls on key columns
      2. Physical range filters (data contract)
      3. Toxicity / scarcity flags  ← NEW
      4. Theoretical penalty         ← NEW
      5. Physically grounded DFT scores
      6. Quality gate CSV (W04 artifact)
    """
    print("\n[SILVER] Cleaning + scoring...")
    t0 = time.time()

    df = pd.read_parquet(P["bronze"])
    df.columns = [c.lower().strip() for c in df.columns]
    df["elements"] = df["elements"].astype(str)

    # ── SQL cleaning via DuckDB (W02/W03 pattern) ─────────────────────────
    con = duckdb.connect()
    con.register("raw", df)
    df = con.execute("""
        SELECT DISTINCT *
        FROM raw
        WHERE material_id IS NOT NULL
          AND formula      IS NOT NULL
          AND band_gap     IS NOT NULL
          AND band_gap     BETWEEN 0.1 AND 4.0
          AND energy_above_hull < 0.2
          AND density      BETWEEN 0.1 AND 25.0
    """).df()

    # ── elements_clean: robust → "Ag,Ho,Se" (no spaces, sorted) ─────────
    df["elements_clean"] = df["elements"].apply(
        lambda s: ",".join(sorted(parse_elements(s)))
    )

    # ── Toxicity / scarcity flags (NEW — filter 1 & 2) ───────────────────
    def flag(s, bad_set):
        return bool(parse_elements(s) & bad_set)

    df["contains_toxic"]  = df["elements"].apply(flag, bad_set=TOXIC)
    df["contains_scarce"] = df["elements"].apply(flag, bad_set=SCARCE)

    # ── DFT-grounded scores ───────────────────────────────────────────────
    df["band_gap_score_sq"] = gauss(df["band_gap"], SQ_EG,   0.40)
    df["band_gap_score_si"] = gauss(df["band_gap"], SI_EG,   0.30)
    df["stability_score"]   = np.exp(-df["energy_above_hull"] / 0.05)
    df["dielectric_score"]  = df["n"].apply(
        lambda n: gauss(n, N_MID, N_HW) if pd.notna(n) else 0.5)
    df["mechanical_score"]  = df["bulk_modulus_vrh"].apply(
        lambda b: gauss(b, BM_IDEAL, 60.0) if (pd.notna(b) and b > 0) else 0.5)
    df["magnetic_score"]    = df.apply(
        lambda r: 1.0 if not r["is_magnetic"] else
                  0.5 if r.get("ordering") == "AFM" else 0.0, axis=1)
    df["direct_gap_bonus"]  = df["is_gap_direct"].apply(
        lambda v: 0.10 if v is True else 0.0)

    df["semiconductor_score"] = (
        df["band_gap_score_sq"] * 0.25 +
        df["band_gap_score_si"] * 0.15 +
        df["stability_score"]   * 0.25 +
        df["dielectric_score"]  * 0.15 +
        df["mechanical_score"]  * 0.10 +
        df["magnetic_score"]    * 0.10 +
        df["direct_gap_bonus"]
    )

    # ── Theoretical penalty (NEW — filter 3) ─────────────────────────────
    df.loc[df["theoretical"] == True, "semiconductor_score"] *= THEORETICAL_PENALTY

    # ── Quality gate (W04 artifact) ───────────────────────────────────────
    qg = pd.DataFrame([{
        "rows":             len(df),
        "null_band_gap":    df["band_gap"].isna().sum(),
        "duplicates":       df.duplicated("material_id").sum(),
        "unstable_gt02":    (df["energy_above_hull"] > 0.2).sum(),
        "toxic_flagged":    df["contains_toxic"].sum(),
        "scarce_flagged":   df["contains_scarce"].sum(),
        "theoretical":      df["theoretical"].sum(),
        "have_n":           df["n"].notna().sum(),
        "have_bulk_mod":    df["bulk_modulus_vrh"].notna().sum(),
        "direct_gap_count": (df["is_gap_direct"] == True).sum(),
    }])
    qg.to_csv(P["quality"], index=False)

    df.to_parquet(P["silver"])
    to_csv(df, P["csv_silver"], SILVER_COLS)
    timing("silver", time.time() - t0)

    print(f"[SILVER] {len(df)} rows  |  "
          f"n={df['n'].notna().sum()}  B={df['bulk_modulus_vrh'].notna().sum()}  "
          f"direct={int((df['is_gap_direct']==True).sum())}  "
          f"toxic={df['contains_toxic'].sum()}  scarce={df['contains_scarce'].sum()}")

# ── MANY-TO-MANY element analysis (W03 JOIN pattern) ─────────────────────────
def many_to_many_analysis(con):
    """
    Explodes elements_clean → one row per (material, element),
    then aggregates per element over the GOLD-filtered candidates only
    (NOT toxic, NOT scarce). This ensures the element ranking reflects
    which elements appear most in high-scoring, viable materials.
    Table gold_candidates must already exist in the connection.
    """
    print("\n[JOIN M:N] Element analysis over gold candidates...")

    # Explode elements_clean of gold candidates (already filtered)
    con.execute("""
        CREATE OR REPLACE TABLE material_elements AS
        SELECT
            material_id,
            trim(UNNEST(string_split(elements_clean, ','))) AS element
        FROM gold_candidates
        WHERE elements_clean != ''
    """)

    result = con.execute("""
        SELECT
            me.element,
            COUNT(*)                                        AS materials_count,
            ROUND(AVG(m.band_gap),          3)             AS avg_band_gap,
            ROUND(AVG(m.energy_above_hull), 5)             AS avg_energy_above_hull,
            ROUND(AVG(m.n),                 3)             AS avg_n,
            ROUND(AVG(m.bulk_modulus_vrh),  1)             AS avg_bulk_modulus_gpa,
            ROUND(AVG(m.dielectric_score),  4)             AS avg_dielectric_score,
            ROUND(AVG(m.mechanical_score),  4)             AS avg_mechanical_score,
            ROUND(AVG(m.semiconductor_score), 4)           AS avg_score,
            SUM(CASE WHEN m.is_stable        THEN 1 ELSE 0 END) AS stable_count,
            SUM(CASE WHEN m.is_gap_direct    THEN 1 ELSE 0 END) AS direct_gap_count,
            SUM(CASE WHEN NOT m.is_magnetic  THEN 1 ELSE 0 END) AS non_magnetic_count
        FROM material_elements me
        JOIN gold_candidates m USING (material_id)
        GROUP BY me.element
        HAVING me.element NOT IN ('', ' ')
        ORDER BY avg_score DESC
    """).df()

    to_csv(result, P["csv_elements"])
    print(f"[JOIN M:N] {len(result)} unique elements in gold candidates")
    return result

# ── GOLD layer (W05/W06 EXPLAIN + star schema) ────────────────────────────────
def gold_layer():
    print("\n[GOLD] Building rankings...")
    t0 = time.time()

    con = duckdb.connect()
    df  = pd.read_parquet(P["silver"])
    con.register("silver_df", df)
    con.execute("CREATE OR REPLACE TABLE silver AS SELECT * FROM silver_df")

    SEL = ", ".join(GOLD_COLS)

    # ── Query 1: All top-200 candidates ──────────────────────────────────
    q_all = f"""
        SELECT {SEL}
        FROM silver
        WHERE NOT contains_toxic
          AND NOT contains_scarce
        ORDER BY semiconductor_score DESC
        LIMIT 200
    """
    top_all = con.execute(q_all).df()
    top_all.to_parquet(P["gold"])
    to_csv(top_all, P["csv_candidates"], GOLD_COLS)

    # Register gold_candidates so M:N analysis runs over filtered set only
    con.register("gold_candidates_df", top_all)
    con.execute("CREATE OR REPLACE TABLE gold_candidates AS SELECT * FROM gold_candidates_df")

    # Run M:N analysis over gold-filtered candidates (not all silver)
    elem_df = many_to_many_analysis(con)

    # ── Query 2: Alloy candidates (nelements >= 2) ────────────────────────
    q_alloy = f"""
        SELECT {SEL}
        FROM silver
        WHERE nelements >= 2
          AND NOT contains_toxic
          AND NOT contains_scarce
        ORDER BY semiconductor_score DESC
        LIMIT 200
    """
    alloy_cand = con.execute(q_alloy).df()
    to_csv(alloy_cand, P["csv_alloy_cand"], GOLD_COLS)

    # ── Query 3: Best alloys — strict physical criteria ───────────────────
    q_best = f"""
        SELECT {SEL}
        FROM silver
        WHERE nelements          >= 2
          AND energy_above_hull   < 0.05
          AND is_stable           = true
          AND is_magnetic         = false
          AND band_gap            BETWEEN 0.5 AND 3.5
          AND NOT contains_toxic
          AND NOT contains_scarce
        ORDER BY semiconductor_score DESC
        LIMIT 100
    """
    best = con.execute(q_best).df()
    to_csv(best, P["csv_best"], GOLD_COLS)

    # ── EXPLAIN ANALYZE (W05 artifact) ────────────────────────────────────
    explain = con.execute(f"EXPLAIN ANALYZE {q_all}").fetchall()
    with open(P["explain"], "w", encoding="utf-8") as f:
        for row in explain:
            f.write(str(row) + "\n")

    timing("gold", time.time() - t0)
    print(f"[GOLD] candidates={len(top_all)}  alloy_cand={len(alloy_cand)}  "
          f"best_alloys={len(best)}")
    return top_all, alloy_cand, best, elem_df

# ── PDF REPORT ────────────────────────────────────────────────────────────────
C_DARK  = colors.HexColor("#1A3A5C")
C_MID   = colors.HexColor("#2E6DA4")
C_LITE  = colors.HexColor("#D0E4F5")
C_GOLD  = colors.HexColor("#C9992B")
C_LGREY = colors.HexColor("#F2F2F2")
C_MGREY = colors.HexColor("#CCCCCC")
C_WHITE = colors.white

def _style(base, **kw):
    s = ParagraphStyle("_", parent=base)
    for k, v in kw.items():
        setattr(s, k, v)
    return s

def _tbl(data, widths=None, gold_row1=False):
    t = Table(data, colWidths=widths, repeatRows=1)
    cmds = [
        ("BACKGROUND",    (0,0),(-1,0), C_DARK),
        ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0), 7.5),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("FONTNAME",      (0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",      (0,1),(-1,-1), 7),
        ("GRID",          (0,0),(-1,-1), 0.35, C_MGREY),
        ("LINEABOVE",     (0,1),(-1,1),  1,    C_DARK),
    ]
    for i in range(1, len(data)):
        cmds.append(("BACKGROUND",(0,i),(-1,i), C_LGREY if i%2==0 else C_WHITE))
    if gold_row1 and len(data) > 1:
        cmds += [
            ("BACKGROUND",(0,1),(-1,1), colors.HexColor("#FFF8DC")),
            ("FONTNAME",  (0,1),(-1,1), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(cmds))
    return t

def _v(val, fmt=".3f"):
    try:
        return "-" if pd.isna(val) else format(float(val), fmt)
    except Exception:
        return str(val) if val else "-"

def _rows_from_df(df, cols_fmt):
    """Build table rows from dataframe given [(col, fmt), ...] spec."""
    out = []
    for _, r in df.iterrows():
        out.append([_v(r.get(c), f) for c, f in cols_fmt])
    return out

def generate_pdf(top_all, alloy_cand, best, elem_df):
    print("\n[REPORT] Generating PDF...")
    styles = getSampleStyleSheet()
    h1   = _style(styles["Heading1"], textColor=C_DARK, fontSize=13,
                  spaceAfter=4, spaceBefore=10)
    cap  = _style(styles["Italic"],   fontSize=7.5, textColor=colors.grey, spaceAfter=5)
    body = _style(styles["BodyText"], fontSize=8.5)

    story = []
    def hr(): story.append(HRFlowable(width="100%", thickness=1, color=C_LITE, spaceAfter=5))

    # ── Cover ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 0.6*inch),
        Paragraph("Semiconductor Alloy Discovery Report",
                  _style(styles["Title"], fontSize=22, textColor=C_DARK)),
        Paragraph("Materials Project · Bronze → Silver → Gold · DFT-grounded scores · "
                  "Toxicity & scarcity filters",
                  _style(styles["Normal"], fontSize=10, textColor=C_MID)),
        HRFlowable(width="100%", thickness=2, color=C_GOLD, spaceAfter=8),
        Paragraph(f"Generado: {datetime.now():%Y-%m-%d %H:%M:%S}",
                  _style(styles["Normal"], fontSize=8, textColor=colors.grey)),
        Spacer(1, 0.25*inch),
        Paragraph(
            "Pipeline reproducible con trazabilidad SHA-256, quality gates, SQL de limpieza, "
            "JOINs muchos-a-muchos, EXPLAIN ANALYZE y star-schema Gold. "
            "Scores calculados a partir de propiedades DFT reales de Materials Project. "
            "Se aplican tres filtros nuevos: <b>(1) exclusión de elementos tóxicos/radiactivos</b> "
            "(Hg, Be, Tl, Pb, Th, U…), <b>(2) exclusión de tierras raras y metales escasos</b> "
            "(Ho, Er, Os, Ir, Re…), <b>(3) penalización del 10 % a materiales puramente teóricos</b>.",
            body),
        PageBreak(),
    ]

    # ── Sec 1: Scoring methodology ───────────────────────────────────────
    story.append(Paragraph("1. Metodología de Scoring (DFT real)", h1)); hr()
    met = [
        ["Métrica", "Campo API", "Fórmula", "Peso", "Referencia física"],
        ["band_gap_score_sq","band_gap","Gauss(Eg,1.34,0.4)","25%","Límite S–Q: óptimo 1.34 eV"],
        ["band_gap_score_si","band_gap","Gauss(Eg,1.12,0.3)","15%","Referencia Si: 1.12 eV"],
        ["stability_score","energy_above_hull","exp(−E_hull/0.05)","25%","E_hull=0 → casco convexo"],
        ["dielectric_score","n (DFT)","Gauss(n,3.25,0.75)","15%","n∈[2.5,4.0] → optoelectrónica"],
        ["mechanical_score","bulk_modulus_vrh","Gauss(B,130,60)","10%","B~80–200 GPa (Si:98,GaAs:75)"],
        ["magnetic_score","ordering","NM=1 AFM=0.5 FM=0","10%","No magnético preferido"],
        ["direct_gap_bonus","is_gap_direct","+0.10 si directa","bonus","Emisión eficiente (LEDs)"],
        ["theoretical_penalty","theoretical","×0.90 si teórico","—","No sintetizado aún"],
    ]
    story.append(_tbl(met, widths=[1.5*inch,1.3*inch,1.8*inch,0.55*inch,3.6*inch]))
    story.append(Paragraph("Tabla 1. Scores y filtros del pipeline.", cap))
    story.append(PageBreak())

    # ── Sec 2: Top-20 candidates ─────────────────────────────────────────
    story.append(Paragraph("2. Top-20 Candidatos Semiconductores", h1)); hr()
    story.append(Paragraph(
        f"Excluidos: tóxicos, escasos. CSV: <i>{P['csv_candidates']}</i>", body))
    story.append(Spacer(1,4))

    spec2 = [("material_id","s"),("formula","s"),("band_gap",".3f"),
             ("is_gap_direct","s"),("n",".2f"),("e_total",".1f"),
             ("bulk_modulus_vrh",".0f"),("energy_above_hull",".4f"),
             ("formation_energy_per_atom",".3f"),("crystal_system","s"),
             ("nelements","s"),("is_stable","s"),("theoretical","s"),
             ("semiconductor_score",".4f")]
    hdr2 = ["ID","Fórmula","Eg (eV)","Gap","n","ε_tot","B (GPa)",
            "E_hull","ΔHf","Sist.","n_el","Est.","Teór.","Score"]
    rows2 = [[_v(r.get(c), f if f != "s" else "") for c, f in spec2]
             for _, r in top_all.head(20).iterrows()]
    # boolean display
    for row, (_, r) in zip(rows2, top_all.head(20).iterrows()):
        row[3]  = "Dir." if r.get("is_gap_direct") else "Ind."
        row[11] = "Sí"   if r.get("is_stable")     else "No"
        row[12] = "Sí"   if r.get("theoretical")   else "No"

    story.append(_tbl([hdr2]+rows2,
        widths=[0.85*inch,1.1*inch,0.6*inch,0.45*inch,0.55*inch,0.55*inch,
                0.65*inch,0.65*inch,0.65*inch,0.6*inch,0.4*inch,
                0.4*inch,0.45*inch,0.7*inch], gold_row1=True))
    story.append(Paragraph("Tabla 2. Top-20 candidatos — sin tóxicos ni escasos.", cap))
    story.append(PageBreak())

    # ── Sec 3: Alloy candidates ──────────────────────────────────────────
    story.append(Paragraph("3. Top-30 Candidatos a Aleaciones (nelem ≥ 2)", h1)); hr()
    story.append(Paragraph(
        f"Todos los atributos de evaluación. CSV: <i>{P['csv_alloy_cand']}</i>", body))
    story.append(Spacer(1,4))

    hdr3 = ["ID","Fórmula","n_el","Eg","Gap","Sc_SQ","Sc_Si",
            "E_hull","Sc_Est","n","ε_e","Sc_Di","B","Sc_Me",
            "Mag","Sc_Ma","Bonus","Score"]
    spec3 = [
        ("material_id","s"),("formula","s"),("nelements","s"),
        ("band_gap",".3f"),("is_gap_direct","s"),
        ("band_gap_score_sq",".3f"),("band_gap_score_si",".3f"),
        ("energy_above_hull",".4f"),("stability_score",".3f"),
        ("n",".2f"),("e_electronic",".2f"),("dielectric_score",".3f"),
        ("bulk_modulus_vrh",".0f"),("mechanical_score",".3f"),
        ("is_magnetic","s"),("magnetic_score",".2f"),
        ("direct_gap_bonus",".2f"),("semiconductor_score",".4f"),
    ]
    rows3 = []
    for _, r in alloy_cand.head(30).iterrows():
        row = [_v(r.get(c), f if f != "s" else "") for c, f in spec3]
        row[4]  = "Dir." if r.get("is_gap_direct") else "Ind."
        row[14] = "Sí"   if r.get("is_magnetic")   else "No"
        rows3.append(row)

    story.append(_tbl([hdr3]+rows3,
        widths=[0.7*inch,0.95*inch,0.38*inch,0.55*inch,0.42*inch,
                0.55*inch,0.55*inch,0.58*inch,0.55*inch,
                0.48*inch,0.5*inch,0.55*inch,
                0.5*inch,0.55*inch,
                0.4*inch,0.52*inch,0.52*inch,0.65*inch], gold_row1=True))
    story.append(Paragraph(
        "Tabla 3. Top-30 aleaciones candidatas con todos los atributos DFT.", cap))
    story.append(PageBreak())

    # ── Sec 4: Best alloys ───────────────────────────────────────────────
    story.append(Paragraph("4. Mejores Aleaciones — Criterios Estrictos", h1)); hr()
    story.append(Paragraph(
        "nelements≥2 · E_hull&lt;0.05 · is_stable · ¬magnético · "
        "0.5≤Eg≤3.5 · ¬tóxico · ¬escaso. "
        f"CSV: <i>{P['csv_best']}</i>", body))
    story.append(Spacer(1,4))

    if len(best) == 0:
        story.append(Paragraph("Sin resultados con los criterios actuales.",
                                _style(body, textColor=colors.red)))
    else:
        n_show = min(30, len(best))
        rows_a, rows_b = [], []
        for _, r in best.head(n_show).iterrows():
            elems = ",".join(sorted(parse_elements(str(r.get("elements","")))))
            if len(elems) > 22:
                elems = elems[:20] + "…"
            rows_a.append([
                str(r["material_id"]),
                str(r["formula"]),
                str(int(r["nelements"])),
                elems,
                str(r.get("crystal_system","-"))[:7],
                _v(r["band_gap"]),
                "Dir." if r.get("is_gap_direct") else "Ind.",
                _v(r.get("n"),".2f"),
                _v(r.get("e_total"),".1f"),
                _v(r.get("bulk_modulus_vrh"),".0f"),
                _v(r.get("shear_modulus_vrh"),".0f"),
                _v(r["energy_above_hull"],".4f"),
                _v(r.get("formation_energy_per_atom"),".3f"),
                "Sí" if r.get("is_stable") else "No",
                "Sí" if r.get("theoretical") else "No",
            ])
            rows_b.append([
                str(r["formula"]),
                _v(r.get("band_gap_score_sq"),".3f"),
                _v(r.get("band_gap_score_si"),".3f"),
                _v(r.get("stability_score"),".3f"),
                _v(r.get("dielectric_score"),".3f"),
                _v(r.get("mechanical_score"),".3f"),
                _v(r.get("magnetic_score"),".2f"),
                _v(r.get("direct_gap_bonus"),".2f"),
                _v(r["semiconductor_score"],".4f"),
            ])

        # Sub-table A: physical properties
        hdr_a = ["ID","Fórmula","n_el","Elementos","Sist.",
                 "Eg (eV)","Gap","n (DFT)","ε_tot","B (GPa)","G (GPa)",
                 "E_hull","ΔHf/át","Est.","Teór."]
        story.append(Paragraph("4a. Propiedades físicas DFT:", h1))
        story.append(_tbl([hdr_a]+rows_a,
            widths=[0.72*inch,0.9*inch,0.38*inch,1.15*inch,0.65*inch,
                    0.58*inch,0.45*inch,0.6*inch,0.55*inch,0.62*inch,0.62*inch,
                    0.6*inch,0.6*inch,0.42*inch,0.42*inch],
            gold_row1=True))
        story.append(Paragraph(
            f"Tabla 4a. Propiedades físicas — top-{n_show} mejores aleaciones "
            f"({len(best)} totales cumplen criterios estrictos).", cap))
        story.append(Spacer(1, 8))

        # Sub-table B: scores breakdown
        hdr_b = ["Fórmula","Sc_SQ","Sc_Si","Sc_Est.","Sc_Diel.",
                 "Sc_Mec.","Sc_Mag.","Bonus_Dir.","Score Total"]
        story.append(Paragraph("4b. Desglose de scores:", h1))
        story.append(_tbl([hdr_b]+rows_b,
            widths=[1.1*inch,0.75*inch,0.75*inch,0.75*inch,
                    0.75*inch,0.75*inch,0.75*inch,0.8*inch,0.85*inch],
            gold_row1=True))
        story.append(Paragraph(
            "Tabla 4b. Scores por componente — fila dorada = mejor aleación.", cap))
    story.append(PageBreak())

    # ── Sec 5: Element analysis ──────────────────────────────────────────
    story.append(Paragraph("5. Análisis por Elemento (JOIN M:N)", h1)); hr()
    story.append(Paragraph(
        f"Un elemento por fila. CSV: <i>{P['csv_elements']}</i>", body))
    story.append(Spacer(1,4))

    hdr5 = ["Elemento","N° mat.","Eg med.","E_hull med.",
            "n med.","B med.(GPa)","Sc_Di","Sc_Me",
            "Score med.","Estables","Dir.","No mag.","Tóxicos","Escasos"]
    rows5 = []
    for _, r in elem_df.head(25).iterrows():
        rows5.append([
            str(r["element"]).strip(),
            str(int(r["materials_count"])),
            _v(r["avg_band_gap"]),
            _v(r["avg_energy_above_hull"],".4f"),
            _v(r.get("avg_n"),".2f"),
            _v(r.get("avg_bulk_modulus_gpa"),".0f"),
            _v(r.get("avg_dielectric_score"),".3f"),
            _v(r.get("avg_mechanical_score"),".3f"),
            _v(r["avg_score"],".4f"),
            str(int(r.get("stable_count",0))),
            str(int(r.get("direct_gap_count",0))),
            str(int(r.get("non_magnetic_count",0))),
            str(int(r.get("toxic_count",0))),
            str(int(r.get("scarce_count",0))),
        ])
    story.append(_tbl([hdr5]+rows5,
        widths=[0.7*inch,0.55*inch,0.65*inch,0.75*inch,
                0.65*inch,0.75*inch,0.6*inch,0.6*inch,
                0.7*inch,0.6*inch,0.5*inch,0.62*inch,0.6*inch,0.6*inch]))
    story.append(Paragraph("Tabla 5. Top-25 elementos por score promedio.", cap))
    story.append(PageBreak())

    # ── Sec 6: Executive summary ─────────────────────────────────────────
    story.append(Paragraph("6. Resumen Ejecutivo", h1)); hr()

    sv = pd.read_csv(P["csv_silver"])
    kv = [["Indicador","Valor"]] + [
        ["Materiales en Silver",              str(len(sv))],
        ["Con n DFT real",                    str(sv["n"].notna().sum())],
        ["Con módulo volumétrico B (DFT)",    str(sv["bulk_modulus_vrh"].notna().sum())],
        ["Con brecha directa",                str((sv["is_gap_direct"]==True).sum())],
        ["Flagged tóxicos",                   str(sv["contains_toxic"].sum())],
        ["Flagged escasos",                   str(sv["contains_scarce"].sum())],
        ["Candidatos Top-200 (sin tóx/esc.)", str(len(top_all))],
        ["Candidatos aleaciones Top-200",     str(len(alloy_cand))],
        ["Mejores aleaciones (criterios est.)",str(len(best))],
        ["Score máximo",   _v(best["semiconductor_score"].max(),".4f") if len(best)>0 else "-"],
        ["Mejor aleación (fórmula)",          str(best.iloc[0]["formula"]) if len(best)>0 else "-"],
        ["Eg mejor aleación (eV)",            _v(best.iloc[0]["band_gap"])  if len(best)>0 else "-"],
        ["n mejor aleación",                  _v(best.iloc[0].get("n"),".2f") if len(best)>0 else "-"],
        ["B_VRH mejor aleación (GPa)",        _v(best.iloc[0].get("bulk_modulus_vrh"),".0f") if len(best)>0 else "-"],
        ["E_hull mejor aleación",             _v(best.iloc[0]["energy_above_hull"],".4f") if len(best)>0 else "-"],
    ]
    story.append(_tbl(kv, widths=[3.2*inch, 2.5*inch]))
    story.append(Paragraph("Tabla 6. Resumen ejecutivo.", cap))

    doc = SimpleDocTemplate(P["report"], pagesize=landscape(letter),
                            leftMargin=0.55*inch, rightMargin=0.55*inch,
                            topMargin=0.6*inch,  bottomMargin=0.5*inch)
    doc.build(story)
    print(f"[REPORT] {P['report']}")

# ── Orchestration ─────────────────────────────────────────────────────────────
def run_pipeline():
    t0 = time.time()
    ensure_dirs()
    extract_raw()
    bronze_layer()
    silver_layer()
    top_all, alloy_cand, best, elem_df = gold_layer()
    generate_all_plots(P["silver"], top_all, alloy_cand, best, elem_df)  # ← aquí
    generate_pdf(top_all, alloy_cand, best, elem_df)
    generate_pdf(top_all, alloy_cand, best, elem_df)
    from interactive_periodic_table import open_explorer  # opcional si lo conviertes a .py
    print(f"\nPipeline completado en {time.time()-t0:.1f}s")
    print("\nOutputs:")
    for k, v in P.items():
        if os.path.exists(v):
            print(f"  {k:18s}: {v}")

if __name__ == "__main__":
    run_pipeline()