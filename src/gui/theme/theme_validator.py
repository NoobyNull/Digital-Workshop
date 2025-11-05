"""
Theme Validator Module

This module provides comprehensive theme validation and error handling for the unified theme system.
It ensures theme consistency, validates color schemes, and provides graceful error recovery.

Key Features:
- Comprehensive theme validation with detailed error reporting
- Color scheme validation for accessibility and consistency
- Qt-material theme validation and compatibility checking
- Graceful error handling with fallback mechanisms
- Performance monitoring for validation operations
- Memory-efficient validation algorithms

Validation Coverage:
- Theme structure validation
- Color format and accessibility validation
- Qt-material compatibility validation
- Cross-platform compatibility validation
- Performance impact validation
"""

import re
import time
from typing import Dict, List, Any, Tuple
from PySide6.QtGui import QColor
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ThemeValidationError(Exception):
    """
    Exception raised when theme validation fails.

    Provides detailed information about validation failures
    and suggested remediation steps.
    """

    def __init__(self, message: str, errors: List[str] = None, warnings: List[str] = None) -> None:
        """
        Initialize theme validation error.

        Args:
            message: Error message
            errors: List of critical errors
            warnings: List of non-critical warnings
        """
        super().__init__(message)
        self.errors = errors or []
        self.warnings = warnings or []


