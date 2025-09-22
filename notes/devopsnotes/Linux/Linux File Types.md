
# Linux File Types & DevOps Applications

## File Type Identification

### **Standard File Types (from `ls -l` first character)**
- **Regular File (`-`)**: Normal data file, scripts, binaries, documents
- **Directory (`d`)**: Folder containing files/directories
- **Symbolic Link (`l`)**: Pointer to another file or directory
- **Character Device (`c`)**: Device transferring data character-wise (terminals, serial ports)
- **Block Device (`b`)**: Device transferring data in blocks (hard drives, SSDs)
- **Named Pipe (FIFO) (`p`)**: IPC channel, first-in-first-out queue
- **Socket (`s`)**: IPC endpoint for network/local communication

### **File Type Detection Commands**
```bash
# Basic file type identification
file /path/to/file                     # Identify file type and content
file -b /path/to/file                  # Brief output without filename
file -i /path/to/file                  # MIME type information
file -s /dev/sda1                      # Check filesystem on block device

# Detailed file information
stat /path/to/file                     # Complete file metadata
ls -la /path/to/file                   # Permissions and basic info
lsattr /path/to/file                   # Extended attributes (ext2/3/4)

# Find files by type
find /path -type f                     # Regular files only
find /path -type d                     # Directories only
find /path -type l                     # Symbolic links only
find /path -type s                     # Sockets only
find /path -type p                     # Named pipes only
```

## DevOps-Specific File Types and Applications

### **Configuration Files**

#### **YAML Files (.yml, .yaml)**
```bash
# Common in DevOps for configuration
# Docker Compose, Kubernetes, Ansible, CI/CD pipelines

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))" || echo "Invalid YAML"

# Parse YAML with yq
yq eval '.spec.containers[0].image' k8s-deployment.yaml

# Examples of YAML usage:
# - docker-compose.yml: Container orchestration
# - .gitlab-ci.yml: GitLab CI/CD pipelines
# - ansible-playbook.yml: Infrastructure automation
# - k8s-manifests.yaml: Kubernetes resource definitions
```

#### **JSON Configuration Files (.json)**
```bash
# API configurations, package definitions, configurations

# Validate JSON syntax
python -m json.tool config.json > /dev/null && echo "Valid JSON"

# Parse JSON with jq
jq '.version' package.json
jq '.spec.template.spec.containers[].image' k8s-deployment.json

# Pretty print JSON
jq '.' messy-config.json > formatted-config.json

# Common JSON files in DevOps:
# - package.json: Node.js dependencies
# - tsconfig.json: TypeScript configuration
# - .vscode/settings.json: Editor configuration
```

#### **Environment and Configuration Files**
```bash
# .env files (environment variables)
# .config files (application configuration)
# .ini files (configuration sections)

# Validate environment files
grep -v '^#' .env | grep -v '^$' | grep -v '=' && echo "Invalid .env format"

# Source environment files safely
set -a; source .env; set +a

# Common patterns:
# DATABASE_URL=postgresql://user:pass@localhost/db
# API_KEY=your-secret-key
# DEBUG=true
```

### **Container and Virtualization Files**

#### **Dockerfile and Container Files**
```bash
# Dockerfile analysis
file Dockerfile                        # Should be ASCII text
head -1 Dockerfile                     # Should start with FROM

# Container image analysis
docker image inspect image:tag         # Image metadata
docker history image:tag               # Layer history

# Best practices validation
hadolint Dockerfile                    # Dockerfile linter
dive image:tag                         # Layer analysis tool
```

#### **Kubernetes Manifest Files**
```bash
# Validate Kubernetes YAML
kubectl apply --dry-run=client -f manifest.yaml

# Check resource definitions
kubectl explain deployment.spec.template.spec

# Analyze manifest files
file *.yaml | grep -v "ASCII text"     # Find binary files
find . -name "*.yaml" -exec yamllint {} \;
```

### **Infrastructure as Code Files**

#### **Terraform Files (.tf, .tfvars)**
```bash
# Terraform file validation
terraform fmt -check                   # Check formatting
terraform validate                     # Validate syntax
terraform plan                         # Preview changes

# Analyze Terraform files
find . -name "*.tf" -exec terraform fmt -check {} \;
grep -r "resource\|data\|module" *.tf  # Find resource definitions
```

#### **Ansible Files (.yml)**
```bash
# Ansible playbook validation
ansible-playbook --syntax-check playbook.yml
ansible-lint playbook.yml

# Inventory file validation
ansible-inventory --list -i inventory.ini

# Role structure validation
find roles/ -name "*.yml" -exec ansible-lint {} \;
```

### **Executable and Script Files**

