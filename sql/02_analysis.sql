USE nepal_flood;
GO


-- ============================================================
-- COPERNICUS EMSR927 ANALYSIS
--
-- This file explores:
-- 1. Population impact
-- 2. Residential building impact
-- 3. Transportation impact
-- 4. Land-use impact
-- 5. Landslide impact
-- 6. Combined AOI comparison
-- ============================================================



-- ============================================================
-- 1. POPULATION IMPACT BY AREA OF INTEREST
-- ============================================================

SELECT
    p.aoi_name,

    pop.total_value AS population_total,

    pop.affected_value AS population_affected,

    ROUND(
        (pop.affected_value / NULLIF(pop.total_value, 0)) * 100,
        2
    ) AS affected_population_pct

FROM copernicus_products AS p

INNER JOIN copernicus_population AS pop
    ON p.copernicus_product_key =
       pop.copernicus_product_key

ORDER BY affected_population_pct DESC;
GO



-- ============================================================
-- 2. RESIDENTIAL BUILDING IMPACT
-- ============================================================

SELECT
    p.aoi_name,

    b.total_value AS residential_buildings_total,

    b.affected_value AS residential_buildings_affected,

    ROUND(
        (b.affected_value / NULLIF(b.total_value, 0)) * 100,
        2
    ) AS affected_buildings_pct

FROM copernicus_products AS p

INNER JOIN copernicus_builtup AS b
    ON p.copernicus_product_key =
       b.copernicus_product_key

WHERE b.category = 'Residential Buildings'

ORDER BY affected_buildings_pct DESC;
GO



-- ============================================================
-- 3. ALL BUILT-UP CATEGORIES
--
-- Lets us inspect everything Copernicus recorded
-- under the Built-up group.
-- ============================================================

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
GO



-- ============================================================
-- 4. BUILDING IMPACT PERCENTAGE BY CATEGORY
--
-- This works for any built-up category where total_value
-- is available.
-- ============================================================

SELECT
    p.aoi_name,
    b.category,

    b.total_value,
    b.affected_value,

    ROUND(
        (b.affected_value / NULLIF(b.total_value, 0)) * 100,
        2
    ) AS affected_pct,

    b.unit

FROM copernicus_products AS p

INNER JOIN copernicus_builtup AS b
    ON p.copernicus_product_key =
       b.copernicus_product_key

WHERE b.total_value IS NOT NULL
  AND b.total_value > 0

ORDER BY
    affected_pct DESC,
    p.aoi_name;
GO



-- ============================================================
-- 5. ALL TRANSPORTATION STATISTICS
--
-- IMPORTANT:
-- We keep unit visible because Copernicus transportation
-- categories are not always measured the same way.
-- ============================================================

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
GO



-- ============================================================
-- 6. PRIMARY ROAD IMPACT
-- ============================================================

SELECT
    p.aoi_name,

    t.total_value AS primary_road_total,

    t.affected_value AS primary_road_affected,

    t.unit,

    ROUND(
        (t.affected_value / NULLIF(t.total_value, 0)) * 100,
        2
    ) AS primary_road_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_transportation AS t
    ON p.copernicus_product_key =
       t.copernicus_product_key

WHERE t.category = 'Primary Road'

ORDER BY primary_road_affected_pct DESC;
GO



-- ============================================================
-- 7. LOCAL ROAD IMPACT
-- ============================================================

SELECT
    p.aoi_name,

    t.total_value AS local_road_total,

    t.affected_value AS local_road_affected,

    t.unit,

    ROUND(
        (t.affected_value / NULLIF(t.total_value, 0)) * 100,
        2
    ) AS local_road_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_transportation AS t
    ON p.copernicus_product_key =
       t.copernicus_product_key

WHERE t.category = 'Local Road'

ORDER BY local_road_affected_pct DESC;
GO



-- ============================================================
-- 8. CART TRACK IMPACT
-- ============================================================

SELECT
    p.aoi_name,

    t.total_value AS cart_track_total,

    t.affected_value AS cart_track_affected,

    t.unit,

    ROUND(
        (t.affected_value / NULLIF(t.total_value, 0)) * 100,
        2
    ) AS cart_track_affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_transportation AS t
    ON p.copernicus_product_key =
       t.copernicus_product_key

WHERE t.category = 'Cart Track'

ORDER BY cart_track_affected_pct DESC;
GO



-- ============================================================
-- 9. BRIDGE STATISTICS
--
-- DO NOT compare values across rows without checking unit.
--
-- Some Copernicus products use counts.
-- Others may use kilometers.
-- ============================================================

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

WHERE t.category = 'Bridges and elevated highways'

ORDER BY p.aoi_name;
GO



-- ============================================================
-- 10. TRANSPORTATION IMPACT PERCENTAGE
--
-- Only compares rows within their own category.
-- Unit remains visible.
-- ============================================================

SELECT
    p.aoi_name,
    t.category,
    t.total_value,
    t.affected_value,
    t.unit,

    ROUND(
        (t.affected_value / NULLIF(t.total_value, 0)) * 100,
        2
    ) AS affected_pct

FROM copernicus_products AS p

INNER JOIN copernicus_transportation AS t
    ON p.copernicus_product_key =
       t.copernicus_product_key

