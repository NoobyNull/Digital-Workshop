#!/usr/bin/env python3
"""
Migration Utilities for GUI Layout Refactoring

This module provides automated tools for migrating code from the legacy theme system
to the new qt-material-based UnifiedThemeManager system.

Usage:
    python tools/migration_utils.py [command] [options]

Commands:
    update-imports    Update import statements across the codebase
    migrate-styles    Convert hardcoded styles to qt-material
    validate-migration Validate migration completeness
    generate-report   Generate migration progress report

Options:
    --dry-run        Show what would be changed without making changes
    --backup         Create backup files before making changes
    --verbose        Enable verbose logging
    --files FILE     Process specific files (default: all files)
"""

import os
import re
import json
import shutil
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ImportMigration:
    """Information about an import migration."""

    file_path: str
    line_number: int
    old_import: str
    new_import: str
    migration_type: str  # 'theme_manager', 'colors', 'service'
    risk_level: str
    backup_content: str


@dataclass
class StyleMigration:
    """Information about a style migration."""

    file_path: str
    line_number: int
    old_stylesheet: str
    new_stylesheet: str
    migration_type: str
    hardcoded_colors: List[str]
    backup_content: str


@dataclass
class MigrationReport:
    """Complete migration report."""

    summary: Dict[str, Any]
    import_migrations: List[ImportMigration]
    style_migrations: List[StyleMigration]
    errors: List[str]
    warnings: List[str]


