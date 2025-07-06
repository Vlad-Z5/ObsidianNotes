## Repository Structure

- `.git/`: Git repository data
    - `config`: Repository configuration
    - `HEAD`: Current branch pointer
    - `index`: Staging area
    - `objects/`: Git objects (commits, trees, blobs)
    - `refs/`: Branch and tag references
        - `heads/`: Local branches
        - `remotes/`: Remote branches
        - `tags/`: Tags
- `.gitignore`: Files to ignore
- `.gitattributes`: Path-specific settings

## File States

- **Untracked:** New files not in Git
- **Tracked:** Files under Git control
    - **Unmodified:** No changes since last commit
    - **Modified:** Changes made but not staged
    - **Staged:** Changes ready for commit

## Common Configuration Files

- `~/.gitconfig`: Global Git configuration
- `.git/config`: Repository-specific configuration
- `.gitignore`: Project ignore files and patterns
- `~/.gitignore_global`: Global ignore files and patterns