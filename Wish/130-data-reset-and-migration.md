# 130 Data, Reset & Migration (Installer)

## 130.10 Objective
- Migrate existing tool databases/settings smoothly.
- Provide clear separation of installer components and guardrails for backups.

## 130.20 Implementation Steps

### 130.20.10 Import Existing Assets
1. Detect previous installs by scanning for `tools.db` and config folders.
2. Offer users the choice to reuse the existing DB or start fresh (with automatic backup of the old DB).

### 130.20.20 Post-Import Backup
1. After importing vendor libraries, prompt to snapshot the resulting `tools.db` as a “factory libraries” backup to simplify rollbacks.

### 130.20.30 Component Separation
1. Expose installer sections for:
   - Tool libraries/vendor payloads.
   - User settings/preferences.
   - Sample/project/example files.
2. Allow each section to be installed or upgraded independently when possible.
