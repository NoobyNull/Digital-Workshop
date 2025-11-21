# Digital Workshop (Beta)

Digital Workshop is a desktop workflow environment for CNC-oriented studios.  
It unifies photo-real previews, project-scoped asset management, G-code review, and revenue-facing tooling (quoting, invoicing, feeds & speeds) under a single PySide6 application.

## Why It Matters
- **Import intelligence** – FastHasher-powered deduplication, metadata extraction, and thumbnailing keep huge model libraries searchable.
- **Project hub** – Every feature (tab data, cost estimator, G-code edits, tool libraries) persists directly inside the active project to keep teams audit-proof.
- **Operational guardrails** – Built-in analyzers, linters, and 350+ automated tests secure the Beta without slowing execution.

## Quick Start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pip install -r requirements-dev.txt   # optional QA helpers
python src/main.py
```

### Build & Ship
- `python scripts/easy_build.py quick` - local smoke build (no tests).
- `python scripts/easy_build.py full` - run tests + build artifacts (mirrors CI).
- Build numbers follow GitLab/GitHub pipeline IID -> `Digital Workshop.XXXXX.exe`.

### Release Push (develop → main)
- `python scripts/auto_release_push.py --version 0.1.6` - pushes `develop`, fast-forwards `main`, creates an annotated tag `v0.1.6` with recent commit summaries, and pushes both branch and tag so CI can build the Windows EXE. Run on a clean tree.

### Test Coverage
```bash
pytest -m "not slow"          # fast feedback
pytest tests/unit             # core logic
pytest tests/integration      # GUI + pipeline coverage
```

## Project Layout
| Path | Purpose |
| --- | --- |
| `src/core/` | Import pipeline, services (FastHasher, TabDataManager, etc.). |
| `src/gui/` | PySide6 interface: MainWindow, import dialogs, project tools. |
| `src/resources/` | Icons, themes, metadata used at runtime/build time. |
| `scripts/` | Repeatable automation: builds, changelog, CI bootstrap. |
| `tests/` | 350+ unit/integration/visual validation assets. |
| `tools/` | Developer utilities (dependency analysis, migration tooling, visual regression). |
| `docs/` | Living documentation index (see `docs/README.md`). |
| `Wish/` | Active product wishlists/specs still in scope for Beta. |

## Key Documents
- `docs/README.md` – documentation hub + pointers by audience.
- `docs/FEATURES_GUIDE.md` – walk-through of every shipping capability.
- `docs/SYSTEM_ARCHITECTURE.md` – services, threading model, dependency graph.
- `build_system/README.md` - CI build number + artifact lifecycle.

## Contributing
1. Create/activate a virtual environment.
2. Run `python scripts/easy_build.py setup` once for local tooling.
3. Use feature branches + conventional commits (`feat:`, `fix:`, etc.).
4. Add/extend tests and docs alongside the implementation.
5. Open a Merge Request/PR with screenshots for UI changes.

## License
Commercial license – contact `team@digitalworkshop.app` for evaluation builds or enterprise terms.
