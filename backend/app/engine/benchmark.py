"""Performance benchmarking utilities for the drone delivery engine.

Provides decorators and context managers to measure runtime, CPU usage,
and memory consumption of routing, simulation, and dispatch operations.
All metrics are emitted via Python's logging module.
"""

from __future__ import annotations

import functools
import logging
import os
import resource
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("drone_delivery.benchmark")


@dataclass
class BenchmarkResult:
    """Holds metrics from a single benchmarked invocation."""

    name: str
    wall_time_ms: float
    cpu_user_ms: float
    cpu_system_ms: float
    peak_rss_kb: int
    rss_delta_kb: int

    def log(self) -> None:
        logger.info(
            "[BENCH] %-30s  wall=%8.2f ms  cpu_user=%8.2f ms  cpu_sys=%8.2f ms  "
            "peak_rss=%d KB  rss_delta=%+d KB",
            self.name,
            self.wall_time_ms,
            self.cpu_user_ms,
            self.cpu_system_ms,
            self.peak_rss_kb,
            self.rss_delta_kb,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "wall_time_ms": round(self.wall_time_ms, 3),
            "cpu_user_ms": round(self.cpu_user_ms, 3),
            "cpu_system_ms": round(self.cpu_system_ms, 3),
            "peak_rss_kb": self.peak_rss_kb,
            "rss_delta_kb": self.rss_delta_kb,
        }


@dataclass
class AggregateStats:
    """Accumulates results across multiple calls for summary statistics."""

    name: str
    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    @property
    def count(self) -> int:
        return len(self.results)

    def summary(self) -> dict[str, Any]:
        if not self.results:
            return {"name": self.name, "count": 0}
        walls = [r.wall_time_ms for r in self.results]
        cpus = [r.cpu_user_ms + r.cpu_system_ms for r in self.results]
        return {
            "name": self.name,
            "count": self.count,
            "wall_time_ms": {
                "mean": round(statistics.mean(walls), 3),
                "median": round(statistics.median(walls), 3),
                "min": round(min(walls), 3),
                "max": round(max(walls), 3),
                "stdev": round(statistics.stdev(walls), 3) if len(walls) > 1 else 0.0,
            },
            "cpu_total_ms": {
                "mean": round(statistics.mean(cpus), 3),
                "median": round(statistics.median(cpus), 3),
                "min": round(min(cpus), 3),
                "max": round(max(cpus), 3),
            },
            "peak_rss_kb": max(r.peak_rss_kb for r in self.results),
        }

    def log_summary(self) -> None:
        s = self.summary()
        if s["count"] == 0:
            return
        wt = s["wall_time_ms"]
        logger.info(
            "[BENCH-SUMMARY] %-25s  calls=%d  wall=[%.2f / %.2f / %.2f ms] (min/med/max)  "
            "peak_rss=%d KB",
            s["name"],
            s["count"],
            wt["min"],
            wt["median"],
            wt["max"],
            s["peak_rss_kb"],
        )


# ---------------------------------------------------------------------------
# Global registry for per-function aggregate stats
# ---------------------------------------------------------------------------
_registry: dict[str, AggregateStats] = {}


def get_stats(name: str) -> AggregateStats:
    return _registry.setdefault(name, AggregateStats(name=name))


def all_stats() -> dict[str, AggregateStats]:
    return dict(_registry)


def log_all_summaries() -> None:
    for stats in _registry.values():
        stats.log_summary()


def reset_all_stats() -> None:
    _registry.clear()


# ---------------------------------------------------------------------------
# Measurement helpers
# ---------------------------------------------------------------------------

