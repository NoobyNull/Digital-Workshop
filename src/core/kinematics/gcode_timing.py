"""G-code path length and timing analysis utilities.

This module operates on generic move objects (such as the GUI's
``GcodeMove``) and computes aggregate path lengths and machining times
using the helpers in :mod:`timing_engine`.

The functions are intentionally tolerant of partial data and use
attribute access with sensible fallbacks, so they can work with any
object that exposes ``x``, ``y``, ``z``, ``feed_rate`` and the boolean
flags ``is_rapid``, ``is_cutting``, ``is_arc``, and ``is_tool_change``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable

from .timing_engine import best_case_move_time_seconds, trapezoidal_move_time_seconds


def analyze_gcode_moves(
    moves: Iterable[Any],
    max_feed_mm_min: float,
    accel_mm_s2: float,
    feed_override_pct: float,
) -> Dict[str, float]:
    """Compute aggregate distances and times for a sequence of moves.

    Parameters
    ----------
    moves:
        Iterable of move-like objects (e.g. ``GcodeMove`` instances).
    max_feed_mm_min:
        Machine's maximum feed rate in mm/min (before override).
    accel_mm_s2:
        Machine acceleration in mm/s^2.
    feed_override_pct:
        Feed override percentage (10-200). 100 means no change.

    Returns
    -------
    Dict[str, float]
        Keys are aligned with the ``gcode_metrics`` table:

        - ``total_time_seconds``
        - ``cutting_time_seconds``
        - ``rapid_time_seconds``
        - ``tool_changes``
        - ``distance_cut``
        - ``distance_rapid``
        - ``best_case_time_seconds``
        - ``time_correction_factor`` (k = total_time / best_case_time)
    """

    total_time_us = 0
    best_case_time_us = 0
    cutting_time_us = 0
    rapid_time_us = 0

    distance_cut_mm = 0.0
    distance_rapid_mm = 0.0
    tool_changes = 0

    # Track last known position; assume origin at (0, 0, 0).
    prev_x = 0.0
    prev_y = 0.0
    prev_z = 0.0
    has_prev = False

    for move in moves:
        # Tool-change bookkeeping is independent of motion.
        if getattr(move, "is_tool_change", False):
            tool_changes += 1

        is_rapid = getattr(move, "is_rapid", False)
        is_cutting = getattr(move, "is_cutting", False)
        is_arc = getattr(move, "is_arc", False)

        # Only motion moves contribute to path length and time.
        if not (is_rapid or is_cutting or is_arc):
            continue

        x = float(getattr(move, "x", prev_x))
        y = float(getattr(move, "y", prev_y))
        z = float(getattr(move, "z", prev_z))

        if not has_prev:
            # First motion move: treat distance from origin.
            dx = x - prev_x
            dy = y - prev_y
            dz = z - prev_z
            has_prev = True
        else:
            dx = x - prev_x
            dy = y - prev_y
            dz = z - prev_z

        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        prev_x, prev_y, prev_z = x, y, z

        if distance <= 0.0:
            continue

        feed_rate = getattr(move, "feed_rate", None)
        try:
            feed_val = float(feed_rate) if feed_rate is not None else None
        except (TypeError, ValueError):
            feed_val = None

        # Best-case (no acceleration) and full trapezoidal timing.
        t_best = best_case_move_time_seconds(
            distance_mm=distance,
            feed_rate_mm_min=feed_val,
            max_feed_mm_min=max_feed_mm_min,
            feed_override_pct=feed_override_pct,
        )
        t_full = trapezoidal_move_time_seconds(
            distance_mm=distance,
            feed_rate_mm_min=feed_val,
            max_feed_mm_min=max_feed_mm_min,
            accel_mm_s2=accel_mm_s2,
            feed_override_pct=feed_override_pct,
        )

        delta_best_us = int(round(t_best * 1_000_000.0))
        delta_full_us = int(round(t_full * 1_000_000.0))

        best_case_time_us += delta_best_us
        total_time_us += delta_full_us

        # Cutting vs rapid time and distances.
        if is_rapid:
            distance_rapid_mm += distance
            rapid_time_us += delta_full_us
        else:
            # Treat both linear cuts and arcs as cutting moves.
            distance_cut_mm += distance
            cutting_time_us += delta_full_us

    total_time_seconds = total_time_us / 1_000_000.0
    cutting_time_seconds = cutting_time_us / 1_000_000.0
    rapid_time_seconds = rapid_time_us / 1_000_000.0
    best_case_time_seconds = best_case_time_us / 1_000_000.0

    if best_case_time_seconds > 0.0:
        time_correction_factor = total_time_seconds / best_case_time_seconds
    else:
        time_correction_factor = 1.0

    return {
        "total_time_seconds": total_time_seconds,
        "cutting_time_seconds": cutting_time_seconds,
        "rapid_time_seconds": rapid_time_seconds,
        "tool_changes": tool_changes,
        "distance_cut": distance_cut_mm,
        "distance_rapid": distance_rapid_mm,
        "best_case_time_seconds": best_case_time_seconds,
        "time_correction_factor": time_correction_factor,
    }

