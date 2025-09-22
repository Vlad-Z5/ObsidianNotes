# Linux System Administration User Group Management

**User and Group Management** covers comprehensive user account administration, group management, bulk operations, and security auditing for Linux systems.

## Core User Administration Files

### Essential User Management Files
Understanding the core files that control user management is fundamental for system administration:

- **`/etc/passwd`** - Stores user account details (username, UID, GID, home directory, shell)
- **`/etc/shadow`** - Stores encrypted user passwords and password policies
- **`/etc/group`** - Stores group information and group memberships
- **`/etc/gshadow`** - Stores secure group details and group passwords

### File Format Understanding
```bash
# /etc/passwd format: username:x:UID:GID:GECOS:home:shell
root:x:0:0:root:/root:/bin/bash
user1:x:1000:1000:User One,,,:/home/user1:/bin/bash
service:x:999:999:Service Account:/var/lib/service:/usr/sbin/nologin

# /etc/shadow format: username:password:lastchange:min:max:warn:inactive:expire
root:$6$hash...:19000:0:99999:7:::
user1:$6$hash...:19000:7:90:14:30:19365
locked:!:19000:0:99999:7:::

# /etc/group format: groupname:x:GID:members
root:x:0:
users:x:100:user1,user2
sudo:x:27:user1
docker:x:999:user1,user2,user3

# /etc/gshadow format: groupname:password:admins:members
users:!::user1,user2
sudo:!:user1:user1
docker:!::user1,user2,user3
```

## User Account Management

### Creating and Managing Users
```bash
# Basic user creation
useradd username                       # Create user with defaults
useradd -m username                    # Create user with home directory
useradd -m -s /bin/bash username       # Create user with home and bash shell
useradd -m -G sudo,docker username     # Create user and add to groups
useradd -m -e 2024-12-31 username      # Create user with account expiration

# Advanced user creation options
useradd -m -u 1500 -g users -G sudo,docker -s /bin/bash \
  -c "John Doe" -d /home/johndoe johndoe

# System account creation
useradd -r -s /usr/sbin/nologin -d /var/lib/service service_account
useradd -r -M -s /bin/false backup_user  # No home, no shell

# Set password for new user
passwd username                        # Interactive password setting
echo "username:password" | chpasswd    # Non-interactive password setting

# Generate random password
openssl rand -base64 12 | passwd --stdin username  # RHEL/CentOS
echo "username:$(openssl rand -base64 12)" | chpasswd  # All distributions
```

### User Modification and Management
```bash
# User modification
usermod -aG sudo username              # Add user to sudo group
usermod -aG docker,wheel username      # Add to multiple groups
usermod -g newgroup username           # Change primary group
usermod -s /bin/zsh username           # Change user shell
usermod -l newname oldname             # Rename user
usermod -d /new/home -m username       # Change and move home directory
usermod -L username                    # Lock user account
usermod -U username                    # Unlock user account
usermod -e 2024-12-31 username         # Set account expiration

# Account status management
passwd -l username                     # Lock password
passwd -u username                     # Unlock password
passwd -S username                     # Show password status
passwd -d username                     # Delete password (passwordless login)

# User deletion
userdel username                       # Delete user (keep home directory)
userdel -r username                    # Delete user and home directory
userdel -f username                    # Force delete user (even if logged in)
```

### User Information and Queries
```bash
# User information
id username                            # Show user ID and groups
finger username                        # Show detailed user information
getent passwd username                 # Get user from all configured sources
groups username                        # Show user's groups
w username                             # Show user activity
last username                          # Show user login history

# List users
getent passwd | cut -d: -f1            # List all users
awk -F: '$3 >= 1000 {print $1}' /etc/passwd  # List regular users (UID >= 1000)
awk -F: '$3 < 1000 {print $1}' /etc/passwd   # List system users (UID < 1000)
who                                    # Currently logged-in users
users                                  # Simple list of logged-in users
```

## Group Management

