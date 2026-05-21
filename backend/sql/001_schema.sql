-- Drone Delivery Router – Database Schema
-- Requires PostgreSQL 14+ with PostGIS extension

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- HUBS (base stations / charging stations)
-- ============================================================
CREATE TABLE IF NOT EXISTS hubs (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    is_charging_station BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- DRONES
-- ============================================================
CREATE TYPE drone_status AS ENUM ('idle', 'charging', 'en_route');

CREATE TABLE IF NOT EXISTS drones (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(100)   NOT NULL,
    status               drone_status   NOT NULL DEFAULT 'idle',
    max_payload_kg       DOUBLE PRECISION NOT NULL,
    battery_capacity_mah INTEGER        NOT NULL,
    battery_pct          DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    latitude             DOUBLE PRECISION NOT NULL,
    longitude            DOUBLE PRECISION NOT NULL,
    home_hub_id          INTEGER REFERENCES hubs(id)
);

-- ============================================================
-- ORDERS
-- ============================================================
CREATE TYPE order_status   AS ENUM ('pending','assigned','in_transit','delivered','cancelled');
CREATE TYPE priority_level AS ENUM ('low','medium','high','critical');

CREATE TABLE IF NOT EXISTS orders (
    id                SERIAL PRIMARY KEY,
    pickup_lat        DOUBLE PRECISION NOT NULL,
    pickup_lon        DOUBLE PRECISION NOT NULL,
    dropoff_lat       DOUBLE PRECISION NOT NULL,
    dropoff_lon       DOUBLE PRECISION NOT NULL,
    package_weight_kg DOUBLE PRECISION NOT NULL,
    priority          priority_level   NOT NULL DEFAULT 'medium',
    status            order_status     NOT NULL DEFAULT 'pending',
    assigned_drone_id INTEGER REFERENCES drones(id)
);

-- ============================================================
-- NO-FLY ZONES (stored as GeoJSON text for portability;
--               a PostGIS geometry column is added for spatial queries)
-- ============================================================
CREATE TABLE IF NOT EXISTS no_fly_zones (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    polygon_geojson TEXT         NOT NULL,
    geom            GEOMETRY(Polygon, 4326)
);

-- Trigger: auto-populate geom from polygon_geojson on insert/update
CREATE OR REPLACE FUNCTION nfz_sync_geom() RETURNS TRIGGER AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_GeomFromGeoJSON(NEW.polygon_geojson), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_nfz_sync ON no_fly_zones;
CREATE TRIGGER trg_nfz_sync
    BEFORE INSERT OR UPDATE ON no_fly_zones
    FOR EACH ROW EXECUTE FUNCTION nfz_sync_geom();

CREATE INDEX IF NOT EXISTS idx_nfz_geom ON no_fly_zones USING GIST (geom);
