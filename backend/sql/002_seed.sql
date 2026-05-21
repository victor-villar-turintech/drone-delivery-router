-- Seed data: San Francisco area
-- ============================================================
-- HUBS
-- ============================================================
INSERT INTO hubs (name, latitude, longitude, is_charging_station) VALUES
('SF Downtown Hub',      37.7749, -122.4194, TRUE),
('Mission District Hub', 37.7599, -122.4148, TRUE),
('SoMa Charging Pad',   37.7785, -122.3950, TRUE),
('Marina Hub',           37.8020, -122.4370, TRUE),
('Sunset Hub',           37.7535, -122.4950, TRUE);

-- ============================================================
-- DRONES
-- ============================================================
INSERT INTO drones (name, status, max_payload_kg, battery_capacity_mah, battery_pct, latitude, longitude, home_hub_id) VALUES
('Falcon-1',   'idle', 5.0,  8000, 100.0, 37.7749, -122.4194, 1),
('Falcon-2',   'idle', 3.0,  6000,  95.0, 37.7749, -122.4194, 1),
('Hawk-1',     'idle', 8.0, 12000, 100.0, 37.7599, -122.4148, 2),
('Sparrow-1',  'idle', 2.0,  5000,  88.0, 37.7785, -122.3950, 3),
('Sparrow-2',  'idle', 2.5,  5000, 100.0, 37.8020, -122.4370, 4),
('Eagle-1',    'idle',10.0, 15000, 100.0, 37.7535, -122.4950, 5),
('Kite-1',     'idle', 4.0,  7000,  92.0, 37.7749, -122.4194, 1),
('Kite-2',     'idle', 4.0,  7000, 100.0, 37.7599, -122.4148, 2);

-- ============================================================
-- ORDERS (sample pending deliveries)
-- ============================================================
INSERT INTO orders (pickup_lat, pickup_lon, dropoff_lat, dropoff_lon, package_weight_kg, priority, status) VALUES
(37.7749, -122.4194, 37.7849, -122.4094, 1.2, 'high',     'pending'),
(37.7599, -122.4148, 37.7700, -122.4000, 2.5, 'medium',   'pending'),
(37.7785, -122.3950, 37.7650, -122.4100, 0.8, 'critical', 'pending'),
(37.8020, -122.4370, 37.7900, -122.4200, 3.0, 'low',      'pending'),
(37.7535, -122.4950, 37.7600, -122.4800, 4.5, 'medium',   'pending');

-- ============================================================
-- NO-FLY ZONES (polygons around sensitive SF areas)
-- ============================================================
INSERT INTO no_fly_zones (name, polygon_geojson) VALUES
(
    'SFO Airport Vicinity',
    '{"type":"Polygon","coordinates":[[[-122.393,37.615],[-122.393,37.625],[-122.370,37.625],[-122.370,37.615],[-122.393,37.615]]]}'
),
(
    'Alcatraz Island Buffer',
    '{"type":"Polygon","coordinates":[[[-122.427,37.824],[-122.427,37.830],[-122.418,37.830],[-122.418,37.824],[-122.427,37.824]]]}'
),
(
    'Golden Gate Park Event Zone',
    '{"type":"Polygon","coordinates":[[[-122.460,37.768],[-122.460,37.772],[-122.450,37.772],[-122.450,37.768],[-122.460,37.768]]]}'
),
(
    'Presidio Restricted Airspace',
    '{"type":"Polygon","coordinates":[[[-122.470,37.798],[-122.470,37.805],[-122.455,37.805],[-122.455,37.798],[-122.470,37.798]]]}'
);
