import streamlit as st
import pandas as pd
import pymssql
import folium
from streamlit_folium import st_folium
from pathlib import Path


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="🇳🇵 Nepal Flood Impact Analysis",
    layout="wide"
)


# ============================================================
# SQL SERVER CONNECTION
# ============================================================

server = "localhost"
port = 1433
database = "nepal_flood"
username = "sa"
data_source = st.secrets["app"]["data_source"]

password = None

if data_source == "sql":
    password = st.secrets["database"]["password"]


# ============================================================
# DATA SOURCE SETUP
# ============================================================

data_source = str(data_source).strip().lower()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


# ============================================================
# HELPER FUNCTION: RUN SQL QUERY
# ============================================================

def run_query(query):

    connection = pymssql.connect(
        server=server,
        port=port,
        user=username,
        password=password,
        database=database
    )

    cursor = connection.cursor()

    cursor.execute(query)

    rows = cursor.fetchall()

    columns = [
        column[0]
        for column in cursor.description
    ]

    dataframe = pd.DataFrame(
        rows,
        columns=columns
    )

    cursor.close()
    connection.close()

    return dataframe


# ============================================================
# LOAD DATA FROM SQL SERVER
# ============================================================

def load_sql_data():

    summary_query = """
    SELECT
        s.*,
        p.latitude,
        p.longitude
    FROM vw_copernicus_aoi_summary AS s
    INNER JOIN copernicus_products AS p
        ON s.aoi_name = p.aoi_name
    ORDER BY s.population_affected_pct DESC;
    """


    builtup_query = """
    SELECT
        p.aoi_name,
        b.category,
        b.total_value,
        b.affected_value,
        b.unit
    FROM copernicus_products AS p
    INNER JOIN copernicus_builtup AS b
        ON p.copernicus_product_key =
           b.copernicus_product_key
    ORDER BY
        p.aoi_name,
        b.category;
    """


    transportation_query = """
    SELECT
        p.aoi_name,
        t.category,
        t.total_value,
        t.affected_value,
        t.unit
    FROM copernicus_products AS p
    INNER JOIN copernicus_transportation AS t
        ON p.copernicus_product_key =
           t.copernicus_product_key
    ORDER BY
        p.aoi_name,
        t.category;
    """


    landuse_query = """
    SELECT
        p.aoi_name,
        l.category,
        l.total_value,
        l.affected_value,
        l.unit
    FROM copernicus_products AS p
    INNER JOIN copernicus_landuse AS l
        ON p.copernicus_product_key =
           l.copernicus_product_key
    ORDER BY
        p.aoi_name,
        l.category;
    """


    landslide_query = """
    SELECT *
    FROM vw_copernicus_landslide_impact
    ORDER BY landslide_affected_area_ha DESC;
    """


    summary_df = run_query(
        summary_query
    )

    builtup_df = run_query(
        builtup_query
    )

    transportation_df = run_query(
        transportation_query
    )

    landuse_df = run_query(
        landuse_query
    )

    landslide_df = run_query(
        landslide_query
    )

    return (
        summary_df,
        builtup_df,
        transportation_df,
        landuse_df,
        landslide_df
    )


# ============================================================
# LOAD DATA FROM CSV FILES
# ============================================================

