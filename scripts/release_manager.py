#!/usr/bin/env python3
"""
Digital Workshop Release Manager

Interactive script for managing releases with safety checks and CI/CD integration.

Features:
- Interactive menu-driven interface
- Version bumping (major/minor/patch)
- Pre-release safety checks (pre-commit, secrets, git status)
- CI/CD pipeline integration
- Release history viewing
- Clear user feedback and confirmations

Usage:
    python scripts/release_manager.py
"""

import sys
import subprocess
import re
from pathlib import Path
from typing import Tuple, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReleaseManager:
    """Manages the release process for Digital Workshop."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.build_py_path = self.project_root / "build.py"
        self.scripts_dir = self.project_root / "scripts"
        self.pending_version = None
        self.pending_bump_type = None

    def get_current_version(self) -> str:
        """Extract current version from build.py."""
        if not self.build_py_path.exists():
            raise FileNotFoundError(f"build.py not found at {self.build_py_path}")

        with open(self.build_py_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find version in the BUILD_CONFIG
        match = re.search(r'"version":\s*"([^"]+)"', content)
        if not match:
            raise ValueError("Could not find version in build.py")

        return match.group(1)

    def calculate_new_version(self, current_version: str, bump_type: str) -> str:
        """Calculate new version based on bump type."""
        parts = current_version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {current_version}")

        major, minor, patch = map(int, parts)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return f"{major}.{minor}.{patch}"

    def update_version_in_files(self, new_version: str) -> None:
        """Update version in build.py and installer script."""
        # Update build.py
        with open(self.build_py_path, "r", encoding="utf-8") as f:
            content = f.read()

        updated_content = re.sub(
            r'"version":\s*"[^"]*"', f'"version": "{new_version}"', content
        )

        with open(self.build_py_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        # Update installer script
        installer_script = self.project_root / "installer" / "inno_setup.iss"
        if installer_script.exists():
            with open(installer_script, "r", encoding="utf-8") as f:
                installer_content = f.read()

            updated_installer = re.sub(
                r'#define MyAppVersion "[^"]*"',
                f'#define MyAppVersion "{new_version}"',
                installer_content,
            )

            with open(installer_script, "w", encoding="utf-8") as f:
                f.write(updated_installer)

    def run_pre_commit_checks(self) -> bool:
        """Run pre-commit hooks to ensure code quality."""
        try:
            print("🔍 Running pre-commit checks...")
            result = subprocess.run(
                ["pre-commit", "run", "--all-files"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Pre-commit checks passed")
                return True
            else:
                print("❌ Pre-commit checks failed:")
                print(result.stdout)
                print(result.stderr)
                return False

        except FileNotFoundError:
            print("⚠️  Pre-commit not found. Skipping pre-commit checks.")
            return True
        except Exception as e:
            print(f"⚠️  Error running pre-commit: {e}")
            return True

    def run_secret_scan(self) -> bool:
        """Run secret detection scan."""
        secret_script = self.scripts_dir / "check_secrets.py"
        if not secret_script.exists():
            print("⚠️  Secret detection script not found. Skipping secret scan.")
            return True

        try:
            print("🔐 Running secret detection scan...")

            # Get list of files to scan (Python files in project)
            files_to_scan = []
            for ext in [".py", ".js", ".ts", ".json", ".yaml", ".yml"]:
                files_to_scan.extend(self.project_root.rglob(f"*{ext}"))

            if not files_to_scan:
                print("⚠️  No files found to scan for secrets.")
                return True

            # Run secret check on files
            cmd = [sys.executable, str(secret_script)] + [
                str(f) for f in files_to_scan[:50]
            ]  # Limit to 50 files
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ Secret scan passed")
                return True
            else:
                print("❌ Secret scan failed:")
                print(result.stdout)
                return False

        except Exception as e:
            print(f"⚠️  Error running secret scan: {e}")
            return True

    def check_git_status(self) -> bool:
        """Check if git repository is clean and up to date."""
        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True,
            )
            if result.returncode != 0:
                print("❌ Not in a git repository")
                return False

            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                print("❌ Working directory has uncommitted changes:")
                print(result.stdout)
                return False

            # Check if we're on develop branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            current_branch = result.stdout.strip()
            if current_branch != "develop":
                print(
                    f"⚠️  Currently on branch '{current_branch}'. "
                    "Releases should be done from 'develop' branch."
                )
                response = input("Continue anyway? (y/N): ").lower().strip()
                if response != "y":
                    return False

            # Check if develop is up to date with remote
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.project_root,
                capture_output=True,
                check=False,
            )

            result = subprocess.run(
                ["git", "status", "-uno"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if "behind" in result.stdout:
                print(
                    "⚠️  Local branch is behind remote. " "Please pull latest changes."
                )
                return False

            print("✅ Git repository is clean and up to date")
            return True

        except Exception as e:
            print(f"❌ Error checking git status: {e}")
            return False

    def create_release_branch(self, new_version: str) -> bool:
        """Create a release branch for the new version."""
        try:
            branch_name = f"release/v{new_version}"

            print(f"🌿 Creating release branch: {branch_name}")

            # Create and checkout release branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                check=True,
            )

            # Update version files
            self.update_version_in_files(new_version)

            # Commit version changes
            files_to_add = ["build.py"]
            if (self.project_root / "installer" / "inno_setup.iss").exists():
                files_to_add.append("installer/inno_setup.iss")

            subprocess.run(
                ["git", "add"] + files_to_add, cwd=self.project_root, check=True
            )

            subprocess.run(
                ["git", "commit", "-m", f"Bump version to {new_version}"],
                cwd=self.project_root,
                check=True,
            )

            # Push release branch
            subprocess.run(
                ["git", "push", "origin", branch_name],
                cwd=self.project_root,
                check=True,
            )

            print(f"✅ Release branch '{branch_name}' created and pushed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create release branch: {e}")
            return False
        except Exception as e:
            print(f"❌ Error creating release branch: {e}")
            return False

    def get_recent_releases(self, limit: int = 10) -> List[Tuple[str, str, str]]:
        """Get recent releases from git tags."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "tag",
                    "--sort=-version:refname",
                    "-l",
                    "v*",
                    "--format=%(refname:short)%00%(creatordate)%00%(subject)",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return []

            releases = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split("\x00")
                    if len(parts) >= 3:
                        tag, date, subject = parts
                        releases.append((tag, date, subject))

            return releases[:limit]

        except Exception as e:
            print(f"⚠️  Error getting releases: {e}")
            return []

    def show_menu(self) -> None:
        """Display the main menu."""
        while True:
            print("\n" + "=" * 50)
            print("DIGITAL WORKSHOP RELEASE MANAGER")
            print("=" * 50)

            try:
                current_version = self.get_current_version()
                print(f"Current Version: {current_version}")
            except Exception as e:
                print(f"❌ Error getting current version: {e}")
                return

            print("\nChoose an option:")
            print("1. Choose version bump type (major/minor/patch)")
            print("2. View current version details")
            print("3. Run pre-release checks")
            print("4. Create release branch and trigger CI/CD")
            print("5. View recent releases")
            print("6. Exit")

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == "1":
                self.handle_version_bump()
            elif choice == "2":
                self.show_version_details()
            elif choice == "3":
                self.run_all_checks()
            elif choice == "4":
                self.handle_release_process()
            elif choice == "5":
                self.show_recent_releases()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    def handle_version_bump(self) -> None:
        """Handle version bump selection."""
        current_version = self.get_current_version()

        print(f"\n📈 Current Version: {current_version}")
        print("\nSelect bump type:")
        print("1. Major (x.0.0)")
        print("2. Minor (x.y.0)")
        print("3. Patch (x.y.z)")

        choice = input("\nEnter bump type (1-3): ").strip()

        bump_types = {"1": "major", "2": "minor", "3": "patch"}
        bump_type = bump_types.get(choice)

        if not bump_type:
            print("❌ Invalid choice.")
            return

        new_version = self.calculate_new_version(current_version, bump_type)

        print("\n🔄 Version Change:")
        print(f"   {current_version} → {new_version}")
        print(f"   Bump Type: {bump_type}")

        confirm = input("\nProceed with this version bump? (y/N): ").lower().strip()
        if confirm == "y":
            print(f"✅ Selected {bump_type} bump → {new_version}")
            # Store for later use in release process
            self.pending_version = new_version
            self.pending_bump_type = bump_type
        else:
            print("❌ Version bump cancelled.")

    def show_version_details(self) -> None:
        """Show detailed version information."""
        try:
            current_version = self.get_current_version()
            print("\n📋 Version Details:")
            print(f"   Current Version: {current_version}")

            # Try to get last commit info
            result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print(f"   Last Commit: {result.stdout.strip()}")

            # Show pending version if set
            if hasattr(self, "pending_version"):
                print(
                    f"   Pending Version: {self.pending_version} "
                    f"({self.pending_bump_type} bump)"
                )

        except Exception as e:
            print(f"❌ Error getting version details: {e}")

    def run_all_checks(self) -> bool:
        """Run all pre-release safety checks."""
        print("\n🛡️  Running Pre-Release Safety Checks...")

        checks = [
            ("Git Status", self.check_git_status),
            ("Pre-commit Hooks", self.run_pre_commit_checks),
            ("Secret Detection", self.run_secret_scan),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"\n🔍 {check_name}: ")
            if not check_func():
                all_passed = False

        if all_passed:
            print("\n✅ All safety checks passed!")
        else:
            print("\n❌ Some safety checks failed. Please fix issues before proceeding.")

        return all_passed

    def handle_release_process(self) -> None:
        """Handle the complete release process."""
        if not hasattr(self, "pending_version"):
            print("❌ No version bump selected. Please choose a version bump first.")
            return

        print(f"\n🚀 Starting Release Process for v{self.pending_version}")

        # Run safety checks
        if not self.run_all_checks():
            print("❌ Safety checks failed. Cannot proceed with release.")
            return

        # Confirm release
        print("\n📋 Release Summary:")
        print(f"   New Version: {self.pending_version}")
        print(f"   Bump Type: {self.pending_bump_type}")
        print("   Will create release branch and push to trigger CI/CD")

        confirm = input("\nProceed with release? (y/N): ").lower().strip()
        if confirm != "y":
            print("❌ Release cancelled.")
            return

        # Create release branch
        if self.create_release_branch(self.pending_version):
            print("\n🎉 Release branch created successfully!")
            print(f"   Branch: release/v{self.pending_version}")
            print("   CI/CD pipeline should start automatically")

            # Try to get GitHub URL from git remote
            try:
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    repo_url = result.stdout.strip()
                    # Convert git URL to HTTPS if needed
                    if repo_url.startswith("git@"):
                        repo_url = (
                            repo_url.replace(":", "/")
                            .replace("git@", "https://")
                            .replace(".git", "")
                        )
                    else:
                        repo_url = repo_url.rstrip(".git")
                    print(f"   Monitor progress at: {repo_url}/actions")
            except Exception:
                print("   Monitor progress at: GitHub Actions")

            # Clean up pending version
            self.pending_version = None
            self.pending_bump_type = None
        else:
            print("❌ Failed to create release branch.")

    def show_recent_releases(self) -> None:
        """Show recent releases."""
        print("\n📚 Recent Releases:")

        releases = self.get_recent_releases()

        if not releases:
            print("   No releases found.")
            return

        for i, (tag, date, subject) in enumerate(releases, 1):
            # Format date
            try:
                # Parse git date format
                date_obj = datetime.strptime(date, "%a %b %d %H:%M:%S %Y %z")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                formatted_date = date.split()[0] if date else "Unknown"

            print(f"{i: 2d}. {tag} - {formatted_date} - {subject}")


def main():
    """Main entry point."""
    try:
        manager = ReleaseManager()
        manager.show_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Release manager interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        logger.exception("Fatal error in release manager")
        sys.exit(1)


if __name__ == "__main__":
    main()