WHERE t.unit = 'km'

ORDER BY
    t.category,
    affected_pct DESC;


-- ============================================================
-- 11. ALL LAND-USE STATISTICS
-- ============================================================

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
GO



-- ============================================================
-- 12. LAND-USE IMPACT PERCENTAGE
-- ============================================================

SELECT
    p.aoi_name,
    l.category,

    l.total_value,
    l.affected_value,

    ROUND(
        (l.affected_value / NULLIF(l.total_value, 0)) * 100,
        2
    ) AS affected_pct,

    l.unit

FROM copernicus_products AS p

INNER JOIN copernicus_landuse AS l
    ON p.copernicus_product_key =
       l.copernicus_product_key

WHERE l.total_value IS NOT NULL
  AND l.total_value > 0

ORDER BY
    affected_pct DESC,
    p.aoi_name;
GO



-- ============================================================
-- 13. OTHER COPERNICUS STATISTICS
--
-- Includes groups such as:
-- Landslide
-- Dams
-- Power plant
-- ============================================================

SELECT
    p.aoi_name,
    o.group_name,
    o.category,
    o.total_value,
    o.affected_value,
    o.unit

FROM copernicus_products AS p

INNER JOIN copernicus_other_stats AS o
    ON p.copernicus_product_key =
       o.copernicus_product_key

ORDER BY
    p.aoi_name,
    o.group_name,
    o.category;
GO



-- ============================================================
-- 14. LANDSLIDE AFFECTED AREA
--
-- Copernicus provides NA for total landslide area in these
-- products, so we focus on affected_value.
-- ============================================================

SELECT
    p.aoi_name,

    o.affected_value AS landslide_affected_area,

    o.unit

FROM copernicus_products AS p

INNER JOIN copernicus_other_stats AS o
    ON p.copernicus_product_key =
       o.copernicus_product_key

WHERE o.group_name = 'Landslide'

ORDER BY landslide_affected_area DESC;
GO



-- ============================================================
-- 15. AOI SUMMARY
--
-- Combines three important impact indicators:
--
-- population
-- residential buildings
-- landslide area
--
-- LEFT JOIN is used so an AOI can still appear even if
-- one category is missing.
-- ============================================================

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

    AND landslide.group_name = 'Landslide'


ORDER BY population_affected_pct DESC;
GO



-- ============================================================
-- 16. ABSOLUTE POPULATION IMPACT RANKING
--
-- Important distinction:
--
-- Percentage tells us intensity.
-- Absolute affected population tells us scale.
-- ============================================================

SELECT
    p.aoi_name,
    pop.affected_value AS population_affected

FROM copernicus_products AS p

INNER JOIN copernicus_population AS pop
    ON p.copernicus_product_key =
       pop.copernicus_product_key

ORDER BY population_affected DESC;
GO



-- ============================================================
-- 17. POPULATION IMPACT:
-- ABSOLUTE VS PERCENTAGE
--
-- This is especially useful for the portfolio.
--
-- Example:
-- An AOI can have a lower percentage but still have
-- many more affected people.
-- ============================================================

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
       pop.copernicus_product_key

ORDER BY population_affected DESC;
GO



-- ============================================================
-- 18. RESIDENTIAL BUILDINGS:
-- ABSOLUTE VS PERCENTAGE
-- ============================================================

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

WHERE b.category = 'Residential Buildings'

ORDER BY residential_buildings_affected DESC;
GO



-- ============================================================
-- 19. DATA QUALITY CHECK:
-- FIND NULL VALUES
--
-- Useful for understanding incomplete source data.
-- ============================================================

SELECT
    p.aoi_name,
    o.group_name,
    o.category,
    o.total_value,
    o.affected_value,
    o.unit

FROM copernicus_products AS p

INNER JOIN copernicus_other_stats AS o
    ON p.copernicus_product_key =
       o.copernicus_product_key

WHERE o.total_value IS NULL
   OR o.affected_value IS NULL

ORDER BY
    p.aoi_name,
    o.group_name;
GO



-- ============================================================
-- 20. DATA QUALITY CHECK:
-- FIND ALL UNITS USED IN TRANSPORTATION
--
-- Helps prevent invalid comparisons.
-- ============================================================

SELECT DISTINCT
    category,
    unit

FROM copernicus_transportation

ORDER BY category, unit;
GO



-- ============================================================
-- 21. DATA QUALITY CHECK:
-- FIND CATEGORIES THAT USE MORE THAN ONE UNIT
--
-- This is particularly useful for catching cases like bridges.
-- ============================================================

SELECT
    category,

    COUNT(DISTINCT COALESCE(unit, 'NULL')) AS number_of_units

FROM copernicus_transportation

GROUP BY category

HAVING COUNT(
    DISTINCT COALESCE(unit, 'NULL')
) > 1;
GO



-- ============================================================
-- 22. VERIFY PRODUCT SELECTION
--
-- Shows which Copernicus product/version we selected
-- for every usable AOI.
-- ============================================================

SELECT
    aoi_name,
    product_id,
    monitoring,
    monitoring_number,
    version_number

FROM copernicus_products

ORDER BY aoi_name;
GO