def load_csv_data():

    products = pd.read_csv(
        RAW_DATA_DIR / "copernicus_products.csv"
    )

    population = pd.read_csv(
        RAW_DATA_DIR / "copernicus_population.csv"
    )

    builtup = pd.read_csv(
        RAW_DATA_DIR / "copernicus_builtup.csv"
    )

    transportation = pd.read_csv(
        RAW_DATA_DIR / "copernicus_transportation.csv"
    )

    landuse = pd.read_csv(
        RAW_DATA_DIR / "copernicus_landuse.csv"
    )

    other_stats = pd.read_csv(
        RAW_DATA_DIR / "copernicus_other_stats.csv"
    )


    # --------------------------------------------------------
    # POPULATION SUMMARY
    # --------------------------------------------------------

    population_summary = population[
        [
            "product_id",
            "total_value",
            "affected_value"
        ]
    ].copy()

    population_summary = population_summary.rename(
        columns={
            "total_value":
                "population_total",
            "affected_value":
                "population_affected"
        }
    )


    # --------------------------------------------------------
    # RESIDENTIAL BUILDING SUMMARY
    # --------------------------------------------------------

    residential = builtup[
        builtup["category"]
        == "Residential Buildings"
    ][
        [
            "product_id",
            "total_value",
            "affected_value"
        ]
    ].copy()

    residential = residential.rename(
        columns={
            "total_value":
                "residential_buildings_total",
            "affected_value":
                "residential_buildings_affected"
        }
    )


    # --------------------------------------------------------
    # LANDSLIDE SUMMARY
    # --------------------------------------------------------

    landslide = other_stats[
        other_stats["group_name"]
        == "Landslide"
    ][
        [
            "product_id",
            "affected_value"
        ]
    ].copy()

    landslide = landslide.rename(
        columns={
            "affected_value":
                "landslide_affected_area_ha"
        }
    )


    # --------------------------------------------------------
    # BUILD OVERVIEW DATAFRAME
    # --------------------------------------------------------

    summary_df = products[
        [
            "product_id",
            "aoi_name",
            "latitude",
            "longitude"
        ]
    ].copy()


    summary_df = summary_df.merge(
        population_summary,
        on="product_id",
        how="left"
    )


    summary_df = summary_df.merge(
        residential,
        on="product_id",
        how="left"
    )


    summary_df = summary_df.merge(
        landslide,
        on="product_id",
        how="left"
    )


    # --------------------------------------------------------
    # CALCULATE PERCENTAGES
    # --------------------------------------------------------

    summary_df[
        "population_affected_pct"
    ] = (
        summary_df["population_affected"]
        / summary_df["population_total"]
        * 100
    )


    summary_df[
        "residential_buildings_affected_pct"
    ] = (
        summary_df[
            "residential_buildings_affected"
        ]
        / summary_df[
            "residential_buildings_total"
        ]
        * 100
    )


    # --------------------------------------------------------
    # ADD AOI NAMES TO DETAIL TABLES
    # --------------------------------------------------------

    product_names = products[
        [
            "product_id",
            "aoi_name"
        ]
    ].copy()


    builtup_df = product_names.merge(
        builtup,
        on="product_id",
        how="inner"
    )


    transportation_df = product_names.merge(
        transportation,
        on="product_id",
        how="inner"
    )


    landuse_df = product_names.merge(
        landuse,
        on="product_id",
        how="inner"
    )


    landslide_df = product_names.merge(
        landslide,
        on="product_id",
        how="inner"
    )


    # Keep the same columns used by the SQL version.

    builtup_df = builtup_df[
        [
            "aoi_name",
            "category",
            "total_value",
            "affected_value",
            "unit"
        ]
    ]


    transportation_df = transportation_df[
        [
            "aoi_name",
            "category",
            "total_value",
            "affected_value",
            "unit"
        ]
    ]


    landuse_df = landuse_df[
        [
            "aoi_name",
            "category",
            "total_value",
            "affected_value",
            "unit"
        ]
    ]


    landslide_df = landslide_df[
        [
            "aoi_name",
            "landslide_affected_area_ha"
        ]
    ]


    summary_df = summary_df.sort_values(
        by="population_affected_pct",
        ascending=False
    )


    landslide_df = landslide_df.sort_values(
        by="landslide_affected_area_ha",
        ascending=False
    )


    return (
        summary_df,
        builtup_df,
        transportation_df,
        landuse_df,
        landslide_df
    )


# ============================================================
# APP HEADER
# ============================================================

st.title(
    "🇳🇵 Nepal Flood Impact Analysis"
)

st.caption(
    "Analysis of mapped physical damage, infrastructure impact, "
    "land impact and population exposure across selected "
    "Copernicus Areas of Interest that includes Bidur, Nuwakot; SyapruBesi, Rasuwa; Timure, Rasuwa; Phosretar, Dhading."
)


