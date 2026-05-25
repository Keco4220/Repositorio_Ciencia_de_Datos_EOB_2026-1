"""
plots_annex.py — Anexo de gráficas para el Semiconductor Alloy Discovery Pipeline
Generado para integrarse al pipeline principal (main.py / pipeline.py).

USO EN EL PIPELINE PRINCIPAL:
    from plots_annex import generate_all_plots
    # Llamar después de gold_layer() y antes o después de generate_pdf():
    generate_all_plots(silver_path, top_all, alloy_cand, best, elem_df)

DEPENDENCIAS (agregar a requirements si no están):
    matplotlib>=3.7
    seaborn>=0.12
    scipy>=1.10
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                        # backend sin pantalla
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.stats import gaussian_kde

warnings.filterwarnings("ignore")

# ── Directorio de salida ───────────────────────────────────────────────────────
PLOT_DIR = "artifacts/plots"

# ── Paleta corporativa (hereda colores del reporte PDF) ───────────────────────
C_DARK  = "#1A3A5C"
C_MID   = "#2E6DA4"
C_LITE  = "#D0E4F5"
C_GOLD  = "#C9992B"
C_RED   = "#C0392B"
C_GREEN = "#27AE60"
C_GREY  = "#7F8C8D"

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "font.family":       "DejaVu Sans",
    "axes.titlesize":    12,
    "axes.labelsize":    10,
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "legend.fontsize":   8,
    "figure.facecolor":  "white",
})

def _save(fig, name: str) -> str:
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  [PLOT] {path}")
    return path


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE S — SILVER (toda la capa limpia)
# ══════════════════════════════════════════════════════════════════════════════

def plot_s1_bandgap_histogram(sv: pd.DataFrame) -> str:
    """S1 · Histograma de distribución de band gap (Silver)."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(sv["band_gap"].dropna(), bins=60, color=C_MID, edgecolor="white", linewidth=0.4)
    ax.axvline(1.12, color=C_GOLD,  linestyle="--", linewidth=1.5, label="Si  1.12 eV")
    ax.axvline(1.34, color=C_RED,   linestyle="--", linewidth=1.5, label="S–Q 1.34 eV")
    ax.set_xlabel("Band Gap (eV)")
    ax.set_ylabel("N° de materiales")
    ax.set_title("S1 · Distribución de Band Gap — capa Silver")
    ax.legend()
    return _save(fig, "S1_bandgap_histogram.png")


def plot_s2_density_vs_bandgap(sv: pd.DataFrame) -> str:
    """S2 · Dispersión densidad vs band gap, coloreado por is_gap_direct."""
    df = sv[sv["density"].notna() & sv["band_gap"].notna()].copy()
    df["gap_type"] = df["is_gap_direct"].map({True: "Directa", False: "Indirecta"}).fillna("N/D")

    fig, ax = plt.subplots(figsize=(7, 5))
    colors_map = {"Directa": C_GREEN, "Indirecta": C_MID, "N/D": C_GREY}
    for gtype, grp in df.groupby("gap_type"):
        ax.scatter(grp["band_gap"], grp["density"],
                   alpha=0.45, s=14, color=colors_map[gtype], label=gtype)
    ax.axvline(1.12, color=C_GOLD, linestyle="--", linewidth=1.2, label="Si 1.12 eV")
    ax.axvline(1.34, color=C_RED,  linestyle="--", linewidth=1.2, label="S–Q 1.34 eV")
    ax.set_xlabel("Band Gap (eV)")
    ax.set_ylabel("Densidad (g/cm³)")
    ax.set_title("S2 · Densidad vs Band Gap — Silver")
    ax.legend(markerscale=1.8, framealpha=0.8)
    return _save(fig, "S2_density_vs_bandgap.png")