#### **Script File Identification**
```bash
# Identify script interpreters
head -1 script.sh                      # Check shebang line
file script.py                         # Python script detection
file binary_executable                 # Compiled binary detection

# Find executable files
find /usr/local/bin -type f -executable
find . -name "*.sh" -executable

# Security analysis
file /usr/bin/*                        # System binaries analysis
ldd /usr/bin/executable                # Library dependencies
strings binary_file | head -20         # Extract readable strings
```

#### **Binary Analysis for DevOps**
```bash
# Analyze deployed binaries
ldd application_binary                  # Check library dependencies
objdump -p binary | grep NEEDED        # Required shared libraries
readelf -d binary                      # Dynamic section information

# Container binary analysis
docker run --rm -v $(pwd):/app alpine sh -c "ldd /app/binary"
```

### **Special DevOps File Types**

#### **Log Files and Structured Data**
```bash
# Log file analysis
file /var/log/nginx/access.log          # Should be ASCII text
tail -f /var/log/application.log | jq . # JSON log parsing

# Log rotation and compression
find /var/log -name "*.gz" -mtime +30   # Old compressed logs
zcat old_log.gz | grep ERROR            # Search compressed logs

# Structured log analysis
awk '{print $1}' access.log | sort | uniq -c | sort -nr  # IP analysis
jq -r '.timestamp' application.json.log # Extract JSON fields
```

#### **Certificate and Key Files**
```bash
# SSL/TLS certificate analysis
file certificate.crt                   # Should be ASCII text
openssl x509 -in certificate.crt -text -noout

# Private key analysis
file private.key                       # Should be ASCII text
openssl rsa -in private.key -check     # Validate private key

# Certificate chain validation
openssl verify -CAfile ca-bundle.crt certificate.crt

# Common certificate formats:
# .pem: Privacy Enhanced Mail (Base64 encoded)
# .der: Distinguished Encoding Rules (binary)
# .crt/.cer: Certificate files
# .key: Private key files
# .p12/.pfx: PKCS#12 format (contains both cert and key)
```

#### **Archive and Backup Files**
```bash
# Archive file identification
file backup.tar.gz                     # Compressed tar archive
file application.zip                   # ZIP archive
file database.sql.bz2                  # Compressed SQL dump

# Archive content analysis without extraction
tar -tzf archive.tar.gz | head -10     # List contents
unzip -l application.zip               # List ZIP contents
7z l archive.7z                        # List 7zip contents

# Backup integrity verification
sha256sum backup.tar.gz > backup.sha256
sha256sum -c backup.sha256              # Verify integrity
```

### **Database and Data Files**

#### **Database File Analysis**
```bash
# SQLite database files
file database.sqlite3                  # SQLite database
sqlite3 database.sqlite3 ".tables"     # List tables

# MySQL dump files
file mysql_dump.sql                    # ASCII text, SQL dump
head -20 mysql_dump.sql                # Check dump header

# PostgreSQL files
file postgresql.dump                   # PostgreSQL custom format
pg_restore --list postgresql.dump      # List dump contents
```

## File Handling Best Practices for DevOps

### **File Security and Permissions**
```bash
# Secure file permissions for secrets
chmod 600 ~/.ssh/id_rsa               # SSH private keys
chmod 600 /etc/ssl/private/*.key      # SSL private keys
chmod 640 /etc/mysql/my.cnf           # Database config
chmod 644 /etc/nginx/nginx.conf       # Web server config

# Find files with problematic permissions
find /etc -type f -perm /o+w           # World-writable files
find /home -type f -perm /g+w,o+w      # Group/world writable
find / -type f -perm /u+s              # SUID files
find / -type f -perm /g+s              # SGID files
```

### **Automated File Management**
```bash
# File monitoring and automation
inotifywait -m /etc/nginx/ -e modify --format '%w%f' | \
    while read file; do
        nginx -t && systemctl reload nginx
    done

# Configuration file validation before deployment
validate_config() {
    local config_file="$1"
    case "$config_file" in
        *.json) jq empty "$config_file" ;;
        *.yaml|*.yml) python -c "import yaml; yaml.safe_load(open('$config_file'))" ;;
        *.nginx) nginx -t -c "$config_file" ;;
        *.apache) apache2ctl configtest ;;
        *) echo "Unknown config type" && return 1 ;;
    esac
}
```

### **Integration with DevOps Workflows**
```bash
# Pre-commit hooks for file validation
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Validate all configuration files before commit

find . -name "*.json" -exec jq empty {} \;
find . -name "*.yml" -o -name "*.yaml" -exec yamllint {} \;
find . -name "Dockerfile" -exec hadolint {} \;
find . -name "*.tf" -exec terraform fmt -check {} \;
EOF

chmod +x .git/hooks/pre-commit
```

## Cross-References
- **[[Linux Commands]]** - File manipulation and analysis commands
- **[[Linux fundamental]]** - File system concepts and inodes
- **[[Linux Filesystem]]** - Directory structure and file organization
- **[[Linux Security]]** - File permissions and security considerations