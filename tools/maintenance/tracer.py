#!/usr/bin/env python3
"""
Dependency Tracer Utility - Analyze codebase dependencies and dependants.

Traces:
- Direct imports (from X import Y)
- Class inheritance (class X(BaseClass))
- Function/method calls (obj.method())

Usage:
    python tools/maintenance/tracer.py trace VTKWidget
    python tools/maintenance/tracer.py trace main.py
    python tools/maintenance/tracer.py trace src.gui.main_window
    python tools/maintenance/tracer.py update
    python tools/maintenance/tracer.py interactive
"""

import os
import sys
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import ast


class DependencyTracer:
    """Analyzes Python codebase for dependencies and dependants."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # What X depends on
        self.dependants: Dict[str, Set[str]] = defaultdict(set)    # What depends on X
        self.definitions: Dict[str, str] = {}                       # Where things are defined
        self.file_map: Dict[str, Path] = {}                         # Module name to file path
        self.file_imports: Dict[str, Set[str]] = defaultdict(set)   # What each file imports
        self.cache_file = Path(".tracer_cache.json")
        self.scanned_files = set()

    def scan_codebase(self, force: bool = False) -> None:
        """Scan all Python files and build dependency graph."""
        if not force and self.cache_file.exists():
            self.load_cache()
            print(f"[OK] Loaded cache with {len(self.definitions)} definitions")
            return

        print("[*] Scanning codebase...")
        self.dependencies.clear()
        self.dependants.clear()
        self.definitions.clear()
        self.file_map.clear()
        self.scanned_files.clear()

        # Find all Python files
        python_files = list(self.root_dir.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_skip(f)]

        print(f"[*] Found {len(python_files)} Python files")

        # First pass: collect definitions
        for py_file in python_files:
            self._extract_definitions(py_file)

        # Second pass: collect dependencies
        for py_file in python_files:
            self._extract_dependencies(py_file)

        self.save_cache()
        print(f"[OK] Scanned {len(self.scanned_files)} files")
        print(f"[OK] Found {len(self.definitions)} definitions")

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {".venv", "__pycache__", ".git", "build", "dist", "node_modules"}
        skip_files = {"tracer.py"}

        if file_path.name in skip_files:
            return True

        for part in file_path.parts:
            if part in skip_dirs:
                return True

        return False

    def _extract_definitions(self, file_path: Path) -> None:
        """Extract class and function definitions from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            module_name = self._get_module_name(file_path)
            self.file_map[module_name] = file_path

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    full_name = f"{module_name}.{node.name}"
                    self.definitions[node.name] = full_name
                    self.definitions[full_name] = full_name

                elif isinstance(node, ast.FunctionDef):
                    full_name = f"{module_name}.{node.name}"
                    self.definitions[node.name] = full_name

            self.scanned_files.add(str(file_path))

        except Exception as e:
            print(f"[!] Error parsing {file_path}: {e}")

    def _extract_dependencies(self, file_path: Path) -> None:
        """Extract dependencies from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            module_name = self._get_module_name(file_path)

            # Extract imports - track what this file imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_dependency(module_name, alias.name)
                        self.file_imports[module_name].add(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_dependency(module_name, node.module)
                        self.file_imports[module_name].add(node.module)
                        for alias in node.names:
                            full_name = f"{node.module}.{alias.name}"
                            self._add_dependency(module_name, full_name)
                            self.file_imports[module_name].add(full_name)
                            # Also track just the name for easier lookup
                            self._add_dependency(module_name, alias.name)
                            self.file_imports[module_name].add(alias.name)

                elif isinstance(node, ast.ClassDef):
                    # Track inheritance
                    for base in node.bases:
                        base_name = self._get_name_from_node(base)
                        if base_name:
                            self._add_dependency(module_name, base_name)

                elif isinstance(node, ast.Call):
                    # Track function calls
                    call_name = self._get_name_from_node(node.func)
                    if call_name:
                        self._add_dependency(module_name, call_name)

        except Exception as e:
            print(f"[!] Error extracting dependencies from {file_path}: {e}")

    def _add_dependency(self, source: str, target: str) -> None:
        """Add a dependency relationship."""
        if source and target and source != target:
            # Normalize the target to handle various import formats
            normalized_target = target.split('.')[0] if '.' in target else target
            self.dependencies[source].add(target)
            self.dependants[target].add(source)
            # Also add the module-level dependency
            if '.' in target:
                self.dependants[normalized_target].add(source)

    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        try:
            rel_path = file_path.relative_to(self.root_dir)
            module = str(rel_path).replace("\\", "/").replace("/", ".").replace(".py", "")
            return module
        except ValueError:
            return file_path.stem

    def _get_name_from_node(self, node: ast.expr) -> Optional[str]:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name_from_node(node.value)
            if value:
                return f"{value}.{node.attr}"
        return None

    def trace(self, query: str) -> None:
        """Trace dependencies and dependants for a query."""
        # Normalize query
        query = query.strip()
        if query.endswith(".py"):
            query = query[:-3]

        # Find matching definitions
        matches = self._find_matches(query)

        if not matches:
            print(f"[!] No matches found for '{query}'")
            return

        for match in matches:
            self._print_trace(match)

    def _find_matches(self, query: str) -> List[str]:
        """Find all matching definitions."""
        matches = []

        # Exact match
        if query in self.definitions:
            matches.append(self.definitions[query])

        # Partial matches
        for key, full_name in self.definitions.items():
            if query.lower() in key.lower() or query.lower() in full_name.lower():
                if full_name not in matches:
                    matches.append(full_name)

        # Also check for package-level re-exports
        # If searching for "ModelLibraryWidget", also find "src.gui.model_library.ModelLibraryWidget"
        for key, full_name in self.definitions.items():
            if key == query and "." not in query:
                # This is a short name, check if it's re-exported from __init__.py
                for pkg_key, pkg_full_name in self.definitions.items():
                    if pkg_key.endswith(f".{query}") and pkg_full_name not in matches:
                        matches.append(pkg_full_name)

        return matches

    def _print_trace(self, name: str) -> None:
        """Print trace information for a name."""
        print(f"\n{'='*70}")
        print(f"TRACE: {name}")
        print(f"{'='*70}")

        # Show definition location
        if name in self.file_map:
            file_path = self.file_map[name]
            print(f"\n📍 Defined in: {file_path}")

        # Show dependencies (what this depends on)
        deps = self.dependencies.get(name, set())
        if deps:
            print(f"\n📦 Dependencies ({len(deps)}):")
            for dep in sorted(deps)[:20]:  # Limit to 20
                print(f"   ├─ {dep}")
            if len(deps) > 20:
                print(f"   └─ ... and {len(deps) - 20} more")
        else:
            print("\n📦 Dependencies: None")

        # Show dependants (what depends on this)
        dependants = self.dependants.get(name, set())

        # Also find files that import this symbol
        importers = set()
        short_name = name.split(".")[-1]  # Get just the class/function name

        for file_module, imports in self.file_imports.items():
            for imp in imports:
                # Check for exact match
                if imp == name:
                    importers.add(file_module)
                # Check for short name match (e.g., "ModelLibraryWidget")
                elif imp == short_name:
                    importers.add(file_module)
                # Check for package-level import (e.g., "src.gui.model_library.ModelLibraryWidget")
                elif imp.endswith(f".{short_name}") and short_name in name:
                    importers.add(file_module)

        all_dependants = dependants | importers

        if all_dependants:
            print(f"\n🔗 Dependants ({len(all_dependants)}):")
            for dep in sorted(all_dependants)[:20]:  # Limit to 20
                print(f"   ├─ {dep}")
            if len(all_dependants) > 20:
                print(f"   └─ ... and {len(all_dependants) - 20} more")
        else:
            print("\n🔗 Dependants: None")

        print()

    def save_cache(self) -> None:
        """Save dependency graph to cache."""
        cache_data = {
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "dependants": {k: list(v) for k, v in self.dependants.items()},
            "definitions": self.definitions,
            "file_map": {k: str(v) for k, v in self.file_map.items()},
            "file_imports": {k: list(v) for k, v in self.file_imports.items()},
        }

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

    def load_cache(self) -> None:
        """Load dependency graph from cache."""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            self.dependencies = defaultdict(set, {k: set(v) for k, v in cache_data.get("dependencies", {}).items()})
            self.dependants = defaultdict(set, {k: set(v) for k, v in cache_data.get("dependants", {}).items()})
            self.definitions = cache_data.get("definitions", {})
            self.file_map = {k: Path(v) for k, v in cache_data.get("file_map", {}).items()}
            self.file_imports = defaultdict(set, {k: set(v) for k, v in cache_data.get("file_imports", {}).items()})

        except Exception as e:
            print(f"[!] Error loading cache: {e}")

    def interactive(self) -> None:
        """Start interactive tracer mode."""
        print("\n" + "="*70)
        print("DEPENDENCY TRACER - Interactive Mode")
        print("="*70)
        print("Commands:")
        print("  trace <name>  - Trace dependencies and dependants")
        print("  update        - Rescan codebase")
        print("  stats         - Show statistics")
        print("  help          - Show this help")
        print("  exit          - Exit tracer")
        print("="*70 + "\n")

        while True:
            try:
                cmd = input("tracer> ").strip()

                if not cmd:
                    continue

                if cmd == "exit":
                    print("Goodbye!")
                    break

                elif cmd == "update":
                    self.scan_codebase(force=True)

                elif cmd == "stats":
                    print(f"\nDefinitions: {len(self.definitions)}")
                    print(f"Dependencies: {len(self.dependencies)}")
                    print(f"Dependants: {len(self.dependants)}")
                    print(f"Scanned files: {len(self.scanned_files)}\n")

                elif cmd == "help":
                    print("Commands: trace, update, stats, help, exit\n")

                elif cmd.startswith("trace "):
                    query = cmd[6:].strip()
                    self.trace(query)

                else:
                    print(f"Unknown command: {cmd}\n")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    """Main entry point."""
    tracer = DependencyTracer()

    if len(sys.argv) < 2:
        tracer.scan_codebase()
        tracer.interactive()

    elif sys.argv[1] == "trace" and len(sys.argv) > 2:
        tracer.scan_codebase()
        query = " ".join(sys.argv[2:])
        tracer.trace(query)

    elif sys.argv[1] == "update":
        tracer.scan_codebase(force=True)

    elif sys.argv[1] == "interactive":
        tracer.scan_codebase()
        tracer.interactive()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()

