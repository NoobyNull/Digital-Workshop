#!/usr/bin/env python3
"""
Test script to verify GitLab API connectivity
"""

import requests
import json
import sys
from urllib.parse import quote


def test_gitlab_connectivity():
    """Test basic GitLab connectivity and API access"""

    gitlab_url = "https://gitlab.yax.family"
    project_path = "mty/digital-workshop"

    print(f"Testing GitLab connectivity to: {gitlab_url}")
    print(f"Project path: {project_path}")
    print("=" * 50)

    # Test basic connectivity
    try:
        response = requests.get(gitlab_url, timeout=10)
        print(f"[OK] Basic connectivity: {response.status_code}")
        if response.status_code == 302:
            print("   Redirecting to login (expected for unauthenticated access)")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Basic connectivity failed: {e}")
        return False

    # Test API without authentication
    try:
        api_url = f"{gitlab_url}/api/v4/projects"
        response = requests.get(api_url, timeout=10)
        print(f"[OK] API endpoint accessible: {response.status_code}")
        if response.status_code == 200:
            projects = response.json()
            print(f"   Found {len(projects)} public projects")
        elif response.status_code == 401:
            print("   Authentication required (expected)")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API access failed: {e}")
        return False

    # Test specific project access
    try:
        encoded_project = quote(project_path, safe="")
        project_url = f"{gitlab_url}/api/v4/projects/{encoded_project}"
        response = requests.get(project_url, timeout=10)
        print(f"[OK] Project API: {response.status_code}")
        if response.status_code == 200:
            project_data = response.json()
            print(f"   Project: {project_data.get('name', 'Unknown')}")
            print(
                f"   Description: {project_data.get('description', 'No description')[:100]}..."
            )
            print(f"   Stars: {project_data.get('star_count', 0)}")
            print(f"   Forks: {project_data.get('forks_count', 0)}")
        elif response.status_code == 404:
            print("   Project not found or private")
        elif response.status_code == 401:
            print("   Authentication required")
    except requests.exceptions.RequestException as e:
        print(f"❌ Project API access failed: {e}")
        return False

    # Test web interface
    try:
        web_url = f"{gitlab_url}/{project_path}"
        response = requests.get(web_url, timeout=10)
        print(f"[OK] Web interface: {response.status_code}")
        if response.status_code == 200:
            print("   Project page accessible")
        elif response.status_code == 302:
            print("   Redirecting to login (expected for private projects)")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Web interface access failed: {e}")
        return False

    print("=" * 50)
    print("GitLab connectivity test completed successfully!")
    return True


if __name__ == "__main__":
    success = test_gitlab_connectivity()
    sys.exit(0 if success else 1)
