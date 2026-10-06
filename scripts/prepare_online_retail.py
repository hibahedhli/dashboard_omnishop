from pathlib import Path
import pandas as pd


SOURCE = Path(r"C:\Users\BICHA\Desktop\online+retail\Online Retail.xlsx")
OUTPUT = Path("data/online_retail_dashboard.csv")


def classify_category(description):
    """Assign a transparent category from the real product description."""
    if pd.isna(description):
        return "Other"

    text = str(description).strip().upper()

    # Shipping / postage
    if "POSTAGE" in text or "CARRIAGE" in text:
        return "Shipping"

    # Christmas / seasonal / party
    seasonal_keywords = [
        "CHRISTMAS",
        "XMAS",
        "SANTA",
        "HALLOWEEN",
        "PARTY",
        "BUNTING",
        "EASTER",
    ]
    if any(keyword in text for keyword in seasonal_keywords):
        return "Party & Seasonal"

    # Bags
    bag_keywords = [
        "JUMBO BAG",
        "LUNCH BAG",
        "SHOPPER",
        "CHARLOTTE BAG",
        "TOTE BAG",
        "PURSE",
        "HANDBAG",
        "BAG",
    ]
    if any(keyword in text for keyword in bag_keywords):
        return "Bags & Accessories"

    # Kitchen / dining
    kitchen_keywords = [
        "CAKE",
        "CAKESTAND",
        "BAKING",
        "BAKE",
        "KITCHEN",
        "TEACUP",
        "TEA SET",
        "MUG",
        "CUP",
        "PLATE",
        "BOWL",
        "SPOON",
        "FORK",
        "KNIFE",
        "CUTLERY",
        "JAR",
        "JELLY MOULD",
        "COOKIE CUTTER",
        "SPICE",
        "NAPKIN",
        "LUNCH BOX",
        "FOOD",
        "RECIPE BOX",
    ]
    if any(keyword in text for keyword in kitchen_keywords):
        return "Kitchen & Dining"

    # Garden
    garden_keywords = [
        "GARDEN",
        "GARDENER",
        "PLANT",
        "FLOWER",
        "BIRD",
        "BUTTERFLY",
        "WATERING",
        "SEED",
        "KNEELING PAD",
    ]
    if any(keyword in text for keyword in garden_keywords):
        return "Garden"

    # Lighting
    lighting_keywords = [
        "T-LIGHT",
        "LIGHT HOLDER",
        "LANTERN",
        "LAMP",
        "CANDLE",
    ]
    if any(keyword in text for keyword in lighting_keywords):
        return "Lighting"

    # Clocks / household
    clock_keywords = [
        "CLOCK",
        "DOORMAT",
        "HOT WATER BOTTLE",
        "SCALES",
        "COAT RACK",
        "STORAGE",
    ]
    if any(keyword in text for keyword in clock_keywords):
        return "Home & Household"

    # Home decoration
    decor_keywords = [
        "HEART",
        "ORNAMENT",
        "FRAME",
        "PICTURE",
        "SIGN",
        "DECOR",
        "TRINKET",
        "HOLDER",
        "CHALKBOARD",
        "WOODEN",
        "MIRROR",
    ]
    if any(keyword in text for keyword in decor_keywords):
        return "Home & Decor"

    # Stationery / office
    stationery_keywords = [
        "PAPER",
        "PEN",
        "PENCIL",
        "NOTEBOOK",
        "NOTE PAD",
        "STATIONERY",
        "CARD",
        "RIBBON",
        "TAPE",
        "LABEL",
    ]
    if any(keyword in text for keyword in stationery_keywords):
        return "Stationery"

    # Toys / children
    toy_keywords = [
        "TOY",
        "DOLL",
        "GAME",
        "CHILDREN",
        "KIDS",
        "LUNCH BOX",
    ]
    if any(keyword in text for keyword in toy_keywords):
        return "Toys & Children"

    # Personal care / health
    personal_care_keywords = [
        "CREAM",
        "SOAP",
        "PLASTER",
        "TOILET",
        "BATH",
        "BEAUTY",
        "COSMETIC",
    ]
    if any(keyword in text for keyword in personal_care_keywords):
        return "Health & Personal Care"

    return "Other"


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE}")

    print("Reading Online Retail.xlsx...")
    df = pd.read_excel(SOURCE)

    print(f"Original rows: {len(df):,}")

    # Keep rows with usable product information.
    df = df.dropna(subset=["Description"]).copy()

    # Remove only impossible negative prices.
    # Negative quantities are intentionally preserved because they represent
    # real returns/cancellations in the source dataset.
    df = df[df["UnitPrice"] >= 0].copy()

    result = pd.DataFrame(
        {
            "ID_Commande": df["InvoiceNo"].astype(str),
            "ID_Produit": df["StockCode"].astype(str),
            "Produit": df["Description"].astype(str).str.strip(),
            "Prix": pd.to_numeric(df["UnitPrice"], errors="coerce"),
            "Quantite": pd.to_numeric(df["Quantity"], errors="coerce"),
            "Remise": 0.0,
            "Categorie": df["Description"].apply(classify_category),
            "Date": pd.to_datetime(df["InvoiceDate"], errors="coerce"),
        }
    )

    # Remove rows where the required numeric/date fields could not be parsed.
    result = result.dropna(
        subset=["Prix", "Quantite", "Date"]
    ).copy()

    # Format the date for the dashboard's CSV adapter.
    result["Date"] = result["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print()
    print("Conversion complete.")
    print(f"Output: {OUTPUT}")
    print(f"Rows: {len(result):,}")
    print(f"Products: {result['ID_Produit'].nunique():,}")
    print(f"Orders: {result['ID_Commande'].nunique():,}")
    print(f"Categories: {result['Categorie'].nunique():,}")
    print()
    print("Category distribution:")
    print(result["Categorie"].value_counts().to_string())
    print()
    print("Negative quantity rows preserved:", (result["Quantite"] < 0).sum())
    print("Zero-price rows preserved:", (result["Prix"] == 0).sum())


if __name__ == "__main__":
    main()
