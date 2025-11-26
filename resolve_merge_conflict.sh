#!/bin/bash
# Script to resolve merge conflicts on Pi
# This will stash local changes and handle untracked files

echo "Resolving merge conflicts..."

cd ~/AITUNER/2025-AI-TUNER-AGENTV3

# Check git status
echo "Current git status:"
git status

# Stash local changes to tracked files
echo ""
echo "Stashing local changes to tracked files..."
git stash push -m "Local changes before merge - $(date)"

# Handle untracked file (ai_advisor_reasoning.py)
if [ -f "services/ai_advisor_reasoning.py" ]; then
    echo ""
    echo "Found untracked file: services/ai_advisor_reasoning.py"
    echo "Options:"
    echo "1. Add and commit it"
    echo "2. Move it to backup location"
    echo "3. Remove it"
    echo ""
    read -p "Choose option (1/2/3) [default: 1]: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            echo "Adding and committing untracked file..."
            git add services/ai_advisor_reasoning.py
            git commit -m "Add ai_advisor_reasoning.py before merge"
            ;;
        2)
            echo "Moving to backup location..."
            mkdir -p ~/AITUNER/backups
            mv services/ai_advisor_reasoning.py ~/AITUNER/backups/ai_advisor_reasoning.py.backup
            echo "File backed up to ~/AITUNER/backups/ai_advisor_reasoning.py.backup"
            ;;
        3)
            echo "Removing untracked file..."
            rm services/ai_advisor_reasoning.py
            echo "File removed"
            ;;
    esac
fi

# Now try to pull
echo ""
echo "Attempting to pull from origin..."
git pull origin main

echo ""
echo "Merge conflict resolution complete!"
echo ""
echo "If you need to restore your stashed changes, run:"
echo "  git stash list"
echo "  git stash pop"

