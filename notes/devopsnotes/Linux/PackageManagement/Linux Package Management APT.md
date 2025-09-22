# Linux Package Management APT

**APT (Advanced Package Tool)** is the primary package management system for Debian-based distributions including Ubuntu, providing comprehensive package installation, dependency resolution, and repository management.

## APT Command Structure

### Package Information and Search
```bash
# List packages
apt list                            # List all available packages
apt list --installed               # List installed packages
apt list --upgradable              # List packages with updates
apt list --manual-installed        # List manually installed packages

# Search packages
apt search "keyword"               # Search package descriptions
apt search --names-only "keyword"  # Search package names only
apt-cache search "keyword"         # Alternative search method

# Package details
apt show package_name              # Show package details
apt-cache show package_name        # Alternative package information
apt-cache policy package_name      # Show package versions and repositories
apt-cache depends package_name     # Show package dependencies
apt-cache rdepends package_name    # Show reverse dependencies
```

### Package Installation and Removal
```bash
# Basic operations
apt update                         # Update package lists
apt upgrade                        # Upgrade all packages
apt full-upgrade                   # Upgrade with dependency changes
apt dist-upgrade                   # Upgrade distribution (legacy)

# Install packages
apt install package_name           # Install package
apt install package_name=version   # Install specific version
apt install package1 package2      # Install multiple packages
apt install ./local_package.deb    # Install local .deb file

# Remove packages
apt remove package_name            # Remove package (keep config)
apt purge package_name             # Remove package and config files
apt autoremove                     # Remove unused dependencies
apt autoremove --purge             # Remove unused dependencies and configs

# Cache management
apt autoclean                      # Remove old package files
apt clean                          # Remove all cached packages
```

## Advanced APT Operations

### Repository Management
```bash
# Edit sources
apt edit-sources                   # Edit sources list with default editor
nano /etc/apt/sources.list         # Direct edit of sources
ls /etc/apt/sources.list.d/        # Additional repository files

# Add repositories
apt-add-repository ppa:user/repo   # Add PPA repository
apt-add-repository "deb http://example.com/repo focal main"
apt-add-repository --remove ppa:user/repo  # Remove repository

# GPG key management
apt-key list                       # List trusted keys
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys KEY_ID
curl -fsSL https://example.com/key.gpg | apt-key add -
```

### Package Pinning and Preferences
```bash
# Package pinning configuration
cat << 'EOF' > /etc/apt/preferences.d/pin-package
Package: nginx
Pin: version 1.18*
Pin-Priority: 1001
EOF

# Pin priority levels
Pin-Priority: 1001     # Downgrade if necessary
Pin-Priority: 990      # Install even if not default
Pin-Priority: 500      # Default priority
Pin-Priority: 100      # Install only if no other version
Pin-Priority: -1       # Never install

# Hold packages from updates
apt-mark hold package_name         # Prevent package updates
apt-mark unhold package_name       # Allow package updates
apt-mark showhold                  # Show held packages
apt-mark manual package_name       # Mark as manually installed
apt-mark auto package_name         # Mark as automatically installed
```

### Package Verification and Information
```bash
# Package ownership and files
dpkg -S /path/to/file             # Which package owns file
dpkg -L package_name              # List files installed by package
apt-file search /path/to/file      # Find package containing file (requires apt-file)
apt-file list package_name        # List files that would be installed

# Package verification
debsums -c                        # Verify installed packages
debsums -l                        # List packages with missing checksums
apt-cache show package_name       # Detailed package information
apt-cache showpkg package_name    # Show package relationships
```

## APT Configuration

### Main Configuration Files
```bash
# Main configuration directory
/etc/apt/apt.conf.d/              # Configuration fragments

# Custom APT configuration
cat << 'EOF' > /etc/apt/apt.conf.d/99custom
APT::Install-Recommends "false";   # Don't install recommended packages
APT::Install-Suggests "false";     # Don't install suggested packages
APT::Get::Assume-Yes "true";       # Assume yes for prompts
APT::Get::Fix-Broken "true";       # Automatically fix broken packages

# Dpkg options
Dpkg::Options {
   "--force-confdef";              # Use default for config conflicts
   "--force-confold";              # Keep old config files
}

# Download settings
Acquire::Retries "3";              # Retry failed downloads
Acquire::http::Timeout "60";       # HTTP timeout
Acquire::https::Verify-Peer "true"; # Verify SSL certificates
EOF
```

### Repository Sources Configuration
```bash
# Main sources list
cat << 'EOF' > /etc/apt/sources.list
# Main Ubuntu repositories
deb http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-backports main restricted universe multiverse

# Source packages (for development)
deb-src http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse
EOF

# Additional repository file
cat << 'EOF' > /etc/apt/sources.list.d/docker.list
deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/ubuntu focal stable
EOF
```

