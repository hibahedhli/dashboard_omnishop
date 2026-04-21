# OmniShop — Dashboard d'Automatisation des Ventes

> Projet de Fin d'Année · Matière : Logiciels · Faculté des Sciences de Tunis

---

## 1. Titre & Description

**OmniShop** est un dashboard web complet pour l'analyse automatisée des ventes d'une entreprise e-commerce.

L'application remplace un fichier Excel classique devenu trop volumineux par un système d'analyse dynamique capable de :

- Générer et importer des fichiers CSV de ventes
- Calculer automatiquement le **CA Brut**, le **CA Net** et la **TVA (20%)**
- Identifier le **meilleur produit** par chiffre d'affaires
- Afficher des **graphiques interactifs** par produit, catégorie et mois
- Simuler n'importe quelle transaction en temps réel
- Exporter les résultats dans un fichier `resultats_final.csv`

### Stack Technologique

| Couche | Technologie |
|--------|-------------|
| Backend | **Python 3.13** · Flask |
| Analyse données | **Python** · module CSV natif |
| Visualisation Python | **Matplotlib** |
| Frontend | **HTML5 · CSS3 · JavaScript ES2022** |
| Graphiques web | **Chart.js 4** |
| Typographie | Google Fonts (DM Sans · JetBrains Mono) |

---

## 2. Prérequis

Avant de lancer le projet, assurez-vous d'avoir installé :

| Logiciel | Version minimale | Lien |
|----------|-----------------|------|
| **Python** | 3.10 ou plus | https://www.python.org/downloads/ |
| **VS Code** | Dernière version | https://code.visualstudio.com/ |
| **Extension Python** pour VS Code | — | Installer depuis VS Code Extensions |
| **Navigateur web** | Chrome, Edge ou Firefox | — |

> Node.js n'est **pas** nécessaire pour ce projet.

---

## 3. Installation

### Étape 1 — Télécharger le projet

Décompresser le fichier `ventes_dashboard.zip` dans un dossier de votre choix.

### Étape 2 — Ouvrir dans VS Code

```
Fichier → Ouvrir le dossier → sélectionner ventes_dashboard
```

### Étape 3 — Ouvrir le terminal

```
Ctrl + ù
```

### Étape 4 — Se placer dans le bon dossier

```bash
cd ventes_dashboard
```

### Étape 5 — Créer l'environnement virtuel

```bash
python -m venv .venv --without-pip
```

### Étape 6 — Activer l'environnement virtuel

**Windows :**
```bash
.venv\Scripts\activate
```

**Mac / Linux :**
```bash
source .venv/bin/activate
```

Le terminal affiche `(.venv)` — l'environnement est actif

### Étape 7 — Installer pip

```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

### Étape 8 — Installer les dépendances

```bash
pip install -r requirements.txt
```

Dépendances installées :

| Package | Version | Rôle |
|---------|---------|------|
| Flask | 3.1.x | Serveur web |
| matplotlib | 3.10.x | Graphiques Python |
| Werkzeug | 3.1.x | Utilitaires Flask |

---

## 4. Utilisation

### Lancer le projet

```bash
python app.py
```

Le terminal affiche :
```
Running on http://127.0.0.1:5000
```

### Ouvrir le dashboard

Ouvrir un navigateur et aller sur :
```
http://localhost:5000
```

### Sections disponibles

| Section | Description |
|---------|-------------|
| **Dashboard** | Vue d'ensemble — KPIs, graphiques mensuels, meilleur produit |
| **Commandes** | Tableau paginé avec recherche et filtre par catégorie |
| **Produits** | Top 5 produits, CA Brut vs Net, grille de performance |
| **Analytiques** | Indicateurs financiers avancés, répartition par catégorie |
| **Simulateur** | Calcul instantané CA Brut/Net/TVA + analyse graphique par produit |
| **Import / Export** | Importer CSV, générer des données, télécharger les résultats |

### Formules de calcul

```
CA Brut  = Prix x Quantite
CA Net   = CA Brut x (1 - Remise / 100)
TVA      = CA Net x 0.20
CA TTC   = CA Net + TVA
```

### Format CSV pour l'import

```csv
ID_Commande,ID_Produit,Produit,Prix,Quantite,Remise,Categorie
1001,201,Laptop Dell,3799.00,1,5,Informatique
1002,213,Chargeur USB-C,89.00,3,0,Accessoire
```

Le separateur doit etre une virgule et les decimales un point.

### Arrêter le serveur

```
Ctrl + C
```

---

## 5. Auteurs

| Nom | Role |
|-----|------|
| **Hiba Hedhli** | Developpement complet du projet |

---

*Faculte des Sciences de Tunis — Projet de Fin d'Annee 2025/2026*