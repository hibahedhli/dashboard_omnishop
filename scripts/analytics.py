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
    """Résumé global des ventes avec meilleure commande."""
    if not results:
        return {}

    ca_total = sum(r["CA_Net"] for r in results)
    tva_total = sum(r["TVA"] for r in results)
    ca_brut_total = sum(r["CA_Brut"] for r in results)

    total_orders = len(results)
    avg_order = round(ca_total / total_orders, 2)

    # Meilleure commande (max CA_Net)
    best_order = max(results, key=lambda r: r["CA_Net"])
    worst_order = min(results, key=lambda r: r["CA_Net"])

    # Catégories
    by_category: Dict[str, float] = {}
    for r in results:
        cat = r.get("Categorie", "Autre")
        by_category[cat] = round(by_category.get(cat, 0) + r["CA_Net"], 2)

    # CA par produit (pour le simulateur)
    by_product: Dict[str, float] = {}
    for r in results:
        prod = r.get("Produit", "Autre")
        by_product[prod] = round(by_product.get(prod, 0) + r["CA_Net"], 2)

    # CA mensuel (index cyclique sur 12 mois car pas de date dans le CSV)
    months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
              "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    monthly_ca: Dict[str, float] = {m: 0.0 for m in months}
    for i, r in enumerate(results):
        m = months[i % 12]
        monthly_ca[m] = round(monthly_ca[m] + r["CA_Net"], 2)

    # Top 5 commandes
    top5_orders = sorted(results, key=lambda r: r["CA_Net"], reverse=True)[:5]

    return {
        "ca_total": round(ca_total, 2),
        "ca_brut_total": round(ca_brut_total, 2),
        "tva_total": round(tva_total, 2),
        "total_orders": total_orders,
        "avg_order": avg_order,

        "best_order_id": best_order.get("ID_Commande"),
        "best_order_ca": best_order["CA_Net"],

        "worst_order_id": worst_order.get("ID_Commande"),

        "top5_orders": top5_orders,
        "by_category": by_category,
        "by_product": by_product,
        "monthly_ca": monthly_ca,
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
    print(f"Meilleure commande : ID {summary['best_order_id']} - {summary['best_order_ca']:.2f} DT")
    return summary
 
 
if __name__ == "__main__":
    run_full_analysis()