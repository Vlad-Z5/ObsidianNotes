**Purpose:** Create parallel development lines, work on features independently, and merge changes back together.

## Basic Branch Operations

```bash
# List branches
git branch # Local branches
git branch -r # Remote branches  
git branch -a # All branches

# Create and switch branches
git branch feature # Create branch
git checkout feature # Switch to branch
git checkout -b feature # Create and switch

# Modern syntax
git switch feature # Switch to branch
git switch -c feature # Create and switch
```

## Merging

```bash
# Merge branch into current branch
git merge feature # Merge feature into current

# Merge types
git merge --ff-only feature # Fast-forward only
git merge --no-ff feature # Always create merge commit
git merge --squash feature # Squash commits into one
```

## Branch Management

```bash
# Delete branches
git branch -d feature # Delete merged branch
git branch -D feature # Force delete unmerged

# Rename branch
git branch -m old-name new-name # Rename branch

# Track remote branch
git branch --set-upstream-to=origin/feature feature # Track remote
```

## Merge Conflicts

```bash
# When conflicts occur
git status # Show conflicted files
# Edit files to resolve conflicts
git add conflicted-file.txt # Mark as resolved
git commit # Complete merge

# Abort merge
git merge --abort # Cancel the merge
```

## Common Workflows

```bash
# Feature branch workflow
git checkout -b feature # Create from main/develop
# Make changes and commits
git checkout main # Switch back
git merge feature # Merge feature into main
git branch -d feature # Cleanup

# Hotfix workflow
git checkout -b hotfix main # Hotfix from main
# Fix and commit
git checkout main # Switch back
git merge hotfix # Merge fix into main
git checkout develop # Switch to dev
git merge hotfix # Merge fix into develop
git branch -d hotfix # Cleanup
```

## Branch Comparison

```bash
# Show differences between branches
git diff main..feature # Code changes
git log main..feature # Commit history
git show-branch main feature # Branch tips and history
```