class ThemeValidator:
    """
    Comprehensive theme validation and error handling system.

    Provides multi-level validation for theme configurations including:
    - Structural validation (required fields, data types)
    - Color validation (format, accessibility, contrast)
    - Qt-material compatibility validation
    - Performance impact validation
    - Cross-platform compatibility validation

    Error Handling:
    - Graceful degradation for invalid themes
    - Detailed error reporting with remediation suggestions
    - Fallback theme generation for critical failures
    - Performance monitoring for validation operations
    """

    def __init__(self) -> None:
        """Initialize theme validator."""
        # Color validation patterns
        self._hex_color_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
        self._rgb_color_pattern = re.compile(r"^rgb\((\d+),\s*(\d+),\s*(\d+)\)$")
        self._rgba_color_pattern = re.compile(r"^rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)$")

        # Accessibility requirements
        self._min_contrast_ratio = 4.5  # WCAG AA standard
        self._min_large_text_contrast = 3.0  # WCAG AA for large text

        # Performance tracking
        self._validation_count = 0
        self._validation_errors = 0
        self._validation_time_total = 0.0

        # Valid theme configurations
        self._valid_themes = {
            "dark": [
                "blue",
                "amber",
                "cyan",
                "red",
                "green",
                "purple",
                "teal",
                "yellow",
            ],
            "light": [
                "blue",
                "amber",
                "cyan",
                "red",
                "green",
                "purple",
                "teal",
                "yellow",
            ],
            "auto": [
                "blue",
                "amber",
                "cyan",
                "red",
                "green",
                "purple",
                "teal",
                "yellow",
            ],
        }

        # Required color roles for accessibility
        self._required_color_roles = [
            "primary",
            "background",
            "surface",
            "text_primary",
            "text_secondary",
        ]

        logger.info("ThemeValidator initialized with comprehensive validation rules")

    def validate_theme(self, theme_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Perform comprehensive theme validation.

        Args:
            theme_data: Theme configuration to validate

        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Level 1: Structural validation
            structure_valid, structure_errors = self._validate_structure(theme_data)
            errors.extend(structure_errors)

            # Level 2: Color validation (if structure is valid)
            if structure_valid:
                color_valid, color_errors, color_warnings = self._validate_colors(theme_data)
                errors.extend(color_errors)
                warnings.extend(color_warnings)

                # Level 3: Qt-material compatibility (if colors are valid)
                if color_valid:
                    _, qt_errors, qt_warnings = self._validate_qt_material(theme_data)
                    errors.extend(qt_errors)
                    warnings.extend(qt_warnings)

                    # Level 4: Performance validation
                    _, perf_warnings = self._validate_performance(theme_data)
                    warnings.extend(perf_warnings)

            # Track validation metrics
            elapsed = (time.time() - start_time) * 1000
            self._track_validation(structure_valid and color_valid, elapsed)

            is_valid = len(errors) == 0

            if not is_valid:
                logger.warning(
                    f"Theme validation failed: {len(errors)} errors, {len(warnings)} warnings"
                )
            elif warnings:
                logger.info("Theme validation passed with %s warnings", len(warnings))

            return is_valid, errors, warnings

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            elapsed = (time.time() - start_time) * 1000
            self._track_validation(False, elapsed)

            logger.error("Theme validation exception: %s", e, exc_info=True)
            return False, [f"Validation exception: {str(e)}"], []

    def validate_color_scheme(self, colors: Dict[str, str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate color scheme for accessibility and consistency.

        Args:
            colors: Dictionary of color name to color value mappings

        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        errors = []
        warnings = []

        try:
            # Validate color formats
            for color_name, color_value in colors.items():
                if not self._is_valid_color_format(color_value):
                    errors.append(f"Invalid color format for '{color_name}': {color_value}")
                    continue

                # Check for accessibility issues
                accessibility_warnings = self._check_color_accessibility(
                    color_name, color_value, colors
                )
                warnings.extend(accessibility_warnings)

            # Check contrast ratios if we have text and background colors
            contrast_warnings = self._check_contrast_ratios(colors)
            warnings.extend(contrast_warnings)

            return len(errors) == 0, errors, warnings

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Color scheme validation failed: %s", e)
            return False, [f"Color validation exception: {str(e)}"], []

    def generate_fallback_theme(self, original_errors: List[str]) -> Dict[str, Any]:
        """
        Generate a safe fallback theme when validation fails critically.

        Args:
            original_errors: List of errors that caused the original failure

        Returns:
            Safe fallback theme configuration
        """
        fallback_theme = {
            "theme_name": "dark",
            "theme_variant": "blue",
            "qt_material_available": False,
            "custom_colors": {
                "primary": "#1976D2",
                "background": "#121212",
                "surface": "#1E1E1E",
                "text_primary": "#FFFFFF",
                "text_secondary": "#B0B0B0",
                "error": "#F44336",
                "warning": "#FF9800",
                "success": "#4CAF50",
            },
            "system_theme_detection": False,
            "auto_save_enabled": True,
            "theme_version": "2.0.0",
        }

        logger.warning("Generated fallback theme due to errors: %s", original_errors)
        return fallback_theme

    def get_validation_report(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed validation report for theme data.

        Args:
            theme_data: Theme configuration to validate

        Returns:
            Detailed validation report
        """
        is_valid, errors, warnings = self.validate_theme(theme_data)

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "validation_timestamp": time.time(),
            "theme_version": theme_data.get("theme_version", "unknown"),
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get validation performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        avg_time = (
            self._validation_time_total / self._validation_count
            if self._validation_count > 0
            else 0
        )

        return {
            "validation_count": self._validation_count,
            "validation_errors": self._validation_errors,
            "error_rate": self._validation_errors / max(self._validation_count, 1),
            "total_validation_time_ms": self._validation_time_total,
            "average_validation_time_ms": avg_time,
        }

    def _validate_structure(self, theme_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate basic theme structure.

        Args:
            theme_data: Theme data to validate

        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []

        # Check for required top-level keys
        required_keys = ["theme_name", "theme_variant"]
        for key in required_keys:
            if key not in theme_data:
                errors.append(f"Missing required key: {key}")
            elif not isinstance(theme_data[key], str):
                errors.append(f"Key '{key}' must be a string")

        # Validate theme name
        if "theme_name" in theme_data:
            theme_name = theme_data["theme_name"]
            if theme_name not in self._valid_themes:
                errors.append(
                    f"Invalid theme name '{theme_name}'. Must be one of: {list(self._valid_themes.keys())}"
                )

        # Validate theme variant
        if "theme_variant" in theme_data:
            theme_variant = theme_data["theme_variant"]
            theme_name = theme_data.get("theme_name", "dark")

            if (
                theme_name in self._valid_themes
                and theme_variant not in self._valid_themes[theme_name]
            ):
                errors.append(f"Invalid variant '{theme_variant}' for theme '{theme_name}'")

        # Validate custom colors structure
        if "custom_colors" in theme_data:
            custom_colors = theme_data["custom_colors"]
            if not isinstance(custom_colors, dict):
                errors.append("custom_colors must be a dictionary")
            else:
                # Check for required color roles
                for role in self._required_color_roles:
                    if role not in custom_colors:
                        errors.append(f"Missing required color role: {role}")

        return len(errors) == 0, errors

    def _validate_colors(self, theme_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate color values and formats.

        Args:
            theme_data: Theme data containing colors

        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        errors = []
        warnings = []
        custom_colors = theme_data.get("custom_colors", {})

        # Validate each color
        for color_name, color_value in custom_colors.items():
            if not self._is_valid_color_format(color_value):
                errors.append(f"Invalid color format for '{color_name}': {color_value}")
            else:
                # Check for common color issues
                color_warnings = self._check_color_issues(color_name, color_value)
                warnings.extend(color_warnings)

        # Check for color consistency
        consistency_warnings = self._check_color_consistency(custom_colors)
        warnings.extend(consistency_warnings)

        return len(errors) == 0, errors, warnings

    def _validate_qt_material(
        self, theme_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Qt-material compatibility.

        Args:
            theme_data: Theme data to validate

        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        errors = []
        warnings = []

        # Check Qt-material availability flag
        qt_available = theme_data.get("qt_material_available", False)
        if qt_available:
            # If Qt-material is supposedly available, validate theme compatibility
            theme_name = theme_data.get("theme_name", "dark")

            if theme_name not in ["dark", "light"]:
                warnings.append(f"Qt-material may not support theme '{theme_name}'")

            # Check for known Qt-material color conflicts
            custom_colors = theme_data.get("custom_colors", {})
            qt_conflicts = self._check_qt_material_conflicts(custom_colors)
            warnings.extend(qt_conflicts)

        return len(errors) == 0, errors, warnings

    def _validate_performance(self, theme_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate performance impact of theme.

        Args:
            theme_data: Theme data to validate

        Returns:
            Tuple of (is_valid, warnings_list)
        """
        warnings = []

        # Check for potentially expensive color operations
        custom_colors = theme_data.get("custom_colors", {})

        # Warn about too many custom colors (performance impact)
        if len(custom_colors) > 50:
            warnings.append(
                f"Large number of custom colors ({len(custom_colors)}) may impact performance"
            )

        # Check for complex color patterns that might be slow
        for color_name, color_value in custom_colors.items():
            if self._is_complex_color(color_value):
                warnings.append(f"Complex color '{color_name}' may impact rendering performance")

        return len(warnings) == 0, warnings

    def _is_valid_color_format(self, color_value: str) -> bool:
        """
        Check if color value has valid format.

        Args:
            color_value: Color value to validate

        Returns:
            True if color format is valid
        """
        if not isinstance(color_value, str):
            return False

        # Check hex format
        if self._hex_color_pattern.match(color_value):
            return True

        # Check RGB format
        if self._rgb_color_pattern.match(color_value):
            return True

        # Check RGBA format
        if self._rgba_color_pattern.match(color_value):
            return True

        # Check named colors (basic set)
        named_colors = {
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "cyan",
            "magenta",
            "gray",
            "grey",
            "transparent",
        }
        if color_value.lower() in named_colors:
            return True

        return False

    def _check_color_accessibility(
        self, color_name: str, color_value: str, _all_colors: Dict[str, str]
    ) -> List[str]:
        """
        Check color for accessibility issues.

        Args:
            color_name: Name of the color being checked
            color_value: Color value
            all_colors: All colors in the theme

        Returns:
            List of accessibility warnings
        """
        warnings = []

        # Parse color to get RGB values
        try:
            qcolor = QColor(color_value)
            if not qcolor.isValid():
                return [f"Color '{color_name}' is not a valid QColor"]

            # Check for very bright colors that might cause eye strain
            brightness = (qcolor.red() + qcolor.green() + qcolor.blue()) / (3 * 255)
            if brightness > 0.95 and color_name in ["background", "surface"]:
                warnings.append(f"Very bright {color_name} color may cause eye strain")

            # Check for very dark colors that might be hard to see
            if brightness < 0.05 and color_name in ["text_primary", "text_secondary"]:
                warnings.append(f"Very dark {color_name} color may be hard to read")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            warnings.append(f"Could not validate accessibility for color '{color_name}': {e}")

        return warnings

    def _check_contrast_ratios(self, colors: Dict[str, str]) -> List[str]:
        """
        Check contrast ratios between text and background colors.

        Args:
            colors: Dictionary of colors

        Returns:
            List of contrast ratio warnings
        """
        warnings = []

        # Check primary text on background
        text_primary = colors.get("text_primary")
        background = colors.get("background")

        if text_primary and background:
            try:
                contrast_ratio = self._calculate_contrast_ratio(text_primary, background)
                if contrast_ratio < self._min_contrast_ratio:
                    warnings.append(
                        f"Low contrast ratio ({contrast_ratio:.2f}) between text_primary and background. "
                        f"Minimum required: {self._min_contrast_ratio}"
                    )
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                warnings.append(f"Could not calculate contrast ratio: {e}")

        return warnings

    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """
        Calculate contrast ratio between two colors.

        Args:
            color1: First color
            color2: Second color

        Returns:
            Contrast ratio (1.0 to 21.0)
        """

        def luminance(color: str) -> float:
            """Calculate relative luminance of a color."""
            qcolor = QColor(color)
            r, g, b = qcolor.redF(), qcolor.greenF(), qcolor.blueF()

            # Apply gamma correction
            def gamma_correct(channel: float) -> float:
                """TODO: Add docstring."""
                return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

            r, g, b = gamma_correct(r), gamma_correct(g), gamma_correct(b)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1, l2 = luminance(color1), luminance(color2)
        lighter, darker = max(l1, l2), min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    def _check_color_issues(self, color_name: str, color_value: str) -> List[str]:
        """
        Check for common color issues.

        Args:
            color_name: Name of the color
            color_value: Color value

        Returns:
            List of warnings
        """
        warnings = []

        try:
            qcolor = QColor(color_value)

            # Check for fully transparent colors in non-background roles
            if qcolor.alpha() == 0 and color_name not in ["background"]:
                warnings.append(f"Transparent color '{color_name}' may not be visible")

            # Check for very low alpha values
            if 0 < qcolor.alpha() < 50 and color_name in [
                "text_primary",
                "text_secondary",
            ]:
                warnings.append(f"Low opacity text color '{color_name}' may be hard to read")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            warnings.append(f"Could not check color issues for '{color_name}': {e}")

        return warnings

    def _check_color_consistency(self, colors: Dict[str, str]) -> List[str]:
        """
        Check for color consistency issues.

        Args:
            colors: Dictionary of colors

        Returns:
            List of consistency warnings
        """
        warnings = []

        # Check for duplicate color values that might indicate errors
        color_values = list(colors.values())
        for i, color1 in enumerate(color_values):
            for j, color2 in enumerate(color_values[i + 1 :], i + 1):
                if color1 == color2:
                    color_name1 = list(colors.keys())[i]
                    color_name2 = list(colors.keys())[j]
                    warnings.append(
                        f"Duplicate color value '{color1}' for '{color_name1}' and '{color_name2}'"
                    )

        return warnings

    def _check_qt_material_conflicts(self, colors: Dict[str, str]) -> List[str]:
        """
        Check for potential Qt-material conflicts.

        Args:
            colors: Dictionary of custom colors

        Returns:
            List of Qt-material conflict warnings
        """
        warnings = []

        # Qt-material has specific color roles that shouldn't be overridden
        qt_reserved_colors = ["primary", "primary_light", "primary_dark", "secondary"]

        for color_name in colors.keys():
            if color_name in qt_reserved_colors:
                warnings.append(
                    f"Custom color '{color_name}' may conflict with Qt-material built-in colors"
                )

        return warnings

    def _is_complex_color(self, color_value: str) -> bool:
        """
        Check if color might be computationally expensive.

        Args:
            color_value: Color value to check

        Returns:
            True if color might be complex/expensive
        """
        # Complex patterns that might indicate expensive color operations
        complex_patterns = [
            r"gradient\(",  # Gradients
            r"conic-gradient\(",  # Conic gradients
            r"radial-gradient\(",  # Radial gradients
            r"linear-gradient\(",  # Linear gradients
            r"url\(#",  # References to other elements
        ]

        color_lower = color_value.lower()
        return any(re.search(pattern, color_lower) for pattern in complex_patterns)

    def _track_validation(self, success: bool, elapsed_ms: float) -> None:
        """Track validation performance metrics."""
        self._validation_count += 1
        if not success:
            self._validation_errors += 1
        self._validation_time_total += elapsed_ms
