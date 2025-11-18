"""Timing and kinematics helpers for CNC toolpath analysis.

This module implements a continuous trapezoidal motion model and a simple
"best-case" timing model that ignores acceleration. All inputs are in
metric units (mm, mm/min, mm/s^2) and results are returned in seconds.

These helpers are intentionally UI-agnostic and do not depend on Qt.
"""

from __future__ import annotations

import math
from typing import Optional


def _effective_feed_mm_s(
    feed_rate_mm_min: Optional[float],
    max_feed_mm_min: float,
    feed_override_pct: float,
) -> float:
    """Compute effective feed in mm/s after clamping and override.

    The commanded feed is first clamped to the machine's max feed
    (after applying a 10-200% override). If no feed is commanded,
    the machine's effective max feed is used.
    """

    if max_feed_mm_min <= 0:
        return 0.0

    # Feed override is expressed as a percentage [10, 200].
    override_factor = max(feed_override_pct, 0.0) / 100.0 if feed_override_pct else 1.0
    effective_max_feed = max_feed_mm_min * override_factor
    if effective_max_feed <= 0:
        return 0.0

    if feed_rate_mm_min is None or feed_rate_mm_min <= 0:
        clamped_feed = effective_max_feed
    else:
        clamped_feed = min(feed_rate_mm_min, effective_max_feed)

    return clamped_feed / 60.0  # mm/min -> mm/s


def best_case_move_time_seconds(
    distance_mm: float,
    feed_rate_mm_min: Optional[float],
    max_feed_mm_min: float,
    feed_override_pct: float,
) -> float:
    """Compute best-case move time ignoring acceleration.

    The move is assumed to travel ``distance_mm`` at constant velocity
    equal to the clamped feed (commanded vs machine limit * override).
    """

    if distance_mm <= 0:
        return 0.0

    v = _effective_feed_mm_s(feed_rate_mm_min, max_feed_mm_min, feed_override_pct)
    if v <= 0:
        return 0.0

    return distance_mm / v


def trapezoidal_move_time_seconds(
    distance_mm: float,
    feed_rate_mm_min: Optional[float],
    max_feed_mm_min: float,
    accel_mm_s2: float,
    feed_override_pct: float,
) -> float:
    """Compute move time using a symmetric trapezoidal motion profile.

    The motion model assumes:
    - Start and end velocity are zero for each move.
    - Acceleration and deceleration magnitudes are equal (``accel_mm_s2``).
    - Velocity is limited by the clamped feed (commanded vs machine max * override).

    For very short moves where the path length is insufficient to reach the
    target velocity, a triangular profile is used instead.
    """

    if distance_mm <= 0:
        return 0.0

    v = _effective_feed_mm_s(feed_rate_mm_min, max_feed_mm_min, feed_override_pct)
    if v <= 0:
        return 0.0

    if accel_mm_s2 <= 0:
        # Degenerate case: treat as constant-velocity motion.
        return distance_mm / v

    # Distance required to accelerate from 0 to v and then back to 0.
    # Using v^2 = 2 * a * d  =>  d = v^2 / (2a)
    d_acc = (v * v) / (2.0 * accel_mm_s2)

    if distance_mm >= 2.0 * d_acc:
        # Trapezoidal profile: accel -> cruise -> decel.
        t_acc = v / accel_mm_s2
        d_flat = distance_mm - 2.0 * d_acc
        t_flat = d_flat / v if d_flat > 0 else 0.0
        return 2.0 * t_acc + t_flat

    # Triangular profile: accelerate up to a peak velocity then decelerate.
    # Total time for symmetric triangular motion over distance d is:
    #   t_total = 2 * sqrt(d / a)
    return 2.0 * math.sqrt(distance_mm / accel_mm_s2)
