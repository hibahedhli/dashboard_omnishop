"""
analytics.py
Sales intelligence engine.

The module works with the normalized schema produced by data_adapter.py.
It calculates financial metrics, order performance, product performance,
category performance and time-based analysis when dates are available.
"""

import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    from .data_adapter import adapt_dataset
except ImportError:
    from data_adapter import adapt_dataset



def fmt_currency(value: float) -> str:
    """Format a currency value using French/Tunisian notation."""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")

def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Load and normalize a sales CSV.

    The original CSV column names are detected automatically by
    data_adapter.py.
    """
    adapted = adapt_dataset(filepath)
    return adapted["rows"]


def compute_metrics(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate financial metrics for every normalized sales line.

    Expected normalized fields:
        order_id
        product_id
        product_name
        price
        quantity
        discount
        vat_rate
        category
        date
    """
    results: List[Dict[str, Any]] = []

    for row in rows:
        price = float(row["price"])
        quantity = int(row["quantity"])
        discount = float(row.get("discount") or 0)

        ca_brut = round(price * quantity, 2)
        remise_montant = round(ca_brut * discount / 100, 2)
        ca_net = round(ca_brut - remise_montant, 2)

        vat_rate = row.get("vat_rate")
        if vat_rate is not None:
            vat_rate = float(vat_rate)
            tva = round(ca_net * vat_rate / 100, 2)
            ca_ttc = round(ca_net + tva, 2)
        else:
            tva = None
            ca_ttc = None

        result = {
            **row,
            "CA_Brut": ca_brut,
            "Remise_Montant": remise_montant,
            "CA_Net": ca_net,
            "TVA": tva,
            "CA_TTC": ca_ttc,
        }

        results.append(result)

    return results


def _group_key(value: Any, fallback: str = "Unknown") -> str:
    """Return a safe string key for grouping."""
    if value is None:
        return fallback

    text = str(value).strip()

    return text if text else fallback


