"""Profile the supplied CSV, JSON, and Parquet source files."""

from pathlib import Path
import json
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def logical_type(column_name, series):
    """Give a simple logical type based on values and column name."""
    name = column_name.lower()

    if "date" in name or "time" in name:
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.notna().any():
            return "date/timestamp"

    if pd.api.types.is_integer_dtype(series):
        return "integer"

    if pd.api.types.is_numeric_dtype(series):
        return "number"

    return "string"


def profile_csv(path):
    print("\n" + "=" * 60)
    print("CSV PROFILE:", path.name)
    print("=" * 60)

    df = pd.read_csv(path)

    print("File size (bytes):", path.stat().st_size)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Column names:", list(df.columns))

    print("\nLogical types:")
    for col in df.columns:
        print(f"  {col}: {logical_type(col, df[col])}")

    print("\nMissing values by column:")
    print(df.isna().sum())

    print("\nExact duplicate rows:", int(df.duplicated().sum()))

    if "customer_id" in df.columns:
        print(
            "customer_id is unique:",
            bool(df["customer_id"].is_unique)
        )
        print(
            "Duplicate customer_id values:",
            int(df["customer_id"].duplicated().sum())
        )

    print("\nFirst five records:")
    print(df.head())

    print("\nCandidate validation rules:")
    print("1. customer_id should not be null.")
    print("2. customer_id should be unique.")
    print("3. signup_date should contain valid dates.")
    print("4. email should follow a valid email format.")


def profile_json(path):
    print("\n" + "=" * 60)
    print("JSON PROFILE:", path.name)
    print("=" * 60)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print("File size (bytes):", path.stat().st_size)
    print("Top-level structure:", type(data).__name__)

    if not isinstance(data, list):
        print("Expected a list of records.")
        return

    print("Record count:", len(data))

    all_keys = sorted(
        set().union(*(record.keys() for record in data))
    )

    print("Top-level keys:", all_keys)

    nested_fields = set()
    timestamp_fields = set()
    numeric_fields = set()

    for record in data:
        for key, value in record.items():

            if isinstance(value, (dict, list)):
                nested_fields.add(key)

            if "date" in key.lower() or "time" in key.lower():
                timestamp_fields.add(key)

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric_fields.add(key)

    print("Nested fields:", sorted(nested_fields))
    print("Timestamp/date fields:", sorted(timestamp_fields))
    print("Numeric fields:", sorted(numeric_fields))

    print("\nNull or missing values by key:")

    for key in all_keys:
        missing = sum(
            1 for record in data
            if key not in record or record.get(key) is None
        )
        print(f"  {key}: {missing}")

    print("\nFirst record:")
    print(json.dumps(data[0], indent=2))

    print("\nPossible downstream representations of shipping:")
    print("1. Keep shipping as a nested JSON object.")
    print("2. Flatten it into columns such as shipping_region and shipping_method.")


def profile_parquet(path):
    print("\n" + "=" * 60)
    print("PARQUET PROFILE:", path.name)
    print("=" * 60)

    df = pd.read_parquet(path)

    print("File size (bytes):", path.stat().st_size)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Shape:", df.shape)

    print("\nColumn data types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nFirst five records:")
    print(df.head())

    csv_compare = DATA_DIR / "products_optional_compare.csv"
    json_compare = DATA_DIR / "products_optional_compare.json"

    print("\nFormat size comparison:")
    print("Parquet:", path.stat().st_size, "bytes")

    if csv_compare.exists():
        print("CSV:", csv_compare.stat().st_size, "bytes")

    if json_compare.exists():
        print("JSON:", json_compare.stat().st_size, "bytes")

    print("\nFormat observation:")
    print(
        "Parquet stores schema and data types more explicitly than plain "
        "CSV and is optimized for analytical storage."
    )


if __name__ == "__main__":
    profile_csv(DATA_DIR / "customers.csv")
    profile_json(DATA_DIR / "orders.json")
    profile_parquet(DATA_DIR / "products.parquet")