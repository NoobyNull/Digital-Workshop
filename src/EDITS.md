# Developer Notes and Incomplete Work Inventory

This filtered inventory keeps only developer-facing notes that still represent incomplete functionality or missing behavior. Purely documentary placeholders and noisy comment references have been removed so the list highlights legitimate TODO work that affects runtime features.

Legend:
- **[FUNC]** – Functional gap or feature not yet implemented / explicit TODO about behavior.

## 1. Source Code (`src/`)

### 1.1 Core services and infrastructure
- **src/core/import_analysis_service.py** – [FUNC] TODO at line 470: "Add support for OBJ, STEP, 3MF, etc."; [FUNC] TODO at line 908: "Implement database storage when model_analysis table is created."
- **src/core/import_coordinator.py** – [FUNC] TODO at line 462: "Implement actual database storage."
- **src/core/services/image_pairing_service.py** – [FUNC] TODO at line 228: "Could add PIL/Pillow validation to check if image is actually readable."

### 1.2 GUI: general widgets and services
- **src/gui/layout/snapping/snap_engine.py** – [FUNC] TODO at line 332: "Implement signal connections when configuration change signals are available."
- **src/gui/main_window.py** – [FUNC] TODOs at lines 1667–1668: "Add material roughness/metallic sliders in picker" and "Add export material presets feature."
- **src/gui/project_details_widget.py** – [FUNC] TODO at line 216: "Add support for related files (textures, materials, etc.)."
- **src/gui/thumbnail_generation_coordinator.py** – [FUNC] TODOs at lines 163, 169: "Implement pause in worker" and "Implement resume in worker."

### 1.3 GUI: VTK diagnostics and detection stubs
- **src/gui/vtk/diagnostic_tools.py** – [FUNC] return-value stubs indicating unimplemented detection logic:
  - Line 184: "OpenGL version detection not implemented".
  - Line 192: "Extension detection not implemented".
  - Line 265: "DirectX version detection not implemented".
  - Line 273: "WGL extension detection not implemented".
  - Line 289: "GLX extension detection not implemented".
