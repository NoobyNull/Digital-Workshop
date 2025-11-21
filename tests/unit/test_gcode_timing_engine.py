#!/usr/bin/env python3
"""Unit tests for the kinematic timing engine.

These tests are intentionally lightweight and avoid any Qt/VTK imports.
They validate the numerical behaviour of the timing helpers that underpin
cutting-time estimation in the G-code previewer.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Add project root to path so ``src`` can be imported consistently with
# the existing G-code viewer tests.
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.kinematics.timing_engine import (  # type: ignore  # noqa: E402
    best_case_move_time_seconds,
    trapezoidal_move_time_seconds,
)
from src.core.kinematics.gcode_timing import analyze_gcode_moves  # type: ignore  # noqa: E402
from src.gui.gcode_previewer_components.gcode_parser import (  # type: ignore  # noqa: E402
    GcodeMove,
)


def test_best_case_matches_simple_distance_over_speed() -> None:
    """Best-case time should match distance / feed when under the limit.

    For a 60 mm move at 600 mm/min the theoretical best-case time is::

        t = (60 mm) / (600 mm/min) = 0.1 min = 6 seconds
    """

    distance_mm = 60.0
    feed_rate_mm_min = 600.0
    max_feed_mm_min = 600.0
    feed_override_pct = 100.0

    t_best = best_case_move_time_seconds(
        distance_mm=distance_mm,
        feed_rate_mm_min=feed_rate_mm_min,
        max_feed_mm_min=max_feed_mm_min,
        feed_override_pct=feed_override_pct,
    )

    assert math.isclose(t_best, 6.0, rel_tol=1e-6, abs_tol=1e-6)


def test_trapezoidal_profile_respects_acceleration_limit() -> None:
    """Trapezoidal timing must be no shorter than the best-case time.

    The continuous kinematic model (with acceleration) can only make a move
    slower or equal compared to the best-case model that ignores acceleration.
    """

    distance_mm = 100.0
    feed_rate_mm_min = 1200.0
    max_feed_mm_min = 1200.0
    accel_mm_s2 = 100.0
    feed_override_pct = 100.0

    t_best = best_case_move_time_seconds(
        distance_mm=distance_mm,
        feed_rate_mm_min=feed_rate_mm_min,
        max_feed_mm_min=max_feed_mm_min,
        feed_override_pct=feed_override_pct,
    )
    t_trap = trapezoidal_move_time_seconds(
        distance_mm=distance_mm,
        feed_rate_mm_min=feed_rate_mm_min,
        max_feed_mm_min=max_feed_mm_min,
        accel_mm_s2=accel_mm_s2,
        feed_override_pct=feed_override_pct,
    )

    assert t_trap >= t_best


def test_analyze_gcode_moves_computes_consistent_correction_factor() -> None:
    """End-to-end analysis should return a sensible correction factor.

    For a simple path consisting entirely of cutting moves at a constant
    feed rate, the kinematic time should be close to the best-case time and
    the correction factor ``k = total_time / best_case_time`` should be near 1.
    """

    # Construct a simple sequence of cutting moves totalling 100 mm.
    moves = [
        GcodeMove(
            x=0.0,
            y=0.0,
            z=0.0,
            feed_rate=600.0,
            spindle_speed=0.0,
            is_rapid=False,
            is_cutting=True,
            is_arc=False,
            is_tool_change=False,
            tool_number="1",
            line_number=1,
            raw_command="G01 X0 Y0 Z0 F600",
        ),
        GcodeMove(
            x=100.0,
            y=0.0,
            z=0.0,
            feed_rate=600.0,
            spindle_speed=0.0,
            is_rapid=False,
            is_cutting=True,
            is_arc=False,
            is_tool_change=False,
            tool_number="1",
            line_number=2,
            raw_command="G01 X100 Y0 Z0 F600",
        ),
    ]

    metrics = analyze_gcode_moves(
        moves=moves,
        max_feed_mm_min=600.0,
        accel_mm_s2=100.0,
        feed_override_pct=100.0,
    )

    assert metrics["distance_cut"] == pytest.approx(100.0, rel=1e-6)
    assert metrics["distance_rapid"] == pytest.approx(0.0, rel=1e-6)

    # The correction factor should be close to 1 for this simple case. We
    # allow a small tolerance because the kinematic model may introduce a
    # modest conservatism depending on the acceleration profile.
    assert metrics["time_correction_factor"] == pytest.approx(1.0, rel=2e-2)
