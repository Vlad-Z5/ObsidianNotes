# Linux Package Management Automation

**Package management automation** integrates package operations into DevOps workflows, CI/CD pipelines, and infrastructure as code for consistent, scalable software deployment.

## Package Management in Ansible

### Basic Package Tasks
```yaml
# Ansible package management playbook
---
- name: Package Management Tasks
  hosts: all
  become: yes
  tasks:

    - name: Update package cache (Debian/Ubuntu)
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Update package cache (RHEL/CentOS)
      dnf:
        update_cache: yes
      when: ansible_os_family == "RedHat"

    - name: Install essential packages
      package:
        name:
          - curl
          - wget
          - git
          - vim
          - htop
          - tree
          - unzip
        state: present

    - name: Install distribution-specific packages
      apt:
        name:
          - build-essential
          - software-properties-common
        state: present
      when: ansible_os_family == "Debian"

    - name: Install development tools (RHEL)
      dnf:
        name: "@Development Tools"
        state: present
      when: ansible_os_family == "RedHat"
```

### Advanced Package Management
```yaml
---
- name: Advanced Package Management
  hosts: all
  become: yes
  vars:
    package_versions:
      nginx: "1.18.0-0ubuntu1"
      docker: "20.10.7-0ubuntu5"

  tasks:
    - name: Install specific package versions
      apt:
        name: "{{ item.key }}={{ item.value }}"
        state: present
        allow_downgrade: yes
      loop: "{{ package_versions | dict2items }}"
      when: ansible_os_family == "Debian"

    - name: Hold packages from updates
      dpkg_selections:
        name: "{{ item.key }}"
        selection: hold
      loop: "{{ package_versions | dict2items }}"
      when: ansible_os_family == "Debian"

    - name: Remove unnecessary packages
      package:
        name:
          - apache2
          - sendmail
          - telnet
        state: absent
        autoremove: yes

    - name: Configure automatic updates
      template:
        src: 50unattended-upgrades.j2
        dest: /etc/apt/apt.conf.d/50unattended-upgrades
        mode: '0644'
      notify: restart unattended-upgrades
      when: ansible_os_family == "Debian"

  handlers:
    - name: restart unattended-upgrades
      systemd:
        name: unattended-upgrades
        state: restarted
```

### Package Repository Management
```yaml
---
- name: Repository Management
  hosts: all
  become: yes
  tasks:

    - name: Add Docker repository key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present
      when: ansible_os_family == "Debian"

    - name: Add Docker repository
      apt_repository:
        repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"

    - name: Add EPEL repository (RHEL)
      dnf:
        name: epel-release
        state: present
      when: ansible_os_family == "RedHat"

    - name: Add custom repository (RPM)
      yum_repository:
        name: company-repo
        description: Company Internal Repository
        baseurl: https://repo.company.com/rhel8/
        gpgcheck: yes
        gpgkey: https://repo.company.com/RPM-GPG-KEY
        enabled: yes
      when: ansible_os_family == "RedHat"
```

## DevOps Package Management Scripts

