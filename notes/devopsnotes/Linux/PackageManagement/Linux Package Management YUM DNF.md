# Linux Package Management YUM DNF

**YUM (Yellowdog Updater Modified)** and **DNF (Dandified YUM)** are package management systems for Red Hat-based distributions including RHEL, CentOS, Fedora, and Rocky Linux.

## DNF Command Structure

### Package Information and Search
```bash
# List packages
dnf list                           # List all packages
dnf list installed                 # List installed packages
dnf list available                 # List available packages
dnf list updates                   # List packages with updates
dnf list obsoletes                 # List obsoleted packages

# Search packages
dnf search "keyword"               # Search package names and descriptions
dnf search --all "keyword"         # Search all package metadata
dnf provides /path/to/file         # Find package providing file
dnf provides "*/command"           # Find package providing command

# Package details
dnf info package_name              # Show package details
dnf info --installed package_name  # Show installed package info
dnf repoquery package_name         # Query package information
dnf repoquery --requires package_name  # Show dependencies
```

### Package Installation and Removal
```bash
# Basic operations
dnf check-update                   # Check for updates
dnf update                         # Update all packages
dnf update package_name            # Update specific package
dnf upgrade                        # Upgrade all packages (same as update)

# Install packages
dnf install package_name           # Install package
dnf install package_name-version   # Install specific version
dnf install package1 package2      # Install multiple packages
dnf install ./local_package.rpm    # Install local RPM file
dnf reinstall package_name         # Reinstall package

# Remove packages
dnf remove package_name            # Remove package
dnf erase package_name             # Remove package (alternative)
dnf autoremove                     # Remove unused dependencies
dnf autoremove package_name        # Remove package and unused dependencies

# Cache management
dnf clean all                      # Clean all cache
dnf clean packages                 # Clean package cache
dnf clean metadata                 # Clean metadata cache
dnf makecache                      # Download metadata
```

## Repository Management

### Repository Configuration
```bash
# Repository configuration directory
/etc/yum.repos.d/                  # Repository configuration files

# Custom repository file
cat << 'EOF' > /etc/yum.repos.d/custom.repo
[custom-repo]
name=Custom Repository
baseurl=https://repo.example.com/packages/
enabled=1
gpgcheck=1
gpgkey=https://repo.example.com/keys/RPM-GPG-KEY
priority=1
cost=100
EOF

# Repository with multiple URLs
cat << 'EOF' > /etc/yum.repos.d/multi-url.repo
[multi-url-repo]
name=Multi URL Repository
baseurl=https://mirror1.example.com/packages/
        https://mirror2.example.com/packages/
        https://mirror3.example.com/packages/
enabled=1
gpgcheck=1
gpgkey=https://example.com/RPM-GPG-KEY
EOF
```

### Repository Operations
```bash
# Repository management
dnf config-manager --add-repo https://repo.example.com/repo.repo
dnf config-manager --enable repository_name
dnf config-manager --disable repository_name
dnf config-manager --set-enabled repository_name
dnf config-manager --set-disabled repository_name

# Repository information
dnf repolist                       # List enabled repositories
dnf repolist --all                 # List all repositories
dnf repolist --disabled            # List disabled repositories
dnf repoinfo repository_name       # Repository details

# Repository priority and cost
dnf config-manager --save --setopt=repository_name.priority=1
dnf config-manager --save --setopt=repository_name.cost=100
```

## Advanced DNF Operations

### Package Groups
```bash
# Group management
dnf group list                     # List package groups
dnf group list --hidden            # Include hidden groups
dnf group info "Development Tools" # Group information
dnf group install "Development Tools"  # Install group
dnf group remove "Development Tools"   # Remove group
dnf group upgrade "Development Tools"  # Upgrade group

# Environment groups
dnf group list --environments      # List environment groups
dnf group install --with-optional "Server with GUI"
```

