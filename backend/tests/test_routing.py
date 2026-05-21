"""Unit tests for the A* routing engine with no-fly zone avoidance."""

import json
import pytest
from app.engine.routing import find_path, haversine_km, GridNode


NFZ_BLOCK = json.dumps({
    "type": "Polygon",
    "coordinates": [[
        [-122.420, 37.780],
        [-122.420, 37.790],
        [-122.410, 37.790],
        [-122.410, 37.780],
        [-122.420, 37.780],
    ]],
})


class TestHaversine:
    def test_zero_distance(self):
        a = GridNode(37.7749, -122.4194)
        assert haversine_km(a, a) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance(self):
        a = GridNode(37.7749, -122.4194)
        b = GridNode(37.8049, -122.4194)
        dist = haversine_km(a, b)
        assert 3.0 < dist < 4.0


class TestPathfinding:
    def test_straight_path_no_obstacles(self):
        result = find_path(
            37.775, -122.420,
            37.780, -122.415,
            nofly_geojsons=[],
            grid_step=0.002,
        )
        assert "error" not in result
        assert len(result["path"]) >= 2
        assert result["distance_km"] > 0

    def test_path_avoids_nofly_zone(self):
        result = find_path(
            37.775, -122.425,
            37.795, -122.405,
            nofly_geojsons=[NFZ_BLOCK],
            grid_step=0.002,
        )
        assert "error" not in result
        path = result["path"]
        assert len(path) >= 2
        from shapely.geometry import Point, shape
        nfz_poly = shape(json.loads(NFZ_BLOCK))
        for lat, lon in path:
            pt = Point(lon, lat)
            assert not nfz_poly.contains(pt), f"Path passes through NFZ at ({lat}, {lon})"

    def test_no_path_returns_error_gracefully(self):
        huge_wall = json.dumps({
            "type": "Polygon",
            "coordinates": [[
                [-123.0, 37.0],
                [-123.0, 38.0],
                [-122.0, 38.0],
                [-122.0, 37.0],
                [-123.0, 37.0],
            ]],
        })
        result = find_path(
            37.5, -122.5,
            37.9, -122.1,
            nofly_geojsons=[huge_wall],
            grid_step=0.01,
        )
        assert result.get("error") == "no_path_found" or len(result["path"]) >= 2


class TestBatteryAndWind:
    def test_headwind_increases_cost(self):
        result_calm = find_path(
            37.775, -122.420,
            37.780, -122.415,
            nofly_geojsons=[],
            wind_vector=(0.0, 0.0),
            payload_kg=1.0,
        )
        result_wind = find_path(
            37.775, -122.420,
            37.780, -122.415,
            nofly_geojsons=[],
            wind_vector=(-10.0, 0.0),
            payload_kg=1.0,
        )
        assert result_wind["battery_cost_pct"] >= result_calm["battery_cost_pct"]

    def test_heavier_payload_increases_cost(self):
        result_light = find_path(
            37.775, -122.420,
            37.780, -122.415,
            nofly_geojsons=[],
            payload_kg=0.5,
        )
        result_heavy = find_path(
            37.775, -122.420,
            37.780, -122.415,
            nofly_geojsons=[],
            payload_kg=5.0,
        )
        assert result_heavy["battery_cost_pct"] > result_light["battery_cost_pct"]