### Creating and Managing Groups
```bash
# Basic group operations
groupadd groupname                     # Create group
groupadd -g 1500 groupname             # Create group with specific GID
groupadd -r system_group               # Create system group
groupmod -n newname oldname            # Rename group
groupmod -g 2000 groupname             # Change group GID
groupdel groupname                     # Delete group

# Group membership management
gpasswd -a username groupname          # Add user to group
gpasswd -d username groupname          # Remove user from group
gpasswd -A username groupname          # Make user group administrator
gpasswd -M user1,user2,user3 groupname # Set group members

# Group information
groups username                        # Show user's groups
getent group groupname                 # Show group members
getent group | grep username           # Show groups containing user
lid -g groupname                       # List group members (if available)
```

### Advanced Group Management
```bash
# Group administration
gpasswd groupname                      # Set group password
gpasswd -r groupname                   # Remove group password
gpasswd -R groupname                   # Disable group password

# Query group information
getent group | cut -d: -f1             # List all groups
awk -F: '{print $1}' /etc/group        # List group names
awk -F: '$3 >= 1000 {print $1}' /etc/group  # List user groups (GID >= 1000)
awk -F: '$3 < 1000 {print $1}' /etc/group   # List system groups (GID < 1000)

# Find empty groups
getent group | awk -F: '$4 == "" {print $1}'

# Group membership audit
for user in $(getent passwd | awk -F: '$3 >= 1000 {print $1}'); do
    echo "$user: $(groups $user | cut -d: -f2)"
done
```

## Advanced User Management

### Bulk User Operations
```bash
# Create multiple users from file
cat << 'EOF' > userlist.txt
user1:password1:1001:1001:User One:/home/user1:/bin/bash
user2:password2:1002:1002:User Two:/home/user2:/bin/bash
user3:password3:1003:1003:User Three:/home/user3:/bin/bash
developer1:devpass1:1004:1004:Developer One:/home/developer1:/bin/bash
EOF

# Process user creation file
newusers userlist.txt

# Alternative bulk user creation script
cat << 'EOF' > create_users.sh
#!/bin/bash
# Bulk user creation script

USERS_FILE="$1"
DEFAULT_GROUP="users"
DEFAULT_SHELL="/bin/bash"

if [[ ! -f "$USERS_FILE" ]]; then
    echo "Usage: $0 <users_file>"
    echo "Format: username:fullname:group"
    exit 1
fi

while IFS=: read -r username fullname group; do
    [[ -z "$username" || "$username" =~ ^# ]] && continue

    group="${group:-$DEFAULT_GROUP}"

    if id "$username" &>/dev/null; then
        echo "User $username already exists"
        continue
    fi

    useradd -m -g "$group" -s "$DEFAULT_SHELL" -c "$fullname" "$username"
    echo "Created user: $username"

    # Generate random password
    password=$(openssl rand -base64 12)
    echo "$username:$password" | chpasswd
    echo "Password for $username: $password"

done < "$USERS_FILE"
EOF

chmod +x create_users.sh

# Example users file for script
cat << 'EOF' > users_to_create.txt
john.doe:John Doe:developers
jane.smith:Jane Smith:developers
admin.user:Admin User:sudo
backup.service:Backup Service:backup
EOF

# Run bulk creation
./create_users.sh users_to_create.txt
```

### Password Management in Bulk
```bash
# Change passwords in bulk
cat << 'EOF' > passwords.txt
user1:newpassword1
user2:newpassword2
user3:newpassword3
EOF

chpasswd < passwords.txt

# Force password change on next login
chage -d 0 user1 user2 user3

# Set password policies for all users
for user in $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do
    chage -M 90 -m 7 -W 14 "$user"  # Max 90 days, min 7 days, warn 14 days
done

# Generate secure passwords for users
cat << 'EOF' > generate_passwords.sh
#!/bin/bash
# Generate secure passwords for users

USERS_FILE="$1"
PASSWORD_LENGTH=16

if [[ ! -f "$USERS_FILE" ]]; then
    echo "Usage: $0 <users_file>"
    exit 1
fi

echo "Username:Password" > new_passwords.txt

while read -r username; do
    [[ -z "$username" || "$username" =~ ^# ]] && continue

    if id "$username" &>/dev/null; then
        password=$(openssl rand -base64 "$PASSWORD_LENGTH" | tr -d "=+/" | cut -c1-"$PASSWORD_LENGTH")
        echo "$username:$password" >> new_passwords.txt
        echo "$username:$password" | chpasswd
        echo "Updated password for: $username"
    else
        echo "User $username does not exist"
    fi
done < "$USERS_FILE"

echo "Passwords saved to: new_passwords.txt"
EOF

chmod +x generate_passwords.sh
```

