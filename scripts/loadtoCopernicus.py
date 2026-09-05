import csv
from decimal import Decimal, InvalidOperation

import pymssql


# ============================================================
# SQL SERVER CONNECTION
# ============================================================

server = "localhost"
port = 1433
database = "nepal_flood"
username = "sa"

# Use your existing local SA password.
# Do not commit the real password to GitHub.
password = "FloodProject#2026"


connection = pymssql.connect(
    server=server,
    port=port,
    user=username,
    password=password,
    database=database
)

cursor = connection.cursor()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """
    Convert blank CSV values into None.
    SQL Server will store None as NULL.
    """

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def clean_numeric(value, field_name="", row_info=""):
    """
    Safely convert CSV values into numbers.

    Examples:
        "450"   -> Decimal("450")
        "3.7"   -> Decimal("3.7")
        ""      -> None
        "None"  -> None

    If Copernicus provides unexpected text in a numeric field,
    we print it and store NULL instead of crashing.
    """

    value = clean_text(value)

    if value is None:
        return None

    # Remove commas from numbers such as 25,000
    cleaned = value.replace(",", "")

    try:
        return Decimal(cleaned)

    except InvalidOperation:

        print(
            f"WARNING: Non-numeric value skipped "
            f"| field={field_name} "
            f"| value={value!r} "
            f"| {row_info}"
        )

        return None


def get_product_key(product_key_map, product_id):
    """
    Find the SQL product key that belongs to
    a Copernicus API product_id.
    """

    product_id = str(product_id)

    if product_id not in product_key_map:
        raise ValueError(
            f"Product ID {product_id} was not found "
            "in copernicus_products."
        )

    return product_key_map[product_id]


# ============================================================
# RESET EXISTING COPERNICUS DATA
#
# Child tables must be cleared before the parent table because
# of foreign-key relationships.
# ============================================================

print("Clearing existing Copernicus data...")


cursor.execute("DELETE FROM copernicus_population")
cursor.execute("DELETE FROM copernicus_builtup")
cursor.execute("DELETE FROM copernicus_transportation")
cursor.execute("DELETE FROM copernicus_landuse")
cursor.execute("DELETE FROM copernicus_other_stats")

cursor.execute("DELETE FROM copernicus_products")


# ============================================================
# RESET IDENTITY COUNTERS
#
# During development this makes IDs start from 1 again.
# ============================================================

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_population', RESEED, 0)"
)

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_builtup', RESEED, 0)"
)

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_transportation', RESEED, 0)"
)

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_landuse', RESEED, 0)"
)

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_other_stats', RESEED, 0)"
)

cursor.execute(
    "DBCC CHECKIDENT ('copernicus_products', RESEED, 0)"
)

connection.commit()


# ============================================================
# STEP 1: LOAD COPERNICUS PRODUCTS
#
# Parent table must be loaded first.
#
# product_key_map connects:
#
# Copernicus product_id
#            ↓
# SQL copernicus_product_key
# ============================================================

product_key_map = {}

products_file = "data/raw/copernicus_products.csv"


with open(
    products_file,
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        monitoring_text = (
            clean_text(row.get("monitoring")) or ""
        ).lower()

        monitoring_value = (
            1 if monitoring_text == "true" else 0
        )

        query = """
        INSERT INTO copernicus_products (
            aoi_name,
            product_id,
            monitoring,
            monitoring_number,
            version_number,
            latitude,
            longitude,
            aoi_extent_wkt
        )
        OUTPUT INSERTED.copernicus_product_key
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                clean_text(row.get("aoi_name")),

                clean_numeric(
                    row.get("product_id"),
                    "product_id",
                    row.get("aoi_name", "")
                ),

                monitoring_value,

                clean_numeric(
                    row.get("monitoring_number"),
                    "monitoring_number",
                    row.get("aoi_name", "")
                ),

                clean_numeric(
                    row.get("version_number"),
                    "version_number",
                    row.get("aoi_name", "")
                ),

                clean_numeric(
                    row.get("latitude"),
                    "latitude",
                    row.get("aoi_name", "")
                ),

                clean_numeric(
                    row.get("longitude"),
                    "longitude",
                    row.get("aoi_name", "")
                ),
                clean_text(
                    row.get("aoi_extent_wkt")
                )
            )
        )

        generated_key = cursor.fetchone()[0]

        product_key_map[
            str(row["product_id"])
        ] = generated_key


connection.commit()

print(
    f"Loaded {len(product_key_map)} Copernicus products."
)

# ============================================================
# STEP 2: LOAD POPULATION
# ============================================================

population_count = 0

with open(
    "data/raw/copernicus_population.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        product_key = get_product_key(
            product_key_map,
            row["product_id"]
        )

        query = """
        INSERT INTO copernicus_population (
            copernicus_product_key,
            total_value,
            affected_value,
            unit
        )
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_key,
                clean_numeric(
                    row.get("total_value"),
                    "total_value",
                    f"product_id={row['product_id']}"
                ),
                clean_numeric(
                    row.get("affected_value"),
                    "affected_value",
                    f"product_id={row['product_id']}"
                ),
                clean_text(row.get("unit"))
            )
        )

        population_count += 1


