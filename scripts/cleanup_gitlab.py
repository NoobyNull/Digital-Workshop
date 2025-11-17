#!/usr/bin/env python3
"""
GitLab Cleanup Script for Digital Workshop
Cleans up failed builds and restarts CI/CD pipeline
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
import requests
import time

def get_gitlab_token():
    """Get GitLab token from environment or user input."""
    token = "glpat-ZDqK9Fh6qb61jRLaKUtkqm86MQp1OjQH.01.0w0ffoze2"
    
    # Try to get from environment
    import os
    token = os.getenv('GITLAB_TOKEN')
    if token:
        print(f"✅ Found GitLab token in environment")
        return token
    
    # If not in environment, ask user
    print("❌ No GITLAB_TOKEN environment variable found")
    print("Please set GITLAB_TOKEN environment variable with your GitLab personal access token")
    print("You can create one at: https://gitlab.yax.family/-/profile/personal_access_tokens")
    print()
    
    token = input("Enter your GitLab personal access token: ").strip()
    if not token:
        print("❌ No token provided")
        sys.exit(1)
    
    return token

def get_gitlab_url():
    """Get GitLab URL from environment or user input."""
    url = os.getenv('GITLAB_URL', 'https://gitlab.yax.family')
    print(f"📍 GitLab URL: {url}")
    return url

def get_failed_jobs(gitlab_url, token):
    """Get list of failed jobs from GitLab API."""
    try:
        headers = {'Private-Token': token}
        response = requests.get(f"{gitlab_url}/api/v4/jobs?scope=failed", headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get failed jobs: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting failed jobs: {e}")
        return None

def cancel_jobs(gitlab_url, token, job_ids):
    """Cancel specified jobs in GitLab."""
    try:
        headers = {'Private-Token': token}
        cancelled_count = 0
        
        for job_id in job_ids:
            response = requests.post(f"{gitlab_url}/api/v4/jobs/{job_id}/cancel", headers=headers, timeout=10)
            
            if response.status_code == 204:
                cancelled_count += 1
                print(f"✅ Cancelled job {job_id}")
            else:
                print(f"❌ Failed to cancel job {job_id}: {response.status_code}")
        
        print(f"📊 Total jobs cancelled: {cancelled_count}")
        return cancelled_count > 0
        
    except Exception as e:
        print(f"❌ Error cancelling jobs: {e}")
        return False

def retry_pipeline(gitlab_url, token):
    """Trigger a new pipeline to restart the build process."""
    try:
        headers = {'Private-Token': token}
        
        # Create a simple commit to trigger new build
        response = requests.post(f"{gitlab_url}/api/v4/projects/mty%2Fdigital-workshop/trigger/pipeline", 
                              headers=headers, timeout=10)
        
        if response.status_code == 201:
            print("✅ New pipeline triggered successfully!")
            print(f"🔗 Pipeline URL: {response.json().get('web_url', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to trigger pipeline: {response.status_code}")
            if response.text:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering pipeline: {e}")
        return False

def cleanup_artifacts(gitlab_url, token, keep_recent=5):
    """Clean up old build artifacts."""
    try:
        headers = {'Private-Token': token}
        
        # Get list of recent builds
        response = requests.get(f"{gitlab_url}/api/v4/projects/mty%2Fdigital-workshop/jobs?per_page=50", headers=headers, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            
            # Find failed or old jobs to clean up
            jobs_to_cleanup = []
            for job in jobs:
                if (job.get('status') == 'failed' or 
                    job.get('status') == 'canceled' or
                    job.get('created_at', '') and 
                    len(jobs_to_cleanup) < keep_recent):
                    
                    jobs_to_cleanup.append(job)
            
            # Cancel old/failed jobs
            if jobs_to_cleanup:
                job_ids = [job['id'] for job in jobs_to_cleanup]
                cancel_jobs(gitlab_url, token, job_ids)
            
            print(f"🧹 Cleaned up {len(jobs_to_cleanup)} old jobs")
            return True
            
        else:
            print(f"❌ Failed to get jobs for cleanup: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error cleaning up artifacts: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Clean up GitLab failed builds and restart pipeline')
    parser.add_argument('--gitlab-url', help='GitLab URL (default: https://gitlab.yax.family)')
    parser.add_argument('--token', help='GitLab personal access token')
    parser.add_argument('--keep-recent', type=int, default=5, help='Number of recent jobs to keep')
    parser.add_argument('--cleanup-only', action='store_true', help='Only cleanup, do not retry pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    print("GitLab Cleanup Tool for Digital Workshop")
    print("=" * 50)
    
    # Get GitLab credentials
    gitlab_url = args.gitlab_url or get_gitlab_url()
    token = args.token or get_gitlab_token()
    
    if not token:
        print("❌ No GitLab token provided - cannot continue")
        sys.exit(1)
    
    print(f"📍 GitLab URL: {gitlab_url}")
    print(f"🔑 Using token: {'*' * (len(token)-4)}****")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Would clean up jobs older than {args.keep_recent} most recent")
        print("Would cancel all failed/cancelled jobs")
        if not args.cleanup_only:
            print("Would trigger new pipeline to restart build process")
        return
    
    # Step 1: Clean up old/failed jobs
    print("\n🧹 Step 1: Cleaning up old/failed jobs...")
    if not cleanup_artifacts(gitlab_url, token, args.keep_recent):
        print("❌ Failed to cleanup artifacts")
        return
    
    # Step 2: Cancel stuck jobs
    print("\n🛑 Step 2: Cancelling stuck jobs...")
    failed_jobs = get_failed_jobs(gitlab_url, token)
    
    if failed_jobs:
        job_ids = [job['id'] for job in failed_jobs]
        if job_ids:
            cancel_jobs(gitlab_url, token, job_ids)
        else:
            print("✅ No stuck jobs found to cancel")
    
    # Step 3: Retry pipeline
    if not args.cleanup_only:
        print("\n🚀 Step 3: Triggering new pipeline...")
        if retry_pipeline(gitlab_url, token):
            print("✅ Pipeline triggered successfully!")
            print("📊 Check GitLab CI/CD for the new build")
        else:
            print("❌ Failed to trigger pipeline")
    
    print("\n✅ Cleanup completed!")
    print("📊 Check GitLab CI/CD at: https://gitlab.yax.family/mty/digital-workshop/-/pipelines")
    print("🔄 Your enhanced CI pipeline will continue with the next build")

if __name__ == "__main__":
    main()