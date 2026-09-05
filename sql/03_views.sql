USE nepal_flood;
GO


-- ============================================================
-- COPERNICUS EMSR927 DASHBOARD VIEWS
--
-- Views are saved SQL queries.
-- They do not duplicate the underlying data.
-- ============================================================


-- ============================================================
-- VIEW 1: POPULATION IMPACT
-- ============================================================

CREATE OR ALTER VIEW vw_copernicus_population_impact
AS

SELECT
    p.aoi_name,

    pop.total_value AS population_total,

    pop.affected_value AS population_affected,

    ROUND(
        (pop.affected_value / NULLIF(pop.total_value, 0)) * 100,
        2
    ) AS population_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_population AS pop
    ON p.copernicus_product_key =
       pop.copernicus_product_key;

GO


-- ============================================================
-- VIEW 2: RESIDENTIAL BUILDING IMPACT
-- ============================================================

CREATE OR ALTER VIEW vw_copernicus_building_impact
AS

SELECT
    p.aoi_name,

    b.total_value AS residential_buildings_total,

    b.affected_value AS residential_buildings_affected,

    ROUND(
        (b.affected_value / NULLIF(b.total_value, 0)) * 100,
        2
    ) AS residential_buildings_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_builtup AS b
    ON p.copernicus_product_key =
       b.copernicus_product_key

WHERE b.category = 'Residential Buildings';

GO


-- ============================================================
-- VIEW 3: ROAD IMPACT
--
-- Only rows explicitly measured in km are included.
-- Bridges are excluded because their units are inconsistent.
-- ============================================================

CREATE OR ALTER VIEW vw_copernicus_road_impact
AS

SELECT
    p.aoi_name,

    t.category,

    t.total_value AS road_total_km,

    t.affected_value AS road_affected_km,

    ROUND(
        (t.affected_value / NULLIF(t.total_value, 0)) * 100,
        2
    ) AS road_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_transportation AS t
    ON p.copernicus_product_key =
       t.copernicus_product_key

WHERE t.unit = 'km'
  AND t.category <> 'Bridges and elevated highways';

GO


-- ============================================================
-- VIEW 4: LANDSLIDE IMPACT
--
-- Copernicus provides NA for total landslide area,
-- so we use affected area only.
-- ============================================================

CREATE OR ALTER VIEW vw_copernicus_landslide_impact
AS

SELECT
    p.aoi_name,

    o.affected_value AS landslide_affected_area_ha

FROM copernicus_products AS p

INNER JOIN copernicus_other_stats AS o
    ON p.copernicus_product_key =
       o.copernicus_product_key

WHERE o.group_name = 'Landslide';

GO


-- ============================================================
-- VIEW 5: MAIN AOI SUMMARY
--
-- This is the main dataset we will use in Streamlit.
-- ============================================================

CREATE OR ALTER VIEW vw_copernicus_aoi_summary
AS

SELECT
    p.aoi_name,

    pop.total_value AS population_total,

    pop.affected_value AS population_affected,

    ROUND(
        (pop.affected_value / NULLIF(pop.total_value, 0)) * 100,
        2
    ) AS population_affected_pct,


    b.total_value AS residential_buildings_total,

    b.affected_value AS residential_buildings_affected,

    ROUND(
        (b.affected_value / NULLIF(b.total_value, 0)) * 100,
        2
    ) AS residential_buildings_affected_pct,


    landslide.affected_value AS landslide_affected_area_ha

FROM copernicus_products AS p


LEFT JOIN copernicus_population AS pop
    ON p.copernicus_product_key =
       pop.copernicus_product_key


LEFT JOIN copernicus_builtup AS b
    ON p.copernicus_product_key =
       b.copernicus_product_key
    AND b.category = 'Residential Buildings'


LEFT JOIN copernicus_other_stats AS landslide
    ON p.copernicus_product_key =
       landslide.copernicus_product_key
    AND landslide.group_name = 'Landslide';

GO


-- ============================================================
-- TEST THE MAIN VIEW
-- ============================================================

SELECT *
FROM vw_copernicus_aoi_summary
ORDER BY population_affected_pct DESC;

GO