## User Environment Setup

### Skeleton Directory Configuration
```bash
# Customize skeleton directory
ls -la /etc/skel/                     # Default files for new users

# Create custom skeleton files
cat << 'EOF' > /etc/skel/.bash_profile
# User specific environment and startup programs
export PATH=$PATH:$HOME/bin:$HOME/.local/bin
export EDITOR=vim
export HISTSIZE=10000
export HISTFILESIZE=20000

# Custom aliases
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# Development environment
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Load additional configurations
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
EOF

cat << 'EOF' > /etc/skel/.vimrc
" Basic vim configuration
set number
set showmatch
set hlsearch
set tabstop=4
set shiftwidth=4
set expandtab
set autoindent
syntax on
EOF

cat << 'EOF' > /etc/skel/.gitconfig
[user]
    name = CHANGEME
    email = CHANGEME@example.com
[core]
    editor = vim
[alias]
    st = status
    co = checkout
    br = branch
    up = rebase
    ci = commit
EOF

# Apply skeleton to existing user
cp -r /etc/skel/. /home/username/
chown -R username:username /home/username
```

### Home Directory Management
```bash
# Set proper permissions
chmod 750 /home/username              # Secure home directory
chown -R username:username /home/username

# Create standard directories
sudo -u username mkdir -p /home/username/{bin,Documents,Downloads,Projects}

# Set up user directories with proper permissions
cat << 'EOF' > setup_user_dirs.sh
#!/bin/bash
# Set up user directories

USERNAME="$1"
if [[ -z "$USERNAME" ]]; then
    echo "Usage: $0 <username>"
    exit 1
fi

if ! id "$USERNAME" &>/dev/null; then
    echo "User $USERNAME does not exist"
    exit 1
fi

USER_HOME="/home/$USERNAME"
DIRECTORIES=(
    "bin"
    "Documents"
    "Downloads"
    "Projects"
    "Scripts"
    ".config"
    ".local/bin"
    ".ssh"
)

for dir in "${DIRECTORIES[@]}"; do
    sudo -u "$USERNAME" mkdir -p "$USER_HOME/$dir"
    echo "Created: $USER_HOME/$dir"
done

# Set SSH directory permissions
chmod 700 "$USER_HOME/.ssh"
echo "Set permissions for SSH directory"

# Create basic SSH config
sudo -u "$USERNAME" cat << 'SSHEOF' > "$USER_HOME/.ssh/config"
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    HashKnownHosts yes
SSHEOF

chmod 600 "$USER_HOME/.ssh/config"
echo "Created SSH config file"
EOF

chmod +x setup_user_dirs.sh
```

## Account Monitoring and Auditing

### User Activity Monitoring
```bash
# Current user activity
who                                    # Currently logged in users
w                                      # Detailed user activity
users                                  # Simple list of logged users
finger                                 # Detailed user information (if available)

# Login history and tracking
last                                   # Login history
last username                          # Specific user login history
last -n 10                             # Last 10 logins
lastb                                  # Failed login attempts
lastlog                                # Last login for all users
lastlog -u username                    # Last login for specific user

# Failed login monitoring
faillog -a                             # Show failed login attempts for all users
faillog -u username                    # Failed logins for specific user
faillog -r -u username                 # Reset failed login count
```