connection.commit()

print(
    f"Loaded {population_count} population statistics."
)


# ============================================================
# STEP 3: LOAD BUILT-UP STATISTICS
# ============================================================

builtup_count = 0

with open(
    "data/raw/copernicus_builtup.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        product_key = get_product_key(
            product_key_map,
            row["product_id"]
        )

        row_info = (
            f"product_id={row['product_id']} "
            f"category={row.get('category')}"
        )

        query = """
        INSERT INTO copernicus_builtup (
            copernicus_product_key,
            category,
            total_value,
            affected_value,
            unit
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_key,
                clean_text(row.get("category")),
                clean_numeric(
                    row.get("total_value"),
                    "total_value",
                    row_info
                ),
                clean_numeric(
                    row.get("affected_value"),
                    "affected_value",
                    row_info
                ),
                clean_text(row.get("unit"))
            )
        )

        builtup_count += 1


connection.commit()

print(
    f"Loaded {builtup_count} built-up statistics."
)


# ============================================================
# STEP 4: LOAD TRANSPORTATION STATISTICS
# ============================================================

transportation_count = 0

with open(
    "data/raw/copernicus_transportation.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        product_key = get_product_key(
            product_key_map,
            row["product_id"]
        )

        row_info = (
            f"product_id={row['product_id']} "
            f"category={row.get('category')}"
        )

        query = """
        INSERT INTO copernicus_transportation (
            copernicus_product_key,
            category,
            total_value,
            affected_value,
            unit
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_key,
                clean_text(row.get("category")),
                clean_numeric(
                    row.get("total_value"),
                    "total_value",
                    row_info
                ),
                clean_numeric(
                    row.get("affected_value"),
                    "affected_value",
                    row_info
                ),
                clean_text(row.get("unit"))
            )
        )

        transportation_count += 1


connection.commit()

print(
    f"Loaded {transportation_count} "
    "transportation statistics."
)


# ============================================================
# STEP 5: LOAD LAND-USE STATISTICS
# ============================================================

landuse_count = 0

with open(
    "data/raw/copernicus_landuse.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        product_key = get_product_key(
            product_key_map,
            row["product_id"]
        )

        row_info = (
            f"product_id={row['product_id']} "
            f"category={row.get('category')}"
        )

        query = """
        INSERT INTO copernicus_landuse (
            copernicus_product_key,
            category,
            total_value,
            affected_value,
            unit
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_key,
                clean_text(row.get("category")),
                clean_numeric(
                    row.get("total_value"),
                    "total_value",
                    row_info
                ),
                clean_numeric(
                    row.get("affected_value"),
                    "affected_value",
                    row_info
                ),
                clean_text(row.get("unit"))
            )
        )

        landuse_count += 1


connection.commit()

print(
    f"Loaded {landuse_count} land-use statistics."
)


# ============================================================
# STEP 6: LOAD OTHER STATISTICS
#
# This was where the previous loader failed.
#
# Numeric values are now safely validated before being sent
# to SQL Server.
# ============================================================

other_count = 0

with open(
    "data/raw/copernicus_other_stats.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        product_key = get_product_key(
            product_key_map,
            row["product_id"]
        )

        row_info = (
            f"product_id={row['product_id']} "
            f"group={row.get('group_name')} "
            f"category={row.get('category')}"
        )

        query = """
        INSERT INTO copernicus_other_stats (
            copernicus_product_key,
            group_name,
            category,
            total_value,
            affected_value,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                product_key,
                clean_text(row.get("group_name")),
                clean_text(row.get("category")),
                clean_numeric(
                    row.get("total_value"),
                    "total_value",
                    row_info
                ),
                clean_numeric(
                    row.get("affected_value"),
                    "affected_value",
                    row_info
                ),
                clean_text(row.get("unit"))
            )
        )

        other_count += 1


connection.commit()

print(
    f"Loaded {other_count} other Copernicus statistics."
)


# ============================================================
# CLOSE CONNECTION
# ============================================================

cursor.close()
connection.close()


print(
    "\nCopernicus data loaded into SQL Server successfully."
)