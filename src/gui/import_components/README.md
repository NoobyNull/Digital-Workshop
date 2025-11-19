# Import Components Package

Source: `src/gui/import_components/`  
This package contains the UI+threading glue that powers Digital Workshop’s multi-file import workflow.

---

## Components

| Name | File | Role |
| --- | --- | --- |
| `ImportDialog` | `import_dialog.py` | Rich PySide6 dialog that orchestrates file selection, validation, progress, and result summaries. |
| `ImportWorker` | `import_worker.py` (spawned inside `import_dialog.py`) | Runs the import pipeline on a background thread so the UI stays responsive. |
| `ImportFileManager` bridge | `import_dialog.py` → `src/core/import_file_manager.py` | Validates files, deduplicates with FastHasher, copies/links into managed storage. |
| `ImportThumbnailService` | `src/core/services/import_thumbnail_service.py` | Generates VTK thumbnails off the GUI thread. |
| `ImportAnalysisService` | `src/core/services/import_analysis_service.py` | Computes geometry metrics + insights. |

---

## User Flow

1. User launches `ImportDialog` (from toolbar/menu).
2. Files drop in via drag/drop or file picker.
3. Options selected (Keep Organized vs Leave in Place, background analysis, etc.).
4. Dialog spawns `ImportWorker` (`QThread`), hands it a serialized job.
5. Worker runs the pipeline, emitting stage + file progress.
6. Dialog surfaces live progress, errors, and the final `ImportResult`.
7. On completion, project tree updates automatically via the event bus.

---

## API Snapshot

```python
from src.gui.import_components import ImportDialog

dialog = ImportDialog(parent=main_window)
dialog.set_project_context(project_id=current_project.id)

if dialog.exec() == dialog.Accepted:
    result = dialog.get_import_result()
    print(result.processed_files, result.failures)
```

- `set_project_context` ensures “Keep Organized” knows where to copy files.
- `get_import_result()` returns counts, warnings, errors, and a list of `ImportSessionItem` objects for analytics.

---

## Progress Model

Import stages run sequentially; the worker emits `(stage, percent, file_name)`:

1. **Validation** – format detection, file-access checks.
2. **Hashing** – `FastHasher` dedup + naming.
3. **Copy/Link** – copy to managed storage or register “leave in place”.
4. **Thumbnails** – `ImportThumbnailService` offscreen renders.
5. **Analysis** – optional, controlled via checkbox.

Each stage writes structured logs so `logs/import/*.jsonl` can be replayed.

---

## Error Handling

- Permission denials and missing files are downgraded to warnings (import continues).
- Hashing, thumbnail, and analysis exceptions are logged per file; the worker never crashes the thread.
- Fatal errors surface in the dialog header with remediation hints.
- A cancellation token stops the worker within the current chunk so the dialog unlocks quickly.

---

## Testing

| Test | Coverage |
| --- | --- |
| `tests/test_import_file_manager.py` | Validation, dedup, storage policies. |
| `tests/test_import_thumbnail_service.py` | Thumbnail generation and cache behavior. |
| `tests/test_import_analysis_service.py` | Geometry metrics and background processing. |
| `tests/test_import_settings.py` | User preference handling (Keep Organized roots, toggles). |

Manual smoke: run the app, import a mix of STL/OBJ/STEP files, toggle background analysis, and verify Project Manager receives the new entries instantly.

---

## Extending

1. Add new options to `ImportDialog` ➜ wire them into the job payload.
2. Update `ImportWorker` to consume the option and notify downstream services.
3. Register any new telemetry fields inside `src/core/import_pipeline/pipeline_coordinator.py`.
4. Extend `tests/test_import_*` to cover the new branch.
5. Document the feature in `docs/features/import_pipeline/*.md`.

---

**Owner:** Import Platform (`imports@digitalworkshop.app`)  
**Status:** Production (Beta customers exercise it daily)
