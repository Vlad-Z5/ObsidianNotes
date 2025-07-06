Fundamental Git operations for tracking changes, committing work, and viewing history.

## Repository Operations

```bash
git init # Initialize new repository
git clone https://github.com/user/repo.git # Clone existing repository
git status # Check repository status
git diff # Working directory vs staging
git diff --staged # Staging vs last commit
git diff HEAD~1 # Current vs previous commit
```

## Adding and Committing

```bash
git add file.txt # Stage files
git add . # Stage all changes
git add -A # Stage all including deletions

git commit -m "Commit message" # Commit changes
git commit -am "Add and commit in one step" # Not recommended
git commit --amend # Amend last commit
```

## Viewing History

```bash
git log # Show commit history
git log --oneline
git log --graph --all
git log -p # Show patches
git log --since="2 weeks ago"

git show <commit-hash> # Show specific commit
git show HEAD~2 # Show commit 2 steps back
```

## Undoing Changes

```bash
git reset HEAD file.txt # Unstage files
git checkout -- file.txt # Discard working directory changes (old syntax)
git restore file.txt # Discard working directory changes (new syntax)

git reset --soft HEAD~1 # Undo commits, keep changes staged
git reset --mixed HEAD~1 # Undo commits, keep changes unstaged
git reset --hard HEAD~1 # Undo commits, discard all changes
```

## File Operations

```bash
git rm file.txt # Remove files
git rm --cached file.txt # Remove from Git but keep file
git mv old.txt new.txt # Move/rename files
```
