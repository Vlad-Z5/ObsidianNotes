# Linux Package Management Repository Management

**Repository management** involves creating, maintaining, and distributing custom package repositories for internal software distribution, mirror management, and enterprise package deployment.

## Creating Custom Repositories

### Debian Repository Setup

#### Repository Structure
```bash
# Create Debian repository structure
mkdir -p /var/www/html/repo/{conf,dists,pool,db}
cd /var/www/html/repo

# Repository configuration
cat << 'EOF' > conf/distributions
Origin: Company Name
Label: company-repo
Codename: focal
Architectures: amd64 arm64 source
Components: main contrib non-free
Description: Company Internal Repository
SignWith: YOUR_GPG_KEY_ID
DebIndices: Packages Release . .gz .bz2
DscIndices: Sources Release .gz .bz2
Contents: .gz .bz2
EOF

# Optional: Multiple distributions
cat << 'EOF' >> conf/distributions

Origin: Company Name
Label: company-repo
Codename: jammy
Architectures: amd64 arm64 source
Components: main contrib non-free
Description: Company Internal Repository (Ubuntu 22.04)
SignWith: YOUR_GPG_KEY_ID
DebIndices: Packages Release . .gz .bz2
DscIndices: Sources Release .gz .bz2
Contents: .gz .bz2
EOF
```

#### Repository Operations
```bash
# Install reprepro
apt install reprepro

# Add packages to repository
reprepro -b /var/www/html/repo includedeb focal package.deb
reprepro -b /var/www/html/repo includedeb jammy package.deb

# Add source packages
reprepro -b /var/www/html/repo includedsc focal package.dsc

# List packages in repository
reprepro -b /var/www/html/repo list focal
reprepro -b /var/www/html/repo listmatched focal '*'

# Remove packages
reprepro -b /var/www/html/repo remove focal package_name
reprepro -b /var/www/html/repo removefilter focal 'Priority (== extra)'

# Update repository indexes
reprepro -b /var/www/html/repo export focal
```

#### GPG Key Management
```bash
# Generate GPG key for repository signing
gpg --full-generate-key
# Select: (1) RSA and RSA, 4096 bits, no expiration
# Enter: Real name, Email, Comment

# Export public key
gpg --armor --export your_email@company.com > /var/www/html/repo/key.gpg

# Configure reprepro to use the key
gpg --list-secret-keys --keyid-format LONG
# Copy the KEY_ID and update conf/distributions
```

### RPM Repository Setup

#### Repository Structure
```bash
# Create RPM repository structure
mkdir -p /var/www/html/repo/{packages,repodata}
cd /var/www/html/repo

# Copy RPM packages
cp /path/to/*.rpm packages/

# Install createrepo tools
dnf install createrepo_c rpm-sign
```

#### Repository Creation
```bash
# Create repository metadata
createrepo --database /var/www/html/repo/

# Update repository (after adding packages)
createrepo --update /var/www/html/repo/

# Sign repository metadata
gpg --detach-sign --armor /var/www/html/repo/repodata/repomd.xml

# Create repository groups (optional)
cat << 'EOF' > comps.xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
  <group>
    <id>company-tools</id>
    <name>Company Tools</name>
    <description>Internal company applications</description>
    <default>false</default>
    <uservisible>true</uservisible>
    <packagelist>
      <packagereq type="mandatory">company-app1</packagereq>
      <packagereq type="default">company-app2</packagereq>
    </packagelist>
  </group>
</comps>
EOF

createrepo --groupfile comps.xml /var/www/html/repo/
```

#### RPM Repository Automation
```bash
#!/bin/bash
# update-rpm-repo.sh

REPO_DIR="/var/www/html/repo"
PACKAGE_DIR="/incoming/packages"

# Copy new packages
find "$PACKAGE_DIR" -name "*.rpm" -newer "$REPO_DIR/.last_update" -exec cp {} "$REPO_DIR/packages/" \;

# Update repository
createrepo --update "$REPO_DIR"

# Sign metadata
gpg --detach-sign --armor "$REPO_DIR/repodata/repomd.xml"

# Update timestamp
touch "$REPO_DIR/.last_update"

echo "Repository updated: $(date)"
```

