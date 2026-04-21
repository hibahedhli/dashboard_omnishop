"""
analytics.py
Moteur d'analyse des ventes : calculs CA Brut, CA Net, TVA, exports.
"""
 
import csv
import os
from pathlib import Path
from typing import Dict, List, Any
 
 
TVA_RATE = 0.20
 
 
def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """Charge dynamiquement n'importe quel fichier CSV de ventes."""
    rows = []
    with open(filepath, "r", encoding="cp1252") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows
 
 
def compute_metrics(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calcule CA Brut, CA Net, TVA pour chaque ligne."""
    results = []
    for row in rows:
        prix = float(row["Prix"])
        quantite = int(row["Quantite"])
        remise = float(row["Remise"])
 
        # Compatibilité ancien format (ID) et nouveau (ID_Commande)
        if "ID_Commande" not in row and "ID" in row:
            row["ID_Commande"] = row["ID"]
            row["ID_Produit"] = row["ID"]
 
        ca_brut = round(prix * quantite, 2)
        ca_net = round(ca_brut * (1 - remise / 100), 2)
        tva = round(ca_net * TVA_RATE, 2)
        ca_ttc = round(ca_net + tva, 2)
 
        result = {**row, "CA_Brut": ca_brut, "CA_Net": ca_net, "TVA": tva, "CA_TTC": ca_ttc}
        results.append(result)
    return results
 
 
def export_results(results, filepath="data/resultats_final.csv"):
    if not results:
        return
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fieldnames = list(results[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Resultats exportes vers {filepath}")
 
 
def get_id(row: Dict[str, Any]) -> str:
    """Retourne l'ID commande quel que soit le format du CSV."""
    return row.get("ID_Commande", row.get("ID", "-"))
 
 
def get_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retourne un résumé global : CA Total, meilleur produit, etc."""
    ca_total = sum(r["CA_Net"] for r in results)
    tva_total = sum(r["TVA"] for r in results)
    ca_brut_total = sum(r["CA_Brut"] for r in results)
    total_orders = len(results)
    avg_order = round(ca_total / total_orders, 2) if total_orders else 0
 
    # Grouper par produit et additionner les CA
    product_totals = {}
    for r in results:
        prod = r.get("Produit", get_id(r))
        product_totals[prod] = round(product_totals.get(prod, 0) + r["CA_Net"], 2)
 
    best_prod_name = max(product_totals, key=product_totals.get)
    worst_prod_name = min(product_totals, key=product_totals.get)
 
    best = next(r for r in results if r.get("Produit", get_id(r)) == best_prod_name)
    worst = next(r for r in results if r.get("Produit", get_id(r)) == worst_prod_name)
 
    best = {**best, "CA_Net": product_totals[best_prod_name]}
    worst = {**worst, "CA_Net": product_totals[worst_prod_name]}
 
    by_category: Dict[str, float] = {}
    for r in results:
        cat = r.get("Categorie", "Autre")
        by_category[cat] = round(by_category.get(cat, 0) + r["CA_Net"], 2)
 
    by_product: Dict[str, float] = {}
    for r in results:
        prod = r.get("Produit", get_id(r))
        by_product[prod] = round(by_product.get(prod, 0) + r["CA_Net"], 2)
 
    top5 = sorted(by_product.items(), key=lambda x: x[1], reverse=True)[:5]
 
    monthly: Dict[str, float] = {}
    months = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun",
              "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]
    for i, r in enumerate(results):
        m = months[i % 12]
        monthly[m] = round(monthly.get(m, 0) + r["CA_Net"], 2)
 
    return {
        "ca_total": round(ca_total, 2),
        "ca_brut_total": round(ca_brut_total, 2),
        "tva_total": round(tva_total, 2),
        "total_orders": total_orders,
        "avg_order": avg_order,
        "best_product_id": best.get("ID_Produit", "—"),
        "best_product_name": best.get("Produit", "—"),
        "best_product_ca": best["CA_Net"],
        "worst_product_id": worst.get("ID_Produit", "—"),
        "by_category": by_category,
        "by_product": by_product,
        "top5_products": top5,
        "monthly_ca": monthly,
        "rows": results,
    }
 
 
def run_full_analysis(csv_path: str = "data/ventes.csv") -> Dict[str, Any]:
    """Pipeline complet : chargement -> calcul -> export -> résumé."""
    rows = load_csv(csv_path)
    results = compute_metrics(rows)
    export_results(results)
    summary = get_summary(results)
    print(f"\nCA Total : {summary['ca_total']:,.2f} DT")
    print(f"Commandes : {summary['total_orders']}")
    print(f"Meilleur produit : ID {summary['best_product_id']} - {summary['best_product_name']}")
    return summary
 
 
if __name__ == "__main__":
    run_full_analysis()