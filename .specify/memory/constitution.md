<!-- Sync Impact Report -->
<!-- Version Change: v1.0.0 → v1.1.0 -->
<!-- Removed: Legacy frame rate requirements, complex performance checks, detailed hardware specs -->
<!-- Simplified: Performance Mandate, Performance Standards, System Requirements, Quality Assurance -->
<!-- Focus: Core principles with practical, straightforward requirements -->
<!-- Governance: Amendment procedures and versioning policy retained -->

# Digital Workshop Constitution
<!-- Formerly 3D-MM: 3D Model Management and Visualization Application -->

## Core Principles

### I. Performance Mandate
Performance drives architectural decisions with practical, achievable goals. The UI must remain responsive during file loading and model interaction. Basic load time targets are established: files under 100MB should load in under 5 seconds. Memory usage must remain under 2GB during typical operations.

### II. Modular Architecture
Each module implements single responsibility principle with clean, documented interfaces. Parser modules operate independently for STL, OBJ, STEP, and 3MF formats. GUI components remain decoupled from business logic through service layers. Database operations flow through facade patterns preventing direct SQL exposure. Theme system operates as pluggable service with consistent API contracts. All modules must be independently testable and documented. Dependencies flow one direction to prevent circular references. Interface changes require version updates and deprecation notices.

### III. Quality Assurance
Basic logging at appropriate levels helps track operations and issues. Simple testing covers key functionality with unit tests for parsers and integration tests for workflows. Documentation exists for public functions and key modules. Code passes basic linting checks. Error handling provides useful messages and logging for debugging. Focus on practical quality measures without complex benchmarking or extensive iteration requirements.

### IV. User Sovereignty
Application operates entirely offline with no remote execution or data transmission. All user data remains local under user control with SQLite database management. No telemetry, analytics, or external communication permitted. User preferences, model libraries, and metadata stored locally with export/import capabilities. Privacy by design: no user behavior tracking or personal data collection. Local file system access follows Windows desktop conventions. User maintains complete control over application behavior, themes, and data management.

### V. Windows Integration
The application is designed for modern Windows systems, adhering to standard desktop conventions.

## System Requirements
The application requires a modern Windows operating system and standard hardware capable of running modern desktop applications.

## Governance
<!-- Amendment procedures, versioning policy, and compliance requirements -->

Constitution supersedes all other practices and development guidelines. Amendments require written proposals with rationale, impact analysis, and migration plans. Versioning follows semantic versioning: MAJOR.MINOR.PATCH format with backwards compatibility guarantees for MINOR and PATCH releases. Breaking changes require MAJOR version increments with 90-day deprecation warnings. Compliance review mandatory for all changes affecting performance, architecture, or user experience. All pull requests must verify constitution compliance with complexity justifications required for deviations. Feature flags required for experimental implementations with logging of toggle changes. Atomic commits enforce single logical changes per commit with descriptive messages referencing affected files.

**Version**: 1.1.0 | **Ratified**: 2025-10-30 | **Last Amended**: 2025-10-30
