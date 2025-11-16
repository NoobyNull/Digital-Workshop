# Digital Workshop Installer Wishlist

## 1. Tool Libraries / Feeds & Speeds
- Bundled tool library selection screen:
  - Show all discovered libraries in `resources/ToolLib` (or installer payload): IDC Woodcraft, Amana, PDXCNC/ZahyoX, and any other vendor JSON/CSV/VTDB/TDB.
  - Checkboxes per library: "Import this vendor library into my tools database".
  - "Select All" / "Deselect All" control.
- Format support hints:
  - If `.tool` files are present, clearly state that Vectric/Amana `.tool` libraries cannot be imported directly.
  - Suggest exporting to VTDB/TDB/CSV/JSON from Vectric and importing those instead.
- Unit preferences on first run:
  - Ask for default units: Imperial / Metric / Auto-detect per tool.
  - Wire this to the existing Feeds & Speeds unit/auto-convert settings.
- Default "My Tools" structure:
  - Option to create starter folders (e.g. `End Mills`, `Drills`, `Ballnose`, `Surfacing`).
  - Option to skip and let the user organize manually.
- Initial tool DB location/profile:
  - Allow choosing a non-default location for `tools.db` (e.g., network/synced folder).

## 2. Application Configuration & Profiles
- Profile type selection:
  - "Single-user workstation" vs. "Shared shop computer".
  - Adjusts where config/state is stored and how shortcuts are created.
- Initial logging settings:
  - Checkboxes: log to file, log to console, log human-readable (`--log-human` implies `--log-console`).
  - Default log level selection (INFO/DEBUG/WARN).
- NUKE reset convenience:
  - Optional desktop/start menu shortcut: "Digital Workshop – Reset (NUKE)".
  - Runs the NUKE CLI with 5-second any-key-to-cancel confirmation.

## 3. CLI / Advanced User Options
- Register CLI entry point:
  - Optionally add a `digital-workshop` (or similar) command to PATH.
  - Toggle for developer-only shortcuts vs. keeping PATH clean.
- Preset CLI flags:
  - Installer "Advanced" page to choose default CLI flags:
    - `--log-human` (implies `--log-console`).
    - Default log level, etc.
  - Optionally generate a launcher script/batch file with these flags baked in.

## 4. Data & Reset / Migration
- Import existing tools from older installs:
  - Detect existing `tools.db` / settings from previous versions.
  - Offer: reuse existing DB, or start clean and back up the old DB.
- Backup after first vendor import:
  - Option to snapshot the initial post-import `tools.db` as a "factory libraries" backup for easy rollback.
- Separation of components:
  - Installer sections for tool libraries, user settings/preferences, and sample/example files.

## 5. OS Integration / Shortcuts
- Start menu / desktop shortcuts:
  - Main application launcher.
  - Optional specialized launchers, e.g. "Digital Workshop – Feeds & Speeds" layout.
  - Optional "Digital Workshop – Reset (NUKE)" entry.
- Future file associations:
  - For any custom project file types (e.g. `*.dwproj`), register open-with and context menu entries.

## 6. Diagnostics & Support
- Diagnostics toggle:
  - Opt-in option to enable more verbose logging and a known log directory (e.g. `~/DigitalWorkshop/logs`).
- Self-test after install:
  - Optional quick self-test:
    - Import small dummy library.
    - Instantiate Qt app + main window + core dock layout.
    - Verify tool DB schema and basic functionality.

