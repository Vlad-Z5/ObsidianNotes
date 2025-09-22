# Linux Security Access Control Authentication

**Access control and authentication** manages user accounts, implements strong password policies, secures SSH access, and establishes robust authentication mechanisms for system security.

## User Account Security

### Strong Password Policies

#### PAM Password Configuration
```bash
# Configure password policies with PAM
cat << 'EOF' > /etc/pam.d/common-password
# Password strength requirements
password required pam_pwquality.so retry=3 \
    minlen=12 \
    dcredit=-1 \
    ucredit=-1 \
    lcredit=-1 \
    ocredit=-1 \
    maxrepeat=3 \
    reject_username \
    enforce_for_root

# Password history - prevent reuse of last 12 passwords
password required pam_unix.so use_authtok sha512 shadow remember=12

# Additional password modules
password optional pam_gnome_keyring.so
EOF

# Install password quality library
apt install libpam-pwquality  # Debian/Ubuntu
dnf install libpwquality      # RHEL/CentOS/Fedora
```

#### Password Quality Configuration
```bash
# Configure password quality requirements
cat << 'EOF' > /etc/security/pwquality.conf
# Minimum password length
minlen = 12

# Character class requirements
minclass = 3
dcredit = -1    # At least 1 digit
ucredit = -1    # At least 1 uppercase letter
lcredit = -1    # At least 1 lowercase letter
ocredit = -1    # At least 1 special character

# Additional restrictions
maxrepeat = 3       # Max consecutive identical characters
maxsequence = 3     # Max monotonic character sequence
gecoscheck = 1      # Check against GECOS field
dictcheck = 1       # Check against dictionary words
usercheck = 1       # Check against username
enforcing = 1       # Enforce for all users including root

# Credit settings (negative = minimum required)
difok = 3          # Minimum different characters from old password
maxclassrepeat = 2  # Maximum consecutive characters from same class
retry = 3          # Number of retries allowed
EOF
```

#### Password Aging Policies
```bash
# Set password aging policies in login.defs
cat << 'EOF' >> /etc/login.defs
# Password aging controls
PASS_MAX_DAYS 90    # Maximum password age (days)
PASS_MIN_DAYS 7     # Minimum password age (days)
PASS_WARN_AGE 14    # Password expiration warning (days)
PASS_MIN_LEN 12     # Minimum password length

# Account creation defaults
UMASK 077           # Default file permissions
CREATE_HOME yes     # Create home directory by default
USERGROUPS_ENAB yes # Create group with same name as user
EOF

# Apply password aging to existing users
echo "Applying password aging policies to existing users..."
for user in $(grep -E '^[^:]+:[^:]+:[0-9]{4,}:' /etc/passwd | cut -d: -f1); do
    if [[ "$user" != "nobody" ]]; then
        chage -M 90 -m 7 -W 14 "$user"
        echo "Applied aging policy to user: $user"
    fi
done

# Check current password aging for users
echo "Current password aging status:"
for user in $(grep -E '^[^:]+:[^:]+:[0-9]{4,}:' /etc/passwd | cut -d: -f1 | head -5); do
    echo "User: $user"
    chage -l "$user"
    echo ""
done
```

### Account Management

#### Account Security Audit
```bash
# Create account security audit script
audit_accounts() {
    echo "=== Account Security Audit ==="
    echo "Date: $(date)"
    echo ""

    # Check for users with empty passwords
    echo "Users with empty passwords:"
    awk -F: '($2 == "" || $2 == "!") {print $1}' /etc/shadow

    echo ""

    # Check for duplicate UIDs
    echo "Duplicate UIDs:"
    awk -F: '{print $3}' /etc/passwd | sort | uniq -d

    echo ""

    # Check for users with UID 0 (should only be root)
    echo "Users with UID 0:"
    awk -F: '($3 == 0) {print $1}' /etc/passwd

    echo ""

    # Check for users with no login shell
    echo "System accounts (no login shell):"
    awk -F: '($7 ~ /nologin|false/) {print $1}' /etc/passwd | head -10

    echo ""

    # Check password expiration
    echo "Users with password expiration issues:"
    for user in $(grep -E '^[^:]+:[^:]+:[0-9]{4,}:' /etc/passwd | cut -d: -f1); do
        expiry=$(chage -l "$user" 2>/dev/null | grep "Password expires" | cut -d: -f2 | xargs)
        if [[ "$expiry" == "never" ]]; then
            echo "$user: Password never expires"
        fi
    done
}

# Run account audit
audit_accounts > /tmp/account_audit.txt
cat /tmp/account_audit.txt
```