def plot_s3_density_by_nelements(sv: pd.DataFrame) -> str:
    """S3 · Barras de densidad promedio por número de elementos (aleaciones)."""
    grp = (sv.groupby("nelements")["density"]
             .agg(mean="mean", sem=lambda x: x.std() / np.sqrt(len(x)), count="count")
             .reset_index())
    grp = grp[grp["count"] >= 3]          # al menos 3 materiales

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(grp["nelements"].astype(str), grp["mean"],
                  yerr=grp["sem"], capsize=4,
                  color=C_MID, edgecolor=C_DARK, linewidth=0.6, error_kw={"ecolor": C_GREY})
    for bar, cnt in zip(bars, grp["count"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f"n={cnt}", ha="center", va="bottom", fontsize=7, color=C_GREY)
    ax.set_xlabel("Número de elementos (nelements)")
    ax.set_ylabel("Densidad promedio (g/cm³)")
    ax.set_title("S3 · Densidad promedio por N° de elementos — Silver")
    return _save(fig, "S3_density_by_nelements.png")


def plot_s4_scatter_density_nelements(sv: pd.DataFrame) -> str:
    """S4 · Dispersión densidad vs número de aleaciones (nelements)."""
    df = sv[sv["density"].notna()].copy()
    jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(df))

    fig, ax = plt.subplots(figsize=(7, 4))
    sc = ax.scatter(df["nelements"] + jitter, df["density"],
                    c=df["band_gap"], cmap="plasma", alpha=0.4, s=10)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Band Gap (eV)", fontsize=8)
    ax.set_xlabel("N° de elementos (jitter ±0.15)")
    ax.set_ylabel("Densidad (g/cm³)")
    ax.set_title("S4 · Dispersión Densidad vs N° de elementos — Silver")
    ax.set_xticks(sorted(df["nelements"].unique()))
    return _save(fig, "S4_scatter_density_nelements.png")


def plot_s5_score_distribution(sv: pd.DataFrame) -> str:
    """S5 · Distribución del semiconductor_score con KDE."""
    scores = sv["semiconductor_score"].dropna()

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(scores, bins=70, density=True, color=C_LITE, edgecolor="white",
            linewidth=0.3, label="Histograma")
    kde_x = np.linspace(scores.min(), scores.max(), 400)
    kde   = gaussian_kde(scores, bw_method=0.15)
    ax.plot(kde_x, kde(kde_x), color=C_DARK, linewidth=2, label="KDE")
    ax.axvline(scores.quantile(0.90), color=C_GOLD, linestyle="--",
               linewidth=1.4, label="P90")
    ax.axvline(scores.quantile(0.95), color=C_RED,  linestyle="--",
               linewidth=1.4, label="P95")
    ax.set_xlabel("semiconductor_score")
    ax.set_ylabel("Densidad de probabilidad")
    ax.set_title("S5 · Distribución del Score Semiconductor — Silver")
    ax.legend()
    return _save(fig, "S5_score_distribution.png")


def plot_s6_stability_vs_score(sv: pd.DataFrame) -> str:
    """S6 · Energy above hull vs semiconductor_score (color = is_stable)."""
    df = sv[sv["energy_above_hull"].notna() & sv["semiconductor_score"].notna()].copy()
    df["estable"] = df["is_stable"].map({True: "Estable", False: "No estable"}).fillna("N/D")

    fig, ax = plt.subplots(figsize=(7, 5))
    cmap = {"Estable": C_GREEN, "No estable": C_RED, "N/D": C_GREY}
    for label, grp in df.groupby("estable"):
        ax.scatter(grp["semiconductor_score"], grp["energy_above_hull"],
                   alpha=0.4, s=12, color=cmap[label], label=label)
    ax.axhline(0.05, color=C_GOLD, linestyle="--", linewidth=1.3, label="E_hull = 0.05 eV")
    ax.set_xlabel("semiconductor_score")
    ax.set_ylabel("Energy above hull (eV/atom)")
    ax.set_title("S6 · Estabilidad vs Score — Silver")
    ax.set_ylim(-0.01, 0.22)
    ax.legend(markerscale=1.8)
    return _save(fig, "S6_stability_vs_score.png")


