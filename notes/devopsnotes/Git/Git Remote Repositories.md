**Purpose:** Collaborate with others by sharing code through remote repositories on platforms like GitHub, GitLab, or Bitbucket.

## Remote Management

```bash
git remote -v # List remotes

git remote add origin https://github.com/user/repo.git # Add remote
git remote add upstream https://github.com/original/repo.git

git remote remove origin # Remove remote

git remote rename origin upstream # Rename remote
```

## Fetching and Pulling

```bash
# Fetch changes (no merge)
git fetch origin
git fetch --all

# Pull changes (fetch + merge)
git pull origin main
git pull --rebase origin main

# Pull with different strategies
git pull --ff-only origin main
git pull --no-ff origin main
```

## Pushing

```bash
# Push to remote
git push origin main
git push origin feature

git push --all origin # Push all branches

# Push tags
git push --tags origin
git push origin v1.0

git push -u origin feature # Set upstream and push
```

## Remote Branches

```bash
git branch -r # List remote branches
git checkout -b feature origin/feature # Checkout remote branch
git branch --track feature origin/feature # Track remote branch
git push origin --delete feature # Delete remote branch
```

## Collaboration Workflows

```bash
# Fork workflow
git clone https://github.com/you/repo.git
git remote add upstream https://github.com/original/repo.git
git fetch upstream
git checkout -b feature upstream/main

# Update fork
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Common Issues

```bash
# Rejected push (non-fast-forward)
git pull --rebase origin main
git push origin main

# Sync with remote
git fetch origin
git reset --hard origin/main   # Dangerous: loses local changes
```