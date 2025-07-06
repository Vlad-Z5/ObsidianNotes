**Purpose:** Rewrite commit history by moving, combining, or editing commits to create a cleaner, more linear history.

## Basic Rebase

```bash
git rebase main # Rebase current branch onto main
git rebase main feature # Rebase specific branch
git rebase --continue # Continue after resolving conflicts
git rebase --abort # Abort rebase
git rebase --skip # Skip current commit
```

## Interactive Rebase

```bash
git rebase -i HEAD~3 # Edit last 3 commits
git rebase -i <commit-hash> # Rebase from specific commit

# Interactive options:
# pick   - Keep commit as is
# reword - Edit commit message
# edit   - Edit commit content
# squash - Combine with previous commit
# fixup  - Combine with previous, discard message
# drop   - Remove commit
```

## Rebase vs Merge

```bash
# Merge (creates merge commit)
git checkout main
git merge feature # History: main → feature → merge commit

# Rebase (linear history)
git checkout feature
git rebase main
git checkout main
git merge feature # Fast-forward merge
# History: main → feature commits in sequence
```

## Advanced Rebase

```bash
git rebase --onto main server client # Rebase onto different base
git rebase --preserve-merges main # Preserve merge commits
git rebase -X theirs main # Prefer their changes
git rebase -X ours main # Prefer our changes
```

## Conflict Resolution

```bash
git status # See conflicted files
# Edit files to resolve
git add resolved-file.txt # Mark as resolved
git rebase --continue # Continue rebase

# Or abort and start over
git rebase --abort
```

## Common Workflows

```bash
# Clean up feature branch before merge
git checkout feature
git rebase -i main # Squash/edit commits
git checkout main
git merge feature # Clean merge

# Update feature with latest main
git checkout feature
git rebase main # Move feature commits to tip of main

# Pull with rebase
git pull --rebase origin main
```

## Golden Rules

- **Never rebase public commits** (pushed to shared repository)
- **Always rebase local commits** before pushing
- **Use rebase for feature branches** to keep history clean
- **Use merge for integration** of completed features