### Comprehensive Package Management Script
```bash
#!/bin/bash
# devops-package-manager.sh

set -euo pipefail

# Configuration
LOG_FILE="/var/log/package-management.log"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_ALERT="${EMAIL_ALERT:-admin@company.com}"
PACKAGE_LIST_FILE="/etc/required-packages.txt"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Notification function
notify_slack() {
    local message="$1"
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"📦 Package Management: $message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

notify_email() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$EMAIL_ALERT" 2>/dev/null || true
}

# Detect package manager
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        echo "apt"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    else
        log "ERROR: No supported package manager found"
        exit 1
    fi
}

# Check for updates
check_updates() {
    local pkg_mgr="$1"
    log "Checking for available updates..."

    case "$pkg_mgr" in
        apt)
            apt update >/dev/null 2>&1
            local updates=$(apt list --upgradable 2>/dev/null | grep -c "upgradable" || echo "0")
            local security=$(apt list --upgradable 2>/dev/null | grep -c "security" || echo "0")
            ;;
        dnf|yum)
            $pkg_mgr check-update >/dev/null 2>&1 || true
            local updates=$($pkg_mgr list updates 2>/dev/null | grep -c "updates" || echo "0")
            local security=$($pkg_mgr updateinfo list security 2>/dev/null | wc -l || echo "0")
            ;;
    esac

    log "Available updates: $updates, Security updates: $security"

    if [[ $security -gt 0 ]]; then
        notify_slack "$security security updates available on $(hostname)"
        notify_email "Security Updates Available" \
                     "$security security updates are available on $(hostname). Please review and apply."
    fi

    echo "$updates:$security"
}

# Install packages from list
install_packages() {
    local pkg_mgr="$1"
    local package_list="$2"

    if [[ ! -f "$package_list" ]]; then
        log "Package list file not found: $package_list"
        return 1
    fi

    log "Installing packages from $package_list"

    while IFS= read -r package; do
        [[ -z "$package" || "$package" =~ ^# ]] && continue

        log "Installing package: $package"
        case "$pkg_mgr" in
            apt)
                apt install -y "$package"
                ;;
            dnf|yum)
                $pkg_mgr install -y "$package"
                ;;
        esac
    done < "$package_list"
}

# Update system packages
update_system() {
    local pkg_mgr="$1"
    local security_only="$2"

    log "Updating system packages (security_only: $security_only)"

    case "$pkg_mgr" in
        apt)
            if [[ "$security_only" == "true" ]]; then
                unattended-upgrades
            else
                apt upgrade -y
            fi
            ;;
        dnf|yum)
            if [[ "$security_only" == "true" ]]; then
                $pkg_mgr update --security -y
            else
                $pkg_mgr update -y
            fi
            ;;
    esac

    log "System update completed"
}

# Cleanup old packages
cleanup_packages() {
    local pkg_mgr="$1"
    log "Cleaning up old packages"

    case "$pkg_mgr" in
        apt)
            apt autoremove -y
            apt autoclean
            ;;
        dnf|yum)
            $pkg_mgr autoremove -y
            $pkg_mgr clean all
            ;;
    esac

    log "Package cleanup completed"
}

# Generate package report
generate_report() {
    local pkg_mgr="$1"
    local report_file="/tmp/package-report-$(date +%Y%m%d).txt"

    log "Generating package report"

    {
        echo "Package Management Report - $(date)"
        echo "======================================="
        echo "Hostname: $(hostname)"
        echo "Package Manager: $pkg_mgr"
        echo ""

        case "$pkg_mgr" in
            apt)
                echo "Installed packages:"
                dpkg -l | grep "^ii" | wc -l
                echo ""
                echo "Available updates:"
                apt list --upgradable 2>/dev/null | grep -v "WARNING"
                ;;
            dnf|yum)
                echo "Installed packages:"
                $pkg_mgr list installed | wc -l
                echo ""
                echo "Available updates:"
                $pkg_mgr check-update 2>/dev/null || true
                ;;
        esac
    } > "$report_file"

    log "Package report generated: $report_file"
    echo "$report_file"
}

# Main function
main() {
    local action="${1:-check}"
    local pkg_mgr
    pkg_mgr=$(detect_package_manager)

    log "Starting package management action: $action"

    case "$action" in
        check)
            check_updates "$pkg_mgr"
            ;;
        install)
            install_packages "$pkg_mgr" "$PACKAGE_LIST_FILE"
            ;;
        update)
            update_system "$pkg_mgr" "false"
            cleanup_packages "$pkg_mgr"
            ;;
        security-update)
            update_system "$pkg_mgr" "true"
            ;;
        cleanup)
            cleanup_packages "$pkg_mgr"
            ;;
        report)
            generate_report "$pkg_mgr"
            ;;
        full)
            check_updates "$pkg_mgr"
            update_system "$pkg_mgr" "false"
            cleanup_packages "$pkg_mgr"
            generate_report "$pkg_mgr"
            ;;
        *)
            echo "Usage: $0 {check|install|update|security-update|cleanup|report|full}"
            exit 1
            ;;
    esac

    log "Package management action completed: $action"
}

# Execute main function
main "$@"
```

## CI/CD Integration

### GitLab CI Package Management
```yaml
# .gitlab-ci.yml
stages:
  - package-audit
  - package-update
  - deploy

variables:
  DEBIAN_FRONTEND: noninteractive

package-audit:
  stage: package-audit
  image: ubuntu:20.04
  script:
    - apt update
    - apt install -y curl
    - |
      # Check for security updates
      SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c security || echo "0")
      echo "Security updates available: $SECURITY_UPDATES"

      if [ "$SECURITY_UPDATES" -gt 0 ]; then
        echo "⚠️ Security updates available!" > security-report.txt
        apt list --upgradable 2>/dev/null | grep security >> security-report.txt
      fi
  artifacts:
    reports:
      junit: security-report.txt
    expire_in: 1 week
  only:
    - schedules

package-update:
  stage: package-update
  image: ubuntu:20.04
  script:
    - apt update
    - apt upgrade -y
    - apt autoremove -y
    - apt autoclean
  only:
    - schedules
    - manual

build-image:
  stage: deploy
  script:
    - docker build -t myapp:$CI_COMMIT_SHA .
    - docker push myapp:$CI_COMMIT_SHA
  dependencies:
    - package-update
```

