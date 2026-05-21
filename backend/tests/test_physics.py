"""Unit tests for battery and wind physics."""

import pytest
from app.engine.physics import (
    BatteryState,
    WindCondition,
    effective_speed,
    should_return_to_base,
    compute_heading,
    DRONE_SPEED_KMH,
)


class TestBatteryState:
    def test_drain(self):
        b = BatteryState(5000, 100.0)
        b.drain(20.0)
        assert b.current_pct == pytest.approx(80.0)

    def test_drain_floor_at_zero(self):
        b = BatteryState(5000, 5.0)
        b.drain(10.0)
        assert b.current_pct == 0.0

    def test_needs_return_below_threshold(self):
        b = BatteryState(5000, 14.9)
        assert b.needs_return is True

    def test_needs_return_above_threshold(self):
        b = BatteryState(5000, 50.0)
        assert b.needs_return is False


class TestWindPhysics:
    def test_no_wind(self):
        w = WindCondition(0.0, 0.0)
        speed = effective_speed(DRONE_SPEED_KMH, w, heading_deg=0.0)
        assert speed == pytest.approx(DRONE_SPEED_KMH)

    def test_headwind_reduces_speed(self):
        w = WindCondition(20.0, 0.0)
        speed = effective_speed(DRONE_SPEED_KMH, w, heading_deg=0.0)
        assert speed < DRONE_SPEED_KMH

    def test_tailwind_increases_speed(self):
        w = WindCondition(20.0, 180.0)
        speed = effective_speed(DRONE_SPEED_KMH, w, heading_deg=0.0)
        assert speed > DRONE_SPEED_KMH

    def test_speed_floor(self):
        w = WindCondition(200.0, 0.0)
        speed = effective_speed(DRONE_SPEED_KMH, w, heading_deg=0.0)
        assert speed >= DRONE_SPEED_KMH * 0.3


class TestReturnToBase:
    def test_low_battery_triggers_return(self):
        b = BatteryState(5000, 20.0)
        w = WindCondition(0.0, 0.0)
        assert should_return_to_base(b, 5.0, 1.0, w, 0.0) is True

    def test_full_battery_no_return(self):
        b = BatteryState(5000, 100.0)
        w = WindCondition(0.0, 0.0)
        assert should_return_to_base(b, 1.0, 0.5, w, 0.0) is False


class TestHeading:
    def test_due_north(self):
        h = compute_heading(37.0, -122.0, 38.0, -122.0)
        assert abs(h - 0.0) < 1.0 or abs(h - 360.0) < 1.0

    def test_due_east(self):
        h = compute_heading(37.0, -122.0, 37.0, -121.0)
        assert 85.0 < h < 95.0
