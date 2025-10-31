#!/usr/bin/env python3
"""
Visual Regression Testing Framework for GUI Layout Refactoring

This framework provides automated visual regression testing to ensure that theme
migrations and UI changes don't break the visual appearance of the application.

Usage:
    python tools/visual_regression_tester.py [options]

Options:
    --baseline DIR   Directory containing baseline screenshots (default: tests/baseline)
    --output DIR     Directory for test output (default: tests/visual_regression)
    --threshold NUM  Pixel difference threshold (0-1, default: 0.05)
    --verbose        Enable verbose logging
    --generate-baselines Generate new baseline images
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TestResult:
    """Result of a visual regression test."""
    test_name: str
    baseline_path: str
    current_path: str
    difference_path: str
    pixel_difference: float
    max_difference: float
    passed: bool
    error_message: str
    test_duration: float


@dataclass
class TestSuite:
    """Complete test suite results."""
    summary: Dict[str, Any]
    results: List[TestResult]
    baseline_dir: str
    output_dir: str
    threshold: float


class VisualRegressionTester:
    """
    Visual regression testing framework for GUI components.
    """

    def __init__(self, baseline_dir: str = "tests/baseline",
                 output_dir: str = "tests/visual_regression",
                 threshold: float = 0.05):
        self.baseline_dir = Path(baseline_dir)
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test components registry
        self.test_components = {}

    def register_component(self, name: str, component_class: type, setup_func: callable = None):
        """
        Register a component for visual regression testing.

        Args:
            name: Unique name for the test
            component_class: The QWidget class to test
            setup_func: Optional function to set up the component before testing
        """
        self.test_components[name] = {
            'class': component_class,
            'setup': setup_func
        }
        self.logger.info(f"Registered test component: {name}")

    def run_test_suite(self, components: List[str] = None) -> TestSuite:
        """
        Run visual regression tests for registered components.

        Args:
            components: List of component names to test (None for all)

        Returns:
            TestSuite with results
        """
        if components is None:
            components = list(self.test_components.keys())

        self.logger.info(f"Running visual regression tests for {len(components)} components")

        results = []
        start_time = time.time()

        # Initialize QApplication if not already running
        app = self._get_or_create_app()

        for component_name in components:
            if component_name not in self.test_components:
                self.logger.warning(f"Component {component_name} not registered, skipping")
                continue

            try:
                result = self._test_component(component_name)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to test component {component_name}: {e}")
                results.append(TestResult(
                    test_name=component_name,
                    baseline_path="",
                    current_path="",
                    difference_path="",
                    pixel_difference=1.0,
                    max_difference=1.0,
                    passed=False,
                    error_message=str(e),
                    test_duration=0.0
                ))

        total_time = time.time() - start_time

        # Generate summary
        passed_tests = [r for r in results if r.passed]
        failed_tests = [r for r in results if not r.passed]

        summary = {
            'total_tests': len(results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'total_time': total_time,
            'average_time_per_test': total_time / len(results) if results else 0,
            'threshold': self.threshold,
            'baseline_dir': str(self.baseline_dir),
            'output_dir': str(self.output_dir)
        }

        return TestSuite(
            summary=summary,
            results=results,
            baseline_dir=str(self.baseline_dir),
            output_dir=str(self.output_dir),
            threshold=self.threshold
        )

    def generate_baselines(self, components: List[str] = None) -> Dict[str, str]:
        """
        Generate baseline images for components.

        Args:
            components: List of component names to generate baselines for

        Returns:
            Dictionary mapping component names to baseline paths
        """
        if components is None:
            components = list(self.test_components.keys())

        self.logger.info(f"Generating baselines for {len(components)} components")

        app = self._get_or_create_app()
        baselines = {}

        for component_name in components:
            try:
                baseline_path = self._generate_component_baseline(component_name)
                baselines[component_name] = baseline_path
                self.logger.info(f"Generated baseline for {component_name}: {baseline_path}")
            except Exception as e:
                self.logger.error(f"Failed to generate baseline for {component_name}: {e}")

        return baselines

    def _get_or_create_app(self) -> QApplication:
        """Get existing QApplication or create a new one."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    def _test_component(self, component_name: str) -> TestResult:
        """Test a single component for visual regression."""
        start_time = time.time()

        component_info = self.test_components[component_name]
        component_class = component_info['class']
        setup_func = component_info['setup']

        # Create component instance
        component = self._create_component_instance(component_class, setup_func)

        # Capture current screenshot
        current_pixmap = self._capture_screenshot(component)
        current_path = self.output_dir / f"{component_name}_current.png"
        current_pixmap.save(str(current_path))

        # Get baseline path
        baseline_path = self.baseline_dir / f"{component_name}.png"

        if not baseline_path.exists():
            error_msg = f"Baseline image not found: {baseline_path}"
            self.logger.error(error_msg)
            return TestResult(
                test_name=component_name,
                baseline_path=str(baseline_path),
                current_path=str(current_path),
                difference_path="",
                pixel_difference=1.0,
                max_difference=1.0,
                passed=False,
                error_message=error_msg,
                test_duration=time.time() - start_time
            )

        # Load baseline
        baseline_pixmap = QPixmap(str(baseline_path))

        # Compare images
        pixel_diff, max_diff, diff_pixmap = self._compare_images(baseline_pixmap, current_pixmap)

        # Save difference image
        diff_path = self.output_dir / f"{component_name}_diff.png"
        if diff_pixmap:
            diff_pixmap.save(str(diff_path))

        # Determine if test passed
        passed = pixel_diff <= self.threshold

        if not passed:
            self.logger.warning(f"Visual regression detected in {component_name}: "
                              f"pixel difference {pixel_diff:.4f} > threshold {self.threshold}")

        return TestResult(
            test_name=component_name,
            baseline_path=str(baseline_path),
            current_path=str(current_path),
            difference_path=str(diff_path),
            pixel_difference=pixel_diff,
            max_difference=max_diff,
            passed=passed,
            error_message="",
            test_duration=time.time() - start_time
        )

    def _create_component_instance(self, component_class: type, setup_func: callable = None) -> QWidget:
        """Create and set up a component instance for testing."""

        # Create main window to hold the component
        window = QMainWindow()
        window.setWindowTitle("Visual Regression Test")
        window.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        window.setCentralWidget(central_widget)

        # Create component instance
        component = component_class()

        # Apply setup function if provided
        if setup_func:
            setup_func(component)

        # Set up layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(component)

        # Ensure component is properly sized
        component.setMinimumSize(400, 300)

        # Process events to ensure rendering
        app = self._get_or_create_app()
        app.processEvents()

        # Give time for rendering
        QTimer.singleShot(100, lambda: None)
        app.processEvents()

        return window

    def _capture_screenshot(self, widget: QWidget) -> QPixmap:
        """Capture screenshot of a widget."""
        # Ensure widget is visible and rendered
        widget.show()
        widget.raise_()

        app = self._get_or_create_app()
        app.processEvents()

        # Small delay for rendering
        time.sleep(0.1)

        # Capture the widget
        pixmap = widget.grab()

        return pixmap

    def _generate_component_baseline(self, component_name: str) -> str:
        """Generate baseline image for a component."""
        component_info = self.test_components[component_name]
        component_class = component_info['class']
        setup_func = component_info['setup']

        # Create component instance
        component = self._create_component_instance(component_class, setup_func)

        # Capture screenshot
        pixmap = self._capture_screenshot(component)

        # Save baseline
        baseline_path = self.baseline_dir / f"{component_name}.png"
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(baseline_path))

        return str(baseline_path)

    def _compare_images(self, baseline: QPixmap, current: QPixmap) -> Tuple[float, float, Optional[QPixmap]]:
        """
        Compare two images and return pixel difference metrics.

        Returns:
            Tuple of (pixel_difference, max_difference, difference_pixmap)
        """
        # Convert to images for pixel-level comparison
        baseline_img = baseline.toImage()
        current_img = current.toImage()

        # Ensure same size
        if baseline_img.size() != current_img.size():
            # Resize current to match baseline
            current_img = current_img.scaled(baseline_img.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        width = baseline_img.width()
        height = baseline_img.height()

        total_pixels = width * height
        different_pixels = 0
        max_diff = 0.0

        # Create difference image
        diff_img = QImage(width, height, QImage.Format_RGB32)
        painter = QPainter(diff_img)

        for y in range(height):
            for x in range(width):
                baseline_color = QColor(baseline_img.pixel(x, y))
                current_color = QColor(current_img.pixel(x, y))

                # Calculate color difference (0-1)
                diff = self._color_difference(baseline_color, current_color)

                if diff > 0.01:  # Only count significant differences
                    different_pixels += 1

                max_diff = max(max_diff, diff)

                # Paint difference image (red for different pixels)
                if diff > 0.01:
                    painter.setPen(QColor(255, 0, 0))
                else:
                    painter.setPen(QColor(0, 255, 0))
                painter.drawPoint(x, y)

        painter.end()

        # Convert difference image back to pixmap
        diff_pixmap = QPixmap.fromImage(diff_img)

        # Calculate overall pixel difference percentage
        pixel_difference = different_pixels / total_pixels if total_pixels > 0 else 1.0

        return pixel_difference, max_diff, diff_pixmap

    def _color_difference(self, color1: QColor, color2: QColor) -> float:
        """Calculate difference between two colors (0-1)."""
        # Convert to RGB 0-1 range
        r1, g1, b1 = color1.redF(), color1.greenF(), color1.blueF()
        r2, g2, b2 = color2.redF(), color2.greenF(), color2.blueF()

        # Euclidean distance in RGB space
        diff = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5

        # Normalize to 0-1 range (max possible difference is sqrt(3))
        return diff / 1.732  # sqrt(3)

    def generate_report(self, test_suite: TestSuite, output_file: str = None) -> str:
        """
        Generate detailed test report.

        Args:
            test_suite: Test suite results
            output_file: Optional output file path

        Returns:
            Path to generated report
        """
        if output_file is None:
            output_file = self.output_dir / "visual_regression_report.html"

        # Generate HTML report
        html = self._generate_html_report(test_suite)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        self.logger.info(f"Test report generated: {output_file}")
        return str(output_file)

    def _generate_html_report(self, test_suite: TestSuite) -> str:
        """Generate HTML test report."""

        # Summary statistics
        passed = len([r for r in test_suite.results if r.passed])
        failed = len([r for r in test_suite.results if not r.passed])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visual Regression Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .test-result {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; }}
                .passed {{ border-left: 5px solid #4CAF50; background: #f0f8f0; }}
                .failed {{ border-left: 5px solid #f44336; background: #fdf0f0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4fd; }}
                .image-comparison {{ display: flex; gap: 10px; margin: 10px 0; }}
                .image-comparison img {{ max-width: 300px; border: 1px solid #ddd; }}
                .error {{ color: #d32f2f; font-weight: bold; }}
                .success {{ color: #4caf50; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Visual Regression Test Report</h1>

            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">Total Tests: {test_suite.summary['total_tests']}</div>
                <div class="metric">Passed: {test_suite.summary['passed_tests']}</div>
                <div class="metric">Failed: {test_suite.summary['failed_tests']}</div>
                <div class="metric">Threshold: {test_suite.threshold}</div>
                <div class="metric">Total Time: {test_suite.summary['total_time']:.2f}s</div>
            </div>

            <h2>Test Results</h2>
        """

        for result in test_suite.results:
            status_class = "passed" if result.passed else "failed"
            status_text = "PASS" if result.passed else "FAIL"

            html += f"""
            <div class="test-result {status_class}">
                <h3>{result.test_name} - <span class="{'success' if result.passed else 'error'}">{status_text}</span></h3>
                <p><strong>Pixel Difference:</strong> {result.pixel_difference:.4f} (Threshold: {test_suite.threshold})</p>
                <p><strong>Max Difference:</strong> {result.max_difference:.4f}</p>
                <p><strong>Duration:</strong> {result.test_duration:.2f}s</p>
            """

            if result.error_message:
                html += f"<p class='error'><strong>Error:</strong> {result.error_message}</p>"

            # Add image comparison if available
            if result.current_path and Path(result.current_path).exists():
                html += """
                <div class="image-comparison">
                    <div>
                        <strong>Baseline</strong><br>
                        <img src="{}" alt="Baseline">
                    </div>
                    <div>
                        <strong>Current</strong><br>
                        <img src="{}" alt="Current">
                    </div>
                    <div>
                        <strong>Differences</strong><br>
                        <img src="{}" alt="Differences">
                    </div>
                </div>
                """.format(
                    self._get_relative_path(result.baseline_path),
                    self._get_relative_path(result.current_path),
                    self._get_relative_path(result.difference_path)
                )

            html += "</div>"

        html += """
        </body>
        </html>
        """

        return html

    def _get_relative_path(self, path: str) -> str:
        """Get relative path from output directory."""
        if not path:
            return ""
        path_obj = Path(path)
        try:
            return str(path_obj.relative_to(self.output_dir))
        except ValueError:
            return path_obj.name


def create_test_components():
    """Create sample test components for demonstration."""

    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
    from PySide6.QtCore import Qt

    def create_main_window_test():
        """Create a test main window component."""
        class TestMainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Test Main Window")
                self.setGeometry(100, 100, 800, 600)

                # Create central widget
                central = QWidget()
                self.setCentralWidget(central)

                layout = QVBoxLayout(central)

                # Add test components
                title = QLabel("Visual Regression Test - Main Window")
                title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
                layout.addWidget(title)

                # Test buttons
                button_layout = QHBoxLayout()

                btn1 = QPushButton("Primary Button")
                btn1.setStyleSheet("""
                    QPushButton {
                        background-color: #1976D2;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1565C0;
                    }
                """)
                button_layout.addWidget(btn1)

                btn2 = QPushButton("Secondary Button")
                btn2.setStyleSheet("""
                    QPushButton {
                        background-color: #757575;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                    }
                """)
                button_layout.addWidget(btn2)

                layout.addLayout(button_layout)

                # Test frame
                frame = QFrame()
                frame.setFrameStyle(QFrame.Box)
                frame.setStyleSheet("""
                    QFrame {
                        background-color: #f5f5f5;
                        border: 2px solid #1976D2;
                        border-radius: 10px;
                        padding: 15px;
                    }
                """)

                frame_layout = QVBoxLayout(frame)
                frame_layout.addWidget(QLabel("Test Frame Content"))
                frame_layout.addWidget(QLabel("This tests frame styling"))

                layout.addWidget(frame)

        return TestMainWindow

    def create_dialog_test():
        """Create a test dialog component."""
        class TestDialog(QWidget):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Test Dialog")
                self.setGeometry(200, 200, 400, 300)

                layout = QVBoxLayout(self)

                # Dialog content
                title = QLabel("Test Dialog")
                title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
                layout.addWidget(title)

                # Form elements
                form_layout = QVBoxLayout()

                label1 = QLabel("Username:")
                input1 = QFrame()  # Simulate input field
                input1.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        padding: 5px;
                        min-height: 25px;
                    }
                """)
                form_layout.addWidget(label1)
                form_layout.addWidget(input1)

                label2 = QLabel("Password:")
                input2 = QFrame()  # Simulate input field
                input2.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        padding: 5px;
                        min-height: 25px;
                    }
                """)
                form_layout.addWidget(label2)
                form_layout.addWidget(input2)

                layout.addLayout(form_layout)

                # Dialog buttons
                button_layout = QHBoxLayout()

                ok_btn = QPushButton("OK")
                ok_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                button_layout.addWidget(ok_btn)

                cancel_btn = QPushButton("Cancel")
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                """)
                button_layout.addWidget(cancel_btn)

                layout.addLayout(button_layout)

        return TestDialog

    return {
        'main_window': create_main_window_test,
        'dialog': create_dialog_test
    }


def main():
    """Main entry point for visual regression testing."""

    parser = argparse.ArgumentParser(description='Visual Regression Testing Framework')
    parser.add_argument('--baseline', default='tests/baseline',
                       help='Directory containing baseline screenshots')
    parser.add_argument('--output', default='tests/visual_regression',
                       help='Directory for test output')
    parser.add_argument('--threshold', type=float, default=0.05,
                       help='Pixel difference threshold (0-1)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--generate-baselines', action='store_true',
                       help='Generate new baseline images')
    parser.add_argument('--components', nargs='*',
                       help='Specific components to test')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize tester
    tester = VisualRegressionTester(args.baseline, args.output, args.threshold)

    # Register sample test components
    test_components = create_test_components()
    for name, component_class in test_components.items():
        tester.register_component(name, component_class)

    if args.generate_baselines:
        # Generate baselines
        baselines = tester.generate_baselines(args.components)
        print(f"Generated {len(baselines)} baseline images:")
        for name, path in baselines.items():
            print(f"  {name}: {path}")

    else:
        # Run tests
        test_suite = tester.run_test_suite(args.components)

        # Generate report
        report_path = tester.generate_report(test_suite)

        # Print summary
        print(f"\n{'='*60}")
        print("VISUAL REGRESSION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total tests: {test_suite.summary['total_tests']}")
        print(f"Passed: {test_suite.summary['passed_tests']}")
        print(f"Failed: {test_suite.summary['failed_tests']}")
        print(f"Threshold: {test_suite.threshold}")
        print(f"Total time: {test_suite.summary['total_time']:.2f}s")
        print(f"Average time per test: {test_suite.summary['average_time_per_test']:.2f}s")

        if test_suite.summary['failed_tests'] > 0:
            print(f"\nFailed tests:")
            for result in test_suite.results:
                if not result.passed:
                    print(f"  - {result.test_name}: {result.pixel_difference:.4f} difference")

        print(f"\nReport: {report_path}")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()