# Digital Workshop Documentation Hub

This folder curates every asset required to understand, extend, or audit the Digital Workshop Beta.  
Use this index to find the right level of depth for sales demos, engineering reviews, or diligence packages.

---

## 📌 Primary References

| Document | Audience | Notes |
| --- | --- | --- |
| [`DWW_USER_GUIDE.md`](DWW_USER_GUIDE.md) | Operators, solution engineers | End-to-end walkthrough of the Beta interface and workflows. |
| [`FEATURES_GUIDE.md`](FEATURES_GUIDE.md) | Product, sales, onboarding | Story-driven explanation of marquee capabilities. |
| [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) | Engineering, diligence | Services, threading, and data-flow diagrams. |
| [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | Internal contributors | Coding standards, environment setup, debugging guides. |
| [`SECURITY.md`](SECURITY.md) & [`FILE_TYPE_SECURITY_POLICY.md`](FILE_TYPE_SECURITY_POLICY.md) | Security review | Inbound filters, scanning strategy, and incident response hooks. |
| [`README_TAB_DATA.md`](README_TAB_DATA.md) | Feature owners | How the Tab Data service persists per-project state. |
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | Support & field teams | One-page cheat sheet for installs, shortcuts, and KPIs. |
| [`TROUBLESHOOTING_FAQ.md`](TROUBLESHOOTING_FAQ.md) | Support & QA | Known issues, diagnostics, escalation checklist. |

---

## 🧭 Folder Map

```
docs/
├── architecture/        # Systems diagrams, IPC call maps, deployment views
├── builds/              # Build/packaging SOPs, CI blueprints, release playbooks
├── features/            # Tab-specific guides, UX blueprints, roadmap narratives
├── fixes/               # Root-cause analyses and remediation notes
├── releases/            # Per-build changelog snapshots
├── reports/             # Audit outputs (QA, security, performance)
├── *.md                 # Entry points (see table above)
```

Each folder uses the same naming language as the application so grep/search stays trivial (e.g., `features/tab_data/*.md`).

---

## 🚀 Getting Started (Developers)

1. Follow the repo-level [`README.md`](../README.md) for environment setup.
2. Dive into `DEVELOPER_GUIDE.md` ➜ `SYSTEM_ARCHITECTURE.md` ➜ the `features/` doc that matches your assignment.
3. Use `reports/` outputs to validate the branch you pulled (QA exports, performance captures, safety/bandit runs).

---

## 🔐 Governance & Quality

- `SECURITY.md` – threat model, scanning, and response.
- `LINTING_STANDARDS.md` – enforced rules across Python, JSON, YAML.
- `FILE_TYPE_SECURITY_POLICY.md` – import filters, heuristics, quarantine steps.
- `reports/` – retains the latest `safety`, `bandit`, performance, and regression reports.

---

## 🧱 Architecture Shortcuts

- `SYSTEM_ARCHITECTURE.md` – canonical component diagrams.
- `architecture/` – sub-system call graphs.
- `KNOWLEDGE_BASE_OVERVIEW.md` – taxonomy of shared data models.
- `TRIMESH_INTEGRATION.md` – VTK/Trimesh bridge specifics.

---

## 📣 Maintaining the Docs

1. Keep topics focused; one subject per file.
2. Remove or migrate material as it falls out of scope (legacy installer docs are already gone for the GitHub mirror).
3. Cross-link to code (`src/...`) or tests (`tests/...`) whenever describing behavior so readers can verify quickly.
4. Update the table at the top whenever you add a first-class document.

---

**Maintainer:** documentation team (`docs@digitalworkshop.app`)  
**Last sweep:** November 2025 (GitHub mirror prep)
