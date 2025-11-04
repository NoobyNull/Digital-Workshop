"""Unit conversion utilities for Feeds & Speeds calculator."""

from typing import Dict


class UnitConverter:
    """Converts between SAE (inches) and MET (metric) units."""

    # Conversion factors
    INCH_TO_MM = 25.4
    MM_TO_INCH = 1 / 25.4

    # Feed rate conversions
    IPM_TO_MMPM = 25.4  # Inches per minute to mm per minute
    MMPM_TO_IPM = 1 / 25.4

    # Speed conversions (RPM stays the same)

    @staticmethod
    def inch_to_mm(value: float) -> float:
        """Convert inches to millimeters."""
        return value * UnitConverter.INCH_TO_MM

    @staticmethod
    def mm_to_inch(value: float) -> float:
        """Convert millimeters to inches."""
        return value * UnitConverter.MM_TO_INCH

    @staticmethod
    def ipm_to_mmpm(value: float) -> float:
        """Convert inches per minute to mm per minute."""
        return value * UnitConverter.IPM_TO_MMPM

    @staticmethod
    def mmpm_to_ipm(value: float) -> float:
        """Convert mm per minute to inches per minute."""
        return value * UnitConverter.MMPM_TO_IPM

    @staticmethod
    def convert_tool_dimensions(tool_data: Dict, to_metric: bool) -> Dict:
        """
        Convert tool dimensions between units.

        Args:
            tool_data: Tool data dictionary
            to_metric: True to convert to metric, False to convert to inches

        Returns:
            Converted tool data
        """
        converted = tool_data.copy()

        # Geometry dimensions to convert
        geometry_keys = ["DC", "LB", "LCF", "OAL", "SFDM"]

        if "geometry" in converted:
            for key in geometry_keys:
                if key in converted["geometry"]:
                    value = converted["geometry"][key]
                    if to_metric:
                        converted["geometry"][key] = UnitConverter.inch_to_mm(value)
                    else:
                        converted["geometry"][key] = UnitConverter.mm_to_inch(value)

        return converted

    @staticmethod
    def convert_feed_rates(feed_data: Dict, to_metric: bool) -> Dict:
        """
        Convert feed rates between units.

        Args:
            feed_data: Feed rate data dictionary
            to_metric: True to convert to metric, False to convert to inches

        Returns:
            Converted feed rate data
        """
        converted = feed_data.copy()

        # Feed rate keys to convert (IPM to MMPM)
        feed_keys = [
            "v_f",
            "v_f_leadIn",
            "v_f_leadOut",
            "v_f_plunge",
            "v_f_ramp",
            "v_f_transition",
        ]

        for key in feed_keys:
            if key in converted:
                value = converted[key]
                if to_metric:
                    converted[key] = UnitConverter.ipm_to_mmpm(value)
                else:
                    converted[key] = UnitConverter.mmpm_to_ipm(value)

        # Stepdown and stepover (linear dimensions)
        linear_keys = ["stepdown", "stepover"]
        for key in linear_keys:
            if key in converted:
                value = converted[key]
                if to_metric:
                    converted[key] = UnitConverter.inch_to_mm(value)
                else:
                    converted[key] = UnitConverter.mm_to_inch(value)

        return converted

    @staticmethod
    def get_unit_label(is_metric: bool, unit_type: str = "length") -> str:
        """
        Get unit label for display.

        Args:
            is_metric: True for metric, False for SAE
            unit_type: 'length', 'feed_rate', or 'speed'

        Returns:
            Unit label string
        """
        if unit_type == "length":
            return "mm" if is_metric else "in"
        elif unit_type == "feed_rate":
            return "mm/min" if is_metric else "in/min"
        elif unit_type == "speed":
            return "RPM"  # Same for both
        else:
            return ""

    @staticmethod
    def format_value(
        value: float, is_metric: bool, unit_type: str = "length", decimals: int = 3
    ) -> str:
        """
        Format a value with appropriate unit label.

        Args:
            value: Value to format
            is_metric: True for metric, False for SAE
            unit_type: 'length', 'feed_rate', or 'speed'
            decimals: Number of decimal places

        Returns:
            Formatted string with unit
        """
        unit = UnitConverter.get_unit_label(is_metric, unit_type)
        return f"{value:.{decimals}f} {unit}"