### GitHub Actions Package Management
```yaml
# .github/workflows/package-management.yml
name: Package Management

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  package-audit:
    runs-on: ubuntu-latest
    steps:
      - name: Check for security updates
        run: |
          sudo apt update
          SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c security || echo "0")
          echo "SECURITY_UPDATES=$SECURITY_UPDATES" >> $GITHUB_ENV

          if [ "$SECURITY_UPDATES" -gt 0 ]; then
            echo "::warning::$SECURITY_UPDATES security updates available"
            apt list --upgradable 2>/dev/null | grep security
          fi

      - name: Create security report
        if: env.SECURITY_UPDATES > 0
        run: |
          apt list --upgradable 2>/dev/null | grep security > security-updates.txt

      - name: Upload security report
        if: env.SECURITY_UPDATES > 0
        uses: actions/upload-artifact@v2
        with:
          name: security-updates
          path: security-updates.txt

  package-update:
    runs-on: ubuntu-latest
    needs: package-audit
    if: github.event_name == 'workflow_dispatch'
    steps:
      - name: Update packages
        run: |
          sudo apt update
          sudo apt upgrade -y
          sudo apt autoremove -y
          sudo apt autoclean

      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Package update completed on ${{ github.repository }}'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Infrastructure as Code

### Terraform Package Management
```hcl
# package-management.tf
resource "null_resource" "package_management" {
  count = length(var.server_ips)

  connection {
    type        = "ssh"
    host        = var.server_ips[count.index]
    user        = var.ssh_user
    private_key = file(var.ssh_private_key)
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt update",
      "sudo apt install -y curl wget git vim htop",
      "sudo apt autoremove -y",
      "sudo systemctl enable unattended-upgrades"
    ]
  }

  triggers = {
    always_run = timestamp()
  }
}

# Output package management status
output "package_management_completed" {
  value = "Package management completed for ${length(var.server_ips)} servers"
}
```

### Docker Package Management
```dockerfile
# Multi-stage Dockerfile with package management
FROM ubuntu:20.04 AS base

# Set non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Update and install packages
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        build-essential && \
    apt autoremove -y && \
    apt autoclean && \
    rm -rf /var/lib/apt/lists/*

# Production stage
FROM base AS production

# Copy application files
COPY . /app
WORKDIR /app

# Install application dependencies
RUN apt update && \
    apt install -y --no-install-recommends \
        python3 \
        python3-pip && \
    pip3 install -r requirements.txt && \
    apt remove -y python3-pip && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

CMD ["python3", "app.py"]
```

## Monitoring and Alerting

### Package Management Monitoring Script
```bash
#!/bin/bash
# package-monitoring.sh

METRIC_FILE="/var/lib/package-metrics"
PROMETHEUS_TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"

# Function to write Prometheus metrics
write_metric() {
    local metric_name="$1"
    local metric_value="$2"
    local help_text="$3"

    {
        echo "# HELP $metric_name $help_text"
        echo "# TYPE $metric_name gauge"
        echo "${metric_name} ${metric_value}"
    } >> "$PROMETHEUS_TEXTFILE_DIR/package_metrics.prom.tmp"
}

# Detect package manager and gather metrics
if command -v apt >/dev/null 2>&1; then
    apt update >/dev/null 2>&1

    TOTAL_PACKAGES=$(dpkg -l | grep "^ii" | wc -l)
    AVAILABLE_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "upgradable" || echo "0")
    SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "security" || echo "0")

elif command -v dnf >/dev/null 2>&1; then
    dnf check-update >/dev/null 2>&1 || true

    TOTAL_PACKAGES=$(dnf list installed | wc -l)
    AVAILABLE_UPDATES=$(dnf list updates 2>/dev/null | wc -l || echo "0")
    SECURITY_UPDATES=$(dnf updateinfo list security 2>/dev/null | wc -l || echo "0")
fi

# Write metrics to Prometheus format
> "$PROMETHEUS_TEXTFILE_DIR/package_metrics.prom.tmp"

write_metric "packages_total" "$TOTAL_PACKAGES" "Total number of installed packages"
write_metric "packages_updates_available" "$AVAILABLE_UPDATES" "Number of available package updates"
write_metric "packages_security_updates_available" "$SECURITY_UPDATES" "Number of available security updates"
write_metric "packages_last_check_timestamp" "$(date +%s)" "Timestamp of last package check"

# Atomically update metrics file
mv "$PROMETHEUS_TEXTFILE_DIR/package_metrics.prom.tmp" "$PROMETHEUS_TEXTFILE_DIR/package_metrics.prom"

echo "Package metrics updated: Total=$TOTAL_PACKAGES, Updates=$AVAILABLE_UPDATES, Security=$SECURITY_UPDATES"
```