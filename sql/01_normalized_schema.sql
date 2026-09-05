USE nepal_flood;
GO

-- ============================================================
-- COPERNICUS EMSR927
-- NORMALIZED DATABASE SCHEMA
--
-- DEVELOPMENT MODE:
-- Every time this file runs, the existing Copernicus tables
-- are deleted and recreated from scratch.
--
-- IMPORTANT:
-- Child tables must be dropped BEFORE the parent table because
-- they have foreign-key relationships.
-- ============================================================


-- ============================================================
-- STEP 1: DROP OLD TABLES
-- ============================================================

DROP TABLE IF EXISTS copernicus_population;
DROP TABLE IF EXISTS copernicus_builtup;
DROP TABLE IF EXISTS copernicus_transportation;
DROP TABLE IF EXISTS copernicus_landuse;
DROP TABLE IF EXISTS copernicus_other_stats;

-- Parent table must be dropped after child tables
DROP TABLE IF EXISTS copernicus_products;

-- Old flat table from our previous design
DROP TABLE IF EXISTS copernicus_stats;

GO


-- ============================================================
-- STEP 2: CREATE PRODUCT TABLE
--
-- One row = one selected Copernicus product for one AOI
-- ============================================================

CREATE TABLE copernicus_products (
    copernicus_product_key INT IDENTITY(1,1) PRIMARY KEY,
    aoi_name VARCHAR(100) NOT NULL,
    product_id INT NOT NULL,
    monitoring BIT,
    monitoring_number INT,
    version_number INT,
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    CONSTRAINT UQ_copernicus_product UNIQUE (product_id)
);
GO


-- ============================================================
-- STEP 3: CREATE POPULATION TABLE
-- ============================================================

CREATE TABLE copernicus_population (

    population_id INT IDENTITY(1,1) PRIMARY KEY,

    copernicus_product_key INT NOT NULL,

    total_value DECIMAL(18,2),

    affected_value DECIMAL(18,2),

    unit VARCHAR(50),

    CONSTRAINT FK_population_product
        FOREIGN KEY (copernicus_product_key)
        REFERENCES copernicus_products(copernicus_product_key)
);

GO


-- ============================================================
-- STEP 4: CREATE BUILT-UP TABLE
--
-- Examples:
-- Residential Buildings
-- Institutional
-- School / Research
-- Other non-residential buildings
-- ============================================================

CREATE TABLE copernicus_builtup (

    builtup_id INT IDENTITY(1,1) PRIMARY KEY,

    copernicus_product_key INT NOT NULL,

    category VARCHAR(150) NOT NULL,

    total_value DECIMAL(18,2),

    affected_value DECIMAL(18,2),

    unit VARCHAR(50),

    CONSTRAINT FK_builtup_product
        FOREIGN KEY (copernicus_product_key)
        REFERENCES copernicus_products(copernicus_product_key)
);

GO


-- ============================================================
-- STEP 5: CREATE TRANSPORTATION TABLE
--
-- Examples:
-- Primary Road
-- Local Road
-- Cart Track
-- Highways
-- Bridges and elevated highways
--
-- Unit is stored because different categories/AOIs can use
-- different measurement units.
-- ============================================================

CREATE TABLE copernicus_transportation (

    transportation_id INT IDENTITY(1,1) PRIMARY KEY,

    copernicus_product_key INT NOT NULL,

    category VARCHAR(150) NOT NULL,

    total_value DECIMAL(18,2),

    affected_value DECIMAL(18,2),

    unit VARCHAR(50),

    CONSTRAINT FK_transportation_product
        FOREIGN KEY (copernicus_product_key)
        REFERENCES copernicus_products(copernicus_product_key)
);

GO


-- ============================================================
-- STEP 6: CREATE LAND-USE TABLE
--
-- Examples:
-- Forests
-- Wetlands
-- Agricultural areas
-- Shrub / herbaceous vegetation
-- ============================================================

CREATE TABLE copernicus_landuse (

    landuse_id INT IDENTITY(1,1) PRIMARY KEY,

    copernicus_product_key INT NOT NULL,

    category VARCHAR(150) NOT NULL,

    total_value DECIMAL(18,2),

    affected_value DECIMAL(18,2),

    unit VARCHAR(50),

    CONSTRAINT FK_landuse_product
        FOREIGN KEY (copernicus_product_key)
        REFERENCES copernicus_products(copernicus_product_key)
);

GO


-- ============================================================
-- STEP 7: CREATE OTHER STATISTICS TABLE
--
-- Used for statistics that do not belong in the main groups.
--
-- Examples:
-- Landslide
-- Power plant
-- Dams
-- ============================================================

CREATE TABLE copernicus_other_stats (

    other_stat_id INT IDENTITY(1,1) PRIMARY KEY,

    copernicus_product_key INT NOT NULL,

    group_name VARCHAR(100) NOT NULL,

    category VARCHAR(150),

    total_value DECIMAL(18,2),

    affected_value DECIMAL(18,2),

    unit VARCHAR(50),

    CONSTRAINT FK_other_stats_product
        FOREIGN KEY (copernicus_product_key)
        REFERENCES copernicus_products(copernicus_product_key)
);

GO


-- ============================================================
-- STEP 8: VERIFY TABLES
-- ============================================================

SELECT
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE 'copernicus%'
ORDER BY TABLE_NAME;

GO