# ============================================================
# LOAD SELECTED DATA SOURCE
# ============================================================

try:

    if data_source == "sql":

        (
            df,
            builtup_df,
            transportation_df,
            landuse_df,
            landslide_df
        ) = load_sql_data()

    elif data_source == "csv":

        (
            df,
            builtup_df,
            transportation_df,
            landuse_df,
            landslide_df
        ) = load_csv_data()

    else:

        st.error(
            "Invalid data source. "
            "Use 'sql' or 'csv'."
        )

        st.stop()


except Exception as error:

    st.error(
        f"Data loading failed: {error}"
    )

    st.stop()


# ============================================================
# CONVERT NUMERIC VALUES
# ============================================================

summary_numeric_columns = [
    "population_total",
    "population_affected",
    "population_affected_pct",
    "residential_buildings_total",
    "residential_buildings_affected",
    "residential_buildings_affected_pct",
    "landslide_affected_area_ha",
    "latitude",
    "longitude"
]


for column in summary_numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


for dataframe in [
    builtup_df,
    transportation_df,
    landuse_df
]:

    dataframe["total_value"] = pd.to_numeric(
        dataframe["total_value"],
        errors="coerce"
    )

    dataframe["affected_value"] = pd.to_numeric(
        dataframe["affected_value"],
        errors="coerce"
    )


landslide_df[
    "landslide_affected_area_ha"
] = pd.to_numeric(
    landslide_df[
        "landslide_affected_area_ha"
    ],
    errors="coerce"
)


# ============================================================
# PREPARE ROAD DATA
# ============================================================

road_df = transportation_df[
    (
        transportation_df["unit"] == "km"
    )
    &
    (
        transportation_df["category"]
        != "Bridges and elevated highways"
    )
].copy()


road_df["affected_pct"] = (
    road_df["affected_value"]
    / road_df["total_value"]
    * 100
)


bridge_df = transportation_df[
    transportation_df["category"]
    == "Bridges and elevated highways"
].copy()


# ============================================================
# PREPARE HOTSPOT MAP DATA
# ============================================================

hotspot_df = df[
    [
        "aoi_name",
        "latitude",
        "longitude",
        "residential_buildings_affected"
    ]
].copy()


hotspot_df = hotspot_df.dropna(
    subset=[
        "latitude",
        "longitude",
        "residential_buildings_affected"
    ]
)


hotspot_df["latitude"] = (
    hotspot_df["latitude"].astype(float)
)

hotspot_df["longitude"] = (
    hotspot_df["longitude"].astype(float)
)

hotspot_df[
    "residential_buildings_affected"
] = (
    hotspot_df[
        "residential_buildings_affected"
    ].astype(float)
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

affected_population = (
    df["population_affected"].sum()
)

affected_buildings = (
    df["residential_buildings_affected"].sum()
)

landslide_area = (
    df["landslide_affected_area_ha"].sum()
)

affected_road_km = (
    road_df["affected_value"].sum()
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Overview",
        "Built Environment",
        "Infrastructure",
        "Hazard & Land",
        "Population Exposure"
    ]
)


# ============================================================
# TAB 1: OVERVIEW
# ============================================================