#### Account Lockout and Security
```bash
# Configure account lockout policies
cat << 'EOF' > /etc/pam.d/common-auth
# Account lockout after failed attempts
auth required pam_faillock.so preauth audit silent deny=5 unlock_time=1800 fail_interval=900

# Standard authentication
auth [success=1 default=ignore] pam_unix.so nullok_secure
auth [default=die] pam_faillock.so authfail audit deny=5 unlock_time=1800 fail_interval=900
auth sufficient pam_faillock.so authsucc audit deny=5 unlock_time=1800 fail_interval=900

# Fallback
auth requisite pam_deny.so
auth required pam_permit.so
EOF

# Account session management
cat << 'EOF' > /etc/pam.d/common-session
# Required session modules
session [default=1] pam_permit.so
session requisite pam_deny.so
session required pam_permit.so

# Optional session modules
session required pam_limits.so
session optional pam_systemd.so
session optional pam_ck_connector.so nox11

# Log session information
session required pam_lastlog.so showfailed
EOF

# Lock unused system accounts
system_accounts=(
    "games" "news" "uucp" "proxy" "www-data" "backup"
    "list" "irc" "gnats" "_apt" "nobody"
)

echo "Locking unused system accounts..."
for account in "${system_accounts[@]}"; do
    if id "$account" &>/dev/null; then
        usermod -L "$account"
        usermod -s /usr/sbin/nologin "$account"
        echo "Locked account: $account"
    fi
done

# Check and report failed login attempts
check_failed_logins() {
    echo "=== Failed Login Attempts ==="

    # Check faillog
    echo "Recent failed login attempts:"
    faillog -a | grep -v "Never" | head -10

    echo ""

    # Check last failed logins from auth log
    if [[ -f /var/log/auth.log ]]; then
        echo "Recent authentication failures:"
        grep "authentication failure" /var/log/auth.log | tail -5
    elif [[ -f /var/log/secure ]]; then
        echo "Recent authentication failures:"
        grep "authentication failure" /var/log/secure | tail -5
    fi
}

check_failed_logins
```

### Sudo Configuration and Management

