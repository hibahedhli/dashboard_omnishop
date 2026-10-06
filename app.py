"""
app.py - Flask server for the OmniShop sales intelligence dashboard.
"""

from pathlib import Path
import json

from flask import Flask, jsonify, render_template, request, send_from_directory

from scripts.generate_data import generate_ventes
from scripts.analytics import run_full_analysis, generate_insights
from scripts.charts import generate_all_charts


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

DATA_DIR.mkdir(exist_ok=True)

VENTES_CSV = DATA_DIR / "ventes.csv"
RESULTS_CSV = DATA_DIR / "resultats_final.csv"
DATASET_CONFIG = DATA_DIR / "dataset_config.json"


def get_currency_config():
    """Load the fallback currency configuration for the active dataset."""
    default = {
        "currency": "TND",
        "symbol": "DT",
        "locale": "fr-TN",
    }

    if not DATASET_CONFIG.exists():
        return default

    try:
        with DATASET_CONFIG.open("r", encoding="utf-8-sig") as file:
            config = json.load(file)

        return {
            "currency": config.get("currency", default["currency"]),
            "symbol": config.get("symbol", default["symbol"]),
            "locale": config.get("locale", default["locale"]),
        }

    except (OSError, json.JSONDecodeError):
        return default

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(STATIC_DIR),
)

_cache = None
_cache_mtime = None


def get_analysis(force=False):
    """
    Load and cache the analysis of the current dataset.

    The cache is automatically invalidated when ventes.csv changes.
    """
    global _cache, _cache_mtime

    if not VENTES_CSV.exists():
        generate_ventes(str(VENTES_CSV), 2000)

    current_mtime = VENTES_CSV.stat().st_mtime

    if (
        _cache is None
        or force
        or _cache_mtime != current_mtime
    ):
        summary = run_full_analysis(str(VENTES_CSV))

        detected_currency = (
            summary.get("profile", {})
            .get("currency", {})
        )

        if detected_currency.get("detected"):
            summary["currency"] = {
                "currency": detected_currency.get("code"),
                "symbol": detected_currency.get("symbol"),
                "locale": "en-GB" if detected_currency.get("code") == "GBP" else "fr-TN",
                "source": "column",
            }
        else:
            summary["currency"] = {
                **get_currency_config(),
                "source": "config",
            }

        summary["insights"] = generate_insights(summary)

        try:
            generate_all_charts(summary)
        except Exception as exc:
            app.logger.warning("Chart generation failed: %s", exc)

        _cache = summary
        _cache_mtime = current_mtime

    return _cache


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    summary = get_analysis()

    return jsonify({
        key: value
        for key, value in summary.items()
        if key not in {"rows"}
    })


@app.route("/api/profile")
def api_profile():
    """
    Return information about the detected dataset schema.
    """
    summary = get_analysis()

    return jsonify(summary.get("profile", {}))


@app.route("/api/orders")
def api_orders():
    summary = get_analysis()

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(int(request.args.get("per_page", 10)), 100))
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    search = request.args.get("search", "").lower().strip()
    category = request.args.get("category", "").strip()

    rows = list(summary.get("rows", []))

    if search:
        search_clean = search.lstrip("#")

        def matches_search(row):
            searchable_fields = [
                row.get("order_id"),
                row.get("product_id"),
                row.get("product_name"),
                row.get("category"),
                row.get("date"),
            ]

            return any(
                search_clean in str(value).lower()
                for value in searchable_fields
                if value is not None
            )

        rows = [row for row in rows if matches_search(row)]

    if category:
        rows = [
            row for row in rows
            if str(row.get("category") or "") == category
        ]

    total = len(rows)
    start = (page - 1) * per_page
    paginated = rows[start:start + per_page]

    return jsonify({
        "rows": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/categories")
def api_categories():
    summary = get_analysis()

    categories = sorted(
        {
            str(row["category"])
            for row in summary.get("rows", [])
            if row.get("category")
        }
    )

    return jsonify(categories)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}

    try:
        n = int(data.get("n", 50))
    except (TypeError, ValueError):
        return jsonify({"error": "n must be an integer"}), 400

    n = max(5, min(n, 5000))

    generate_ventes(str(VENTES_CSV), n)

    summary = get_analysis(force=True)

    return jsonify({
        "success": True,
        "rows_generated": n,
        "profile": summary.get("profile", {}),
    })


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Validate an uploaded CSV before replacing the active dataset.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files["file"]

    if not uploaded_file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not uploaded_file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    temp_path = DATA_DIR / "_uploaded_dataset.csv"

    try:
        uploaded_file.save(str(temp_path))

        # Validate and analyze before replacing the active dataset.
        test_summary = run_full_analysis(str(temp_path))

        # Replace the active dataset only after successful validation.
        temp_path.replace(VENTES_CSV)

        summary = get_analysis(force=True)

        return jsonify({
            "success": True,
            "filename": uploaded_file.filename,
            "profile": summary.get("profile", {}),
            "summary": {
                "ca_total": summary.get("ca_total", 0),
                "total_orders": summary.get("total_orders", 0),
                "total_rows": summary.get("total_rows", 0),
                "product_count": summary.get("product_count", 0),
            },
        })

    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()

        return jsonify({
            "error": f"Unable to process the CSV: {str(exc)}"
        }), 400


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json(silent=True) or {}

    try:
        prix = float(data["prix"])
        quantite = int(data["quantite"])
        remise = float(data.get("remise", 0))
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "error": f"Invalid simulation data: {exc}"
        }), 400

    if prix < 0:
        return jsonify({"error": "Price cannot be negative"}), 400

    if quantite <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400

    if not 0 <= remise <= 100:
        return jsonify({
            "error": "Discount must be between 0 and 100"
        }), 400

    ca_brut = round(prix * quantite, 2)
    remise_montant = round(ca_brut * (remise / 100), 2)
    ca_net = round(ca_brut - remise_montant, 2)

    tva = round(ca_net * 0.20, 2)
    ca_ttc = round(ca_net + tva, 2)

    return jsonify({
        "ca_brut": ca_brut,
        "ca_net": ca_net,
        "tva": tva,
        "ca_ttc": ca_ttc,
        "remise_montant": remise_montant,
    })


@app.route("/static/images/<path:filename>")
def serve_chart(filename):
    return send_from_directory(
        STATIC_DIR / "images",
        filename,
    )


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(
        DATA_DIR,
        filename,
    )


@app.route("/api/chart_product")
def api_chart_product():
    from scripts.charts import chart_ca_single_product

    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({
            "error": "Parameter 'name' is required"
        }), 400

    summary = get_analysis()

    path = chart_ca_single_product(name, summary)

    if not path:
        return jsonify({
            "error": f"Product not found: {name}"
        }), 404

    path = Path(path)

    try:
        filename = path.relative_to(STATIC_DIR / "images")
    except ValueError:
        filename = path.name

    return jsonify({
        "image_url": f"/static/images/{filename.as_posix()}"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