def plot_s7_crystal_system_counts(sv: pd.DataFrame) -> str:
    """S7 · Barras del conteo de materiales por sistema cristalino."""
    counts = sv["crystal_system"].value_counts().reset_index()
    counts.columns = ["crystal_system", "count"]

    fig, ax = plt.subplots(figsize=(7, 4))
    palette = sns.color_palette("Blues_d", len(counts))
    ax.barh(counts["crystal_system"], counts["count"],
            color=palette, edgecolor=C_DARK, linewidth=0.5)
    for i, (_, row) in enumerate(counts.iterrows()):
        ax.text(row["count"] + 5, i, str(row["count"]), va="center", fontsize=8)
    ax.set_xlabel("N° de materiales")
    ax.set_title("S7 · Materiales por sistema cristalino — Silver")
    ax.invert_yaxis()
    return _save(fig, "S7_crystal_system_counts.png")


def plot_s8_dielectric_vs_bandgap(sv: pd.DataFrame) -> str:
    """S8 · Índice de refracción n (DFT) vs band gap."""
    df = sv[sv["n"].notna() & sv["band_gap"].notna() & (sv["n"] < 10)].copy()

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(df["band_gap"], df["n"],
                    c=df["semiconductor_score"], cmap="viridis",
                    alpha=0.45, s=14)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("semiconductor_score", fontsize=8)
    ax.axhspan(2.5, 4.0, alpha=0.08, color=C_GREEN, label="Rango ideal n [2.5–4.0]")
    ax.set_xlabel("Band Gap (eV)")
    ax.set_ylabel("Índice de refracción n (DFT)")
    ax.set_title("S8 · Índice de refracción vs Band Gap — Silver")
    ax.legend()
    return _save(fig, "S8_dielectric_vs_bandgap.png")


def plot_s9_bulk_modulus_boxplot(sv: pd.DataFrame) -> str:
    """S9 · Boxplot del módulo volumétrico B_VRH por tipo de gap."""
    df = sv[sv["bulk_modulus_vrh"].notna()].copy()
    df["gap_type"] = df["is_gap_direct"].map({True: "Directa", False: "Indirecta"}).fillna("N/D")

    fig, ax = plt.subplots(figsize=(6, 4))
    order = ["Directa", "Indirecta", "N/D"]
    colors_bp = [C_GREEN, C_MID, C_GREY]
    bp = ax.boxplot(
        [df.loc[df["gap_type"] == g, "bulk_modulus_vrh"].values for g in order],
        labels=order, patch_artist=True, notch=False,
        medianprops={"color": C_GOLD, "linewidth": 2},
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.4},
    )
    for patch, c in zip(bp["boxes"], colors_bp):
        patch.set_facecolor(c); patch.set_alpha(0.6)
    ax.axhline(130, color=C_RED, linestyle="--", linewidth=1.2, label="B ideal 130 GPa")
    ax.set_ylabel("B_VRH (GPa)")
    ax.set_title("S9 · Módulo volumétrico por tipo de gap — Silver")
    ax.legend()
    return _save(fig, "S9_bulk_modulus_boxplot.png")


def plot_s10_score_components_heatmap(sv: pd.DataFrame) -> str:
    """S10 · Heatmap de correlación entre sub-scores y propiedades clave."""
    cols = ["band_gap", "density", "energy_above_hull", "n", "bulk_modulus_vrh",
            "band_gap_score_sq", "band_gap_score_si", "stability_score",
            "dielectric_score", "mechanical_score", "semiconductor_score"]
    corr = sv[[c for c in cols if c in sv.columns]].corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", linewidths=0.4,
                cmap="coolwarm", center=0, ax=ax,
                annot_kws={"size": 7}, square=True)
    ax.set_title("S10 · Correlación: propiedades DFT y sub-scores — Silver", pad=10)
    return _save(fig, "S10_score_components_heatmap.png")


def plot_s11_toxic_scarce_flags(sv: pd.DataFrame) -> str:
    """S11 · Barras apiladas: materiales sin/con toxicidad y escasez."""
    labels  = ["Sin flag", "Tóxicos", "Escasos", "Tóxicos\n+Escasos"]
    neither = (~sv["contains_toxic"] & ~sv["contains_scarce"]).sum()
    only_t  = ( sv["contains_toxic"] & ~sv["contains_scarce"]).sum()
    only_s  = (~sv["contains_toxic"] &  sv["contains_scarce"]).sum()
    both    = ( sv["contains_toxic"] &  sv["contains_scarce"]).sum()
    counts  = [neither, only_t, only_s, both]

    fig, ax = plt.subplots(figsize=(6, 4))
    palette = [C_GREEN, C_RED, C_GOLD, "#8E44AD"]
    bars = ax.bar(labels, counts, color=palette, edgecolor=C_DARK, linewidth=0.6)
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                str(cnt), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_ylabel("N° de materiales")
    ax.set_title("S11 · Flags de toxicidad y escasez — Silver")
    return _save(fig, "S11_toxic_scarce_flags.png")


