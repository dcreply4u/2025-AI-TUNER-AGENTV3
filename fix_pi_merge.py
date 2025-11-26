#!/usr/bin/env python3
"""
Python script to fix merge conflicts on Pi
Can be run directly without shell script issues
"""

import subprocess
import os
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Main function to fix merge conflicts on Pi."""
    # Try multiple possible paths
    possible_paths = [
        Path.home() / "AITUNER" / "2025-AI-TUNER-AGENTV3",
        Path("/home/aituner/AITUNER/2025-AI-TUNER-AGENTV3"),
        Path.cwd() / "2025-AI-TUNER-AGENTV3",
        Path.cwd(),
    ]
    
    repo_path = None
    for path in possible_paths:
        if path.exists() and (path / ".git").exists():
            repo_path = path
            break
    
    if not repo_path:
        print("Repository not found. Please run this script from the repository directory.")
        print("Tried paths:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    print(f"Working in: {repo_path}")
    os.chdir(repo_path)
    
    # Step 1: Check status
    print("\n=== Step 1: Checking git status ===")
    success, stdout, stderr = run_cmd("git status", cwd=repo_path)
    print(stdout)
    if stderr:
        print("Errors:", stderr)
    
    # Step 2: Add untracked file
    print("\n=== Step 2: Adding untracked file ===")
    untracked_file = repo_path / "services" / "ai_advisor_reasoning.py"
    if untracked_file.exists():
        print(f"Found untracked file: {untracked_file}")
        success, stdout, stderr = run_cmd(f"git add {untracked_file}", cwd=repo_path)
        if success:
            print("Added untracked file")
        else:
            print(f"Error adding file: {stderr}")
    else:
        print("Untracked file not found (may have been removed)")
    
    # Step 3: Add all modified files
    print("\n=== Step 3: Adding all modified files ===")
    success, stdout, stderr = run_cmd("git add -A", cwd=repo_path)
    if success:
        print("All files staged")
    else:
        print(f"Error staging files: {stderr}")
    
    # Step 4: Commit everything
    print("\n=== Step 4: Committing changes ===")
    success, stdout, stderr = run_cmd(
        'git commit -m "Local changes before merge"',
        cwd=repo_path
    )
    if success:
        print("Changes committed")
        print(stdout)
    else:
        if "nothing to commit" in stderr.lower() or "nothing to commit" in stdout.lower():
            print("Nothing to commit (changes may already be committed)")
        else:
            print(f"Commit result: {stdout}")
            print(f"Errors: {stderr}")
    
    # Step 5: Try to pull
    print("\n=== Step 5: Pulling from origin ===")
    success, stdout, stderr = run_cmd("git pull origin main", cwd=repo_path)
    print(stdout)
    if stderr:
        print("Errors:", stderr)
    
    if success:
        print("\n✓ Successfully pulled from origin!")
    else:
        print("\n✗ Pull failed. You may need to resolve merge conflicts manually.")
        print("\nTo see conflicts, run: git status")
        print("To abort merge: git merge --abort")
        print("To resolve manually, edit conflicted files and run: git add <file> && git commit")

if __name__ == "__main__":
    main()

