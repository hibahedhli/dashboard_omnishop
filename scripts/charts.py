"""
charts.py
Generate Matplotlib charts for the generic sales intelligence dashboard.
"""

import re
from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "static" / "images"


def ensure_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(value: str) -> str:
    """Create a safe filename from a product name."""
    value = str(value).strip()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    return value[:100] or "product"


def _format_dt(value: float) -> str:
    """Format a monetary value for chart labels."""
    return f"{value:,.2f} DT"


def _style_axes(ax):
    """Apply the dashboard's dark chart styling."""
    ax.set_facecolor("#1e293b")

    ax.tick_params(colors="#94a3b8")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_edgecolor("#334155")
    ax.spines["bottom"].set_edgecolor("#334155")

    ax.grid(
        axis="y",
        color="#334155",
        linestyle="--",
        linewidth=0.7,
        alpha=0.5,
    )


def chart_ca_by_product(summary: Dict[str, Any]) -> str:
    """
    Generate a horizontal bar chart of the top products by revenue.
    """
    ensure_dir()

    top_products = summary.get("top5_products", [])

    if not top_products:
        return ""

    names = [
        str(product.get("product_name") or product.get("product_id") or "Unknown")
        for product in top_products
    ]

    values = [
        float(product.get("revenue", 0))
        for product in top_products
    ]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor("#0f172a")

    bars = ax.barh(
        names[::-1],
        values[::-1],
        color="#6366f1",
        height=0.55,
        edgecolor="none",
    )

    max_value = max(values) if values else 1

    for bar, value in zip(bars, values[::-1]):
        ax.text(
            bar.get_width() + max_value * 0.015,
            bar.get_y() + bar.get_height() / 2,
            _format_dt(value),
            va="center",
            ha="left",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    _style_axes(ax)

    ax.set_xlabel(
        "Revenue (DT)",
        color="#94a3b8",
        fontsize=10,
    )

    ax.set_title(
        "Top 5 Products by Revenue",
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    ax.set_xlim(0, max_value * 1.25)

    plt.tight_layout()

    path = OUTPUT_DIR / "chart_products.png"

    fig.savefig(
        path,
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return str(path)


def chart_ca_by_category(summary: Dict[str, Any]) -> str:
    """
    Generate revenue distribution by category.

    Returns an empty string when category data is unavailable.
    """
    ensure_dir()

    if not summary.get("has_category", False):
        return ""

    categories = summary.get("by_category", {})

    if not categories:
        return ""

    categories = {
        str(category): float(value)
        for category, value in categories.items()
        if value is not None
    }

    if not categories:
        return ""

    labels = list(categories.keys())
    values = list(categories.values())

    fig, ax = plt.subplots(figsize=(7, 5.5))
    fig.patch.set_facecolor("#0f172a")

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops={
            "edgecolor": "#0f172a",
            "linewidth": 2,
        },
        pctdistance=0.75,
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    legend = ax.legend(
        wedges,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        fontsize=8,
        frameon=False,
        labelcolor="#cbd5e1",
    )

    ax.set_title(
        "Revenue by Category",
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=10,
    )

    plt.tight_layout()

    path = OUTPUT_DIR / "chart_categories.png"

    fig.savefig(
        path,
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return str(path)


def chart_monthly_ca(summary: Dict[str, Any]) -> str:
    """
    Generate monthly revenue evolution.

    Returns an empty string when date information is unavailable.
    """
    ensure_dir()

    if not summary.get("has_date", False):
        return ""

    monthly = summary.get("monthly_ca", {})

    if not monthly:
        return ""

    months = list(monthly.keys())
    values = [
        float(monthly[month])
        for month in months
    ]

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#0f172a")

    _style_axes(ax)

    x = range(len(months))

    ax.fill_between(
        x,
        values,
        alpha=0.20,
        color="#6366f1",
    )

    ax.plot(
        x,
        values,
        color="#6366f1",
        linewidth=2.5,
        marker="o",
        markersize=5,
        markerfacecolor="white",
        markeredgecolor="#6366f1",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        months,
        color="#94a3b8",
        fontsize=9,
    )

    ax.set_ylabel(
        "Revenue (DT)",
        color="#94a3b8",
        fontsize=10,
    )

    ax.set_title(
        "Monthly Revenue Evolution",
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    plt.tight_layout()

    path = OUTPUT_DIR / "chart_monthly.png"

    fig.savefig(
        path,
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return str(path)


def chart_ca_single_product(
    product_name: str,
    summary: Dict[str, Any],
) -> str:
    """
    Generate detailed revenue analysis for one product.
    """
    ensure_dir()

    product_name = str(product_name).strip()

    rows = [
        row
        for row in summary.get("rows", [])
        if str(row.get("product_name") or "").strip().lower()
        == product_name.lower()
    ]

    if not rows:
        return ""

    total_gross = sum(
        float(row.get("CA_Brut", 0))
        for row in rows
    )

    total_discount = sum(
        float(row.get("Remise_Montant", 0))
        for row in rows
    )

    total_net = sum(
        float(row.get("CA_Net", 0))
        for row in rows
    )

    total_tax = sum(
        float(row.get("TVA", 0))
        for row in rows
    )

    total_ttc = sum(
        float(row.get("CA_TTC", 0))
        for row in rows
    )

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(12, 4.8),
    )

    fig.patch.set_facecolor("#0f172a")

    # ---------------------------------------------------------
    # Chart 1: gross -> discount -> net revenue
    # ---------------------------------------------------------

    ax1.set_facecolor("#1e293b")

    labels = [
        "Gross Revenue",
        "Discount",
        "Net Revenue",
    ]

    values = [
        total_gross,
        total_discount,
        total_net,
    ]

    bars = ax1.bar(
        labels,
        values,
        color=[
            "#8b5cf6",
            "#f43f5e",
            "#6366f1",
        ],
        edgecolor="none",
        width=0.55,
    )

    max_value = max(values) if values else 1

    for bar, value in zip(bars, values):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_value * 0.02,
            _format_dt(value),
            ha="center",
            va="bottom",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    _style_axes(ax1)

    ax1.set_ylabel(
        "Amount (DT)",
        color="#94a3b8",
        fontsize=10,
    )

    ax1.set_title(
        f"Revenue — {product_name}",
        color="white",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )

    ax1.set_ylim(0, max_value * 1.25)

    # ---------------------------------------------------------
    # Chart 2: useful financial indicators
    # ---------------------------------------------------------

    ax2.set_facecolor("#1e293b")

    indicator_labels = [
        "Net Revenue",
        "VAT",
        "Gross incl. VAT",
    ]

    indicator_values = [
        total_net,
        total_tax,
        total_ttc,
    ]

    bars2 = ax2.bar(
        indicator_labels,
        indicator_values,
        color=[
            "#6366f1",
            "#f59e0b",
            "#10b981",
        ],
        edgecolor="none",
        width=0.55,
    )

    max_indicator = max(indicator_values) if indicator_values else 1

    for bar, value in zip(bars2, indicator_values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_indicator * 0.02,
            _format_dt(value),
            ha="center",
            va="bottom",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    _style_axes(ax2)

    ax2.set_ylabel(
        "Amount (DT)",
        color="#94a3b8",
        fontsize=10,
    )

    ax2.set_title(
        "Financial Indicators",
        color="white",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )

    ax2.set_ylim(0, max_indicator * 1.25)

    plt.tight_layout()

    safe_name = _safe_filename(product_name)

    path = OUTPUT_DIR / f"chart_prod_{safe_name}.png"

    fig.savefig(
        path,
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return str(path)


def generate_all_charts(summary: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate all charts supported by the current dataset.

    Optional charts are skipped when their required fields are unavailable.
    """
    paths = {}

    product_chart = chart_ca_by_product(summary)
    if product_chart:
        paths["products"] = product_chart

    category_chart = chart_ca_by_category(summary)
    if category_chart:
        paths["categories"] = category_chart

    monthly_chart = chart_monthly_ca(summary)
    if monthly_chart:
        paths["monthly"] = monthly_chart

    print("Charts generated:", list(paths.values()))

    return paths