with tab1:

    st.markdown(
        "## Disaster Impact Overview"
    )

    st.write(
        "This dashboard prioritizes mapped physical impact. "
        "Population exposure is included as supporting context "
        "rather than being treated as a complete count of all "
        "people affected by the disaster."
    )


    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            label="Affected Residential Buildings",
            value=f"{affected_buildings:,.0f}"
        )


    with col2:

        st.metric(
            label="Affected Road Length",
            value=f"{affected_road_km:,.1f} km"
        )


    with col3:

        st.metric(
            label="Landslide Affected Area",
            value=f"{landslide_area:,.1f} ha"
        )


    with col4:

        st.metric(
            label="Mapped Population Exposure",
            value=f"{affected_population:,.0f}"
        )


    st.caption(
        "Road length includes only transportation categories "
        "explicitly measured in kilometres. Bridges are excluded "
        "because Copernicus reports inconsistent bridge units."
    )


    # --------------------------------------------------------
    # PHYSICAL IMPACT HOTSPOT MAP
    # --------------------------------------------------------

    st.markdown(
        "### Physical Impact Hotspot Map"
    )

    st.write(
        "Circle size represents affected residential buildings. "
        "Larger circles indicate greater mapped physical impact "
        "on residential structures."
    )


    nepal_map = folium.Map(
        location=[28.3949, 84.1240],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True
    )


    for _, row in hotspot_df.iterrows():

        marker_buildings = row[
            "residential_buildings_affected"
        ]

        marker_radius = max(
            7,
            min(
                25,
                marker_buildings ** 0.5 / 2
            )
        )


        folium.CircleMarker(
            location=[
                row["latitude"],
                row["longitude"]
            ],
            radius=marker_radius,
            tooltip=(
                f'{row["aoi_name"]} | '
                f'Affected buildings: '
                f'{marker_buildings:,.0f}'
            ),
            popup=folium.Popup(
                html=(
                    f'<b>{row["aoi_name"]}</b><br>'
                    f'Affected residential buildings: '
                    f'{marker_buildings:,.0f}'
                ),
                max_width=300
            ),
            fill=True,
            fill_opacity=0.7,
            weight=2
        ).add_to(nepal_map)


    st_folium(
        nepal_map,
        width=None,
        height=500
    )


    st.caption(
        "Markers use the centre of each Copernicus AOI extent. "
        "They do not represent the exact location of individual "
        "damaged buildings."
    )


    # --------------------------------------------------------
    # HOTSPOT RANKING
    # --------------------------------------------------------

    st.markdown(
        "### Residential Building Impact Ranking"
    )


    hotspot_ranking = hotspot_df[
        [
            "aoi_name",
            "residential_buildings_affected"
        ]
    ].copy()


    hotspot_ranking = (
        hotspot_ranking
        .sort_values(
            by="residential_buildings_affected",
            ascending=False
        )
    )


    hotspot_ranking = hotspot_ranking.rename(
        columns={
            "aoi_name":
                "Area",
            "residential_buildings_affected":
                "Affected Residential Buildings"
        }
    )


    st.dataframe(
        hotspot_ranking,
        width="stretch",
        hide_index=True
    )


    # --------------------------------------------------------
    # AOI SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### Area of Interest Summary"
    )


    overview_table = df[
        [
            "aoi_name",
            "residential_buildings_affected",
            "landslide_affected_area_ha",
            "population_affected"
        ]
    ].copy()


    overview_table = overview_table.rename(
        columns={
            "aoi_name":
                "Area",
            "residential_buildings_affected":
                "Affected Residential Buildings",
            "landslide_affected_area_ha":
                "Landslide Area (ha)",
            "population_affected":
                "Mapped Population Exposure"
        }
    )


    overview_table = overview_table.sort_values(
        by="Affected Residential Buildings",
        ascending=False
    )


    st.dataframe(
        overview_table,
        width="stretch",
        hide_index=True
    )


# ============================================================
# TAB 2: BUILT ENVIRONMENT
# ============================================================