### Account Security Auditing
```bash
# Security audit script
cat << 'EOF' > user_security_audit.sh
#!/bin/bash
# User Security Audit Script

echo "=== User Security Audit Report ==="
echo "Date: $(date)"
echo

# Users with UID 0 (root privileges)
echo "Users with UID 0 (root privileges):"
awk -F: '$3 == 0 {print $1}' /etc/passwd
echo

# Users with no password
echo "Users with no password:"
awk -F: '$2 == "" {print $1}' /etc/shadow
echo

# Users with expired passwords
echo "Users with expired passwords:"
while IFS=: read -r user pass lastchange min max warn inactive expire; do
    if [[ -n "$lastchange" && "$lastchange" != "0" && -n "$max" && "$max" != "99999" ]]; then
        current_date=$(date +%s)
        current_days=$((current_date / 86400))
        expire_date=$((lastchange + max))

        if [[ $current_days -gt $expire_date ]]; then
            echo "$user (expired $((current_days - expire_date)) days ago)"
        fi
    fi
done < /etc/shadow
echo

# Users with weak passwords (if john is available)
if command -v john &> /dev/null; then
    echo "Running password strength check..."
    john --show /etc/shadow 2>/dev/null | grep -v "password hashes cracked"
fi
echo

# Accounts that haven't logged in recently
echo "Accounts with no recent login (30+ days):"
while IFS=: read -r username uid; do
    if [[ $uid -ge 1000 && $uid -le 60000 ]]; then
        last_login=$(lastlog -u "$username" 2>/dev/null | tail -n 1 | awk '{print $4, $5, $6, $7}')
        if [[ "$last_login" == "** Never logged in **" ]] || [[ -z "$last_login" ]]; then
            echo "$username: Never logged in"
        fi
    fi
done < <(awk -F: '{print $1 ":" $3}' /etc/passwd)
echo

# Group membership audit
echo "Users in privileged groups:"
for group in sudo wheel admin root; do
    if getent group "$group" &>/dev/null; then
        members=$(getent group "$group" | cut -d: -f4)
        if [[ -n "$members" ]]; then
            echo "$group: $members"
        fi
    fi
done
echo

# Home directory permissions audit
echo "Home directories with incorrect permissions:"
while IFS=: read -r username uid gid gecos home shell; do
    if [[ $uid -ge 1000 && $uid -le 60000 && -d "$home" ]]; then
        perms=$(stat -c "%a" "$home" 2>/dev/null)
        owner=$(stat -c "%U" "$home" 2>/dev/null)

        if [[ "$owner" != "$username" ]]; then
            echo "$home: Owned by $owner (should be $username)"
        fi

        if [[ ${perms:0:1} -gt 7 || ${perms:1:1} -gt 5 ]]; then
            echo "$home: Permissions $perms (too permissive)"
        fi
    fi
done < /etc/passwd
echo

echo "=== End of Audit ==="
EOF

chmod +x user_security_audit.sh
./user_security_audit.sh
```

### Automated User Management Tasks
```bash
# Cleanup inactive accounts
cat << 'EOF' > cleanup_inactive_users.sh
#!/bin/bash
# Cleanup inactive user accounts

INACTIVE_DAYS=90
DRY_RUN=true  # Set to false to actually delete accounts

echo "Looking for accounts inactive for more than $INACTIVE_DAYS days..."

while IFS=: read -r username uid gid gecos home shell; do
    # Skip system accounts
    if [[ $uid -lt 1000 || $uid -gt 60000 ]]; then
        continue
    fi

    # Check last login
    last_login=$(lastlog -u "$username" 2>/dev/null | tail -n 1)

    if echo "$last_login" | grep -q "Never logged in"; then
        echo "User $username has never logged in"
        if [[ "$DRY_RUN" == "false" ]]; then
            echo "Would delete: $username"
            # userdel -r "$username"
        fi
    else
        # Check if login was more than INACTIVE_DAYS ago
        last_date=$(echo "$last_login" | awk '{print $4, $5, $6, $7}')
        if [[ -n "$last_date" ]]; then
            last_timestamp=$(date -d "$last_date" +%s 2>/dev/null)
            current_timestamp=$(date +%s)
            days_since=$((( current_timestamp - last_timestamp ) / 86400))

            if [[ $days_since -gt $INACTIVE_DAYS ]]; then
                echo "User $username: Last login $days_since days ago"
                if [[ "$DRY_RUN" == "false" ]]; then
                    echo "Would delete: $username"
                    # userdel -r "$username"
                fi
            fi
        fi
    fi
done < /etc/passwd

if [[ "$DRY_RUN" == "true" ]]; then
    echo "This was a dry run. Set DRY_RUN=false to actually delete accounts."
fi
EOF

chmod +x cleanup_inactive_users.sh
./cleanup_inactive_users.sh
```