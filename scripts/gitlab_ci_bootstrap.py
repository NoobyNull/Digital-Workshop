#!/usr/bin/env python3
"""
Bootstrap GitLab project-level CI/CD settings for Digital Workshop.

This helper:
  * Validates connectivity with the GitLab instance (defaults to http://192.168.0.40).
  * Creates or updates CI/CD variables by calling the GitLab REST API.
  * (Optionally) protects commonly used branches so only Maintainers can push.

Example:
    python scripts/gitlab_ci_bootstrap.py \
        --url http://192.168.0.40 \
        --token <PERSONAL_ACCESS_TOKEN> \
        --project-id 87 \
        --set RUN_TESTS=false \
        --set WINDOWS_RUNNER_TAGS=windows,digital-workshop \
        --protect-branch main \
        --protect-branch develop
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, Optional


class GitLabClient:
    """Minimal GitLab API helper that only uses the standard library."""

    def __init__(self, base_url: str, token: str, dry_run: bool = False) -> None:
        if not base_url:
            raise ValueError("GitLab URL cannot be empty")
        if not token:
            raise ValueError("API token cannot be empty")

        self.base_url = base_url.rstrip("/")
        self.token = token
        self.dry_run = dry_run

    def request(
        self,
        method: str,
        path: str,
        *,
        data: Optional[Dict] = None,
        ok_status: Iterable[int] = (200, 201, 204),
    ) -> Dict:
        """Send an HTTP request and parse JSON response."""

        url = f"{self.base_url}/{path.lstrip('/')}"
        body: Optional[bytes] = None
        headers = {"PRIVATE-TOKEN": self.token}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self.dry_run:
            print(f"[dry-run] {method} {url}")
            if data:
                print(f"          payload: {json.dumps(data)}")
            return {}

        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.getcode()
                if status not in ok_status:
                    raise RuntimeError(f"Unexpected status {status} for {method} {url}")
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type.lower():
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload if isinstance(payload, dict) else {}
                return {}
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"{method} {url} failed: {exc.code} {exc.reason} {exc.read().decode('utf-8')}"
            ) from exc

    def get_project(self, project_id: str) -> Dict:
        return self.request("GET", f"api/v4/projects/{urllib.parse.quote_plus(project_id)}")

    def set_variable(
        self,
        project_id: str,
        key: str,
        value: str,
        *,
        masked: bool = False,
        protected: bool = False,
    ) -> None:
        """Create or update a CI/CD variable."""

        payload = {
            "value": value,
            "masked": masked,
            "protected": protected,
            "variable_type": "env_var",
        }
        path = f"api/v4/projects/{urllib.parse.quote_plus(project_id)}/variables/{urllib.parse.quote_plus(key)}"
        try:
            self.request("PUT", path, data=payload)
            print(f"[updated] variable {key}")
        except RuntimeError as error:
            if "404" in str(error):
                create_path = f"api/v4/projects/{urllib.parse.quote_plus(project_id)}/variables"
                payload["key"] = key
                self.request("POST", create_path, data=payload, ok_status=(201,))
                print(f"[created] variable {key}")
            else:
                raise

    def protect_branch(self, project_id: str, branch: str) -> None:
        """Ensure a branch is protected (maintainer push/merge)."""

        encoded_branch = urllib.parse.quote_plus(branch)
        delete_path = f"api/v4/projects/{urllib.parse.quote_plus(project_id)}/protected_branches/{encoded_branch}"
        self.request("DELETE", delete_path, ok_status=(204, 404))

        payload = {
            "name": branch,
            "push_access_level": 40,  # Maintainers only
            "merge_access_level": 40,
            "unprotect_access_level": 40,
        }
        create_path = f"api/v4/projects/{urllib.parse.quote_plus(project_id)}/protected_branches"
        self.request("POST", create_path, data=payload, ok_status=(201,))
        print(f"[protected] branch {branch}")


def parse_kv(value: str) -> Dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Use KEY=VALUE syntax for --set")
    key, raw_value = value.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("Variable key cannot be empty")
    return {key: raw_value}


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://192.168.0.40", help="GitLab base URL")
    parser.add_argument("--token", required=True, help="GitLab personal access token (api scope)")
    parser.add_argument("--project-id", required=True, help="Numeric project ID or URL-encoded path")
    parser.add_argument(
        "--set",
        dest="variables",
        metavar="KEY=VALUE",
        type=parse_kv,
        action="append",
        help="Create/update a CI variable (repeatable)",
    )
    parser.add_argument(
        "--protect-branch",
        dest="branches",
        action="append",
        default=[],
        help="Protect a branch so only Maintainers can push (repeatable)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without changing GitLab")
    return parser.parse_args(argv)


def flatten_variables(pairs: Optional[Iterable[Dict[str, str]]]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    if not pairs:
        return merged
    for kv in pairs:
        merged.update(kv)
    return merged


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    variables = flatten_variables(args.variables)
    client = GitLabClient(args.url, args.token, dry_run=args.dry_run)

    try:
        project = client.get_project(args.project_id)
    except RuntimeError as error:
        print(f"Failed to connect to GitLab: {error}", file=sys.stderr)
        return 1

    print(f"Configuring project '{project.get('name')}' ({project.get('id')}) at {args.url}")

    for key, value in variables.items():
        masked = key.endswith(("TOKEN", "PASSWORD", "SECRET"))
        client.set_variable(args.project_id, key, value, masked=masked, protected=False)

    for branch in args.branches:
        client.protect_branch(args.project_id, branch)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