## Client Repository Configuration

### Debian Client Setup
```bash
# Add repository to sources
echo "deb https://repo.company.com focal main" > /etc/apt/sources.list.d/company.list
echo "deb-src https://repo.company.com focal main" >> /etc/apt/sources.list.d/company.list

# Add GPG key
wget -qO - https://repo.company.com/key.gpg | apt-key add -

# Modern GPG key management (Ubuntu 20.04+)
wget -qO - https://repo.company.com/key.gpg | gpg --dearmor -o /usr/share/keyrings/company.gpg
echo "deb [signed-by=/usr/share/keyrings/company.gpg] https://repo.company.com focal main" > /etc/apt/sources.list.d/company.list

# Update package lists
apt update
```

### RPM Client Setup
```bash
# Create repository configuration
cat << 'EOF' > /etc/yum.repos.d/company.repo
[company-repo]
name=Company Repository
baseurl=https://repo.company.com/
enabled=1
gpgcheck=1
gpgkey=https://repo.company.com/RPM-GPG-KEY-company
priority=1
cost=100
EOF

# Import GPG key
rpm --import https://repo.company.com/RPM-GPG-KEY-company

# Update repository metadata
dnf makecache
```

## Mirror Management

### APT Mirror Setup
```bash
# Install apt-mirror
apt install apt-mirror

# Configure mirror
cat << 'EOF' > /etc/apt/mirror.list
# Mirror configuration
set base_path /var/spool/apt-mirror
set mirror_path $base_path/mirror
set skel_path $base_path/skel
set var_path $base_path/var
set cleanscript $var_path/clean.sh
set defaultarch amd64
set postmirror_script $var_path/postmirror.sh
set run_postmirror 0
set nthreads 20
set _tilde 0

# Ubuntu repositories to mirror
deb http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu focal-backports main restricted universe multiverse

# Source packages (optional)
deb-src http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse

# Cleanup old packages
clean http://archive.ubuntu.com/ubuntu
EOF

# Run mirror synchronization
apt-mirror /etc/apt/mirror.list
```

### DNF Mirror Setup
```bash
# Install reposync
dnf install dnf-plugins-core

# Sync specific repository
dnf reposync --repoid=fedora --download-metadata --download-path=/var/www/html/mirror/

# Sync with architecture filter
dnf reposync --repoid=fedora --arch=x86_64 --download-metadata --download-path=/var/www/html/mirror/

# Create local repository from synced packages
createrepo /var/www/html/mirror/fedora/
```

## Repository Automation

### Automated Repository Updates
```bash
#!/bin/bash
# automated-repo-update.sh

REPO_TYPE="$1"  # deb or rpm
REPO_DIR="/var/www/html/repo"
LOG_FILE="/var/log/repo-update.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

case "$REPO_TYPE" in
    deb)
        log "Starting Debian repository update"

        # Process new packages
        for pkg in /incoming/packages/*.deb; do
            if [ -f "$pkg" ]; then
                log "Adding package: $(basename "$pkg")"
                reprepro -b "$REPO_DIR" includedeb focal "$pkg"
                mv "$pkg" /processed/
            fi
        done

        # Export repository
        reprepro -b "$REPO_DIR" export focal
        log "Debian repository update completed"
        ;;

    rpm)
        log "Starting RPM repository update"

        # Copy new packages
        find /incoming/packages -name "*.rpm" -exec cp {} "$REPO_DIR/packages/" \;

        # Update repository metadata
        createrepo --update "$REPO_DIR"

        # Sign metadata
        gpg --detach-sign --armor "$REPO_DIR/repodata/repomd.xml"

        log "RPM repository update completed"
        ;;

    *)
        echo "Usage: $0 {deb|rpm}"
        exit 1
        ;;
esac
```

