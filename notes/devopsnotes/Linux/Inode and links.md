**Inode** stores metadata about a file, excluding its name. Filenames point to inodes

**Hard link** is a direct pointer to the same inode; multiple names, one file. Data remains until all hard links are deleted. Command: ln

**Soft link** is a separate file pointing to a path. It has its own inode and is removed if the target is deleted