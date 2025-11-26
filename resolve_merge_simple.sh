#!/bin/bash
# Simple script to resolve merge conflicts - auto-commits everything

cd ~/AITUNER/2025-AI-TUNER-AGENTV3

echo "Resolving merge conflicts (auto-commit method)..."

# Add all changes including untracked files
git add -A

# Commit all changes
git commit -m "Local changes before merge - $(date +%Y-%m-%d_%H-%M-%S)"

# Now pull
echo "Pulling from origin..."
git pull origin main

echo "Done! If there are merge conflicts, resolve them manually."

