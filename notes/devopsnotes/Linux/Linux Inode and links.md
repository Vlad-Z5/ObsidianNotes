# Linux Inodes and Links

## Understanding Inodes

**Inode** (Index Node) stores metadata about a file, excluding its name:
- Inode number (unique within filesystem)
- File type (regular, directory, symlink, etc.)
- Permissions (read, write, execute)
- Owner UID and GID
- File size in bytes
- Timestamps (access, modify, change times)
- Link count (number of hard links)
- Pointers to data blocks on disk

**Key Concept**: Filenames are just human-readable pointers to inodes. The actual file data and metadata are stored in the inode structure.

## Link Types and Usage

### **Hard Links**
- Direct pointer to the same inode
- Multiple names for one file
- Data remains until ALL hard links are deleted
- Cannot cross filesystem boundaries
- Cannot link to directories (except . and ..)

```bash
# Create hard link
ln original_file hard_link_name

# Check inode numbers (should be identical)
ls -li original_file hard_link_name

# View link count
stat original_file
```

### **Soft Links (Symbolic Links)**
- Separate file with its own inode
- Points to a path (not directly to inode)
- Removed if target is deleted (becomes broken link)
- Can cross filesystem boundaries
- Can link to directories

```bash
# Create symbolic link
ln -s /path/to/original symlink_name

# Check link target
readlink symlink_name
readlink -f symlink_name  # Follow all links to final target

# Find broken symbolic links
find /path -type l ! -exec test -e {} \; -print
```

## Practical Applications in DevOps

### **Configuration Management**
```bash
# Link configuration files for easy management
ln -s /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/
ln -s /opt/app/config/production.conf /etc/app/current.conf

# Version-controlled configurations
ln -s /var/config/v2.1/app.conf /etc/app/app.conf
```

### **Application Deployment**
```bash
# Blue-green deployment pattern
ln -sfn /opt/app/releases/v1.2.3 /opt/app/current
systemctl restart myapp  # Uses /opt/app/current

# Easy rollback
ln -sfn /opt/app/releases/v1.2.2 /opt/app/current
systemctl restart myapp
```

## Cross-References
- **[[Linux File Types]]** - Understanding different file types and their inodes
- **[[Linux Filesystem]]** - How inodes fit in filesystem structure
- **[[Linux Commands]]** - Commands for working with links and inodes
- **[[Linux fundamental]]** - Core filesystem concepts