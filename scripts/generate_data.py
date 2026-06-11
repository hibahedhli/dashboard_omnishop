"""
generate_data.py
Génère un fichier ventes.csv avec des données de démonstration réalistes.
"""
 
import csv
import random
from datetime import date, timedelta

PRODUCTS = [
    ("Smartphone Samsung", 599.99),
    ("Laptop Dell", 1199.99),
    ("Ecouteurs Sony", 149.99),
    ("Tablette iPad", 799.99),
    ("Montre Apple Watch", 399.99),
    ("Clavier Logitech", 89.99),
    ("Souris Razer", 59.99),
    ("Ecran LG 27", 349.99),
    ("Imprimante HP", 199.99),
    ("Disque SSD 1TB", 119.99),
    ("Webcam Logitech", 79.99),
    ("Casque Bose", 299.99),
    ("Chargeur USB-C", 29.99),
    ("Hub USB", 49.99),
    ("Tapis de souris XL", 24.99),
]
 
WEIGHTS = [15, 8, 20, 10, 12, 18, 22, 7, 9, 14, 16, 6, 25, 19, 23]
 
 
def generate_ventes(filename: str = "data/ventes.csv", n: int = 2000) -> None:
    """Génère n lignes de ventes et les écrit dans filename."""
    # Période de 12 mois glissants jusqu'à aujourd'hui
    end_date = date.today()
    start_date = date(end_date.year - 1, end_date.month, 1)
    total_days = (end_date - start_date).days

    with open(filename, "w", newline="", encoding="cp1252") as f:
        writer = csv.writer(f)
        writer.writerow(["ID_Commande", "ID_Produit", "Produit", "Prix", "Quantite", "Remise", "Categorie", "Date"])

        produit_ids = {name: 200 + i for i, (name, _) in enumerate(PRODUCTS)}

        for i in range(1, n + 1):
            product_name, base_price = random.choices(PRODUCTS, weights=WEIGHTS, k=1)[0]
            price = round(base_price * random.uniform(0.9, 1.1), 2)
            quantity = random.randint(1, 5)
            discount = random.choice([0, 0, 0, 5, 5, 10, 10, 15, 20, 25])
            category = get_category(product_name)
            id_produit = produit_ids[product_name]
            order_date = start_date + timedelta(days=random.randint(0, total_days))
            writer.writerow([1000 + i, id_produit, product_name, price, quantity, discount, category,
                             order_date.strftime("%Y-%m-%d")])

    print(f"✅ {n} lignes générées dans {filename}")
 
 
def get_category(product_name: str) -> str:
    categories = {
        "Smartphone": "Mobile",
        "Laptop": "Informatique",
        "Ecouteurs": "Audio",
        "Tablette": "Mobile",
        "Montre": "Wearable",
        "Clavier": "Peripherique",
        "Souris": "Peripherique",
        "Ecran": "Affichage",
        "Imprimante": "Informatique",
        "Disque": "Stockage",
        "Webcam": "Peripherique",
        "Casque": "Audio",
        "Chargeur": "Accessoire",
        "Hub": "Accessoire",
        "Tapis": "Accessoire",
    }
    for key, cat in categories.items():
        if key in product_name:
            return cat
    return "Autre"
 
 
if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    generate_ventes()