def aggregate_orders(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate line items into real orders.

    A single order may contain many rows/products. Those rows are combined
    so that 'Top Orders' represents actual order performance.
    """
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in results:
        order_id = row.get("order_id")

        # If no order identifier exists, order-level analysis is unavailable.
        if order_id is None or str(order_id).strip() == "":
            continue

        key = str(order_id).strip()

        if key not in grouped:
            grouped[key] = {
                "order_id": key,
                "revenue": 0.0,
                "gross_revenue": 0.0,
                "tax": None,
                "total_discount": 0.0,
                "quantity": 0,
                "line_count": 0,
                "products": set(),
                "date": row.get("date"),
            }

        order = grouped[key]

        order["revenue"] += row["CA_Net"]
        order["gross_revenue"] += row["CA_Brut"]
        if row.get("TVA") is not None:
            order["tax"] = (order["tax"] or 0.0) + row["TVA"]
        order["total_discount"] += row.get("Remise_Montant", 0)
        order["quantity"] += row["quantity"]
        order["line_count"] += 1

        product_key = row.get("product_id") or row.get("product_name")

        if product_key:
            order["products"].add(str(product_key))

        if not order.get("date") and row.get("date"):
            order["date"] = row["date"]

    orders = []

    for order in grouped.values():
        order["revenue"] = round(order["revenue"], 2)
        order["gross_revenue"] = round(order["gross_revenue"], 2)
        if order["tax"] is not None:
            order["tax"] = round(order["tax"], 2)
        order["total_discount"] = round(order["total_discount"], 2)
        order["products"] = len(order["products"])

        orders.append(order)

    return orders


def aggregate_products(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate sales independently by product.

    Product ID is preferred. If unavailable, product name is used.
    """
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in results:
        product_id = row.get("product_id")
        product_name = row.get("product_name")

        key = product_id or product_name

        if key is None or str(key).strip() == "":
            continue

        key = str(key).strip()

        if key not in grouped:
            grouped[key] = {
                "product_id": product_id,
                "product_name": product_name,
                "revenue": 0.0,
                "quantity": 0,
                "orders": set(),
                "category": row.get("category"),
            }

        product = grouped[key]

        product["revenue"] += row["CA_Net"]
        product["quantity"] += row["quantity"]

        if row.get("order_id"):
            product["orders"].add(str(row["order_id"]))

    for product in grouped.values():
        product["revenue"] = round(product["revenue"], 2)
        product["orders"] = len(product["orders"]) if product["orders"] else None

    return grouped


def aggregate_categories(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate net revenue by category when category data is available."""
    categories: Dict[str, float] = defaultdict(float)

    for row in results:
        category = row.get("category")

        if category is None or str(category).strip() == "":
            continue

        categories[str(category).strip()] += row["CA_Net"]

    return {
        category: round(value, 2)
        for category, value in sorted(
            categories.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    }

def aggregate_monthly(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate monthly revenue only when valid dates are available.

    No artificial month assignment is performed.
    """
    monthly: Dict[str, float] = defaultdict(float)

    for row in results:
        date_value = row.get("date")

        if not date_value:
            continue

        text = str(date_value).strip()

        # Expected formats include YYYY-MM-DD and YYYY-MM-DD HH:MM:SS.
        if len(text) >= 7 and text[4] == "-":
            month_key = text[:7]
            monthly[month_key] += row["CA_Net"]

    return {
        month: round(value, 2)
        for month, value in sorted(monthly.items())
    }


def get_summary(
    results: List[Dict[str, Any]],
    profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the complete sales intelligence summary."""

    if not results:
        return {}

    ca_total = round(sum(r["CA_Net"] for r in results), 2)
    ca_brut_total = round(sum(r["CA_Brut"] for r in results), 2)
    vat_values = [r["TVA"] for r in results if r.get("TVA") is not None]
    tva_total = round(sum(vat_values), 2) if vat_values else None
    remise_total = round(sum(r["Remise_Montant"] for r in results), 2)
    quantity_total = sum(r["quantity"] for r in results)

    orders = aggregate_orders(results)
    products = aggregate_products(results)
    categories = aggregate_categories(results)
    monthly_ca = aggregate_monthly(results)

    has_order_ids = bool(orders)

    total_orders = len(orders) if has_order_ids else None

    avg_order = (
        round(ca_total / total_orders, 2)
        if total_orders
        else None
    )

    top5_orders = sorted(
        orders,
        key=lambda order: order["revenue"],
        reverse=True,
    )[:5]

    top5_products = sorted(
        products.values(),
        key=lambda product: product["revenue"],
        reverse=True,
    )[:5]

    best_order = top5_orders[0] if top5_orders else None

    product_count = len(products)

    category_count = len(categories)

    top_product_revenue = (
        top5_products[0]["revenue"]
        if top5_products
        else 0
    )

    top_product_share = (
        round((top_product_revenue / ca_total) * 100, 2)
        if ca_total > 0
        else 0
    )

    summary = {
        # Financial KPIs
        "ca_total": ca_total,
        "ca_brut_total": ca_brut_total,
        "tva_total": tva_total,
        "remise_total": remise_total,
        "ca_ttc_total": round(ca_total + tva_total, 2) if tva_total is not None else None,

        # Volume KPIs
        "total_orders": total_orders,
        "total_rows": len(results),
        "total_quantity": quantity_total,
        "product_count": product_count,
        "category_count": category_count,
        "avg_order": avg_order,

        # Best order
        "best_order_id": (
            best_order["order_id"]
            if best_order
            else None
        ),
        "best_order_ca": (
            best_order["revenue"]
            if best_order
            else None
        ),

        # Main analyses
        "top5_orders": top5_orders,
        "top5_products": top5_products,
        "products_detail": list(products.values()),
        "by_category": categories,
        "by_product": {
            (
                product["product_name"]
                or product["product_id"]
                or "Unknown"
            ): product["revenue"]
            for product in products.values()
        },
        "monthly_ca": monthly_ca,

        # Data availability
        "has_order_id": has_order_ids,
        "has_product_id": any(
            row.get("product_id") for row in results
        ),
        "has_product_name": any(
            row.get("product_name") for row in results
        ),
        "has_category": any(
            row.get("category") for row in results
        ),
        "has_date": any(
            row.get("date") for row in results
        ),
        "top_product_share": top_product_share,

        # Normalized rows
        "rows": results,

        # Dataset profile
        "profile": profile or {},
    }

    summary["insights"] = generate_insights(summary)

    return summary


def export_results(
    results: List[Dict[str, Any]],
    filepath: str = "data/resultats_final.csv",
) -> None:
    """Export normalized results and calculated metrics."""
    if not results:
        return

    directory = os.path.dirname(filepath)

    if directory:
        os.makedirs(directory, exist_ok=True)

    fieldnames = list(results[0].keys())

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Results exported to {filepath}")


def get_id(row: Dict[str, Any]) -> str:
    """
    Backward-compatible helper.

    Returns the normalized order ID without inventing one.
    """
    return str(row.get("order_id") or "-")


def generate_insights(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate automatic business insights from the analytics summary.

    Each insight contains:
        type     : informational severity/category
        title    : short business-oriented title
        message  : explanation based on the dataset
        action   : possible business action or investigation
    """
    insights: List[Dict[str, Any]] = []

    # 1. Top revenue-driving product
    top_products = summary.get("top5_products") or []

    if top_products:
        top_product = top_products[0]
        product_name = top_product.get("product_name", "Produit")
        product_revenue = float(top_product.get("revenue", 0) or 0)
        total_revenue = float(summary.get("ca_total", 0) or 0)

        if total_revenue > 0:
            share = (product_revenue / total_revenue) * 100

            insights.append({
                "type": "success",
                "title": "Principal moteur du CA",
                "message": (
                    f"{product_name} génère {fmt_currency(product_revenue)} DT "
                    f"de CA net, soit {share:.1f}% du CA total."
                ),
                "action": (
                    "Surveiller sa disponibilité et analyser les facteurs "
                    "qui expliquent sa performance."
                ),
            })

    # 2. Revenue concentration
    if top_products and summary.get("ca_total", 0):
        top5_revenue = sum(
            float(product.get("revenue", 0) or 0)
            for product in top_products
        )
        total_revenue = float(summary["ca_total"] or 0)

        concentration = (top5_revenue / total_revenue) * 100
        top_count = len(top_products)

        if top_count == 1:
            concentration_message = (
                f"Le produit principal représente "
                f"{concentration:.1f}% du CA net."
            )
        else:
            concentration_message = (
                f"Les {top_count} premiers produits représentent "
                f"{concentration:.1f}% du CA net."
            )

        insights.append({
            "type": "info",
            "title": "Concentration du chiffre d'affaires",
            "message": concentration_message,
            "action": (
                "Évaluer la dépendance à ces produits et identifier "
                "d'autres produits capables de diversifier le CA."
            ),
        })

    # 3. High-volume / low-revenue product
    products_detail = summary.get("products_detail") or []

    if len(products_detail) >= 2 and total_revenue > 0:
        total_quantity = sum(
            int(product.get("quantity", 0) or 0)
            for product in products_detail
        )

        if total_quantity > 0:
            candidates = []

            for product in products_detail:
                quantity = int(product.get("quantity", 0) or 0)
                revenue = float(product.get("revenue", 0) or 0)

                quantity_share = quantity / total_quantity
                revenue_share = revenue / total_revenue
                gap = quantity_share - revenue_share

                if quantity_share >= 0.05 and gap >= 0.05:
                    candidates.append((gap, product, quantity_share, revenue_share))

            if candidates:
                gap, product, quantity_share, revenue_share = max(
                    candidates,
                    key=lambda item: item[0]
                )

                product_name = product.get("product_name") or product.get("product_id") or "Produit"

                insights.append({
                    "type": "warning",
                    "title": "Volume élevé, contribution au CA limitée",
                    "message": (
                        f"{product_name} représente "
                        f"{quantity_share * 100:.1f}% des unités vendues, "
                        f"mais seulement {revenue_share * 100:.1f}% du CA net."
                    ),
                    "action": (
                        "Analyser son prix, sa marge et son rôle dans les ventes "
                        "pour déterminer s'il s'agit d'un produit d'appel, "
                        "d'une opportunité de montée en gamme ou d'un produit "
                        "à faible contribution."
                    ),
                })

    # 4. Largest order vs average order
    best_order = summary.get("best_order_ca")
    average_order = summary.get("avg_order")

    if (
        summary.get("has_order_id")
        and best_order is not None
        and average_order
        and average_order > 0
    ):
        ratio = float(best_order) / float(average_order)

        if ratio >= 3:
            order_id = summary.get("best_order_id")
            insights.append({
                "type": "warning",
                "title": "Commande exceptionnellement élevée",
                "message": (
                    f"La commande #{order_id} atteint {fmt_currency(float(best_order))} DT, "
                    f"soit environ {ratio:.1f} fois le panier moyen."
                ),
                "action": (
                    "Examiner sa composition pour comprendre les produits "
                    "ou quantités responsables de cette valeur élevée."
                ),
            })

    # 5. Best category
    categories = summary.get("by_category") or {}

    if summary.get("has_category") and categories:
        best_category, category_revenue = next(iter(categories.items()))

        insights.append({
            "type": "success",
            "title": "Catégorie la plus performante",
            "message": (
                f"La catégorie « {best_category} » génère "
                f"{fmt_currency(float(category_revenue))} DT de CA net."
            ),
            "action": (
                "Comparer ses produits et identifier les caractéristiques "
                "qui expliquent sa performance."
            ),
        })

    # 6. Monthly trend
    monthly = summary.get("monthly_ca") or {}
    profile = summary.get("profile") or {}
    date_range = profile.get("date_range") or {}

    if summary.get("has_date") and monthly:
        months = list(monthly.items())
        current_month, current_value = months[-1]

        current_value = float(current_value or 0)
        max_date = date_range.get("max")

        is_partial_month = False
        max_date_obj = None

        if max_date:
            try:
                max_date_obj = datetime.strptime(max_date, "%Y-%m-%d")
                is_partial_month = (
                    max_date_obj.strftime("%Y-%m") == current_month
                    and max_date_obj.day < 28
                )
            except (ValueError, TypeError):
                is_partial_month = False

        if is_partial_month:
            insights.append({
                "type": "info",
                "title": "Mois en cours partiel",
                "message": (
                    f"Le CA net du mois {current_month} atteint actuellement "
                    f"{fmt_currency(current_value)} DT, mais les données ne couvrent "
                    f"que jusqu'au {max_date_obj.day} "
                    f"{["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"][max_date_obj.month - 1]}."
                ),
                "action": (
                    "Attendre la fin du mois avant de comparer directement "
                    "sa performance avec le mois précédent."
                ),
            })

        elif len(months) >= 2:
            previous_month, previous_value = months[-2]
            previous_value = float(previous_value or 0)

            if previous_value > 0:
                variation = (
                    (current_value - previous_value)
                    / previous_value
                ) * 100

                trend_type = "success" if variation > 0 else "warning"
                direction = "augmenté" if variation > 0 else "diminué"

                insights.append({
                    "type": trend_type,
                    "title": "Évolution récente du CA",
                    "message": (
                        f"Le CA net a {direction} de "
                        f"{abs(variation):.1f}% entre "
                        f"{previous_month} et {current_month}."
                    ),
                    "action": (
                        "Analyser les produits et catégories responsables "
                        "de cette évolution."
                    ),
                })

    # Product trend detection: compare equal-length periods across months
    if summary.get("has_date"):
        rows = summary.get("rows") or []
        dated_rows = []

        for row in rows:
            date_value = row.get("date")
            if not date_value:
                continue

            try:
                parsed_date = datetime.strptime(str(date_value)[:10], "%Y-%m-%d")
                dated_rows.append((parsed_date, row))
            except (ValueError, TypeError):
                continue

        if dated_rows:
            max_date = max(item[0] for item in dated_rows)

            # Compare the current month up to the latest available day
            # with the same number of days from the previous month.
            current_start = max_date.replace(day=1)
            period_days = max_date.day

            if period_days >= 2:
                if current_start.month == 1:
                    previous_year = current_start.year - 1
                    previous_month = 12
                else:
                    previous_year = current_start.year
                    previous_month = current_start.month - 1

                previous_start = current_start.replace(
                    year=previous_year,
                    month=previous_month,
                    day=1,
                )
                previous_end = previous_start + timedelta(days=period_days - 1)

                current_product_revenue = defaultdict(float)
                previous_product_revenue = defaultdict(float)

                for parsed_date, row in dated_rows:
                    product_name = (
                        row.get("product_name")
                        or row.get("product_id")
                    )

                    if not product_name:
                        continue

                    product_name = str(product_name).strip()
                    revenue = float(row.get("CA_Net") or 0)

                    if current_start <= parsed_date <= max_date:
                        current_product_revenue[product_name] += revenue
                    elif previous_start <= parsed_date <= previous_end:
                        previous_product_revenue[product_name] += revenue

                previous_period_total = sum(previous_product_revenue.values())

                if previous_period_total > 0:
                    candidates = []

                    for product_name, previous_revenue in previous_product_revenue.items():
                        current_revenue = current_product_revenue.get(product_name, 0)

                        # Ignore products with insignificant previous-period sales.
                        if previous_revenue < previous_period_total * 0.05:
                            continue

                        variation = (
                            (current_revenue - previous_revenue)
                            / previous_revenue
                        ) * 100

                        if variation <= -20:
                            candidates.append(
                                (
                                    variation,
                                    product_name,
                                    previous_revenue,
                                    current_revenue,
                                )
                            )

                    if candidates:
                        variation, product_name, previous_revenue, current_revenue = min(
                            candidates,
                            key=lambda item: item[0],
                        )

                        insights.append({
                            "type": "warning",
                            "title": "Produit en forte baisse",
                            "message": (
                                f"Le CA du produit « {product_name} » a diminué de "
                                f"{abs(variation):.1f}% sur la période comparable "
                                f"({fmt_currency(previous_revenue)} DT ? "
                                f"{fmt_currency(current_revenue)} DT)."
                            ),
                            "action": (
                                "Vérifier son stock, son prix, sa disponibilité et "
                                "les éventuelles causes de baisse de demande."
                            ),
                        })

                    growth_candidates = []

                    for product_name, previous_revenue in previous_product_revenue.items():
                        current_revenue = current_product_revenue.get(product_name, 0)

                        # Ignore products with insignificant previous-period sales.
                        if previous_revenue < previous_period_total * 0.05:
                            continue

                        variation = (
                            (current_revenue - previous_revenue)
                            / previous_revenue
                        ) * 100

                        if variation >= 20:
                            growth_candidates.append(
                                (
                                    variation,
                                    product_name,
                                    previous_revenue,
                                    current_revenue,
                                )
                            )

                    if growth_candidates:
                        variation, product_name, previous_revenue, current_revenue = max(
                            growth_candidates,
                            key=lambda item: item[0],
                        )

                        insights.append({
                            "type": "success",
                            "title": "Produit en forte croissance",
                            "message": (
                                f"Le CA du produit « {product_name} » a augmenté de "
                                f"{variation:.1f}% sur la période comparable "
                                f"({fmt_currency(previous_revenue)} DT → "
                                f"{fmt_currency(current_revenue)} DT)."
                            ),
                            "action": (
                                "Analyser les facteurs de cette croissance et vérifier "
                                "si cette dynamique peut être maintenue."
                            ),
                        })

    return insights


def run_full_analysis(
    csv_path: str = "data/ventes.csv",
) -> Dict[str, Any]:
    """
    Complete pipeline:

        CSV
          ?
        schema detection
          ?
        normalization
          ?
        financial calculations
          ?
        aggregation
          ?
        sales intelligence summary
    """
    adapted = adapt_dataset(csv_path)

    rows = adapted["rows"]
    profile = adapted["profile"]

    results = compute_metrics(rows)

    export_results(results)

    summary = get_summary(
        results,
        profile=profile,
    )

    print()
    print(f"CA Total : {summary['ca_total']:,.2f} DT")
    print(f"Lignes de vente : {summary['total_rows']}")

    if summary["total_orders"] is not None:
        print(f"Commandes : {summary['total_orders']}")
        print(
            f"Meilleure commande : "
            f"ID {summary['best_order_id']} - "
            f"{summary['best_order_ca']:.2f} DT"
        )
    else:
        print("Commandes : identifiant de commande non dÃ©tectÃ©")

    print(f"Produits : {summary['product_count']}")

    return summary


if __name__ == "__main__":
    run_full_analysis()
















