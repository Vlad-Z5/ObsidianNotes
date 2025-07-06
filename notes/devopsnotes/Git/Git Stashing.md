**Purpose:** Temporarily save uncommitted changes to switch branches or pull updates without committing incomplete work.

## Basic Stashing

```bash
# Stash current changes
git stash
git stash save "Work in progress on feature"

git stash list # List stashes

git stash apply # Apply most recent stash
git stash apply stash@{2} # Apply specific stash

git stash pop # Apply and remove most recent stash
git stash pop stash@{1} # Apply and remove specific stash
```

## Stash Management

```bash
git stash show # Summary of most recent stash
git stash show -p # Full diff of most recent stash
git stash show stash@{1} # Summary of specific stash

git stash drop # Remove most recent stash
git stash drop stash@{1} # Remove specific stash
git stash clear # Remove all stashes
```

## Advanced Stashing

```bash
git stash push -m "message" file1.txt file2.txt # Stash specific files

# Stash including untracked files
git stash -u
git stash --include-untracked

# Stash everything including ignored files
git stash -a
git stash --all

git stash --keep-index # Keep staged changes while stashing others
```

## Stash Branches

```bash
# Create branch from stash
git stash branch new-feature stash@{1}

# This is equivalent to:
git checkout -b new-feature
git stash apply stash@{1}
git stash drop stash@{1}
```

## Common Workflows

```bash
# Quick branch switch
git stash
git checkout other-branch
# Do work
git checkout original-branch
git stash pop

# Pull with uncommitted changes
git stash
git pull origin main
git stash pop

# Selective stashing
git add file1.txt # Stage files to keep
git stash --keep-index # Stash rest while keeping staged
```

## Stash Inspection

```bash
# Show what's in stash
git stash show stash@{0}
git stash show -p stash@{0}

# Compare stash with branch
git diff stash@{0}
git diff stash@{0} main
```