#!/usr/bin/env python3
"""
Fix Pi Merge Conflicts
Automatically resolves merge conflicts by accepting GitHub version.
Run this on the Pi if sync scripts fail.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, cwd: str = None) -> tuple[str, int]:
    """Run a shell command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return str(e), 1

def main():
    """Main function."""
    # Find project directory
    script_dir = Path(__file__).parent.parent
    project_dir = script_dir
    
    print("=" * 50)
    print("Fix Pi Merge Conflicts")
    print("=" * 50)
    print(f"Project directory: {project_dir}")
    print()
    
    # Check if we're in a git repo
    output, code = run_command("git rev-parse --git-dir", cwd=str(project_dir))
    if code != 0:
        print("❌ Not a git repository!")
        return 1
    
    # Check for conflicts
    print("Step 1: Checking for merge conflicts...")
    output, code = run_command("git status --porcelain", cwd=str(project_dir))
    
    conflicted_files = []
    for line in output.split('\n'):
        if line.startswith('UU') or 'both modified' in line.lower():
            # Extract filename
            parts = line.split()
            if len(parts) >= 2:
                conflicted_files.append(parts[-1])
    
    if not conflicted_files:
        print("✅ No merge conflicts detected")
        
        # Check if we need to pull
        output, code = run_command("git status", cwd=str(project_dir))
        if "Your branch is behind" in output:
            print("⚠️  Branch is behind - attempting pull...")
            output, code = run_command("git pull origin main", cwd=str(project_dir))
            if code == 0:
                print("✅ Successfully pulled latest changes")
                return 0
            else:
                print(f"❌ Pull failed: {output}")
                return 1
        else:
            print("✅ Repository is up to date")
            return 0
    
    print(f"⚠️  Found {len(conflicted_files)} conflicted file(s):")
    for f in conflicted_files:
        print(f"   - {f}")
    print()
    
    # Stash any uncommitted changes
    print("Step 2: Stashing uncommitted changes...")
    output, code = run_command("git stash push -m 'Pre-merge stash'", cwd=str(project_dir))
    if "No local changes" not in output:
        print("✅ Changes stashed")
    else:
        print("ℹ️  No changes to stash")
    print()
    
    # Resolve conflicts by accepting GitHub version
    print("Step 3: Resolving conflicts (accepting GitHub version)...")
    for file in conflicted_files:
        print(f"   Resolving: {file}")
        run_command(f"git checkout --theirs '{file}'", cwd=str(project_dir))
        run_command(f"git add '{file}'", cwd=str(project_dir))
    
    # Complete the merge
    print()
    print("Step 4: Completing merge...")
    output, code = run_command(
        "git commit --no-edit -m 'Merge: Auto-resolved conflicts (accepted GitHub version)'",
        cwd=str(project_dir)
    )
    
    if code == 0:
        print("✅ Merge completed successfully!")
        return 0
    else:
        # If commit fails, try reset
        print("⚠️  Commit failed - resetting to origin/main...")
        output, code = run_command("git reset --hard origin/main", cwd=str(project_dir))
        if code == 0:
            print("✅ Reset to origin/main successful")
            return 0
        else:
            print(f"❌ Reset failed: {output}")
            return 1

if __name__ == "__main__":
    sys.exit(main())

