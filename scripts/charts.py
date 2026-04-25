"""
charts.py
Génère des graphiques Matplotlib pour visualiser les ventes.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from typing import Dict, Any

COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe",
          "#ec4899", "#f43f5e", "#fb923c", "#facc15", "#34d399"]

OUTPUT_DIR = "static/images"


def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def chart_ca_by_product(summary: Dict[str, Any]) -> str:
    ensure_dir()
    top5 = sorted(summary["by_product"].items(), key=lambda x: x[1], reverse=True)[:15]
    names = [t[0][:15] + "…" if len(t[0]) > 15 else t[0] for t in top5]
    values = [t[1] for t in top5]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    bars = ax.barh(names, values, color=COLORS[:len(names)], height=0.5, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}DT", va="center", ha="left", color="white", fontsize=9, fontweight="bold")

    ax.set_xlabel("CA Net (DT)", color="#94a3b8", fontsize=10)
    ax.set_title("Top 5 Produits par CA Net", color="white", fontsize=13, fontweight="bold", pad=15)
    ax.tick_params(colors="#94a3b8")
    ax.spines[:].set_visible(False)
    ax.xaxis.label.set_color("#94a3b8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.set_xlim(0, max(values) * 1.2)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart_products.png"
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def chart_ca_by_category(summary: Dict[str, Any]) -> str:
    ensure_dir()
    cats = summary["by_category"]
    labels = list(cats.keys())
    values = list(cats.values())

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%",
        colors=COLORS[:len(labels)], startangle=140,
        wedgeprops={"edgecolor": "#0f172a", "linewidth": 2},
        pctdistance=0.75
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9)
        at.set_fontweight("bold")

    legend = ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.12),
                       ncol=3, fontsize=8, frameon=False, labelcolor="#cbd5e1")
    ax.set_title("Répartition CA par Catégorie", color="white", fontsize=13, fontweight="bold", pad=10)

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart_categories.png"
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def chart_monthly_ca(summary: Dict[str, Any]) -> str:
    ensure_dir()
    monthly = summary["monthly_ca"]
    months = list(monthly.keys())
    values = list(monthly.values())

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    ax.fill_between(range(len(months)), values, alpha=0.25, color="#6366f1")
    ax.plot(range(len(months)), values, color="#6366f1", linewidth=2.5, marker="o",
            markersize=5, markerfacecolor="white", markeredgecolor="#6366f1")

    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, color="#94a3b8", fontsize=9)
    ax.set_ylabel("CA Net (DT)", color="#94a3b8", fontsize=10)
    ax.set_title("Évolution Mensuelle du CA Net", color="white", fontsize=13, fontweight="bold", pad=15)
    ax.tick_params(colors="#94a3b8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_edgecolor("#334155")
    ax.spines["bottom"].set_edgecolor("#334155")
    ax.yaxis.set_tick_params(labelcolor="#94a3b8")
    ax.grid(axis="y", color="#1e293b", linestyle="--", linewidth=0.8, alpha=0.5)

    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart_monthly.png"
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def generate_all_charts(summary: Dict[str, Any]) -> Dict[str, str]:
    paths = {
        "products": chart_ca_by_product(summary),
        "categories": chart_ca_by_category(summary),
        "monthly": chart_monthly_ca(summary),
    }
    print("✅ Graphiques générés :", list(paths.values()))
    return paths


def chart_ca_single_product(product_name: str, summary: Dict[str, Any]) -> str:
    ensure_dir()
    
    rows = [r for r in summary.get("rows", []) if r.get("Produit") == product_name]
    if not rows:
        return ""
    
    total_ca_brut = sum(float(r["CA_Brut"]) for r in rows)
    total_ca_net  = sum(float(r["CA_Net"]) for r in rows)
    total_tva     = sum(float(r["TVA"]) for r in rows)
    total_ca_ttc  = sum(float(r["CA_TTC"]) for r in rows)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#0f172a")

    # Graphique 1 : barres CA Brut vs CA Net vs TVA vs TTC
    ax1.set_facecolor("#1e293b")
    labels = ["CA Brut", "CA Net", "TVA", "CA TTC"]
    values = [total_ca_brut, total_ca_net, total_tva, total_ca_ttc]
    colors = ["#8b5cf6", "#6366f1", "#f59e0b", "#10b981"]
    bars = ax1.bar(labels, values, color=colors, edgecolor="none", width=0.5)
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                f"{val:,.0f} DT", ha="center", va="bottom", color="white", fontsize=9, fontweight="bold")
    ax1.set_title(f"CA Total — {product_name}", color="white", fontsize=12, fontweight="bold", pad=15)
    ax1.set_ylabel("Montant (DT)", color="#94a3b8", fontsize=10)
    ax1.tick_params(colors="#94a3b8")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_edgecolor("#334155")
    ax1.spines["bottom"].set_edgecolor("#334155")

    # Graphique 2 : camembert répartition
    ax2.set_facecolor("#0f172a")
    remise = total_ca_brut - total_ca_net
    wedges, _, autotexts = ax2.pie(
        [total_ca_net, remise, total_tva],
        labels=None,
        autopct="%1.1f%%",
        colors=["#6366f1", "#f43f5e", "#f59e0b"],
        startangle=140,
        wedgeprops={"edgecolor": "#0f172a", "linewidth": 2},
        pctdistance=0.75
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9)
        at.set_fontweight("bold")
    ax2.legend(wedges, ["CA Net", "Remise", "TVA"],
               loc="lower center", bbox_to_anchor=(0.5, -0.12),
               ncol=3, fontsize=8, frameon=False, labelcolor="#cbd5e1")
    ax2.set_title(f"Répartition — {product_name}", color="white", fontsize=12, fontweight="bold", pad=15)

    plt.tight_layout()
    safe_name = product_name.replace(" ", "_").replace("/", "_")
    path = f"{OUTPUT_DIR}/chart_prod_{safe_name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path