with tab2:

    st.markdown(
        "## Built Environment Impact"
    )


    st.markdown(
        "### Affected Residential Buildings"
    )


    residential_absolute = df[
        [
            "aoi_name",
            "residential_buildings_affected"
        ]
    ].copy()


    residential_absolute[
        "residential_buildings_affected"
    ] = (
        residential_absolute[
            "residential_buildings_affected"
        ].astype(float)
    )


    residential_absolute = (
        residential_absolute
        .dropna()
        .sort_values(
            by="residential_buildings_affected",
            ascending=False
        )
    )


    st.bar_chart(
        residential_absolute,
        x="aoi_name",
        y="residential_buildings_affected",
        x_label="Area of Interest",
        y_label="Affected Residential Buildings",
        width="stretch"
    )


    st.markdown(
        "### Residential Buildings Affected (%)"
    )


    residential_percentage = df[
        [
            "aoi_name",
            "residential_buildings_affected_pct"
        ]
    ].copy()


    residential_percentage[
        "residential_buildings_affected_pct"
    ] = (
        residential_percentage[
            "residential_buildings_affected_pct"
        ].astype(float)
    )


    residential_percentage = (
        residential_percentage
        .dropna()
        .sort_values(
            by="residential_buildings_affected_pct",
            ascending=False
        )
        .set_index("aoi_name")
    )


    st.bar_chart(
        residential_percentage,
        width="stretch"
    )


    st.markdown(
        "### Affected Built-Up Features by Type"
    )


    building_types = builtup_df[
        [
            "aoi_name",
            "category",
            "affected_value"
        ]
    ].copy()


    building_types = building_types.dropna(
        subset=["affected_value"]
    )


    building_types[
        "affected_value"
    ] = (
        building_types[
            "affected_value"
        ].astype(float)
    )


    building_types = (
        building_types
        .sort_values(
            by="affected_value",
            ascending=False
        )
    )


    st.bar_chart(
        building_types,
        x="aoi_name",
        y="affected_value",
        color="category",
        x_label="Area of Interest",
        y_label="Affected Value",
        width="stretch"
    )


    st.caption(
        "Copernicus does not provide an explicit unit for every "
        "built-up category. Values are shown as reported by the "
        "source rather than assuming that all categories use the "
        "same unit."
    )


    with st.expander(
        "View building category data"
    ):

        st.dataframe(
            builtup_df,
            width="stretch",
            hide_index=True
        )


# ============================================================
# TAB 3: INFRASTRUCTURE
# ============================================================

with tab3:

    st.markdown(
        "## Infrastructure Impact"
    )


    st.markdown(
        "### Affected Road Length by Road Type"
    )


    road_absolute = road_df[
        [
            "aoi_name",
            "category",
            "affected_value"
        ]
    ].copy()


    road_absolute[
        "affected_value"
    ] = (
        road_absolute[
            "affected_value"
        ].astype(float)
    )


    road_absolute = (
        road_absolute
        .dropna()
        .sort_values(
            by="affected_value",
            ascending=False
        )
    )


    st.bar_chart(
        road_absolute,
        x="aoi_name",
        y="affected_value",
        color="category",
        x_label="Area of Interest",
        y_label="Affected Road Length (km)",
        width="stretch"
    )


    st.markdown(
        "### Road Type Affected (%)"
    )


    road_percentage = road_df[
        [
            "aoi_name",
            "category",
            "affected_pct"
        ]
    ].copy()


    road_percentage[
        "affected_pct"
    ] = (
        road_percentage[
            "affected_pct"
        ].astype(float)
    )


    road_percentage = (
        road_percentage
        .dropna()
        .sort_values(
            by="affected_pct",
            ascending=False
        )
    )


    st.bar_chart(
        road_percentage,
        x="aoi_name",
        y="affected_pct",
        color="category",
        x_label="Area of Interest",
        y_label="Road Affected (%)",
        width="stretch"
    )


    st.markdown(
        "### Bridges & Elevated Highways"
    )


    st.warning(
        "Bridge statistics are kept separate because Copernicus "
        "does not use a consistent unit across the mapped areas. "
        "Some products have no stated unit, while Phosretar "
        "reports kilometres."
    )


    bridge_display = bridge_df[
        [
            "aoi_name",
            "total_value",
            "affected_value",
            "unit"
        ]
    ].copy()


    bridge_display = bridge_display.rename(
        columns={
            "aoi_name": "Area",
            "total_value": "Total Value",
            "affected_value": "Affected Value",
            "unit": "Source Unit"
        }
    )


    st.dataframe(
        bridge_display,
        width="stretch",
        hide_index=True
    )


    with st.expander(
        "View all transportation category data"
    ):

        st.dataframe(
            transportation_df,
            width="stretch",
            hide_index=True
        )


# ============================================================
# TAB 4: HAZARD & LAND
# ============================================================

