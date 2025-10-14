📘 Project Context: 3D Model Library Manager

🧭 Purpose

To build a Windows-native, SQLite-backed 3D Model Library Manager that ingests, catalogs, and inspects 3D assets across prioritized formats (STL, 3MF, OBJ, STEP). The system provides input sovereignty, production-grade logging, and modular architecture for creators, curators, and engineers who demand clarity, reproducibility, and control.

🧰 Tech Stack

Frontend: PySide5 (Windows shell), Three.js (preview viewer embedded)

Backend: Python (Kivy3D for high-fidelity inspection), SQLite (metadata store)

Utilities: Git (version control), OpenGL (inspection engine)

🧾 Project Conventions

✍️ Code Style

Python: PEP8 with enforced type hints via mypy

JavaScript/TypeScript: ESLint + Prettier, camelCase for variables, PascalCase for components

Naming: Format-prefixed filenames (e.g., model_OBJ_parser.py, viewer_STEP_inspector.ts)

Comments: Docstrings for every function; inline comments only for non-obvious logic

🏗️ Architecture Patterns

Modular Subsystems: Parser, viewer, logger, and database are independently testable

Dual-Engine Viewer: Lightweight preview via Three.js, high-fidelity inspection via OpenGL/Kivy3D

Security: Capability-based isolation

Logging: Rotating logs with timestamped actions and rollback hooks

Deployment: Packaged as a Windows desktop application only — no server, no containerization

UI Style: Modern Windows-esque window styles with Snap layouts and rounded corners

🧪 Testing Strategy

Unit Tests: Pytest for backend, Jest for frontend

Integration Tests: Simulated ingestion-to-inspection pipelines

Regression Tests: Snapshot comparisons of viewer output

CI/CD: GitHub Actions with Windows builds

🌿 Git Workflow

Branching: main (stable), dev (active), feature/* (modular additions), hotfix/* (urgent patches)

Commits: Conventional Commits (feat:, fix:, refactor:), auto-linked to PRs

Tags: Semantic versioning using vX.Y.Z format

🔢 Semantic Versioning: X.Y.Z

Component

Meaning

Example

X (Major)

Architectural guarantees change

2.0.0 → switch to dual-engine viewer

Y (Feature)

New feature added

2.3.0 → third feature under major version 2

Z (Build)

Build number of the feature release

2.3.7 → seventh build of feature 3

🌐 Domain Context

Model Format Priority:

STL – Preferred for simplicity and widespread support

3MF – Rich metadata and modern standard

OBJ – Legacy format with text-based geometry

STEP – CAD-standard, used for high-fidelity inspection

Viewer Guarantees: Input-sovereign controls, reproducible inspection, dual-engine fallback

Metadata: Bounding box, vertex count, format, author, tags, version history

Use Cases: Engineering asset libraries, game asset curation, educational model inspection

⚠️ Important Constraints

Platform Scope: This is a Windows-only desktop application. No compilation, containerization, or server deployment is required.

Security: No remote execution; all inspection must be sandboxed

Performance: Must handle 1000+ models with sub-second metadata queries

Accessibility: Keyboard and mouse input guarantees; no touch-only interactions

Auditability: Every ingestion and inspection must be logged and rollback-capable

Model Size Expectation: Most models will range from 500MB to 1.25GB — viewer must implement dynamic Level of Detail (LOD) to compensate for large asset sizes

🔗 External Dependencies

Three.js: WebGL-based preview engine

Kivy3D: Python-based OpenGL viewer for high-fidelity inspection

SQLite: Embedded database for model metadata and logs

Git: Version control for model history and rollback