#### Secure Sudo Configuration
```bash
# Configure secure sudo policies
cat << 'EOF' > /etc/sudoers.d/security-policy
# Sudo security configuration

# Require password for sudo (disable NOPASSWD)
Defaults passwd_timeout=5
Defaults timestamp_timeout=15
Defaults logfile="/var/log/sudo.log"
Defaults log_input, log_output
Defaults use_pty
Defaults lecture="always"

# Security restrictions
Defaults requiretty
Defaults env_reset
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Allowed environment variables
Defaults env_keep += "LANG LC_ADDRESS LC_CTYPE LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT"
Defaults env_keep += "LC_MESSAGES LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE"
Defaults env_keep += "LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET XAPPLRESDIR"

# Command aliases for specific tasks
Cmnd_Alias NETWORKING = /sbin/route, /sbin/ifconfig, /bin/ping, /sbin/dhclient, /usr/bin/net, /sbin/iptables, /usr/bin/rfcomm, /usr/bin/wvdial, /sbin/iwconfig, /sbin/mii-tool
Cmnd_Alias SOFTWARE = /bin/rpm, /usr/bin/up2date, /usr/bin/yum, /usr/bin/apt-get, /usr/bin/dpkg, /usr/bin/snap
Cmnd_Alias SERVICES = /sbin/service, /sbin/chkconfig, /usr/bin/systemctl, /bin/systemctl
Cmnd_Alias PROCESSES = /bin/nice, /bin/kill, /usr/bin/kill, /usr/bin/killall
Cmnd_Alias STORAGE = /sbin/fdisk, /sbin/sfdisk, /sbin/parted, /sbin/partprobe, /bin/mount, /bin/umount

# User privilege specifications
# Admin group can run all commands
%admin ALL=(ALL:ALL) ALL

# Allow specific groups limited access
%netadmin ALL=(ALL) NETWORKING
%software-mgmt ALL=(ALL) SOFTWARE
%service-mgmt ALL=(ALL) SERVICES

# Individual user examples
# username ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
# username ALL=(ALL) /usr/bin/tail /var/log/nginx/*.log
EOF

# Create sudo log file
touch /var/log/sudo.log
chmod 600 /var/log/sudo.log

# Test sudo configuration
visudo -c -f /etc/sudoers.d/security-policy
```

## SSH Security Hardening

### Advanced SSH Configuration

#### Comprehensive SSH Hardening
```bash
# Backup original SSH configuration
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Create hardened SSH configuration
cat << 'EOF' > /etc/ssh/sshd_config
# SSH Protocol and Network
Protocol 2
Port 2222
AddressFamily inet
ListenAddress 0.0.0.0

# Host Keys
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Cryptography
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
PubkeyAcceptedKeyTypes ssh-rsa,rsa-sha2-256,rsa-sha2-512,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,ssh-ed25519

# Connection Limits and Timeouts
MaxAuthTries 3
MaxSessions 2
MaxStartups 3:30:10
LoginGraceTime 60
ClientAliveInterval 300
ClientAliveCountMax 2

# User and Group Restrictions
AllowGroups sshusers
DenyUsers root guest test
DenyGroups noremote

# Session and Environmental Controls
PermitUserEnvironment no
AcceptEnv LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES
AcceptEnv LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT
AcceptEnv LC_IDENTIFICATION LC_ALL LANGUAGE
AcceptEnv XMODIFIERS

# Forwarding and Tunneling
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no
PermitOpen none

# Logging and Monitoring
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# Miscellaneous Security
StrictModes yes
IgnoreRhosts yes
HostbasedAuthentication no
PrintMotd no
PrintLastLog yes
TCPKeepAlive no
Compression delayed
Banner /etc/ssh/banner

# Subsystem
Subsystem sftp internal-sftp -l INFO -f AUTH
EOF

# Create SSH security banner
cat << 'EOF' > /etc/ssh/banner
********************************************************************************
*                                                                              *
*                           AUTHORIZED ACCESS ONLY                            *
*                                                                              *
*  This system is for the use of authorized users only. All activities on     *
*  this system are monitored and recorded. Unauthorized access is prohibited  *
*  and violators will be prosecuted to the full extent of the law.            *
*                                                                              *
*  By continuing, you acknowledge that you have read and understand this      *
*  warning and agree to comply with all applicable policies and regulations.  *
*                                                                              *
********************************************************************************
EOF

# Create SSH users group
groupadd -f sshusers

# Test SSH configuration before applying
sshd -t -f /etc/ssh/sshd_config

if [[ $? -eq 0 ]]; then
    echo "SSH configuration syntax is valid"
    systemctl restart sshd
    echo "SSH service restarted with new configuration"
else
    echo "SSH configuration has errors. Please check the configuration."
    exit 1
fi
```

### SSH Key Management

