import requests
import csv
import os
import re


# ============================================================
# COPERNICUS EMSR927 API
# ============================================================

url = "https://mapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/"

params = {
    "code": "EMSR927"
}


# ============================================================
# FETCH DATA
# ============================================================

response = requests.get(
    url,
    params=params,
    timeout=30
)

print("Status code:", response.status_code)

if response.status_code != 200:
    print(response.text)
    raise SystemExit


data = response.json()

results = data.get("results", [])

if not results:
    print("No EMSR927 activation found.")
    raise SystemExit


activation = results[0]

print(
    "\nActivation:",
    activation.get("code"),
    "-",
    activation.get("name")
)


# ============================================================
# OUTPUT FOLDER
# ============================================================

output_folder = "data/raw"

os.makedirs(
    output_folder,
    exist_ok=True
)


# ============================================================
# HELPER: GET CENTER OF AOI POLYGON
# ============================================================

def get_polygon_center(wkt_polygon):

    if not wkt_polygon:
        return None, None

    # Extract coordinate pairs from:
    # POLYGON ((longitude latitude, longitude latitude, ...))

    coordinate_pairs = re.findall(
        r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)",
        wkt_polygon
    )

    if not coordinate_pairs:
        return None, None

    longitudes = [
        float(pair[0])
        for pair in coordinate_pairs
    ]

    latitudes = [
        float(pair[1])
        for pair in coordinate_pairs
    ]

    # Simple geographic center of the AOI bounding box

    longitude = (
        min(longitudes) + max(longitudes)
    ) / 2

    latitude = (
        min(latitudes) + max(latitudes)
    ) / 2

    return latitude, longitude


# ============================================================
# EMPTY NORMALIZED DATASETS
# ============================================================

products_rows = []

population_rows = []

builtup_rows = []

transportation_rows = []

landuse_rows = []

other_rows = []


# ============================================================
# LOOP THROUGH AOIs
# ============================================================

aois = activation.get("aois", [])

for aoi in aois:

    aoi_name = aoi.get("name")

    # --------------------------------------------------------
    # Get geographic center from the AOI polygon
    # --------------------------------------------------------

    aoi_extent = aoi.get("extent")

    latitude, longitude = get_polygon_center(
        aoi_extent
    )


    # --------------------------------------------------------
    # Only keep products that actually contain statistics
    # --------------------------------------------------------

    usable_products = [
        product
        for product in aoi.get("products", [])
        if product.get("stats") is not None
    ]

    if not usable_products:

        print(
            f"\nSkipping {aoi_name}: "
            "no completed statistics available."
        )

        continue


    # --------------------------------------------------------
    # Select the most useful completed product
    #
    # Higher monitoring number is preferred.
    # If monitoring number is the same, higher version wins.
    # --------------------------------------------------------

    selected_product = max(
        usable_products,
        key=lambda product: (
            product.get("monitoringNumber", 0),
            product.get("version", {}).get("number", 0)
        )
    )


    product_id = selected_product.get("id")

    monitoring = selected_product.get("monitoring")

    monitoring_number = selected_product.get(
        "monitoringNumber"
    )

    version_number = selected_product.get(
        "version",
        {}
    ).get("number")


    print(
        f"\nSelected {aoi_name}"
        f" → Product {product_id}"
        f" → Lat {latitude:.5f}"
        f", Lon {longitude:.5f}"
    )


    # ========================================================
    # PRODUCT TABLE
    # ========================================================

    products_rows.append({
        "aoi_name": aoi_name,
        "product_id": product_id,
        "monitoring": monitoring,
        "monitoring_number": monitoring_number,
        "version_number": version_number,
        "latitude": latitude,
        "longitude": longitude,
        "aoi_extent_wkt": aoi_extent 
    })

    # ========================================================
    # PRODUCT STATISTICS
    # ========================================================

    stats = selected_product.get(
        "stats",
        {}
    )


    # ========================================================
    # POPULATION
    # ========================================================

    population_group = stats.get(
        "Estimated population",
        {}
    )

    for category, values in population_group.items():

        population_rows.append({
            "product_id": product_id,
            "category": category,
            "total_value": values.get("total"),
            "affected_value": values.get("affected"),
            "unit": values.get("unit")
        })


    # ========================================================
    # BUILT-UP
    # ========================================================

    builtup_group = stats.get(
        "Built-up",
        {}
    )

    for category, values in builtup_group.items():

        builtup_rows.append({
            "product_id": product_id,
            "category": category,
            "total_value": values.get("total"),
            "affected_value": values.get("affected"),
            "unit": values.get("unit")
        })


    # ========================================================
    # TRANSPORTATION
    # ========================================================

    transportation_group = stats.get(
        "Transportation",
        {}
    )

    for category, values in transportation_group.items():

        transportation_rows.append({
            "product_id": product_id,
            "category": category,
            "total_value": values.get("total"),
            "affected_value": values.get("affected"),
            "unit": values.get("unit")
        })


    # ========================================================
    # LAND USE
    # ========================================================

    landuse_group = stats.get(
        "Land use",
        {}
    )

    for category, values in landuse_group.items():

        landuse_rows.append({
            "product_id": product_id,
            "category": category,
            "total_value": values.get("total"),
            "affected_value": values.get("affected"),
            "unit": values.get("unit")
        })


    # ========================================================
    # OTHER STATISTICS
    #
    # Anything that is not one of the main groups above
    # will be stored here.
    # ========================================================

    ignored_groups = {
        "Estimated population",
        "Built-up",
        "Transportation",
        "Land use"
    }

    for group_name, group_data in stats.items():

        if group_name in ignored_groups:
            continue

        if not isinstance(
            group_data,
            dict
        ):
            continue


        for category, values in group_data.items():

            if not isinstance(
                values,
                dict
            ):
                continue


            other_rows.append({
                "product_id": product_id,
                "group_name": group_name,
                "category": category,
                "total_value": values.get("total"),
                "affected_value": values.get("affected"),
                "unit": values.get("unit")
            })


# ============================================================
# CSV HELPER FUNCTION
# ============================================================

def save_csv(
    filename,
    rows
):

    if not rows:

        print(
            f"No data to save for {filename}"
        )

        return


    output_file = os.path.join(
        output_folder,
        filename
    )


    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


    print(
        f"Saved: {output_file}"
    )


# ============================================================
# SAVE NORMALIZED CSV FILES
# ============================================================

print("\nSaving normalized Copernicus datasets...\n")


save_csv(
    "copernicus_products.csv",
    products_rows
)


save_csv(
    "copernicus_population.csv",
    population_rows
)


save_csv(
    "copernicus_builtup.csv",
    builtup_rows
)


save_csv(
    "copernicus_transportation.csv",
    transportation_rows
)


save_csv(
    "copernicus_landuse.csv",
    landuse_rows
)


save_csv(
    "copernicus_other_stats.csv",
    other_rows
)


print(
    "\nCopernicus extraction completed successfully."
)