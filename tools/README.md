# Developer Tooling Index

This folder contains the curated utilities that keep the Digital Workshop Beta shippable.  
Everything here is safe to run locally and inside CI when prepping the GitHub mirror.

---

## Active Toolchain

| Script | Purpose | Typical Command |
| --- | --- | --- |
| `dependency_analysis.py` | Maps ThemeManager/UI dependencies and surfaces hardcoded style risks. | `python tools/dependency_analysis.py --root-path src/gui` |
| `migration_utils.py` | Applies the “Unified Theme” migration (imports, stylesheet conversions, validation). | `python tools/migration_utils.py migrate-styles --backup` |
| `visual_regression_tester.py` | Captures baseline screenshots and flags pixel deltas for PySide6 components. | `python tools/visual_regression_tester.py --generate-baselines` |
| `run_phase0_analysis.py` | Orchestrates the three tools above and emits a consolidated report (JSON/HTML). | `python tools/run_phase0_analysis.py --format html --output reports/gui_migration.html` |
| `quality/` utilities | Generates comprehensive QA digests (see `tools/quality/comprehensive_quality_report.py`). | `python tools/quality/comprehensive_quality_report.py --output reports/quality.json` |

### Workflow Template
```bash
# 1. Understand risk before touching UI code
python tools/dependency_analysis.py --format markdown --output reports/dependency.md

# 2. Apply targeted migrations (imports/styles) with automatic backups
python tools/migration_utils.py update-imports --dry-run
python tools/migration_utils.py migrate-styles --backup

# 3. Validate visuals before committing
python tools/visual_regression_tester.py --components main_window toolbar dock_widgets
```

---

## Legacy / Reference Utilities

Some helpers pre-date the Beta refresh. They remain for forensic work but are **not** part of the shipping workflow:

- `stylesheet_detector.py` – superseded by `dependency_analysis.py`. Keep it around when you need a pure `setStyleSheet()` grep with zero setup.
- `maintenance/monolithic_detector.py` – used once during the layout split; reference-only.
- `demos/*.py` – miniature sandbox scripts demonstrating the exception/logging stack.
- `debug/`, `exceptions/`, `security/` – kept for explorers who want deep dives; see in-file docstrings for usage.

> ✅ If you are cutting a release, you only need the “Active Toolchain” above.

---

## CI / Automation Notes

```yaml
- name: Dependency Map
  run: python tools/dependency_analysis.py --format json --output reports/dependency.json

- name: Verify Migration Completeness
  run: python tools/migration_utils.py validate-migration

- name: Visual Regression (critical widgets)
  run: python tools/visual_regression_tester.py --components main_window import_dialog --threshold 0.02
```

Reports land in `reports/` so GitLab *and* GitHub pipelines can publish them as downloadable artifacts.

---

## Support

Questions? Reach the UI Platform team at `ui-platform@digitalworkshop.app`. When proposing a new helper:
1. Match the CLI style shown above.
2. Emit machine-readable output (JSON/HTML) alongside human-readable text.
3. Update this README so future maintainers know whether the tool is “Active” or “Reference”.
