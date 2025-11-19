# 030 Feeds & Speeds Overhaul (“My Tools” Ecosystem)

## 030.10 Objective
- Turn the Feeds & Speeds tab into a complete tooling environment featuring a Vectric-style table, intelligent material data, dual runtime estimates, and tight integration with projects, G-code, and cost analysis.

## 030.20 Implementation Steps

### 030.20.10 Build the “My Tools” UI
1. Create a split view:
   - Left tree lists folders (End Mills, Drills, Ballnose, Surfacing, user-defined).
   - Right pane contains a detailed editor for the selected tool (geometry, flutes, coatings, chip-load curves, default materials).
2. Enable drag-and-drop to rearrange tools/folders, mirroring Project Manager behavior.
3. Add an “Add to Project Toolbox” button that copies the tool definition to `<project>/tools/tool_<id>.json`.

### 030.20.20 Material Intelligence
1. Seed a material database with Janka hardness, chip-load multipliers, and max spindle RPM recommendations.
2. Allow custom materials stored in `<project>/tools/materials.json`.
3. When a material is chosen, auto-calculate baseline feed/spindle overrides and display them in the editor.

### 030.20.30 Runtime Estimation Modes
1. Quick Estimate: heuristic runtime with no kinematics.
2. Full Kinematics: call the existing G-code timing analyzer for precise results.
3. Display both numbers and the delta so quoting/cost tools can interpret the spread.

### 030.20.40 Apply Tooling to G-code
1. Provide “Apply Tool to G-code”:
   - Updates `gcode_tool_snapshots`.
   - Optionally rewrites feed/spindle commands (preview before commit).
2. When a G-code version has applied tooling, annotate the G-code Tools pane with tool/material metadata.

### 030.20.50 Data Persistence & Sharing
1. Keep the master library in `tools.db`.
2. Store project-specific copies under `<project>/tools/`.
3. Offer import/export (JSON/CSV) so users can move tool profiles between machines.

### 030.20.60 Cost Estimator Integration
1. Surface an API for Cost Estimator to fetch per-tool wear costs, consumable charges, and chosen materials.
2. Add a “Wear Cost per Hour” field to each tool record; Cost Estimator converts it into invoice line items automatically.

## 030.30 Non-Functional Considerations
1. UI must remain responsive with hundreds of tools (lazy loading or virtualization).
2. Include undo/redo for tool edits.
3. Automated tests:
   - Quick vs. kinematic runtime comparison.
   - Drag/drop persistence.
   - Project export/import round trips.
