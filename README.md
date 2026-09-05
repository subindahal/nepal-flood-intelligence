# 🇳🇵 Nepal Flood Impact Analysis

An initial disaster impact analysis examining mapped physical damage, infrastructure impact, land impact, and population exposure across selected areas in Nepal following the August 2026 flood disaster.

The project uses data from the Copernicus Emergency Management Service (EMSR927) and demonstrates API data extraction, Python data processing, normalized SQL Server storage, SQL analysis, automated data refresh, and an interactive Streamlit dashboard.

## Live Project

- **Live Dashboard:** https://nepalflood.streamlit.app
- **Source Code:** https://github.com/subindahal/nepal-flood-intelligence

## Project Question

**Where was the greatest physical impact, and how did that impact differ across settlements, infrastructure, land, and population exposure?**

## Key Findings

Across the four Copernicus Areas of Interest with completed impact statistics, the analysis identified substantial differences in the scale and intensity of mapped physical impact.

- **3,659 residential buildings** were mapped as affected.
- **80.8 km of roads** were mapped as affected across road categories explicitly reported in kilometres. Bridge statistics are excluded because source units are inconsistent.
- **1,421.2 hectares (ha)** of landslide-affected area were mapped.
- **7,300 people** were represented as exposed within the analyzed Copernicus mapping areas. This represents mapped population exposure rather than a complete count of everyone affected by the disaster.

### Area-Level Insights

- **Bidur** recorded the largest absolute residential building impact, with **3,001 affected residential buildings**, and the largest mapped population exposure at **5,000 people**.
- **Timure** experienced the highest proportional residential building impact, with approximately **97%** of mapped residential buildings affected. Its mapped population exposure was also **90%** of the mapped population.
- **Syapru Besi** recorded **392 affected residential buildings**, representing approximately **75.8%** of mapped residential buildings.
- **Phosretar** recorded a lower proportional residential impact of approximately **14.3%**, while still showing substantial mapped impact across land and transportation categories.
- **Bidur** had the largest mapped landslide-affected area at **701.5 ha**, followed by **Phosretar (479.2 ha)**, **Timure (129.4 ha)**, and **Syapru Besi (111.1 ha)**.

### Interpretation

The results demonstrate the importance of considering both **absolute impact** and **proportional impact**. Bidur stands out because of the overall scale of mapped damage, while smaller areas such as Timure experienced much greater impact relative to the mapped population and residential infrastructure present.

## Project Architecture

### Local Analytical Pipeline

The local development workflow uses SQL Server as the normalized analytical database.

```text
Copernicus EMSR927 API
        ↓
Python API Extraction
        ↓
Normalized CSV Files
        ↓
Python SQL Loader
        ↓
SQL Server
        ↓
Normalized Tables
        ↓
SQL Analysis & Views
        ↓
Streamlit Dashboard
```

### Public Deployment Pipeline

The public dashboard uses an automated GitHub-based data refresh so it can run on Streamlit Community Cloud without requiring access to the local SQL Server instance.

```text
Copernicus EMSR927 API
        ↓
GitHub Actions
        ↓
Automated Python Data Refresh
        ↓
Updated CSV Files
        ↓
Streamlit Community Cloud
        ↓
Public Dashboard
```

## Data Model & SQL

The Copernicus API returns multiple categories of impact statistics. Rather than storing everything in one flat table, the data is organized into a normalized SQL Server model.

### Normalized Tables

| Table | Purpose |
|---|---|
| `copernicus_products` | Selected Copernicus product for each Area of Interest, including map coordinates |
| `copernicus_population` | Mapped population totals and exposure |
| `copernicus_builtup` | Built-up feature statistics by category |
| `copernicus_transportation` | Road, bridge, and transportation impact statistics |
| `copernicus_landuse` | Land-use impact statistics |
| `copernicus_other_stats` | Additional hazard statistics such as landslide-affected area |

Each impact table is linked to `copernicus_products`, allowing different impact dimensions to be analyzed by Area of Interest without duplicating product information.

### SQL Analysis

SQL is used to:

- join normalized Copernicus datasets
- calculate affected percentages
- compare absolute and proportional impact
- rank Areas of Interest by impact
- check null values and source units
- identify transportation categories with inconsistent units
- create reusable analytical views for the dashboard

### Analytical Views

The project includes reusable SQL views:

- `vw_copernicus_population_impact`
- `vw_copernicus_building_impact`
- `vw_copernicus_road_impact`
- `vw_copernicus_landslide_impact`
- `vw_copernicus_aoi_summary`

The SQL scripts are organized in execution order:

1. `01_normalized_schema.sql` — creates the normalized database structure
2. `02_analysis.sql` — contains exploratory and validation queries
3. `03_views.sql` — creates reusable analytical views