class CodeMigrator:
    """
    Automated code migration tool for theme system refactoring.
    """

    def __init__(
        self, root_path: str = "src", dry_run: bool = False, create_backups: bool = True
    ):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.create_backups = create_backups
        self.logger = logging.getLogger(__name__)

        # Import migration patterns
        self.import_patterns = {
            "theme_manager": [
                (
                    r"from\s+src\.gui\.theme\s+import\s+ThemeManager",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
                (
                    r"from\s+[\w.]+\s+import\s+.*ThemeManager",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
                (
                    r"import.*ThemeManager",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
            ],
            "legacy_colors": [
                (
                    r"from\s+src\.gui\.theme\s+import\s+COLORS",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
                (
                    r"from\s+[\w.]+\s+import\s+.*COLORS",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
            ],
            "theme_service": [
                (
                    r"from\s+src\.gui\.theme\s+import\s+ThemeService",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
                (
                    r"from\s+[\w.]+\s+import\s+.*ThemeService",
                    "from src.gui.theme import UnifiedThemeManager",
                ),
            ],
        }

        # Style migration patterns
        self.style_patterns = {
            "hardcoded_colors": re.compile(r"#[0-9a-fA-F]{6}"),
            "color_variables": re.compile(r"COLORS\.(\w+)"),
            "qt_properties": re.compile(r"Q[A-Z][A-Za-z]*\s*\{[^}]*\}"),
        }

        # Color mapping for migration
        self.color_mapping = {
            # Legacy color mappings to qt-material equivalents
            "primary": "primary",
            "secondary": "accent",
            "background": "background",
            "surface": "surface",
            "error": "error",
            "success": "success",
            "warning": "warning",
            "text": "text_primary",
            "text_secondary": "text_secondary",
        }

    def update_imports(self, files: List[str] = None) -> List[ImportMigration]:
        """
        Update import statements across the codebase.

        Args:
            files: List of specific files to process (None for all files)

        Returns:
            List of import migrations performed
        """
        if files is None:
            files = self._get_python_files()

        migrations = []

        for file_path in files:
            try:
                file_migrations = self._update_imports_in_file(file_path)
                migrations.extend(file_migrations)
            except Exception as e:
                self.logger.error(f"Failed to update imports in {file_path}: {e}")

        return migrations

    def migrate_styles(self, files: List[str] = None) -> List[StyleMigration]:
        """
        Convert hardcoded styles to qt-material.

        Args:
            files: List of specific files to process (None for all files)

        Returns:
            List of style migrations performed
        """
        if files is None:
            files = self._get_python_files()

        migrations = []

        for file_path in files:
            try:
                file_migrations = self._migrate_styles_in_file(file_path)
                migrations.extend(file_migrations)
            except Exception as e:
                self.logger.error(f"Failed to migrate styles in {file_path}: {e}")

        return migrations

    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate migration completeness.

        Returns:
            Validation report
        """
        validation = {
            "legacy_imports_remaining": [],
            "hardcoded_styles_remaining": [],
            "migration_completeness": 0.0,
            "recommendations": [],
        }

        files = self._get_python_files()

        for file_path in files:
            try:
                issues = self._validate_file_migration(file_path)
                validation["legacy_imports_remaining"].extend(issues["legacy_imports"])
                validation["hardcoded_styles_remaining"].extend(
                    issues["hardcoded_styles"]
                )
            except Exception as e:
                self.logger.error(f"Failed to validate {file_path}: {e}")

        # Calculate completeness
        total_issues = len(validation["legacy_imports_remaining"]) + len(
            validation["hardcoded_styles_remaining"]
        )
        if total_issues == 0:
            validation["migration_completeness"] = 100.0
        else:
            # Estimate based on remaining issues
            validation["migration_completeness"] = max(0, 100.0 - (total_issues * 2))

        # Generate recommendations
        validation["recommendations"] = self._generate_validation_recommendations(
            validation
        )

        return validation

    def _get_python_files(self) -> List[str]:
        """Get list of Python files to process."""
        files = []
        for py_file in self.root_path.rglob("*.py"):
            # Skip certain directories
            if any(
                part in ["__pycache__", ".git", "venv", "env", ".venv", ".env", "tests"]
                for part in py_file.parts
            ):
                continue
            files.append(str(py_file.relative_to(self.root_path)))
        return files

    def _update_imports_in_file(self, file_path: str) -> List[ImportMigration]:
        """Update import statements in a single file."""
        full_path = self.root_path / file_path
        migrations = []

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return migrations

        original_content = content
        lines = content.split("\n")

        # Process each import pattern
        for migration_type, patterns in self.import_patterns.items():
            for pattern, replacement in patterns:
                new_content, pattern_migrations = self._apply_import_pattern(
                    content, lines, pattern, replacement, migration_type, file_path
                )
                content = new_content
                migrations.extend(pattern_migrations)

        # Write changes if not dry run
        if content != original_content and not self.dry_run:
            if self.create_backups:
                self._create_backup(full_path, original_content)

            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"Updated imports in {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to write {file_path}: {e}")

        return migrations

    def _apply_import_pattern(
        self,
        content: str,
        lines: List[str],
        pattern: str,
        replacement: str,
        migration_type: str,
        file_path: str,
    ) -> Tuple[str, List[ImportMigration]]:
        """Apply a specific import pattern."""
        migrations = []
        regex = re.compile(pattern, re.MULTILINE)

        def replace_match(match):
            line_num = content[: match.start()].count("\n") + 1
            old_import = match.group(0)

            # Create migration record
            migration = ImportMigration(
                file_path=file_path,
                line_number=line_num,
                old_import=old_import.strip(),
                new_import=replacement,
                migration_type=migration_type,
                risk_level=self._assess_import_risk(migration_type),
                backup_content=content,
            )
            migrations.append(migration)

            return replacement

        new_content = regex.sub(replace_match, content)
        return new_content, migrations

    def _migrate_styles_in_file(self, file_path: str) -> List[StyleMigration]:
        """Migrate hardcoded styles in a single file."""
        full_path = self.root_path / file_path
        migrations = []

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return migrations

        original_content = content
        lines = content.split("\n")

        # Find setStyleSheet calls
        stylesheet_pattern = re.compile(
            r'(\.setStyleSheet\(["\'])([^"\']+)(["\'])', re.MULTILINE | re.DOTALL
        )

        def replace_stylesheet(match):
            prefix = match.group(1)
            stylesheet_content = match.group(2)
            suffix = match.group(3)

            line_num = content[: match.start()].count("\n") + 1

            # Analyze and migrate stylesheet
            new_stylesheet, migration = self._migrate_stylesheet_content(
                stylesheet_content, file_path, line_num, content
            )

            if migration:
                migrations.append(migration)

            return f"{prefix}{new_stylesheet}{suffix}"

        new_content = stylesheet_pattern.sub(replace_stylesheet, content)

        # Write changes if not dry run
        if new_content != original_content and not self.dry_run:
            if self.create_backups:
                self._create_backup(full_path, original_content)

            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.logger.info(f"Migrated styles in {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to write {file_path}: {e}")

        return migrations

    def _migrate_stylesheet_content(
        self, stylesheet: str, file_path: str, line_num: int, full_content: str
    ) -> Tuple[str, Optional[StyleMigration]]:
        """Migrate stylesheet content to qt-material."""

        # Find hardcoded colors
        hardcoded_colors = self.style_patterns["hardcoded_colors"].findall(stylesheet)

        # Check if already using variables
        if "COLORS." in stylesheet or "{" in stylesheet:
            return stylesheet, None  # Already migrated or using variables

        # Simple migration: replace common hardcoded colors
        new_stylesheet = stylesheet

        # Replace common hardcoded colors with theme variables
        color_replacements = {
            "#1976D2": "{primary}",  # Material blue
            "#2196F3": "{primary}",  # Lighter blue
            "#FFFFFF": "{background}",  # White background
            "#000000": "{text_primary}",  # Black text
            "#FF5722": "{accent}",  # Deep orange
            "#4CAF50": "{success}",  # Green
            "#F44336": "{error}",  # Red
            "#FF9800": "{warning}",  # Orange
        }

        for old_color, new_var in color_replacements.items():
            if old_color in new_stylesheet:
                new_stylesheet = new_stylesheet.replace(old_color, new_var)

        # Only create migration if changes were made
        if new_stylesheet != stylesheet:
            return new_stylesheet, StyleMigration(
                file_path=file_path,
                line_number=line_num,
                old_stylesheet=stylesheet,
                new_stylesheet=new_stylesheet,
                migration_type="color_replacement",
                hardcoded_colors=hardcoded_colors,
                backup_content=full_content,
            )

        return stylesheet, None

    def _validate_file_migration(self, file_path: str) -> Dict[str, List[str]]:
        """Validate migration completeness for a single file."""
        full_path = self.root_path / file_path

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {"legacy_imports": [], "hardcoded_styles": []}

        issues = {"legacy_imports": [], "hardcoded_styles": []}

        # Check for legacy imports
        for migration_type, patterns in self.import_patterns.items():
            for pattern, _ in patterns:
                if re.search(pattern, content):
                    issues["legacy_imports"].append(f"{file_path}: {migration_type}")

        # Check for hardcoded styles in setStyleSheet calls
        stylesheet_calls = re.findall(
            r'\.setStyleSheet\(["\']([^"\']+)["\']', content, re.MULTILINE | re.DOTALL
        )
        for call in stylesheet_calls:
            hardcoded_colors = self.style_patterns["hardcoded_colors"].findall(call)
            if hardcoded_colors and "COLORS." not in call and "{" not in call:
                issues["hardcoded_styles"].append(
                    f"{file_path}: {len(hardcoded_colors)} hardcoded colors"
                )

        return issues

    def _assess_import_risk(self, migration_type: str) -> str:
        """Assess risk level of import migration."""
        risk_levels = {
            "theme_manager": "high",
            "legacy_colors": "medium",
            "theme_service": "medium",
        }
        return risk_levels.get(migration_type, "low")

    def _create_backup(self, file_path: Path, content: str) -> None:
        """Create backup of file before modification."""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.migration_backup")

        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")

    def _generate_validation_recommendations(
        self, validation: Dict[str, Any]
    ) -> List[str]:
        """Generate validation recommendations."""
        recommendations = []

        if validation["legacy_imports_remaining"]:
            recommendations.append(
                f"Migrate {len(validation['legacy_imports_remaining'])} remaining legacy imports"
            )

        if validation["hardcoded_styles_remaining"]:
            recommendations.append(
                f"Convert {len(validation['hardcoded_styles_remaining'])} remaining hardcoded styles"
            )

        if validation["migration_completeness"] < 100:
            recommendations.append(
                f"Complete migration to achieve {100 - validation['migration_completeness']:.1f}% completeness"
            )

        recommendations.extend(
            [
                "Test all migrated components for visual consistency",
                "Update documentation to reflect new import patterns",
                "Consider removing legacy compatibility layer after migration",
                "Run visual regression tests to ensure UI consistency",
            ]
        )

        return recommendations

    def generate_report(
        self,
        import_migrations: List[ImportMigration] = None,
        style_migrations: List[StyleMigration] = None,
    ) -> MigrationReport:
        """
        Generate comprehensive migration report.

        Args:
            import_migrations: Import migrations performed
            style_migrations: Style migrations performed

        Returns:
            Complete migration report
        """
        if import_migrations is None:
            import_migrations = self.update_imports()

        if style_migrations is None:
            style_migrations = self.migrate_styles()

        validation = self.validate_migration()

        summary = {
            "total_import_migrations": len(import_migrations),
            "total_style_migrations": len(style_migrations),
            "migration_completeness": validation["migration_completeness"],
            "legacy_imports_remaining": len(validation["legacy_imports_remaining"]),
            "hardcoded_styles_remaining": len(validation["hardcoded_styles_remaining"]),
            "dry_run": self.dry_run,
            "backups_created": self.create_backups,
        }

        errors = []
        warnings = []

        # Check for potential issues
        if summary["legacy_imports_remaining"] > 0:
            warnings.append(
                f"{summary['legacy_imports_remaining']} legacy imports still need migration"
            )

        if summary["hardcoded_styles_remaining"] > 0:
            warnings.append(
                f"{summary['hardcoded_styles_remaining']} hardcoded styles still need migration"
            )

        return MigrationReport(
            summary=summary,
            import_migrations=import_migrations,
            style_migrations=style_migrations,
            errors=errors,
            warnings=warnings,
        )


def main():
    """Main entry point for migration utilities."""

    parser = argparse.ArgumentParser(
        description="Migration Utilities for Theme Refactoring"
    )
    parser.add_argument(
        "command",
        choices=[
            "update-imports",
            "migrate-styles",
            "validate-migration",
            "generate-report",
        ],
        help="Migration command to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup files before making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--files", nargs="*", help="Specific files to process (default: all files)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="migration_report.json",
        help="Output file for reports",
    )
    parser.add_argument(
        "--root-path", default="src", help="Root path to process (default: src)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Initialize migrator
    migrator = CodeMigrator(args.root_path, args.dry_run, args.backup)

    # Execute command
    if args.command == "update-imports":
        migrations = migrator.update_imports(args.files)
        print(f"Updated imports in {len(migrations)} locations")

    elif args.command == "migrate-styles":
        migrations = migrator.migrate_styles(args.files)
        print(f"Migrated styles in {len(migrations)} locations")

    elif args.command == "validate-migration":
        validation = migrator.validate_migration()
        print(f"Migration completeness: {validation['migration_completeness']:.1f}%")
        print(
            f"Legacy imports remaining: {len(validation['legacy_imports_remaining'])}"
        )
        print(
            f"Hardcoded styles remaining: {len(validation['hardcoded_styles_remaining'])}"
        )

    elif args.command == "generate-report":
        report = migrator.generate_report()

        # Output report
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        print(f"\n{'='*60}")
        print("MIGRATION REPORT")
        print(f"{'='*60}")
        print(f"Import migrations: {report.summary['total_import_migrations']}")
        print(f"Style migrations: {report.summary['total_style_migrations']}")
        print(
            f"Migration completeness: {report.summary['migration_completeness']:.1f}%"
        )
        print(f"Legacy imports remaining: {report.summary['legacy_imports_remaining']}")
        print(
            f"Hardcoded styles remaining: {report.summary['hardcoded_styles_remaining']}"
        )

        if report.warnings:
            print(f"\nWarnings:")
            for warning in report.warnings:
                print(f"  - {warning}")

        print(f"\nReport saved to: {args.output}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