def plot_s12_formation_energy_violin(sv: pd.DataFrame) -> str:
    """S12 · Violín de formation_energy_per_atom por nelements."""
    df = sv[sv["formation_energy_per_atom"].notna() & sv["nelements"].notna()].copy()
    df = df[df["nelements"] <= 5]

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.violinplot(data=df, x="nelements", y="formation_energy_per_atom",
                   palette="muted", inner="quartile", ax=ax, linewidth=0.8)
    ax.axhline(0, color=C_RED, linestyle="--", linewidth=1.2, label="ΔHf = 0")
    ax.set_xlabel("N° de elementos")
    ax.set_ylabel("ΔHf / átomo (eV)")
    ax.set_title("S12 · Energía de formación por N° de elementos — Silver")
    ax.legend()
    return _save(fig, "S12_formation_energy_violin.png")


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE G — GOLD (candidatos filtrados)
# ══════════════════════════════════════════════════════════════════════════════

def plot_g1_top_score_bar(top_all: pd.DataFrame) -> str:
    """G1 · Barras horizontales: top-20 candidatos por semiconductor_score."""
    df = top_all.head(20).copy()
    df["label"] = df["formula"].astype(str)
    df = df.sort_values("semiconductor_score")

    fig, ax = plt.subplots(figsize=(8, 6))
    colors_bars = [C_GOLD if r["is_gap_direct"] else C_MID
                   for _, r in df.iterrows()]
    ax.barh(df["label"], df["semiconductor_score"],
            color=colors_bars, edgecolor=C_DARK, linewidth=0.5)
    ax.set_xlabel("semiconductor_score")
    ax.set_title("G1 · Top-20 candidatos por score — Gold")
    gold_p = mpatches.Patch(color=C_GOLD, label="Gap directo")
    blue_p = mpatches.Patch(color=C_MID,  label="Gap indirecto")
    ax.legend(handles=[gold_p, blue_p])
    return _save(fig, "G1_top_score_bar.png")


def plot_g2_bandgap_score_bubble(top_all: pd.DataFrame) -> str:
    """G2 · Burbuja: band_gap vs score, tamaño = densidad, color = nelements."""
    df = top_all[top_all["density"].notna()].copy()

    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(df["band_gap"], df["semiconductor_score"],
                    s=df["density"] * 15, alpha=0.6,
                    c=df["nelements"], cmap="viridis", edgecolors=C_DARK, linewidths=0.3)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("N° de elementos", fontsize=8)
    ax.axvline(1.12, color=C_GOLD, linestyle="--", linewidth=1.2, label="Si 1.12 eV")
    ax.axvline(1.34, color=C_RED,  linestyle="--", linewidth=1.2, label="S–Q 1.34 eV")
    ax.set_xlabel("Band Gap (eV)")
    ax.set_ylabel("semiconductor_score")
    ax.set_title("G2 · Band Gap vs Score (burbuja = densidad) — Gold Top-200")
    ax.legend()
    return _save(fig, "G2_bandgap_score_bubble.png")


def plot_g3_alloy_score_components(alloy_cand: pd.DataFrame) -> str:
    """G3 · Radar / barras apiladas de sub-scores para top-10 aleaciones."""
    df = alloy_cand.head(10).copy()
    sub = ["band_gap_score_sq", "band_gap_score_si", "stability_score",
           "dielectric_score", "mechanical_score", "magnetic_score", "direct_gap_bonus"]
    sub = [c for c in sub if c in df.columns]
    df_plot = df[["formula"] + sub].set_index("formula")

    fig, ax = plt.subplots(figsize=(10, 5))
    palette = sns.color_palette("tab10", len(sub))
    bottom = np.zeros(len(df_plot))
    for col, color in zip(sub, palette):
        ax.bar(df_plot.index, df_plot[col], bottom=bottom,
               label=col.replace("_score","").replace("_"," "), color=color,
               edgecolor="white", linewidth=0.4)
        bottom += df_plot[col].values
    ax.set_ylabel("Contribución al score")
    ax.set_title("G3 · Desglose de sub-scores — Top-10 aleaciones Gold")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)
    plt.xticks(rotation=30, ha="right")
    return _save(fig, "G3_alloy_score_components.png")