#### SSH Key Generation and Management
```bash
# Generate strong SSH key pairs
generate_ssh_keys() {
    local key_comment="${1:-$(whoami)@$(hostname)-$(date +%Y%m%d)}"

    echo "Generating SSH key pairs..."

    # Generate Ed25519 key (recommended)
    ssh-keygen -t ed25519 -a 100 -f ~/.ssh/id_ed25519 -C "$key_comment" -N ""

    # Generate RSA key (fallback compatibility)
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -C "$key_comment" -N ""

    # Generate ECDSA key
    ssh-keygen -t ecdsa -b 521 -f ~/.ssh/id_ecdsa -C "$key_comment" -N ""

    echo "SSH keys generated successfully"
}

# Secure SSH client configuration
create_ssh_client_config() {
    cat << 'EOF' > ~/.ssh/config
# SSH Client Security Configuration

# Global defaults
Host *
    Protocol 2
    HashKnownHosts yes
    VisualHostKey yes
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    GSSAPIAuthentication no
    StrictHostKeyChecking ask
    VerifyHostKeyDNS yes
    ForwardAgent no
    ForwardX11 no
    ForwardX11Trusted no

    # Cryptographic preferences
    Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
    MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
    KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256
    PubkeyAcceptedKeyTypes ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,ssh-rsa,rsa-sha2-256,rsa-sha2-512

    # Connection settings
    ServerAliveInterval 300
    ServerAliveCountMax 2
    ConnectTimeout 30

    # Key management
    AddKeysToAgent yes
    UseKeychain yes
    IdentitiesOnly yes

# Production servers
Host prod-*
    User deploy
    Port 2222
    IdentityFile ~/.ssh/production_ed25519
    ProxyCommand none
    UserKnownHostsFile ~/.ssh/known_hosts_production

# Development servers
Host dev-*
    User developer
    Port 22
    IdentityFile ~/.ssh/development_ed25519

# Bastion/Jump host configuration
Host bastion
    HostName bastion.company.com
    User jump-user
    Port 2222
    IdentityFile ~/.ssh/bastion_key
    ControlMaster auto
    ControlPath ~/.ssh/control-%h-%p-%r
    ControlPersist 300

# Servers behind bastion
Host internal-*
    ProxyJump bastion
    User internal-user
    IdentityFile ~/.ssh/internal_key
EOF

    chmod 600 ~/.ssh/config
}

# Set proper SSH file permissions
secure_ssh_directory() {
    echo "Securing SSH directory permissions..."

    # Create .ssh directory if it doesn't exist
    mkdir -p ~/.ssh

    # Set directory permissions
    chmod 700 ~/.ssh

    # Set file permissions
    chmod 600 ~/.ssh/id_* 2>/dev/null
    chmod 644 ~/.ssh/id_*.pub 2>/dev/null
    chmod 600 ~/.ssh/authorized_keys 2>/dev/null
    chmod 600 ~/.ssh/known_hosts 2>/dev/null
    chmod 600 ~/.ssh/config 2>/dev/null

    echo "SSH directory secured"
}

# SSH key audit script
audit_ssh_keys() {
    echo "=== SSH Key Security Audit ==="
    echo "Date: $(date)"
    echo ""

    # Check for weak key algorithms
    echo "Checking for weak SSH keys..."
    for key_file in ~/.ssh/id_*; do
        if [[ -f "$key_file" && ! "$key_file" =~ \.pub$ ]]; then
            key_type=$(ssh-keygen -l -f "$key_file" 2>/dev/null | awk '{print $4}')
            key_bits=$(ssh-keygen -l -f "$key_file" 2>/dev/null | awk '{print $1}')

            echo "Key: $(basename "$key_file")"
            echo "  Type: $key_type"
            echo "  Bits: $key_bits"

            # Check for weak keys
            if [[ "$key_type" == "(RSA)" && "$key_bits" -lt 2048 ]]; then
                echo "  ⚠️  WARNING: RSA key is less than 2048 bits"
            elif [[ "$key_type" == "(DSA)" ]]; then
                echo "  🚨 CRITICAL: DSA keys are deprecated"
            fi
            echo ""
        fi
    done

    # Check authorized_keys file
    if [[ -f ~/.ssh/authorized_keys ]]; then
        echo "Authorized keys analysis:"
        echo "  Total keys: $(wc -l < ~/.ssh/authorized_keys)"

        # Check for weak authorized keys
        while read -r line; do
            if [[ "$line" =~ ssh-dss ]]; then
                echo "  🚨 CRITICAL: DSA key found in authorized_keys"
            elif [[ "$line" =~ ssh-rsa ]] && [[ $(echo "$line" | awk '{print $2}' | wc -c) -lt 360 ]]; then
                echo "  ⚠️  WARNING: Weak RSA key found in authorized_keys"
            fi
        done < ~/.ssh/authorized_keys
    fi
}

# Usage examples
# generate_ssh_keys "admin@server-$(date +%Y%m%d)"
# create_ssh_client_config
# secure_ssh_directory
# audit_ssh_keys
```