### Package History and Rollback
```bash
# Transaction history
dnf history                        # Show transaction history
dnf history list                   # Alternative listing
dnf history info transaction_id    # Transaction details
dnf history info last              # Last transaction info

# Rollback operations
dnf history undo transaction_id    # Rollback transaction
dnf history redo transaction_id    # Redo transaction
dnf history rollback transaction_id # Rollback to specific transaction

# History cleanup
dnf history userinstalled          # Show user-installed packages
```

### Package Versioning
```bash
# Version management
dnf --showduplicates list package_name  # Show all available versions
dnf list --showduplicates package_name  # Alternative syntax
dnf downgrade package_name          # Downgrade to previous version
dnf install package_name-version-release.arch  # Install specific version

# Version locking
dnf install 'dnf-command(versionlock)'  # Install versionlock plugin
dnf versionlock add package_name    # Lock package version
dnf versionlock list                # List locked packages
dnf versionlock delete package_name # Unlock package
```

## YUM/DNF Configuration

### Main Configuration File
```bash
# Main configuration: /etc/dnf/dnf.conf
cat << 'EOF' > /etc/dnf/dnf.conf
[main]
# Core settings
gpgcheck=1                         # Verify GPG signatures
installonly_limit=3                # Keep only 3 kernels
clean_requirements_on_remove=True  # Clean unused dependencies
best=False                         # Don't require best candidate
skip_if_unavailable=True           # Skip unavailable repositories

# Performance settings
fastestmirror=True                 # Use fastest mirror
max_parallel_downloads=10          # Parallel downloads
deltarpm=true                      # Use delta RPMs
timeout=60                         # Network timeout

# Cache settings
keepcache=False                    # Don't keep packages after install
cachedir=/var/cache/dnf            # Cache directory
metadata_expire=48h                # Metadata expiration time

# Logging
logdir=/var/log                    # Log directory
debuglevel=2                       # Debug level (0-10)
EOF
```

### Repository Template
```bash
# Standard repository template
cat << 'EOF' > /etc/yum.repos.d/template.repo
[repository-id]
name=Human Readable Repository Name
baseurl=https://repo.example.com/path/
enabled=1                          # 1=enabled, 0=disabled
gpgcheck=1                         # Verify signatures
gpgkey=https://example.com/RPM-GPG-KEY
priority=99                        # Repository priority (1-99)
cost=1000                          # Repository cost
includepkgs=package1 package2      # Include only these packages
exclude=package3 package4          # Exclude these packages
enablegroups=1                     # Enable group functionality
retries=10                         # Download retries
timeout=60                         # Timeout in seconds
throttle=0                         # Bandwidth throttle (bytes/sec)
bandwidth=0                        # Bandwidth limit (bytes/sec)
mirrorlist=https://example.com/mirrors  # Mirror list URL
metalink=https://example.com/metalink   # Metalink URL
EOF
```

## DNF Plugins

### Popular DNF Plugins
```bash
# Install useful plugins
dnf install dnf-plugins-core       # Core plugins
dnf install dnf-automatic          # Automatic updates
dnf install python3-dnf-plugin-versionlock  # Version locking

# Plugin usage
dnf config-manager                 # Repository management
dnf download package_name          # Download packages only
dnf repoquery                      # Query repositories
dnf builddep package_name          # Install build dependencies
```

### DNF Automatic Updates
```bash
# Configure automatic updates
cat << 'EOF' > /etc/dnf/automatic.conf
[commands]
upgrade_type = security            # security, bugfix, enhancement, newpackage
random_sleep = 0                   # Random delay (0-300 seconds)

[emitters]
emit_via = stdio                   # Output method
system_name = hostname             # System identifier

[command_email]
email_from = root@localhost
email_to = admin@example.com
email_host = localhost
EOF

# Enable automatic updates
systemctl enable --now dnf-automatic.timer
systemctl status dnf-automatic.timer
```

## DNF Troubleshooting