def plot_g4_density_vs_bandgap_gold(top_all: pd.DataFrame) -> str:
    """G4 · Dispersión densidad vs band gap (Gold), anotando top-5."""
    df = top_all[top_all["density"].notna()].copy()

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df["band_gap"], df["density"],
               c=df["semiconductor_score"], cmap="plasma", alpha=0.6, s=20,
               edgecolors=C_DARK, linewidths=0.3)
    # anotar top 5
    for _, row in df.head(5).iterrows():
        ax.annotate(str(row["formula"]),
                    (row["band_gap"], row["density"]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points",
                    color=C_DARK, fontweight="bold")
    ax.axvline(1.12, color=C_GOLD, linestyle="--", linewidth=1.2, label="Si 1.12 eV")
    ax.axvline(1.34, color=C_RED,  linestyle="--", linewidth=1.2, label="S–Q 1.34 eV")
    ax.set_xlabel("Band Gap (eV)")
    ax.set_ylabel("Densidad (g/cm³)")
    ax.set_title("G4 · Densidad vs Band Gap — Gold Top-200")
    ax.legend()
    return _save(fig, "G4_density_vs_bandgap_gold.png")


def plot_g5_best_alloys_parallel(best: pd.DataFrame) -> str:
    """G5 · Coordenadas paralelas para mejores aleaciones (criterios estrictos)."""
    if len(best) == 0:
        print("  [PLOT] G5 omitido: sin mejores aleaciones.")
        return ""
    cols = ["band_gap", "energy_above_hull", "density", "n",
            "bulk_modulus_vrh", "semiconductor_score"]
    cols = [c for c in cols if c in best.columns]
    df = best.head(30)[cols].copy().dropna()

    # normalizar 0-1
    df_norm = (df - df.min()) / (df.max() - df.min() + 1e-12)
    df_norm["formula"] = best.head(30)["formula"].values[:len(df_norm)]

    fig, ax = plt.subplots(figsize=(10, 5))
    cmap = plt.cm.viridis
    for i, (_, row) in enumerate(df_norm.iterrows()):
        color = cmap(i / max(len(df_norm) - 1, 1))
        ax.plot(range(len(cols)), [row[c] for c in cols],
                color=color, alpha=0.5, linewidth=1.2)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c.replace("_", "\n") for c in cols], fontsize=8)
    ax.set_ylabel("Valor normalizado [0–1]")
    ax.set_title("G5 · Coordenadas paralelas — mejores aleaciones (criterios estrictos)")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, len(df_norm)-1))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", pad=0.01)
    cbar.set_label("Ranking (0 = mejor)", fontsize=7)
    return _save(fig, "G5_best_alloys_parallel.png")


def plot_g6_element_score_bar(elem_df: pd.DataFrame) -> str:
    """G6 · Top-20 elementos por avg_score (JOIN M:N)."""
    df = elem_df.head(20).sort_values("avg_score")

    fig, ax = plt.subplots(figsize=(7, 6))
    palette = sns.color_palette("viridis_r", len(df))
    ax.barh(df["element"].astype(str), df["avg_score"],
            color=palette, edgecolor=C_DARK, linewidth=0.5)
    ax.set_xlabel("Score promedio")
    ax.set_title("G6 · Top-20 elementos por score promedio — análisis M:N Gold")
    return _save(fig, "G6_element_score_bar.png")