### Repository Health Check
```bash
#!/bin/bash
# repo-health-check.sh

REPO_DIR="/var/www/html/repo"
ALERT_EMAIL="admin@company.com"

check_repo_health() {
    local repo_type="$1"
    local errors=0

    case "$repo_type" in
        deb)
            # Check repository structure
            if [ ! -d "$REPO_DIR/dists" ]; then
                echo "ERROR: Missing dists directory"
                ((errors++))
            fi

            # Check GPG signature
            if ! gpg --verify "$REPO_DIR/dists/focal/Release.gpg" "$REPO_DIR/dists/focal/Release" 2>/dev/null; then
                echo "ERROR: Invalid GPG signature"
                ((errors++))
            fi

            # Check package integrity
            reprepro -b "$REPO_DIR" check focal
            ;;

        rpm)
            # Check repository metadata
            if [ ! -f "$REPO_DIR/repodata/repomd.xml" ]; then
                echo "ERROR: Missing repository metadata"
                ((errors++))
            fi

            # Check GPG signature
            if [ ! -f "$REPO_DIR/repodata/repomd.xml.asc" ]; then
                echo "WARNING: Missing GPG signature"
            fi
            ;;
    esac

    return $errors
}

# Check repository health
if check_repo_health "deb"; then
    echo "Repository health check passed"
else
    echo "Repository health check failed" | mail -s "Repository Alert" "$ALERT_EMAIL"
fi
```

## Enterprise Repository Management

### Multi-Environment Setup
```bash
# Development repository
cat << 'EOF' > conf/distributions.dev
Origin: Company Name
Label: company-repo-dev
Codename: focal-dev
Architectures: amd64 arm64
Components: main
Description: Company Development Repository
SignWith: DEV_GPG_KEY_ID
EOF

# Staging repository
cat << 'EOF' > conf/distributions.staging
Origin: Company Name
Label: company-repo-staging
Codename: focal-staging
Architectures: amd64 arm64
Components: main
Description: Company Staging Repository
SignWith: STAGING_GPG_KEY_ID
EOF

# Production repository
cat << 'EOF' > conf/distributions.prod
Origin: Company Name
Label: company-repo-prod
Codename: focal-prod
Architectures: amd64 arm64
Components: main
Description: Company Production Repository
SignWith: PROD_GPG_KEY_ID
EOF
```

### Package Promotion Pipeline
```bash
#!/bin/bash
# promote-package.sh

PACKAGE="$1"
SOURCE_ENV="$2"
TARGET_ENV="$3"

case "$TARGET_ENV" in
    staging)
        # Promote from dev to staging
        reprepro -b /var/www/html/repo copy focal-staging focal-dev "$PACKAGE"
        ;;
    production)
        # Promote from staging to production
        reprepro -b /var/www/html/repo copy focal-prod focal-staging "$PACKAGE"
        ;;
    *)
        echo "Usage: $0 <package> <source_env> <target_env>"
        echo "Valid environments: staging, production"
        exit 1
        ;;
esac

echo "Package $PACKAGE promoted from $SOURCE_ENV to $TARGET_ENV"
```

## Repository Security

### Access Control
```bash
# Nginx configuration for repository access
cat << 'EOF' > /etc/nginx/sites-available/repo
server {
    listen 443 ssl;
    server_name repo.company.com;

    ssl_certificate /etc/ssl/certs/repo.company.com.crt;
    ssl_certificate_key /etc/ssl/private/repo.company.com.key;

    root /var/www/html/repo;
    autoindex on;

    # Restrict access to internal networks
    allow 10.0.0.0/8;
    allow 192.168.0.0/16;
    deny all;

    # Basic authentication for write access
    location ~ ^/(incoming|admin)/ {
        auth_basic "Repository Admin";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # Public read access to repository
    location / {
        try_files $uri $uri/ =404;
    }
}
EOF

# Create htpasswd file
htpasswd -c /etc/nginx/.htpasswd admin
```

### Repository Backup
```bash
#!/bin/bash
# backup-repository.sh

REPO_DIR="/var/www/html/repo"
BACKUP_DIR="/backup/repository"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup repository
tar czf "$BACKUP_DIR/repo_backup_$DATE.tar.gz" -C "$(dirname "$REPO_DIR")" "$(basename "$REPO_DIR")"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "repo_backup_*.tar.gz" -mtime +7 -delete

echo "Repository backup completed: repo_backup_$DATE.tar.gz"
```