### APT Proxy Configuration
```bash
# HTTP proxy configuration
cat << 'EOF' > /etc/apt/apt.conf.d/01proxy
Acquire::http::Proxy "http://proxy.company.com:8080";
Acquire::https::Proxy "http://proxy.company.com:8080";
Acquire::ftp::Proxy "ftp://proxy.company.com:8080";
EOF

# Proxy authentication
cat << 'EOF' > /etc/apt/apt.conf.d/01proxy-auth
Acquire::http::Proxy "http://username:password@proxy.company.com:8080";
EOF
```

## APT Troubleshooting

### Common Issues and Solutions
```bash
# Fix broken packages
apt --fix-broken install          # Fix dependency issues
apt autoremove                    # Remove broken dependencies
dpkg --configure -a               # Configure unconfigured packages

# Clear package cache
apt clean                         # Remove all cached packages
apt autoclean                     # Remove obsolete cached packages
rm -rf /var/lib/apt/lists/*       # Clear package lists
apt update                        # Rebuild package lists

# Reset package database
dpkg --audit                      # Check for problems
dpkg --verify                     # Verify package integrity
```

### Lock File Issues
```bash
# Remove lock files (when APT is not running)
rm /var/lib/apt/lists/lock
rm /var/cache/apt/archives/lock
rm /var/lib/dpkg/lock*

# Check for running processes
ps aux | grep -E 'apt|dpkg'
lsof /var/lib/dpkg/lock
```

## APT Security

### Package Authentication
```bash
# Verify package signatures
apt-key list                      # List trusted keys
apt-key fingerprint               # Show key fingerprints

# Modern key management (Ubuntu 20.04+)
mkdir -p /usr/share/keyrings
curl -fsSL https://example.com/key.gpg | gpg --dearmor -o /usr/share/keyrings/example.gpg

# Repository with specific key
deb [signed-by=/usr/share/keyrings/example.gpg] https://example.com/repo focal main
```

### Security Updates
```bash
# Security-only updates
apt list --upgradable | grep -i security
apt upgrade -s | grep -i security  # Simulate security updates

# Unattended upgrades configuration
cat << 'EOF' > /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
EOF
```

## APT Performance Optimization

### Parallel Downloads
```bash
# Enable parallel downloads (APT 1.0+)
cat << 'EOF' > /etc/apt/apt.conf.d/99parallel
APT::Acquire::Queue-Mode "host";
APT::Acquire::Retries "3";
EOF
```

### Mirror Selection
```bash
# Use fastest mirror (requires apt-transport-https)
cat << 'EOF' > /etc/apt/sources.list
deb mirror://mirrors.ubuntu.com/mirrors.txt focal main restricted universe multiverse
deb mirror://mirrors.ubuntu.com/mirrors.txt focal-updates main restricted universe multiverse
EOF

# Use CDN mirrors
deb http://archive.ubuntu.com/ubuntu focal main
deb http://security.ubuntu.com/ubuntu focal-security main
```

## APT Automation Scripts

### Update Script
```bash
#!/bin/bash
# apt-update.sh

echo "Starting APT update process..."

# Update package lists
echo "Updating package lists..."
apt update

# Check for updates
UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
echo "Available updates: $((UPDATES - 1))"

if [ $UPDATES -gt 1 ]; then
    echo "Upgrading packages..."
    apt upgrade -y

    echo "Removing unnecessary packages..."
    apt autoremove -y

    echo "Cleaning package cache..."
    apt autoclean
else
    echo "No updates available."
fi

echo "APT update process completed."
```

### Package Installation Script
```bash
#!/bin/bash
# install-packages.sh

PACKAGES=(
    "curl"
    "wget"
    "git"
    "vim"
    "htop"
    "tree"
)

echo "Installing essential packages..."

for package in "${PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package "; then
        echo "Installing $package..."
        apt install -y "$package"
    else
        echo "$package is already installed."
    fi
done

echo "Package installation completed."
```

### System Maintenance Script
```bash
#!/bin/bash
# apt-maintenance.sh

echo "=== APT System Maintenance ==="

# Update package database
echo "1. Updating package database..."
apt update

# Show available updates
echo "2. Available updates:"
apt list --upgradable

# Clean package cache
echo "3. Cleaning package cache..."
apt autoclean

# Remove orphaned packages
echo "4. Removing orphaned packages..."
apt autoremove --purge -y

# Verify package integrity
echo "5. Verifying package integrity..."
debsums -c 2>/dev/null | head -10

echo "=== Maintenance completed ==="
```