**Purpose:** Customize Git behavior through configuration files and settings for user preferences, aliases, and workflow optimization.

## Configuration Levels

bash

```bash
git config --system # System-wide (all users)
git config --global # User-wide (current user)
git config --local # Repository-specific

# View configuration
git config --list
git config --global --list
git config user.name
```

## Essential Settings

bash

```bash
# User identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Default editor
git config --global core.editor "vim"
git config --global core.editor "code --wait"

git config --global init.defaultBranch main # Default branch name

# Line ending handling
git config --global core.autocrlf true    # Windows
git config --global core.autocrlf input   # Mac/Linux
```

## Useful Aliases

bash

```bash
# Basic shortcuts
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# Advanced aliases
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'
git config --global alias.lg 'log --oneline --graph --all'
git config --global alias.pushf 'push --force-with-lease'
```

## Merge and Diff Tools

bash

```bash
# Configure merge tool
git config --global merge.tool vimdiff
git config --global merge.tool meld

# Configure diff tool
git config --global diff.tool vimdiff
git config --global diff.tool meld

# Use tools
git mergetool
git difftool
```

## Performance Settings

bash

```bash
git config --global core.preloadindex true # Enable parallel index operations
git config --global core.fsmonitor true # Enable file system monitor

# Optimize for large repositories
git config --global core.commitgraph true
git config --global gc.writecommitgraph true
```

## Security Settings

bash

```bash
# GPG signing
git config --global user.signingkey <key-id>
git config --global commit.gpgsign true

# SSH key
git config --global user.signingkey ~/.ssh/id_rsa.pub
```

## Configuration Files

- **System:** `/etc/gitconfig` (Linux/Mac), `C:\Program Files\Git\etc\gitconfig` (Windows)
- **Global:** `~/.gitconfig` or `~/.config/git/config`
- **Local:** `.git/config` (repository-specific)

## Common Configurations

bash

```bash
# Colorful output
git config --global color.ui auto

# Better diff algorithm
git config --global diff.algorithm histogram

# Rebase by default on pull
git config --global pull.rebase true

# Prune remote branches automatically
git config --global fetch.prune true
```