### Common Issues and Solutions
```bash
# Fix repository problems
dnf clean all                     # Clear all cache
dnf makecache                     # Rebuild cache
dnf check                         # Check for problems

# Dependency issues
dnf install --best --allowerasing package_name
dnf install --nobest package_name # Allow non-optimal packages
dnf install --skip-broken package_name

# Reset repository metadata
rm -rf /var/cache/dnf/*           # Clear cache
dnf clean all                     # Clean all cache
dnf makecache                     # Rebuild metadata
```

### Database Reconstruction
```bash
# Rebuild RPM database
rpm --rebuilddb                   # Rebuild RPM database
rpm --initdb                      # Initialize new database

# Verify package integrity
rpm -Va                           # Verify all packages
rpm -V package_name               # Verify specific package
```

## DNF Security Features

### GPG Key Management
```bash
# Import GPG keys
rpm --import https://example.com/RPM-GPG-KEY
rpm --import /path/to/key.asc

# List imported keys
rpm -q gpg-pubkey                 # List all imported keys
rpm -qi gpg-pubkey-keyid          # Show key details

# Verify package signatures
rpm --checksig package.rpm        # Check package signature
dnf install --nogpgcheck package  # Skip GPG check (not recommended)
```

### Security Updates
```bash
# Security-focused operations
dnf updateinfo list security      # List security updates
dnf updateinfo info security      # Security update details
dnf upgrade --security            # Install only security updates

# Advisory information
dnf updateinfo list               # List all advisories
dnf updateinfo info RHSA-2021:1234  # Specific advisory info
```

## Performance Optimization

### Mirror Management
```bash
# Fastest mirror configuration
dnf install dnf-plugin-fastestmirror
echo "fastestmirror=True" >> /etc/dnf/dnf.conf

# Mirror selection
dnf config-manager --save --setopt=*.fastestmirror=True
```

### Parallel Downloads
```bash
# Enable parallel downloads
echo "max_parallel_downloads=10" >> /etc/dnf/dnf.conf
echo "fastestmirror=True" >> /etc/dnf/dnf.conf
```

## DNF Automation Scripts

### System Update Script
```bash
#!/bin/bash
# dnf-update.sh

echo "Starting DNF update process..."

# Check for updates
echo "Checking for updates..."
UPDATES=$(dnf check-update --quiet | wc -l)

if [ $UPDATES -gt 0 ]; then
    echo "Found $UPDATES updates available."

    # Update system
    echo "Updating system packages..."
    dnf update -y

    # Clean cache
    echo "Cleaning package cache..."
    dnf clean packages

    # Remove unused packages
    echo "Removing unused packages..."
    dnf autoremove -y

    # Check if reboot required
    if [ -f /var/run/reboot-required ]; then
        echo "Reboot required after updates."
    fi
else
    echo "No updates available."
fi

echo "DNF update process completed."
```

### Repository Management Script
```bash
#!/bin/bash
# manage-repos.sh

case "$1" in
    list)
        dnf repolist --all
        ;;
    enable)
        dnf config-manager --enable "$2"
        ;;
    disable)
        dnf config-manager --disable "$2"
        ;;
    info)
        dnf repoinfo "$2"
        ;;
    clean)
        dnf clean all
        dnf makecache
        ;;
    *)
        echo "Usage: $0 {list|enable|disable|info|clean} [repository]"
        exit 1
        ;;
esac
```

### Package Maintenance Script
```bash
#!/bin/bash
# dnf-maintenance.sh

echo "=== DNF System Maintenance ==="

# Update metadata
echo "1. Updating repository metadata..."
dnf makecache --refresh

# Show available updates
echo "2. Available updates:"
dnf check-update | head -20

# Clean old packages
echo "3. Cleaning package cache..."
dnf clean packages

# Remove orphaned packages
echo "4. Removing orphaned packages..."
dnf autoremove -y

# Show package history
echo "5. Recent package history:"
dnf history list | head -10

echo "=== Maintenance completed ==="
```