def plot_g7_element_bandgap_scatter(elem_df: pd.DataFrame) -> str:
    """G7 · Dispersión: avg_band_gap vs materials_count, tamaño = avg_score."""
    df = elem_df[elem_df["avg_band_gap"].notna()].copy()

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(df["avg_band_gap"], df["materials_count"],
                    s=df["avg_score"] * 400, alpha=0.7,
                    c=df["avg_score"], cmap="YlOrRd",
                    edgecolors=C_DARK, linewidths=0.4)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("avg_score", fontsize=8)
    for _, row in df.head(10).iterrows():
        ax.annotate(str(row["element"]),
                    (row["avg_band_gap"], row["materials_count"]),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.axvline(1.12, color=C_GOLD, linestyle="--", linewidth=1.1, label="Si 1.12 eV")
    ax.axvline(1.34, color=C_RED,  linestyle="--", linewidth=1.1, label="S–Q 1.34 eV")
    ax.set_xlabel("Band Gap promedio (eV)")
    ax.set_ylabel("N° de materiales en Gold")
    ax.set_title("G7 · Elementos: band gap promedio vs frecuencia — Gold M:N")
    ax.legend()
    return _save(fig, "G7_element_bandgap_scatter.png")


def plot_g8_stable_direct_fraction(elem_df: pd.DataFrame) -> str:
    """G8 · Barras agrupadas: fracción de materiales estables y gap directo por elemento (top-15)."""
    df = elem_df.head(15).copy()
    df["frac_stable"] = df["stable_count"] / df["materials_count"]
    df["frac_direct"] = df["direct_gap_count"] / df["materials_count"]

    x = np.arange(len(df))
    w = 0.35
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(x - w/2, df["frac_stable"], w, label="Fracción estable",
           color=C_GREEN, edgecolor=C_DARK, linewidth=0.5, alpha=0.85)
    ax.bar(x + w/2, df["frac_direct"], w, label="Fracción gap directo",
           color=C_GOLD,  edgecolor=C_DARK, linewidth=0.5, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(df["element"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Fracción [0–1]")
    ax.set_title("G8 · Fracción estable y gap directo por elemento — Gold Top-15")
    ax.legend()
    return _save(fig, "G8_stable_direct_fraction.png")


def plot_g9_score_vs_nelements_violin(top_all: pd.DataFrame) -> str:
    """G9 · Violín del semiconductor_score por número de elementos — Gold."""
    df = top_all[top_all["nelements"] <= 5].copy()

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.violinplot(data=df, x="nelements", y="semiconductor_score",
                   palette="muted", inner="quartile", ax=ax, linewidth=0.8)
    ax.set_xlabel("N° de elementos")
    ax.set_ylabel("semiconductor_score")
    ax.set_title("G9 · Score semiconductor por N° de elementos — Gold Top-200")
    return _save(fig, "G9_score_vs_nelements_violin.png")


def plot_g10_hull_vs_formation(top_all: pd.DataFrame) -> str:
    """G10 · Dispersión energy_above_hull vs formation_energy_per_atom."""
    df = top_all[top_all["formation_energy_per_atom"].notna() &
                 top_all["energy_above_hull"].notna()].copy()

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(df["formation_energy_per_atom"], df["energy_above_hull"],
                    c=df["semiconductor_score"], cmap="plasma", alpha=0.55, s=18,
                    edgecolors="none")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("semiconductor_score", fontsize=8)
    ax.axhline(0.05, color=C_RED,  linestyle="--", linewidth=1.2, label="E_hull = 0.05 eV")
    ax.axhline(0.0,  color=C_GREY, linestyle=":",  linewidth=0.8, label="Hull = 0")
    ax.set_xlabel("ΔHf / átomo (eV)")
    ax.set_ylabel("Energy above hull (eV/atom)")
    ax.set_title("G10 · E_hull vs ΔHf — Gold Top-200")
    ax.legend()
    return _save(fig, "G10_hull_vs_formation.png")


def plot_g11_crystal_system_gold(top_all: pd.DataFrame) -> str:
    """G11 · Pie chart de sistemas cristalinos en Gold."""
    counts = top_all["crystal_system"].value_counts()

    fig, ax = plt.subplots(figsize=(6, 5))
    wedge_props = {"edgecolor": "white", "linewidth": 1.2}
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%",
           startangle=140, wedgeprops=wedge_props,
           colors=sns.color_palette("Blues_d", len(counts)))
    ax.set_title("G11 · Sistemas cristalinos — Gold Top-200")
    return _save(fig, "G11_crystal_system_gold.png")


def plot_g12_work_function_vs_score(top_all: pd.DataFrame) -> str:
    """G12 · Función de trabajo ponderada vs semiconductor_score."""
    df = top_all[top_all["weighted_work_function"].notna()].copy()
    if len(df) < 5:
        print("  [PLOT] G12 omitido: datos insuficientes de work function.")
        return ""

    fig, ax = plt.subplots(figsize=(7, 4))
    sc = ax.scatter(df["weighted_work_function"], df["semiconductor_score"],
                    c=df["band_gap"], cmap="viridis", alpha=0.6, s=16,
                    edgecolors=C_DARK, linewidths=0.3)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Band Gap (eV)", fontsize=8)
    ax.set_xlabel("Función de trabajo ponderada (eV)")
    ax.set_ylabel("semiconductor_score")
    ax.set_title("G12 · Función de trabajo vs Score — Gold Top-200")
    return _save(fig, "G12_work_function_vs_score.png")


# ══════════════════════════════════════════════════════════════════════════════
#  ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def generate_all_plots(
    silver_path: str,
    top_all:    pd.DataFrame,
    alloy_cand: pd.DataFrame,
    best:       pd.DataFrame,
    elem_df:    pd.DataFrame,
) -> list[str]:
    """
    Genera todas las gráficas Silver + Gold y las guarda en artifacts/plots/.

    Parámetros
    ----------
    silver_path : ruta al parquet de Silver (ej. P["silver"])
    top_all     : DataFrame Gold top-200
    alloy_cand  : DataFrame Gold aleaciones top-200
    best        : DataFrame mejores aleaciones (criterios estrictos)
    elem_df     : DataFrame análisis M:N por elemento

    Retorna
    -------
    Lista de rutas de archivos PNG generados.
    """
    print("\n[PLOTS] Generando anexo de gráficas...")
    sv = pd.read_parquet(silver_path)
    paths = []

    # ── Silver ────────────────────────────────────────────────────────────
    silver_funcs = [
        (plot_s1_bandgap_histogram,      (sv,)),
        (plot_s2_density_vs_bandgap,     (sv,)),
        (plot_s3_density_by_nelements,   (sv,)),
        (plot_s4_scatter_density_nelements,(sv,)),
        (plot_s5_score_distribution,     (sv,)),
        (plot_s6_stability_vs_score,     (sv,)),
        (plot_s7_crystal_system_counts,  (sv,)),
        (plot_s8_dielectric_vs_bandgap,  (sv,)),
        (plot_s9_bulk_modulus_boxplot,   (sv,)),
        (plot_s10_score_components_heatmap,(sv,)),
        (plot_s11_toxic_scarce_flags,    (sv,)),
        (plot_s12_formation_energy_violin,(sv,)),
    ]

    # ── Gold ──────────────────────────────────────────────────────────────
    gold_funcs = [
        (plot_g1_top_score_bar,           (top_all,)),
        (plot_g2_bandgap_score_bubble,    (top_all,)),
        (plot_g3_alloy_score_components,  (alloy_cand,)),
        (plot_g4_density_vs_bandgap_gold, (top_all,)),
        (plot_g5_best_alloys_parallel,    (best,)),
        (plot_g6_element_score_bar,       (elem_df,)),
        (plot_g7_element_bandgap_scatter, (elem_df,)),
        (plot_g8_stable_direct_fraction,  (elem_df,)),
        (plot_g9_score_vs_nelements_violin,(top_all,)),
        (plot_g10_hull_vs_formation,      (top_all,)),
        (plot_g11_crystal_system_gold,    (top_all,)),
        (plot_g12_work_function_vs_score, (top_all,)),
    ]

    for func, args in silver_funcs + gold_funcs:
        try:
            p = func(*args)
            if p:
                paths.append(p)
        except Exception as exc:
            print(f"  [PLOT] ⚠ {func.__name__} falló: {exc}")

    print(f"[PLOTS] {len(paths)} gráficas guardadas en '{PLOT_DIR}/'")
    return paths
