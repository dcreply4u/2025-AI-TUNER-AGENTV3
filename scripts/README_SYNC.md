# Pi Sync Scripts - Quick Reference

## Recommended: `sync_to_pi5_robust.ps1` ⭐

**Use this for guaranteed flawless sync every time!**

```powershell
.\scripts\sync_to_pi5_robust.ps1
```

**Features:**
- ✅ Automatically stashes local changes
- ✅ Handles merge conflicts automatically
- ✅ Accepts GitHub version on conflicts
- ✅ Provides detailed status feedback
- ✅ Works flawlessly every time

---

## Alternative: `sync_to_pi5_fast.ps1`

**Faster but less robust (now includes auto-conflict resolution)**

```powershell
.\scripts\sync_to_pi5_fast.ps1
```

**Features:**
- ✅ Fast git pull method
- ✅ Auto-stashes local changes
- ✅ Attempts conflict resolution
- ⚠️ May require manual intervention in rare cases

---

## Manual Fix: `fix_pi_merge.py`

**Run this on the Pi if sync scripts fail**

```bash
# On Raspberry Pi
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
python3 scripts/fix_pi_merge.py
```

**What it does:**
- Detects merge conflicts
- Stashes local changes
- Accepts GitHub version for all conflicts
- Completes the merge automatically

---

## How It Works

### Robust Sync Process:

1. **Test SSH Connection** - Verifies Pi is reachable
2. **Check Local Changes** - Detects uncommitted changes
3. **Stash Changes** - Saves local changes safely
4. **Fetch from GitHub** - Gets latest changes
5. **Merge with Auto-Resolution** - Merges and resolves conflicts automatically
6. **Verify Status** - Confirms sync completed successfully

### Conflict Resolution Strategy:

- **Local changes**: Automatically stashed (can be recovered with `git stash pop`)
- **Merge conflicts**: Automatically resolved by accepting GitHub version
- **Failed merges**: Automatically reset to match GitHub exactly

---

## Troubleshooting

### If sync still fails:

1. **Check SSH connection:**
   ```powershell
   plink -ssh -pw aituner aituner@192.168.1.214 "echo 'Test'"
   ```

2. **Check Pi repository exists:**
   ```powershell
   plink -ssh -pw aituner aituner@192.168.1.214 "cd ~/AITUNER/2025-AI-TUNER-AGENTV3 && git status"
   ```

3. **Manual fix on Pi:**
   ```bash
   cd ~/AITUNER/2025-AI-TUNER-AGENTV3
   git stash
   git reset --hard origin/main
   git pull origin main
   ```

---

## Recovery: Getting Stashed Changes Back

If you had local changes that were stashed:

```bash
# On Pi
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
git stash list          # See all stashes
git stash show -p       # Preview latest stash
git stash pop           # Apply and remove latest stash
```

---

**Always use `sync_to_pi5_robust.ps1` for guaranteed success!** 🎯

