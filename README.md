# OmniShop — Dashboard d'Automatisation des Ventes

> Projet de Fin d'Année · Matière : Logiciels · Auteur : Imene Amira

Dashboard web complet pour l'analyse automatisée des ventes e-commerce, inspiré de la plateforme Converty.

---

## Stack Technologique

| Couche | Technologie |
|--------|-------------|
| Backend | **Python 3.10+** · Flask |
| Analyse données | **Python** · CSV stdlib · pandas (optionnel) |
| Visualisation Python | **Matplotlib** |
| Frontend | **HTML5 · CSS3 · JavaScript ES2022** |
| Graphiques web | **Chart.js 4** |
| Typographie | Google Fonts (DM Sans · JetBrains Mono) |

---

## Structure du projet

```
ventes_dashboard/
├── app.py                    # Serveur Flask (routes API + rendu)
├── requirements.txt          # Dépendances Python
├── .venv/                    # Environnement virtuel (créé automatiquement)
├── data/
│   ├── ventes.csv            # Données générées ou importées
│   └── resultats_final.csv   # Export avec colonnes calculées
├── scripts/
│   ├── generate_data.py      # Génération de données aléatoires
│   ├── analytics.py          # Moteur de calcul (CA Brut, CA Net, TVA…)
│   └── charts.py             # Graphiques Matplotlib (PNG)
├── templates/
│   └── index.html            # Dashboard HTML unique (SPA)
└── static/
    ├── css/dashboard.css     # Thème dark Converty-style
    ├── js/dashboard.js       # Logique frontend (Chart.js, API calls)
    └── images/               # Graphiques Matplotlib générés
```

---

## Installation rapide

```bash
# 1. Cloner / décompresser le projet
cd ventes_dashboard

# 2. Créer l'environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer le serveur
python app.py
```

Ouvrez ensuite **http://localhost:5000** dans votre navigateur.

---

## Fonctionnalités

### 📊 Vue d'ensemble
- KPI en temps réel : CA Net, nombre de commandes, panier moyen, TVA collectée
- Graphique d'évolution mensuelle (Chart.js)
- Répartition par catégorie (donut)
- Badge du meilleur produit

### 📦 Commandes
- Tableau paginé de toutes les transactions
- Recherche en temps réel (produit, ID, catégorie)
- Filtrage par catégorie
- Colonnes : CA Brut, CA Net, TVA, CA TTC

### 🖥️ Produits
- Top 5 produits (bar chart horizontal)
- Comparatif CA Brut vs Net vs TVA
- Grille de performance avec barres de progression

### 📈 Analytiques
- 8 indicateurs financiers clés
- Taux Net/Brut (efficacité des remises)
- Graphique catégories en barres

### ⚡ Simulateur
- Calcul instantané pour n'importe quelle transaction
- Curseur de remise interactif (0–50%)
- Décomposition visuelle en donut (CA Net / Remise / TVA)

### ⬆️ Import / Export
- Import de CSV personnalisé (lecture dynamique)
- Génération aléatoire (5 à 500 lignes)
- Téléchargement de `resultats_final.csv`

---

## Formules de calcul

```
CA Brut   = Prix × Quantité
CA Net    = CA Brut × (1 − Remise / 100)
TVA       = CA Net × 0.20
CA TTC    = CA Net + TVA
```

---

## Format CSV attendu

```csv
ID,Produit,Prix,Quantite,Remise,Categorie
101,Smartphone Samsung,599.99,2,10,Mobile
102,Laptop Dell,1199.99,1,5,Informatique
```

Le champ `Produit` et `Categorie` sont optionnels — le script fonctionne aussi avec le format minimal `ID,Prix,Quantite,Remise`.

---

## API REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/summary` | Résumé global (KPIs, catégories, top5…) |
| GET | `/api/orders?page=1&search=` | Liste paginée des commandes |
| POST | `/api/simulate` | Simulation d'une vente |
| POST | `/api/generate` | Génère N lignes aléatoires |
| POST | `/api/upload` | Importe un CSV |

---

## Licence

Projet académique — Faculté des Sciences de Tunis