with tab4:

    st.markdown(
        "## Hazard & Land Impact"
    )


    st.markdown(
        "### Landslide Affected Area"
    )


    landslide_chart = landslide_df[
        [
            "aoi_name",
            "landslide_affected_area_ha"
        ]
    ].copy()


    landslide_chart[
        "landslide_affected_area_ha"
    ] = (
        landslide_chart[
            "landslide_affected_area_ha"
        ].astype(float)
    )


    landslide_chart = (
        landslide_chart
        .dropna()
        .sort_values(
            by="landslide_affected_area_ha",
            ascending=False
        )
    )


    st.bar_chart(
        landslide_chart,
        x="aoi_name",
        y="landslide_affected_area_ha",
        x_label="Area of Interest",
        y_label="Landslide Affected Area (ha)",
        width="stretch"
    )


    st.markdown(
        "### Affected Land by Land-Use Category"
    )


    landuse_chart = landuse_df[
        [
            "aoi_name",
            "category",
            "affected_value"
        ]
    ].copy()


    landuse_chart = landuse_chart.dropna(
        subset=["affected_value"]
    )


    landuse_chart[
        "affected_value"
    ] = (
        landuse_chart[
            "affected_value"
        ].astype(float)
    )


    landuse_chart = (
        landuse_chart
        .sort_values(
            by="affected_value",
            ascending=False
        )
    )


    st.bar_chart(
        landuse_chart,
        x="aoi_name",
        y="affected_value",
        color="category",
        x_label="Area of Interest",
        y_label="Affected Value",
        width="stretch"
    )


    st.caption(
        "Land-use categories are shown using the units supplied "
        "by Copernicus. Use the detailed table below when "
        "interpreting categories with different units."
    )


    with st.expander(
        "View land-use category data"
    ):

        st.dataframe(
            landuse_df,
            width="stretch",
            hide_index=True
        )


# ============================================================
# TAB 5: POPULATION EXPOSURE
# ============================================================

with tab5:

    st.markdown(
        "## Mapped Population Exposure"
    )


    st.info(
        "Population statistics represent population exposure "
        "within the Copernicus mapped areas. They should not be "
        "interpreted as a complete count of every person affected "
        "by the disaster. Travellers, visitors, workers and other "
        "temporary populations may not be represented."
    )


    st.markdown(
        "### Population Exposed in Copernicus Mapping"
    )


    population_absolute = df[
        [
            "aoi_name",
            "population_affected"
        ]
    ].copy()


    population_absolute[
        "population_affected"
    ] = (
        population_absolute[
            "population_affected"
        ].astype(float)
    )


    population_absolute = (
        population_absolute
        .dropna()
        .sort_values(
            by="population_affected",
            ascending=False
        )
    )


    st.bar_chart(
        population_absolute,
        x="aoi_name",
        y="population_affected",
        x_label="Area of Interest",
        y_label="Mapped Population Exposure",
        width="stretch"
    )


    st.markdown(
        "### Mapped Population Exposure (%)"
    )


    population_percentage = df[
        [
            "aoi_name",
            "population_affected_pct"
        ]
    ].copy()


    population_percentage[
        "population_affected_pct"
    ] = (
        population_percentage[
            "population_affected_pct"
        ].astype(float)
    )


    population_percentage = (
        population_percentage
        .dropna()
        .sort_values(
            by="population_affected_pct",
            ascending=False
        )
        .set_index("aoi_name")
    )


    st.bar_chart(
        population_percentage,
        width="stretch"
    )


    st.caption(
        "Absolute exposure and exposure percentage answer "
        "different questions. An area can have a large exposed "
        "population while representing a smaller share of its "
        "mapped population, or vice versa."
    )

    # ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align: center;">
        Developed by <strong>Subin Dahal</strong> ·
        <a href="https://www.linkedin.com/in/subindahal/" target="_blank">LinkedIn</a> ·
        <a href="https://github.com/subindahal/nepal-flood-intelligence"
           target="_blank">GitHub</a><br>
        Data source:
        <a href="https://mapping.emergency.copernicus.eu/"
           target="_blank">Copernicus Emergency Management Service</a>
    </div>
    """,
    unsafe_allow_html=True
)