## Multi-Factor Authentication (MFA)

### TOTP-based MFA Configuration
```bash
# Install Google Authenticator PAM module
apt install libpam-google-authenticator  # Debian/Ubuntu
dnf install google-authenticator          # RHEL/CentOS/Fedora

# Configure PAM for MFA
cat << 'EOF' > /etc/pam.d/sshd
# PAM configuration for SSH with MFA
auth       required     pam_google_authenticator.so
auth       required     pam_permit.so
auth       requisite    pam_nologin.so
auth       include      password-auth
account    required     pam_nologin.so
account    include      password-auth
password   include      password-auth
session    required     pam_selinux.so close
session    required     pam_loginuid.so
session    required     pam_selinux.so open env_params
session    required     pam_limits.so
session    optional     pam_keyinit.so force revoke
session    include      password-auth
EOF

# Enable challenge-response authentication in SSH
sed -i 's/ChallengeResponseAuthentication no/ChallengeResponseAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/UsePAM no/UsePAM yes/' /etc/ssh/sshd_config

# Add authentication methods
echo "AuthenticationMethods publickey,keyboard-interactive" >> /etc/ssh/sshd_config

systemctl restart sshd

# Setup MFA for users (run as each user)
setup_user_mfa() {
    echo "Setting up MFA for user: $(whoami)"
    google-authenticator -t -d -f -r 3 -R 30 -W
    echo "MFA setup completed. Save the backup codes securely!"
}

echo "MFA configuration completed"
echo "Users must run: google-authenticator -t -d -f -r 3 -R 30 -W"
```

### Centralized Authentication with LDAP
```bash
# Install LDAP client packages
apt install libnss-ldap libpam-ldap ldap-utils  # Debian/Ubuntu
dnf install nss-pam-ldapd openldap-clients      # RHEL/CentOS/Fedora

# Configure LDAP authentication
cat << 'EOF' > /etc/ldap/ldap.conf
# LDAP client configuration
BASE dc=company,dc=com
URI ldaps://ldap.company.com:636
LDAP_VERSION 3
TLS_CACERTDIR /etc/ssl/certs
TLS_REQCERT demand
BIND_POLICY soft
EOF

# Configure NSS to use LDAP
cat << 'EOF' > /etc/nsswitch.conf
passwd:         files ldap
group:          files ldap
shadow:         files ldap
hosts:          files dns
networks:       files
protocols:      db files
services:       db files
ethers:         db files
rpc:            db files
EOF

# Configure PAM for LDAP authentication
cat << 'EOF' > /etc/pam.d/common-auth
auth    [success=2 default=ignore]      pam_unix.so nullok_secure
auth    [success=1 default=ignore]      pam_ldap.so use_first_pass
auth    requisite                       pam_deny.so
auth    required                        pam_permit.so
auth    optional                        pam_cap.so
EOF

systemctl restart nscd
echo "LDAP authentication configured"
```