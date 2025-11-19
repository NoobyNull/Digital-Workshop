# 020 G-code Tools Cleanup & Enhancements

## 020.10 Objective
- Modernize the G-code Tools dock so users can load, analyze, edit, and save toolpaths with a clean workflow tied to active projects.

## 020.20 Implementation Steps

### 020.20.10 Dock Layout
1. Replace the monolithic widget with a tabbed interface inside the dock:
   - Loader & Timeline (file import, simulation controls, metrics).
   - Editor (full G-code editing experience).
   - Tool Snapshots (structured list of captured parameters).
2. Preserve wiring to G-code previewer signals but route actions through explicit slots per tab.

### 020.20.20 Editor Improvements
1. Integrate syntax highlighting for motion/spindle/comment tokens.
2. Add incremental search, regex replace, and “replace all”.
3. Implement bi-directional linking with the preview:
   - Selecting a line highlights the corresponding move.
   - Clicking the preview moves the editor caret.
4. Provide checkboxes to filter/grey out rapids, arcs, canned cycles.
5. “Save to Project…” button:
   - Default path `<project>/gcode/` when a project is active; otherwise prompt.
   - After save, call `db_manager.add_file` to link the file.
6. (Optional) Diff view that compares edited vs. original.

### 020.20.30 Tool Snapshot Panel
1. Display columns: Tool #, Diameter, Material, Feed, Plunge, Notes.
2. Buttons:
   - “Add from Editor” to capture current settings.
   - “Export CSV” / “Import CSV”.
3. Keep using the `gcode_tool_snapshots` table for persistence.

### 020.20.40 Loader & Timeline Polish
1. Reorganize metrics summary (runtime, distance, feed overrides) into a compact card.
2. Add “Open Containing Folder” and “Reload” actions near the loader.
3. Show whether the current file is linked to a project (display project name).

### 020.20.50 Integration Hooks
1. Editor must honor project paths and permissions.
2. Tool snapshots should be keyed to G-code version IDs when available.
3. Log edits, saves, and exports at INFO level for auditability.

## 020.30 Non-Functional Considerations
1. Dark/light theme compatibility across all sub-tabs.
2. Large files (>10 MB) must stream without freezing the UI (use worker threads or chunked readers).
3. Testing:
   - Unit tests for save-to-project flow.
   - Snapshot export/import round-trip tests.
