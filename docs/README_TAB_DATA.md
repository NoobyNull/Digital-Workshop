# Tab Data Persistence Service

The Tab Data service guarantees that every high-value workspace (Cut List Optimizer, Feeds & Speeds, Cost Estimator, Viewer snapshots, etc.) saves into the active project automatically.  
This document explains how it works today so feature owners can extend it without re-learning the internals.

---

## System Overview

| Component | Location | Responsibility |
| --- | --- | --- |
| `TabDataManager` | `src/core/services/tab_data_manager.py` | Central API for saving/loading per-tab payloads and linking those files to the project database. |
| Import tabs | `src/gui/CLO/*`, `src/gui/feeds_and_speeds/*`, `src/gui/cost_estimator/*` | Capture UI state → call `set_current_project`, `save_to_project`, `load_from_project`. |
| Project awareness | `src/gui/main_window.py::_on_project_opened` | Propagates the active `project_id` to every tab instance. |
| Export/Import bridge | `src/core/export/dww_export_manager.py` | Includes tab data assets when packaging a `.dww` archive. |
| Verification | `tests/test_dww_export_import.py` | Confirms that all tabs persist data and that exports include the files. |

---

## Project Files

```
<project>/
├── tab_data/
│   ├── cut_list/cut_list.json
│   ├── feeds_and_speeds/feeds_and_speeds.json
│   ├── cost_estimator/invoices/invoice-*.xml
│   └── metadata.json   # internal timestamps + db link references
└── …
```

- JSON/XML payloads always live under `tab_data` so exports/imports can glob them easily.
- When a file is created the manager calls `db_manager.add_file(...)` to make it discoverable inside Project Manager.

---

## Payload Shapes

```jsonc
// cut_list/cut_list.json
{
  "project_id": "9c3a…",
  "saved_at": "2025-11-18T19:02:33Z",
  "active_material": "Maple",
  "parts": [
    {"name": "Side Panel", "qty": 2, "width": 12.0, "length": 30.5},
    {"name": "Drawer Front", "qty": 4, "width": 6.0, "length": 18.0}
  ]
}

// feeds_and_speeds/feeds_and_speeds.json
{
  "project_id": "9c3a…",
  "saved_at": "2025-11-18T19:03:11Z",
  "tool_id": "TOOL-182",
  "material": "6061 Aluminum",
  "chipload": {"rough": 0.007, "finish": 0.003},
  "rpm": 18000,
  "feed": 2200,
  "plunge": 600,
  "notes": "Use mist coolant profile B"
}
```

Cost Estimator persists printable invoices (`invoice-YYYYMMDD-HHMM.xml`) and regenerates PDFs on demand.  
Any tab can store arbitrary data as long as it includes `project_id` and an ISO timestamp; TabDataManager enforces that contract.

---

## Typical Workflow

1. **Project opened** ➜ `MainWindow` emits `_on_project_opened`.
2. **Tab receives ID** ➜ Each widget calls `TabDataManager.set_current_project(project_id)`.
3. **User edits data** ➜ UI keeps everything in memory until the user clicks “Save to Project”.
4. **Persist** ➜ `TabDataManager.save_data(tab_name, payload, relative_path)` writes the file, links it in the DB, and logs to `activity`.
5. **Discover & reload** ➜ “Load from Project” populates the dialog/grid by calling `load_data(tab_name)`.
6. **Project Manager integration** ➜ Linked files show up immediately under the project tree with friendly labels.

Failure handling:
- Missing permissions ➜ surfaces an activity log error and returns `TabDataResult(success=False, message=...)`.
- Corrupt JSON ➜ raises `TabDataValidationError`; callers show a toast and keep the user’s in-memory state untouched.

---

## Testing & Validation

- `pytest tests/test_dww_export_import.py -k tab_data` – verifies save/load + export packaging.
- Widget-specific smoke tests (e.g., `tests/test_import_file_manager.py`) ensure project linking survives regression fixes.
- Manual smoke: open any project → use “Save to Project” in Cut List, Feeds & Speeds, and Cost Estimator → confirm files/materialized nodes appear in Project Manager.

---

## Extending the Service

1. Inject `TabDataManager` into your widget (follow the pattern in `feeds_and_speeds_widget.py`).
2. Call `set_current_project(project_id)` whenever `_on_project_opened` fires.
3. Define a serializer (`to_payload_dict`) and deserializer (`load_from_payload`).
4. Register a relative storage path under `tab_data/<your_tab>/`.
5. Add fixtures/tests so `tests/test_dww_export_import.py` can assert that your tab exports correctly.
6. Update this README and `docs/features/...` with the new tab details.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Save button disabled | Tab has not received `set_current_project` – ensure `project_opened` signal is connected. |
| File exists but not in Project Manager | Run `db_manager.add_file(...)` after saving; TabDataManager handles this automatically if you use `save_data`. |
| Import fails to load tab payload | Confirm the JSON schema version; upgrade logic should live beside your widget. |
| Export missing tab data | Ensure `dww_export_manager` includes your tab folder inside `TAB_DATA_DIRECTORIES`. |

---

**Owner:** Data & Workflow team (`workflow@digitalworkshop.app`)  
**Status:** Production-ready, shipping in Beta builds (mirrors GitLab + GitHub)
