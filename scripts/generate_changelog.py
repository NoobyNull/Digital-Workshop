#!/usr/bin/env python3
"""
Generate changelog from git commits between builds
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_last_build_tag():
    """Get the last build tag from git."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0', '--match=build-*'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_commits_since_tag(tag=None):
    """Get commits since a specific tag or all commits if no tag."""
    if tag:
        result = subprocess.run(
            ['git', 'log', '--oneline', '--since={}'.format(tag), 
             '--pretty=format:%h - %s'],
            capture_output=True, text=True, check=True
        )
    else:
        result = subprocess.run(
            ['git', 'log', '--oneline', '--pretty=format:%h - %s'],
            capture_output=True, text=True, check=True
        )
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def get_commit_info():
    """Get info about the current commit."""
    try:
        commit_hash = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        commit_message = subprocess.run(
            ['git', 'log', '-1', '--pretty=%s'],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        commit_author = subprocess.run(
            ['git', 'log', '-1', '--pretty=%an'],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        
        return {
            'hash': commit_hash,
            'message': commit_message,
            'author': commit_author
        }
    except subprocess.CalledProcessError:
        return {}

def format_changes(commits, build_number):
    """Format commits into a readable changelog."""
    if not commits:
        return ["No changes found for this build"]
    
    changelog = [f"Changes for Build {build_number}"]
    changelog.append("=" * 50)
    changelog.append("")
    
    # Group commits by type (feat, fix, docs, etc.)
    features = []
    fixes = []
    docs = []
    other = []
    
    for commit in commits:
        if not commit.strip():
            continue
            
        parts = commit.split(' - ', 1)
        if len(parts) < 2:
            continue
            
        commit_hash, message = parts
        message_lower = message.lower()
        
        if message_lower.startswith('feat') or message_lower.startswith('add'):
            features.append(f"• {message}")
        elif message_lower.startswith('fix') or 'fix' in message_lower:
            fixes.append(f"• {message}")
        elif message_lower.startswith('docs') or 'doc' in message_lower:
            docs.append(f"• {message}")
        else:
            other.append(f"• {message}")
    
    if features:
        changelog.append("🚀 NEW FEATURES:")
        for feature in features:
            changelog.append(f"  {feature}")
        changelog.append("")
    
    if fixes:
        changelog.append("🐛 BUG FIXES:")
        for fix in fixes:
            changelog.append(f"  {fix}")
        changelog.append("")
    
    if docs:
        changelog.append("📚 DOCUMENTATION:")
        for doc in docs:
            changelog.append(f"  {doc}")
        changelog.append("")
    
    if other:
        changelog.append("🔧 OTHER CHANGES:")
        for change in other:
            changelog.append(f"  {change}")
        changelog.append("")
    
    return changelog

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate changelog for Digital Workshop builds')
    parser.add_argument('--build-number', type=str, help='Build number')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    build_number = args.build_number or "unknown"
    last_tag = get_last_build_tag()
    
    print(f"Generating changelog for build {build_number}")
    if last_tag:
        print(f"Last build tag: {last_tag}")
    else:
        print("No previous build tag found")
    
    commits = get_commits_since_tag(last_tag)
    changelog = format_changes(commits, build_number)
    
    # Add header info
    commit_info = get_commit_info()
    header = [
        f"Digital Workshop Build {build_number}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Commit: {commit_info.get('hash', 'unknown')[:8]}",
        f"Author: {commit_info.get('author', 'unknown')}",
        f"Message: {commit_info.get('message', 'unknown')}",
        "",
        "Full commit history:",
    ]
    
    full_changelog = header + changelog
    
    # Output to file or stdout
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(full_changelog))
        print(f"Changelog written to {output_path}")
    else:
        print('\n'.join(full_changelog))

if __name__ == "__main__":
    main()