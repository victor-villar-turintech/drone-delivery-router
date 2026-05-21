"""A* pathfinding over a lat/lon grid with no-fly zone avoidance."""

from __future__ import annotations

import heapq
import json
import math
from dataclasses import dataclass, field
from typing import Sequence

from shapely.geometry import Point, shape


@dataclass(frozen=True, order=True)
class GridNode:
    lat: float
    lon: float


@dataclass(order=True)
class _PQEntry:
    priority: float
    node: GridNode = field(compare=False)


EARTH_RADIUS_KM = 6371.0


def haversine_km(a: GridNode, b: GridNode) -> float:
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _build_nofly_polygons(zones_geojson: Sequence[str]):
    polys = []
    for gj in zones_geojson:
        geom = shape(json.loads(gj))
        polys.append(geom)
    return polys


def _is_in_nofly(lat: float, lon: float, polys) -> bool:
    pt = Point(lon, lat)
    return any(poly.contains(pt) for poly in polys)


def _neighbors(node: GridNode, step: float) -> list[GridNode]:
    offsets = [
        (step, 0), (-step, 0), (0, step), (0, -step),
        (step, step), (step, -step), (-step, step), (-step, -step),
    ]
    return [GridNode(round(node.lat + dlat, 6), round(node.lon + dlon, 6)) for dlat, dlon in offsets]


def _snap_to_grid(lat: float, lon: float, step: float) -> GridNode:
    return GridNode(round(round(lat / step) * step, 6), round(round(lon / step) * step, 6))


def find_path(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    nofly_geojsons: Sequence[str],
    grid_step: float = 0.002,
    wind_vector: tuple[float, float] = (0.0, 0.0),
    payload_kg: float = 0.0,
    battery_pct: float = 100.0,
    battery_capacity_mah: int = 5000,
) -> dict:
    """Return a route dict with 'path' (list of [lat, lon]),
    'distance_km', and 'battery_cost_pct'."""

    polys = _build_nofly_polygons(nofly_geojsons)
    start = _snap_to_grid(start_lat, start_lon, grid_step)
    goal = _snap_to_grid(end_lat, end_lon, grid_step)

    if _is_in_nofly(start.lat, start.lon, polys):
        start = _find_nearest_clear(start, polys, grid_step)
    if _is_in_nofly(goal.lat, goal.lon, polys):
        goal = _find_nearest_clear(goal, polys, grid_step)

    open_set: list[_PQEntry] = []
    heapq.heappush(open_set, _PQEntry(0.0, start))
    came_from: dict[GridNode, GridNode | None] = {start: None}
    g_score: dict[GridNode, float] = {start: 0.0}

    max_iterations = 50_000
    iterations = 0

    while open_set and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_set).node

        if haversine_km(current, goal) < grid_step * 80:
            path = _reconstruct(came_from, current, goal)
            dist = _path_distance(path)
            cost = compute_battery_cost(dist, payload_kg, battery_capacity_mah, wind_vector)
            return {
                "path": [[n.lat, n.lon] for n in path],
                "distance_km": round(dist, 4),
                "battery_cost_pct": round(cost, 2),
            }

        for nb in _neighbors(current, grid_step):
            if _is_in_nofly(nb.lat, nb.lon, polys):
                continue
            move_cost = _edge_cost(current, nb, wind_vector, payload_kg)
            tentative = g_score[current] + move_cost
            if tentative < g_score.get(nb, float("inf")):
                g_score[nb] = tentative
                f = tentative + haversine_km(nb, goal)
                heapq.heappush(open_set, _PQEntry(f, nb))
                came_from[nb] = current

    return {"path": [], "distance_km": 0.0, "battery_cost_pct": 0.0, "error": "no_path_found"}


def _find_nearest_clear(node: GridNode, polys, step: float, radius: int = 10) -> GridNode:
    for r in range(1, radius + 1):
        for nb in _neighbors(GridNode(node.lat, node.lon), step * r):
            if not _is_in_nofly(nb.lat, nb.lon, polys):
                return nb
    return node


def _edge_cost(a: GridNode, b: GridNode, wind: tuple[float, float], payload_kg: float) -> float:
    dist = haversine_km(a, b)
    bearing_lat = b.lat - a.lat
    bearing_lon = b.lon - a.lon
    norm = math.sqrt(bearing_lat**2 + bearing_lon**2) or 1.0
    bearing_unit = (bearing_lat / norm, bearing_lon / norm)
    headwind = -(wind[0] * bearing_unit[0] + wind[1] * bearing_unit[1])
    wind_factor = 1.0 + 0.15 * headwind
    weight_factor = 1.0 + 0.1 * payload_kg
    return dist * wind_factor * weight_factor


def compute_battery_cost(
    distance_km: float,
    payload_kg: float,
    battery_capacity_mah: int,
    wind_vector: tuple[float, float] = (0.0, 0.0),
) -> float:
    base_drain_per_km = 2.0
    weight_factor = 1.0 + 0.1 * payload_kg
    wind_magnitude = math.sqrt(wind_vector[0] ** 2 + wind_vector[1] ** 2)
    wind_factor = 1.0 + 0.05 * wind_magnitude
    capacity_factor = 5000 / max(battery_capacity_mah, 1)
    return distance_km * base_drain_per_km * weight_factor * wind_factor * capacity_factor


def _reconstruct(came_from: dict, current: GridNode, goal: GridNode) -> list[GridNode]:
    path = [goal, current]
    while came_from.get(current) is not None:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _path_distance(path: list[GridNode]) -> float:
    total = 0.0
    for i in range(len(path) - 1):
        total += haversine_km(path[i], path[i + 1])
    return total