def _get_rss_kb() -> int:
    """Return current RSS in kilobytes (Linux: pages * page_size)."""
    try:
        with open("/proc/self/statm", "r") as f:
            pages = int(f.read().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") // 1024
    except (FileNotFoundError, OSError):
        ru = resource.getrusage(resource.RUSAGE_SELF)
        return ru.ru_maxrss


@contextmanager
def benchmark(name: str, *, collect: bool = True):
    """Context manager that measures wall time, CPU time, and memory.

    Usage::

        with benchmark("find_path") as result:
            path = find_path(...)
        # result.wall_time_ms is available after the block
    """
    ru_before = resource.getrusage(resource.RUSAGE_SELF)
    rss_before = _get_rss_kb()
    t0 = time.perf_counter_ns()

    result = BenchmarkResult(
        name=name,
        wall_time_ms=0.0,
        cpu_user_ms=0.0,
        cpu_system_ms=0.0,
        peak_rss_kb=0,
        rss_delta_kb=0,
    )
    try:
        yield result
    finally:
        elapsed_ns = time.perf_counter_ns() - t0
        ru_after = resource.getrusage(resource.RUSAGE_SELF)
        rss_after = _get_rss_kb()

        result.wall_time_ms = elapsed_ns / 1_000_000
        result.cpu_user_ms = (ru_after.ru_utime - ru_before.ru_utime) * 1000
        result.cpu_system_ms = (ru_after.ru_stime - ru_before.ru_stime) * 1000
        result.peak_rss_kb = ru_after.ru_maxrss
        result.rss_delta_kb = rss_after - rss_before

        result.log()
        if collect:
            get_stats(name).add(result)


def benchmark_fn(name: str | None = None, *, collect: bool = True) -> Callable:
    """Decorator that benchmarks every call to the wrapped function.

    Usage::

        @benchmark_fn("find_path")
        def find_path(...):
            ...

    The ``BenchmarkResult`` is attached as ``_last_benchmark`` on the function
    for programmatic access.
    """

    def decorator(fn: Callable) -> Callable:
        bench_name = name or fn.__qualname__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with benchmark(bench_name, collect=collect) as result:
                ret = fn(*args, **kwargs)
            wrapper._last_benchmark = result  # type: ignore[attr-defined]
            return ret

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with benchmark(bench_name, collect=collect) as result:
                ret = await fn(*args, **kwargs)
            async_wrapper._last_benchmark = result  # type: ignore[attr-defined]
            return ret

        import asyncio

        if asyncio.iscoroutinefunction(fn):
            async_wrapper._last_benchmark = None  # type: ignore[attr-defined]
            return async_wrapper

        wrapper._last_benchmark = None  # type: ignore[attr-defined]
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Standalone benchmark runner for routing & physics
# ---------------------------------------------------------------------------

def run_routing_benchmark(
    *,
    start: tuple[float, float] = (37.7749, -122.4194),
    end: tuple[float, float] = (37.7849, -122.4094),
    nofly_geojsons: list[str] | None = None,
    iterations: int = 5,
    payload_kg: float = 1.5,
    wind_vector: tuple[float, float] = (0.0, 0.0),
) -> dict[str, Any]:
    """Run find_path multiple times and return aggregate stats."""
    from app.engine.routing import find_path

    if nofly_geojsons is None:
        nofly_geojsons = []

    results: list[BenchmarkResult] = []
    route_result = None

    for i in range(iterations):
        with benchmark(f"find_path[{i}]", collect=False) as br:
            route_result = find_path(
                start[0], start[1], end[0], end[1],
                nofly_geojsons,
                wind_vector=wind_vector,
                payload_kg=payload_kg,
            )
        results.append(br)

    agg = AggregateStats(name="find_path")
    for r in results:
        agg.add(r)
    agg.log_summary()

    return {
        "benchmark": agg.summary(),
        "route_sample": route_result,
    }


def run_physics_benchmark(*, iterations: int = 1000) -> dict[str, Any]:
    """Benchmark battery / wind physics computations."""
    from app.engine.physics import (
        BatteryState,
        WindCondition,
        effective_speed,
        compute_heading,
        should_return_to_base,
    )
    from app.engine.routing import compute_battery_cost

    results: list[BenchmarkResult] = []

    with benchmark("physics_batch", collect=False) as br:
        for _ in range(iterations):
            compute_battery_cost(5.0, 2.0, 8000, (10.0, 5.0))
            effective_speed(60.0, WindCondition(20.0, 90.0), 45.0)
            compute_heading(37.77, -122.42, 37.78, -122.41)
            bat = BatteryState(8000, 50.0)
            should_return_to_base(bat, 3.0, 2.0, WindCondition(15.0, 270.0), 90.0)

    results.append(br)
    ops_per_sec = (iterations * 4) / (br.wall_time_ms / 1000) if br.wall_time_ms > 0 else 0

    return {
        "iterations": iterations,
        "total_wall_ms": round(br.wall_time_ms, 3),
        "ops_per_second": round(ops_per_sec),
        "cpu_user_ms": round(br.cpu_user_ms, 3),
        "cpu_system_ms": round(br.cpu_system_ms, 3),
        "peak_rss_kb": br.peak_rss_kb,
    }
