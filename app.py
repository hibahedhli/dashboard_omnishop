"""
app.py  -  Serveur Flask pour le dashboard OmniShop
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from generate_data import generate_ventes
from analytics import run_full_analysis, load_csv, compute_metrics, export_results, get_summary
from charts import generate_all_charts

app = Flask(__name__, template_folder="templates", static_folder="static")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

VENTES_CSV = DATA_DIR / "ventes.csv"
RESULTS_CSV = DATA_DIR / "resultats_final.csv"

_cache: dict = {}


def get_analysis(force=False):
    global _cache
    if not _cache or force:
        if not VENTES_CSV.exists():
            generate_ventes(str(VENTES_CSV), 2000)
        summary = run_full_analysis(str(VENTES_CSV))
        generate_all_charts(summary)
        _cache = summary
    return _cache


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    summary = get_analysis()
    return jsonify(summary)


@app.route("/api/orders")
def api_orders():
    summary = get_analysis()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "").lower().strip()
    category = request.args.get("category", "").strip()
    rows = list(summary["rows"])

    if search:
        search_clean = search.lstrip('#')
        rows = [r for r in rows if
                search_clean in str(r.get("Produit", "")).lower() or
                search_clean == str(r.get("ID_Commande", "")).strip() or
                search_clean == str(r.get("ID_Produit", "")).strip() or
                search_clean == str(r.get("ID", "")).strip() or
                search_clean in str(r.get("Categorie", "")).lower()]

    if category:
        rows = [r for r in rows if r.get("Categorie", "") == category]

    total = len(rows)
    start = (page - 1) * per_page
    paginated = rows[start:start + per_page]
    return jsonify({"rows": paginated, "total": total, "page": page, "per_page": per_page})


@app.route("/api/categories")
def api_categories():
    summary = get_analysis()
    cats = sorted(set(r.get("Categorie", "") for r in summary["rows"] if r.get("Categorie")))
    return jsonify(cats)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json() or {}
    n = max(5, min(int(data.get("n", 50)), 5000))
    generate_ventes(str(VENTES_CSV), n)
    summary = get_analysis(force=True)
    generate_all_charts(summary)
    return jsonify({"success": True, "rows_generated": n})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    if not f.filename.endswith(".csv"):
        return jsonify({"error": "CSV only"}), 400
    f.save(str(VENTES_CSV))
    summary = get_analysis(force=True)
    generate_all_charts(summary)
    return jsonify({"success": True})


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json() or {}
    try:
        prix = float(data["prix"])
        quantite = int(data["quantite"])
        remise = float(data.get("remise", 0))
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    ca_brut = round(prix * quantite, 2)
    ca_net = round(ca_brut * (1 - remise / 100), 2)
    tva = round(ca_net * 0.20, 2)
    ca_ttc = round(ca_net + tva, 2)
    return jsonify({
        "ca_brut": ca_brut,
        "ca_net": ca_net,
        "tva": tva,
        "ca_ttc": ca_ttc,
        "remise_montant": round(ca_brut - ca_net, 2),
    })


@app.route("/static/images/<path:filename>")
def serve_chart(filename):
    return send_from_directory("static/images", filename)


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory("data", filename)

@app.route("/api/chart_product")
def api_chart_product():
    from charts import chart_ca_single_product
    name = request.args.get("name", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    summary = get_analysis()
    path = chart_ca_single_product(name, summary)
    if not path:
        return jsonify({"error": "Produit non trouvé"}), 404
    filename = path.replace("static/images/", "")
    return jsonify({"image_url": f"/static/images/{filename}"})


if __name__ == "__main__":
    get_analysis()
    app.run(debug=True, port=5000)