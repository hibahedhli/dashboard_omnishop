"""
data_adapter.py
Detects and normalizes common sales-dataset schemas.

The rest of the application works with a canonical schema regardless
of the original CSV column names.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


CANONICAL_FIELDS = [
    "order_id",
    "product_id",
    "product_name",
    "price",
    "quantity",
    "discount",
    "vat_rate",
    "category",
    "date",
]


COLUMN_ALIASES = {
    "order_id": [
        "id_commande",
        "order_id",
        "orderid",
        "order id",
        "invoice_no",
        "invoiceno",
        "invoice_id",
        "invoiceid",
        "invoice",
        "transaction_id",
        "transactionid",
        "transaction",
        "commande",
    ],
    "product_id": [
        "id_produit",
        "product_id",
        "productid",
        "product id",
        "sku",
        "stockcode",
        "stock_code",
        "product_code",
        "productcode",
        "item_id",
        "itemid",
    ],
    "product_name": [
        "produit",
        "product",
        "product_name",
        "productname",
        "product name",
        "description",
        "item",
        "item_name",
        "itemname",
        "item name",
    ],
    "price": [
        "prix",
        "price",
        "unit_price",
        "unitprice",
        "unit price",
        "sales_price",
        "salesprice",
        "sale_price",
        "amount",
    ],
    "quantity": [
        "quantite",
        "quantity",
        "qty",
        "units",
        "units_sold",
        "unitssold",
        "count",
    ],
    "discount": [
        "remise",
        "discount",
        "discount_pct",
        "discount_percent",
        "discountpercentage",
        "discount percentage",
    ],
    "vat_rate": [
        "vat_rate",
        "vatrate",
        "vat rate",
        "vat_%",
        "vat percentage",
        "vat_percent",
        "tva_rate",
        "tvarate",
        "tva rate",
        "tva_%",
        "tva percentage",
        "tva_percent",
        "tax_rate",
        "taxrate",
        "tax rate",
        "tax_%",
        "tax percentage",
        "tax_percent",
    ],
    "category": [
        "categorie",
        "category",
        "product_category",
        "productcategory",
        "product category",
        "cat",
    ],
    "date": [
        "date",
        "order_date",
        "orderdate",
        "order date",
        "invoice_date",
        "invoicedate",
        "invoice date",
        "transaction_date",
        "transactiondate",
        "transaction date",
        "sale_date",
        "saledate",
        "created_at",
        "createdat",
    ],
}


REQUIRED_FIELDS = ["price", "quantity"]


def clean_column_name(name: Any) -> str:
    """Normalize a column name for comparison."""
    if name is None:
        return ""

    value = str(name).strip().lower()
    value = value.replace("-", "_")
    value = value.replace("/", "_")
    value = re.sub(r"\s+", " ", value)
    return value


def detect_encoding(filepath: str) -> str:
    """
    Try common encodings used by CSV exports.
    UTF-8 is preferred, with cp1252 as fallback.
    """
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(filepath, "r", encoding=encoding) as f:
                f.read(4096)
            return encoding
        except UnicodeDecodeError:
            continue

    return "utf-8"


def load_raw_csv(filepath: str) -> tuple[List[Dict[str, Any]], List[str], str]:
    """Load a CSV and return rows, original columns and detected encoding."""
    encoding = detect_encoding(filepath)

    with open(filepath, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("The CSV file does not contain a header row.")

        columns = [str(column).strip() for column in reader.fieldnames]
        rows = list(reader)

    return rows, columns, encoding


def find_column(columns: List[str], aliases: List[str]) -> Optional[str]:
    """
    Find the best matching source column for a canonical field.

    Exact normalized matches are preferred.
    """
    normalized_columns = {
        clean_column_name(column): column for column in columns
    }

    for alias in aliases:
        normalized_alias = clean_column_name(alias)
        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]

    return None


def detect_schema(columns: List[str]) -> Dict[str, Optional[str]]:
    """Map canonical fields to the original CSV columns."""
    mapping: Dict[str, Optional[str]] = {}

    for canonical_field, aliases in COLUMN_ALIASES.items():
        mapping[canonical_field] = find_column(columns, aliases)

    return mapping


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely convert a value to float."""
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    text = text.replace(" ", "")

    # Support common decimal formats such as 12,50.
    if "," in text and "." not in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely convert a value to int."""
    number = to_float(value)

    if number is None:
        return default

    return int(number)


def normalize_rows(
    rows: List[Dict[str, Any]],
    mapping: Dict[str, Optional[str]],
) -> List[Dict[str, Any]]:
    """
    Convert source rows into the canonical internal schema.

    Missing optional fields remain None.
    Missing identifiers are NOT fabricated.
    """
    normalized_rows: List[Dict[str, Any]] = []

    for index, source_row in enumerate(rows, start=1):
        price_column = mapping.get("price")
        quantity_column = mapping.get("quantity")

        price = to_float(
            source_row.get(price_column) if price_column else None
        )
        quantity = to_int(
            source_row.get(quantity_column) if quantity_column else None
        )

        # Price and quantity are required for line-level sales analysis.
        if price is None or quantity is None:
            continue

        order_column = mapping.get("order_id")
        product_id_column = mapping.get("product_id")
        product_name_column = mapping.get("product_name")
        discount_column = mapping.get("discount")
        vat_rate_column = mapping.get("vat_rate")
        category_column = mapping.get("category")
        date_column = mapping.get("date")

        normalized = {
            "order_id": (
                str(source_row.get(order_column)).strip()
                if order_column and source_row.get(order_column) not in (None, "")
                else None
            ),
            "product_id": (
                str(source_row.get(product_id_column)).strip()
                if product_id_column
                and source_row.get(product_id_column) not in (None, "")
                else None
            ),
            "product_name": (
                str(source_row.get(product_name_column)).strip()
                if product_name_column
                and source_row.get(product_name_column) not in (None, "")
                else None
            ),
            "price": price,
            "quantity": quantity,
            "discount": to_float(
                source_row.get(discount_column)
                if discount_column
                else None,
                default=0.0,
            ),
            "vat_rate": to_float(
                source_row.get(vat_rate_column)
                if vat_rate_column
                else None,
                default=None,
            ),
            "category": (
                str(source_row.get(category_column)).strip()
                if category_column
                and source_row.get(category_column) not in (None, "")
                else None
            ),
            "date": (
                str(source_row.get(date_column)).strip()
                if date_column
                and source_row.get(date_column) not in (None, "")
                else None
            ),
            "_source_row": index,
        }

        normalized_rows.append(normalized)

    return normalized_rows


def build_profile(
    original_columns: List[str],
    mapping: Dict[str, Optional[str]],
    raw_row_count: int,
    normalized_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a dataset profile for the frontend."""
    valid_rows = normalized_rows

    order_ids = {
        row["order_id"]
        for row in valid_rows
        if row.get("order_id")
    }

    product_keys = {
        row["product_id"] or row["product_name"]
        for row in valid_rows
        if row.get("product_id") or row.get("product_name")
    }

    categories = {
        row["category"]
        for row in valid_rows
        if row.get("category")
    }

    dates = [
        row["date"]
        for row in valid_rows
        if row.get("date")
    ]

    fields = {}

    for field in CANONICAL_FIELDS:
        source_column = mapping.get(field)

        fields[field] = {
            "detected": source_column is not None,
            "source_column": source_column,
        }

    return {
        "original_columns": original_columns,
        "rows": raw_row_count,
        "valid_rows": len(valid_rows),
        "invalid_rows": raw_row_count - len(valid_rows),
        "orders": len(order_ids),
        "products": len(product_keys),
        "categories": len(categories),
        "date_range": {
            "min": min(dates) if dates else None,
            "max": max(dates) if dates else None,
        },
        "fields": fields,
    }


def adapt_dataset(filepath: str) -> Dict[str, Any]:
    """
    Complete adaptation pipeline:

    CSV
      -> schema detection
      -> normalization
      -> dataset profile
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    if path.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are currently supported.")

    rows, columns, encoding = load_raw_csv(str(path))
    mapping = detect_schema(columns)

    missing_required = [
        field for field in REQUIRED_FIELDS
        if not mapping.get(field)
    ]

    if missing_required:
        readable = ", ".join(missing_required)
        raise ValueError(
            f"Unable to identify required sales columns: {readable}. "
            f"Detected columns: {', '.join(columns)}"
        )

    normalized_rows = normalize_rows(rows, mapping)

    if not normalized_rows:
        raise ValueError(
            "No valid sales rows were found. "
            "Check the price and quantity columns."
        )

    profile = build_profile(
        columns,
        mapping,
        len(rows),
        normalized_rows,
    )

    profile["encoding"] = encoding
    profile["mapping"] = mapping

    return {
        "rows": normalized_rows,
        "profile": profile,
    }


