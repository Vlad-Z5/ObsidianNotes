# Enterprise Ansible Vault Security

Advanced secret management, encryption strategies, and enterprise security patterns for protecting sensitive data in Ansible automation.

## Table of Contents
1. [Enterprise Vault Architecture](#enterprise-vault-architecture)
2. [Advanced Encryption Patterns](#advanced-encryption-patterns)
3. [Multi-Environment Security](#multi-environment-security)
4. [External Secret Management](#external-secret-management)
5. [Automated Key Rotation](#automated-key-rotation)
6. [Audit & Compliance](#audit--compliance)
7. [Performance & Scalability](#performance--scalability)
8. [Security Best Practices](#security-best-practices)

## Enterprise Vault Architecture

### Multi-Vault Strategy
```bash
# Enterprise vault structure
vault/
├── production/
│   ├── database_secrets.yml      # Production DB credentials
│   ├── api_keys.yml              # Production API keys
│   ├── certificates.yml          # SSL/TLS certificates
│   └── infrastructure.yml        # Infrastructure secrets
├── staging/
│   ├── database_secrets.yml
│   ├── api_keys.yml
│   └── certificates.yml
├── development/
│   ├── database_secrets.yml
│   ├── api_keys.yml
│   └── certificates.yml
├── shared/
│   ├── monitoring_keys.yml       # Shared monitoring credentials
│   ├── backup_keys.yml           # Backup system credentials
│   └── logging_tokens.yml        # Centralized logging tokens
└── vault_ids/
    ├── prod_vault_id
    ├── staging_vault_id
    ├── dev_vault_id
    └── shared_vault_id
```

### Vault Management Script
```bash
#!/bin/bash
# vault_manager.sh - Enterprise vault management utility

set -euo pipefail

# Configuration
VAULT_DIR="vault"
VAULT_IDS_DIR="${VAULT_DIR}/vault_ids"
ENVIRONMENTS=("production" "staging" "development" "shared")

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Validate environment
validate_environment() {
    local env=$1
    if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${env} " ]]; then
        log "ERROR: Invalid environment '${env}'. Valid options: ${ENVIRONMENTS[*]}"
        exit 1
    fi
}

# Create vault file with proper permissions
create_vault() {
    local env=$1
    local filename=$2
    local vault_id="${env}_vault_id"
    
    validate_environment "$env"
    
    if [[ ! -f "${VAULT_IDS_DIR}/${vault_id}" ]]; then
        log "ERROR: Vault ID file not found: ${VAULT_IDS_DIR}/${vault_id}"
        exit 1
    fi
    
    local vault_file="${VAULT_DIR}/${env}/${filename}"
    
    log "Creating vault file: ${vault_file}"
    ansible-vault create \
        --vault-id "${vault_id}@${VAULT_IDS_DIR}/${vault_id}" \
        "${vault_file}"
        
    # Set restrictive permissions
    chmod 600 "${vault_file}"
    log "Vault file created with restricted permissions"
}

# Edit vault file
edit_vault() {
    local env=$1
    local filename=$2
    local vault_id="${env}_vault_id"
    
    validate_environment "$env"
    
    local vault_file="${VAULT_DIR}/${env}/${filename}"
    
    if [[ ! -f "${vault_file}" ]]; then
        log "ERROR: Vault file not found: ${vault_file}"
        exit 1
    fi
    
    log "Editing vault file: ${vault_file}"
    ansible-vault edit \
        --vault-id "${vault_id}@${VAULT_IDS_DIR}/${vault_id}" \
        "${vault_file}"
}

# Rotate vault keys
rotate_vault_key() {
    local env=$1
    local vault_id="${env}_vault_id"
    
    validate_environment "$env"
    
    log "Rotating vault key for environment: ${env}"
    
    # Backup current vault ID
    cp "${VAULT_IDS_DIR}/${vault_id}" "${VAULT_IDS_DIR}/${vault_id}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Generate new password
    openssl rand -base64 32 > "${VAULT_IDS_DIR}/${vault_id}.new"
    chmod 600 "${VAULT_IDS_DIR}/${vault_id}.new"
    
    # Rekey all vault files for this environment
    for vault_file in "${VAULT_DIR}/${env}/"*.yml; do
        if [[ -f "$vault_file" ]]; then
            log "Rekeying: $vault_file"
            ansible-vault rekey \
                --vault-id "${vault_id}@${VAULT_IDS_DIR}/${vault_id}" \
                --new-vault-id "${vault_id}@${VAULT_IDS_DIR}/${vault_id}.new" \
                "$vault_file"
        fi
    done
    
    # Replace old vault ID with new one
    mv "${VAULT_IDS_DIR}/${vault_id}.new" "${VAULT_IDS_DIR}/${vault_id}"
    
    log "Vault key rotation completed for environment: ${env}"
}

# Audit vault files
audit_vault() {
    local env=${1:-"all"}
    
    log "Starting vault audit for environment: ${env}"
    
    if [[ "$env" == "all" ]]; then
        environments=("${ENVIRONMENTS[@]}")
    else
        validate_environment "$env"
        environments=("$env")
    fi
    
    for environment in "${environments[@]}"; do
        log "Auditing environment: ${environment}"
        
        for vault_file in "${VAULT_DIR}/${environment}/"*.yml; do
            if [[ -f "$vault_file" ]]; then
                log "Checking: $vault_file"
                
                # Check file permissions
                local perms=$(stat -c "%a" "$vault_file" 2>/dev/null || stat -f "%A" "$vault_file")
                if [[ "$perms" != "600" ]]; then
                    log "WARNING: Incorrect permissions on ${vault_file}: ${perms} (should be 600)"
                fi
                
                # Verify file is encrypted
                if ! head -1 "$vault_file" | grep -q "\$ANSIBLE_VAULT"; then
                    log "WARNING: File may not be encrypted: ${vault_file}"
                fi
                
                # Check last modified time
                local modified=$(stat -c "%Y" "$vault_file" 2>/dev/null || stat -f "%m" "$vault_file")
                local current=$(date +%s)
                local age_days=$(( (current - modified) / 86400 ))
                
                if [[ $age_days -gt 90 ]]; then
                    log "INFO: Vault file is ${age_days} days old: ${vault_file}"
                fi
            fi
        done
    done
    
    log "Vault audit completed"
}

# Main function
main() {
    local action=${1:-"help"}
    
    case "$action" in
        "create")
            create_vault "$2" "$3"
            ;;
        "edit")
            edit_vault "$2" "$3"
            ;;
        "rotate")
            rotate_vault_key "$2"
            ;;
        "audit")
            audit_vault "${2:-all}"
            ;;
        "help")
            echo "Usage: $0 {create|edit|rotate|audit} [environment] [filename]"
            echo "  create <env> <filename>  - Create new vault file"
            echo "  edit <env> <filename>    - Edit existing vault file"
            echo "  rotate <env>             - Rotate vault keys for environment"
            echo "  audit [env]              - Audit vault files (default: all)"
            echo "  Environments: ${ENVIRONMENTS[*]}"
            ;;
        *)
            log "ERROR: Unknown action: $action"
            exit 1
            ;;
    esac
}

main "$@"
```

## Advanced Encryption Patterns

### Inline String Encryption
```bash
# Encrypt individual values
ansible-vault encrypt_string 'supersecret123' --name 'database_password'
ansible-vault encrypt_string 'api-key-12345' --vault-id prod@prompt --name 'api_key'

# Encrypt from stdin
echo 'my-secret-value' | ansible-vault encrypt_string --stdin-name 'secret_token'

# Encrypt using environment variable
echo "$SECRET_VALUE" | ansible-vault encrypt_string --vault-id prod@vault_file --stdin-name 'env_secret'
```

### Complex Variable Structures
```yaml
# vault/production/database_secrets.yml
---
database_clusters:
  primary:
    host: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66633839653634373264633839653634373264633839653634373264633839653634373264633839653634
          3732646338396536343732646338396536343732646338396536343732646338396536343732646338396536
          34373264633839653634373264633839653634373264633839653634373264633839653634373264633839
    port: 5432
    username: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          32393931313933653134626331393931313933653134626331393931313933653134626331393931313933
          6531346263313939313339336531346263313939313339336531346263313939313339336531346263313939
          31333365313462633139393133393365313462633139393133393365313462633139393133393365313462
    password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          35646237643238326436353646237643238326436353646237643238326436353646237643238326436353646
          2376432383264363536462376432383264363536462376432383264363536462376432383264363536462376
          43238326436353646237643238326436353646237643238326436353646237643238326436353646237643238
  replica:
    host: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          38653961636237643238326436353646237643238326436353646237643238326436353646237643238326436
          3536462376432383264363536462376432383264363536462376432383264363536462376432383264363536
          46237643238326436353646237643238326436353646237643238326436353646237643238326436353646237
    port: 5432
    username: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          64333938653961636237643238326436353646237643238326436353646237643238326436353646237643238
          3264363536462376432383264363536462376432383264363536462376432383264363536462376432383264
          36353646237643238326436353646237643238326436353646237643238326436353646237643238326436353
    password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          46238326436353646237643238326436353646237643238326436353646237643238326436353646237643238
          3264363536462376432383264363536462376432383264363536462376432383264363536462376432383264
          36353646237643238326436353646237643238326436353646237643238326436353646237643238326436353

api_credentials:
  payment_gateway:
    api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          32646338396536343732646338396536343732646338396536343732646338396536343732646338396536343
          7326463383965363437326463383965363437326463383965363437326463383965363437326463383965363
          43732646338396536343732646338396536343732646338396536343732646338396536343732646338396536
    secret_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          34373264633839653634373264633839653634373264633839653634373264633839653634373264633839653
          6343732646338396536343732646338396536343732646338396536343732646338396536343732646338396536
          34373264633839653634373264633839653634373264633839653634373264633839653634373264633839653
    webhook_url: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          63438396536343732646338396536343732646338396536343732646338396536343732646338396536343732
          6463383965363437326463383965363437326463383965363437326463383965363437326463383965363437
          32646338396536343732646338396536343732646338396536343732646338396536343732646338396536343

ssl_certificates:
  wildcard_cert:
    certificate: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          33839653634373264633839653634373264633839653634373264633839653634373264633839653634373264
          6338396536343732646338396536343732646338396536343732646338396536343732646338396536343732646
          33839653634373264633839653634373264633839653634373264633839653634373264633839653634373264
    private_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          39653634373264633839653634373264633839653634373264633839653634373264633839653634373264633
          8396536343732646338396536343732646338396536343732646338396536343732646338396536343732646338
          39653634373264633839653634373264633839653634373264633839653634373264633839653634373264633
    ca_bundle: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          65363437326463383965363437326463383965363437326463383965363437326463383965363437326463383
          9653634373264633839653634373264633839653634373264633839653634373264633839653634373264633
          83965363437326463383965363437326463383965363437326463383965363437326463383965363437326463
```

### Partial File Encryption Strategy
```yaml
# group_vars/production/main.yml
---
# Public configuration
app_name: "enterprise_app"
app_version: "2.1.0"
environment: "production"
region: "us-west-2"

# Database configuration (mixed)
database:
  engine: "postgresql"
  version: "13"
  host: "prod-db-cluster.company.com"
  port: 5432
  database: "enterprise_app_prod"
  # Encrypted sensitive values
  username: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66633839653634373264633839653634373264633839653634373264633839653634373264633839653634
  password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          32393931313933653134626331393931313933653134626331393931313933653134626331393931313933
  ssl_cert: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          35646237643238326436353646237643238326436353646237643238326436353646237643238326436353646

# Redis configuration
redis:
  cluster_mode: true
  host: "prod-redis-cluster.company.com"
  port: 6379
  # Encrypted auth token
  auth_token: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          38653961636237643238326436353646237643238326436353646237643238326436353646237643238326436

# External service configurations
external_services:
  payment_processor:
    base_url: "https://api.payments.com/v2"
    timeout: 30
    # Encrypted API credentials
    api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          64333938653961636237643238326436353646237643238326436353646237643238326436353646237643238
    webhook_secret: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          46238326436353646237643238326436353646237643238326436353646237643238326436353646237643238
```

## Multi-Environment Security

### Environment-Specific Vault Configuration
```yaml
# ansible.cfg
[defaults]
vault_identity_list = dev@vault/vault_ids/dev_vault_id, staging@vault/vault_ids/staging_vault_id, prod@vault/vault_ids/prod_vault_id, shared@vault/vault_ids/shared_vault_id

# Inventory configuration
[inventory]
enable_plugins = host_list, script, auto, yaml, ini, toml
cache = True
cache_plugin = memory
cache_timeout = 3600
cache_connection = /tmp/ansible_inventory_cache

[ssh_connection]
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s -o StrictHostKeyChecking=no
pipelining = True
control_path_dir = /tmp
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

### Playbook Execution with Multiple Vaults
```bash
#!/bin/bash
# deploy.sh - Multi-environment deployment script with vault management

set -euo pipefail

ENVIRONMENT=${1:-"development"}
PLAYBOOK=${2:-"site.yml"}
EXTRA_VARS=${3:-""}

# Validate environment
case "$ENVIRONMENT" in
    "development"|"dev")
        VAULT_IDS="--vault-id dev@vault/vault_ids/dev_vault_id --vault-id shared@vault/vault_ids/shared_vault_id"
        INVENTORY="inventory/dev.yml"
        ;;
    "staging"|"stage")
        VAULT_IDS="--vault-id staging@vault/vault_ids/staging_vault_id --vault-id shared@vault/vault_ids/shared_vault_id"
        INVENTORY="inventory/staging.yml"
        ;;
    "production"|"prod")
        VAULT_IDS="--vault-id prod@vault/vault_ids/prod_vault_id --vault-id shared@vault/vault_ids/shared_vault_id"
        INVENTORY="inventory/production.yml"
        # Additional production safety checks
        read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            echo "Deployment cancelled."
            exit 1
        fi
        ;;
    *)
        echo "Error: Invalid environment '$ENVIRONMENT'"
        echo "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Pre-deployment vault verification
echo "Verifying vault access for environment: $ENVIRONMENT"
for vault_id in $(echo "$VAULT_IDS" | grep -o '[a-z]*@[^[:space:]]*'); do
    vault_name=$(echo "$vault_id" | cut -d'@' -f1)
    vault_file=$(echo "$vault_id" | cut -d'@' -f2)
    
    if [[ ! -f "$vault_file" ]]; then
        echo "Error: Vault file not found: $vault_file"
        exit 1
    fi
    
    # Test vault access by trying to decrypt a test file
    test_file="vault/${vault_name}/test.yml"
    if [[ -f "$test_file" ]]; then
        if ! ansible-vault view --vault-id "$vault_id" "$test_file" &>/dev/null; then
            echo "Error: Cannot access vault for $vault_name"
            exit 1
        fi
    fi
done

echo "Vault verification successful"

# Run playbook with appropriate vault configurations
echo "Deploying to $ENVIRONMENT using playbook: $PLAYBOOK"
ansible-playbook \
    -i "$INVENTORY" \
    $VAULT_IDS \
    -e "environment=$ENVIRONMENT" \
    ${EXTRA_VARS:+-e "$EXTRA_VARS"} \
    "$PLAYBOOK"

echo "Deployment completed successfully"
```

## External Secret Management

### HashiCorp Vault Integration
```yaml
# Integration with HashiCorp Vault
- name: "Retrieve secrets from HashiCorp Vault"
  block:
    - name: "Authenticate with Vault using role"
      uri:
        url: "{{ vault_addr }}/v1/auth/aws/login"
        method: POST
        body_format: json
        body:
          role: "{{ vault_role }}"
        headers:
          X-Vault-Request: true
      register: vault_auth
      no_log: true
      
    - name: "Retrieve database secrets"
      uri:
        url: "{{ vault_addr }}/v1/secret/data/{{ app_name }}/{{ environment }}/database"
        method: GET
        headers:
          X-Vault-Token: "{{ vault_auth.json.auth.client_token }}"
          X-Vault-Request: true
      register: db_secrets
      no_log: true
      
    - name: "Set database credentials"
      set_fact:
        database_username: "{{ db_secrets.json.data.data.username }}"
        database_password: "{{ db_secrets.json.data.data.password }}"
        database_ssl_cert: "{{ db_secrets.json.data.data.ssl_certificate }}"
      no_log: true
      
  rescue:
    - name: "Fallback to Ansible Vault"
      include_vars:
        file: "vault/{{ environment }}/database_secrets.yml"
        name: vault_db_secrets
      no_log: true
      
    - name: "Set database credentials from Ansible Vault"
      set_fact:
        database_username: "{{ vault_db_secrets.database_clusters.primary.username }}"
        database_password: "{{ vault_db_secrets.database_clusters.primary.password }}"
      no_log: true
```

### AWS Secrets Manager Integration
```yaml
# AWS Secrets Manager lookup
- name: "Retrieve secrets from AWS Secrets Manager"
  set_fact:
    aws_secrets:
      rds_master: "{{ lookup('aws_secret', 'prod/myapp/rds-master', region='us-west-2') | from_json }}"
      api_keys: "{{ lookup('aws_secret', 'prod/myapp/api-keys', region='us-west-2') | from_json }}"
      jwt_secrets: "{{ lookup('aws_secret', 'prod/myapp/jwt-secrets', region='us-west-2') | from_json }}"
  no_log: true
  when: cloud_provider == 'aws'

# Dynamic secret retrieval with rotation
- name: "Get current secret version"
  aws_secretsmanager_secret_info:
    name: "{{ secret_name }}"
    region: "{{ aws_region }}"
  register: secret_info
  
- name: "Retrieve versioned secret"
  set_fact:
    current_secret: |
      {{
        lookup('aws_secret', secret_name, 
               version_id=secret_info.secret.version_ids_to_stages.keys() | select('match', '^[A-Za-z0-9]+$') | first,
               region=aws_region) | from_json
      }}
  no_log: true
```

### Azure Key Vault Integration
```yaml
# Azure Key Vault integration
- name: "Retrieve secrets from Azure Key Vault"
  azure.azcollection.azure_rm_keyvaultsecret_info:
    vault_uri: "{{ azure_key_vault_uri }}"
    name: "{{ item }}"
  loop:
    - database-password
    - api-key
    - ssl-certificate
  register: azure_secrets
  no_log: true
  
- name: "Process Azure secrets"
  set_fact:
    azure_secret_values: |
      {{
        azure_secret_values | default({}) | combine({
          item.item: item.secret.value
        })
      }}
  loop: "{{ azure_secrets.results }}"
  no_log: true
```

## Automated Key Rotation

### Vault Key Rotation Pipeline
```yaml
# .github/workflows/vault-rotation.yml
name: Vault Key Rotation

on:
  schedule:
    - cron: '0 2 1 * *'  # Monthly on 1st at 2 AM
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rotate (dev/staging/prod/all)'
        required: true
        default: 'dev'
        type: choice
        options:
        - dev
        - staging
        - prod
        - all

jobs:
  rotate-vault-keys:
    runs-on: ubuntu-latest
    environment: vault-management
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.VAULT_ROTATION_TOKEN }}
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install Ansible
        run: |
          python -m pip install --upgrade pip
          pip install ansible ansible-vault
          
      - name: Configure Git
        run: |
          git config --global user.name "Vault Rotation Bot"
          git config --global user.email "vault-bot@company.com"
          
      - name: Backup current vault keys
        run: |
          mkdir -p backup/vault_keys/$(date +%Y%m%d_%H%M%S)
          cp -r vault/vault_ids/* backup/vault_keys/$(date +%Y%m%d_%H%M%S)/
          
      - name: Rotate vault keys
        run: |
          ./scripts/vault_manager.sh rotate ${{ github.event.inputs.environment || 'dev' }}
        env:
          ANSIBLE_VAULT_PASSWORD_FILE: ${{ secrets.MASTER_VAULT_PASSWORD_FILE }}
          
      - name: Test vault access
        run: |
          ./scripts/test_vault_access.sh ${{ github.event.inputs.environment || 'dev' }}
          
      - name: Commit rotated keys
        run: |
          git add vault/vault_ids/
          git commit -m "Rotate vault keys for ${{ github.event.inputs.environment || 'dev' }} - $(date +%Y-%m-%d)"
          git push
          
      - name: Notify team
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Vault key rotation completed for ${{ github.event.inputs.environment || "dev" }} environment'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Secret Rotation Playbook
```yaml
# playbooks/rotate_secrets.yml
---
- name: "Automated secret rotation"
  hosts: localhost
  gather_facts: false
  vars:
    rotation_environments:
      - development
      - staging
      - production
    
  tasks:
    - name: "Create rotation backup directory"
      file:
        path: "backup/secrets/{{ ansible_date_time.date }}_{{ ansible_date_time.hour }}{{ ansible_date_time.minute }}"
        state: directory
        mode: '0700'
        
    - name: "Backup current secrets"
      copy:
        src: "vault/{{ item }}/"
        dest: "backup/secrets/{{ ansible_date_time.date }}_{{ ansible_date_time.hour }}{{ ansible_date_time.minute }}/{{ item }}/"
        mode: '0600'
      loop: "{{ rotation_environments }}"
      
    - name: "Generate new database passwords"
      set_fact:
        new_db_passwords: |
          {{
            new_db_passwords | default({}) | combine({
              item: lookup('password', '/dev/null length=32 chars=ascii_letters,digits')
            })
          }}
      loop: "{{ rotation_environments }}"
      no_log: true
      
    - name: "Generate new API keys"
      set_fact:
        new_api_keys: |
          {{
            new_api_keys | default({}) | combine({
              item: lookup('password', '/dev/null length=64 chars=ascii_letters,digits')
            })
          }}
      loop: "{{ rotation_environments }}"
      no_log: true
      
    - name: "Update database passwords in vault"
      copy:
        content: |
          ---
          database_clusters:
            primary:
              password: !vault |
                {{ new_db_passwords[item] | ansible_vault_encrypt(vault_password) }}
        dest: "vault/{{ item }}/database_secrets_new.yml"
        mode: '0600'
      loop: "{{ rotation_environments }}"
      no_log: true
      
    - name: "Validate new vault files"
      ansible.builtin.shell: |
        ansible-vault view --vault-id {{ item }}@vault/vault_ids/{{ item }}_vault_id \
          vault/{{ item }}/database_secrets_new.yml > /dev/null
      loop: "{{ rotation_environments }}"
      register: vault_validation
      
    - name: "Replace old vault files with new ones"
      copy:
        src: "vault/{{ item }}/database_secrets_new.yml"
        dest: "vault/{{ item }}/database_secrets.yml"
        mode: '0600'
      loop: "{{ rotation_environments }}"
      when: vault_validation is succeeded
      
    - name: "Clean up temporary files"
      file:
        path: "vault/{{ item }}/database_secrets_new.yml"
        state: absent
      loop: "{{ rotation_environments }}"
```

## Audit & Compliance

### Comprehensive Vault Audit Script
```python
#!/usr/bin/env python3
# vault_audit.py - Comprehensive Ansible Vault audit tool

import os
import sys
import json
import hashlib
import datetime
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

class VaultAuditor:
    def __init__(self, vault_dir: str = "vault"):
        self.vault_dir = Path(vault_dir)
        self.audit_results = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'vault_files': [],
            'security_issues': [],
            'compliance_status': {},
            'recommendations': []
        }
    
    def audit_file_permissions(self, file_path: Path) -> Dict:
        """Audit file permissions and ownership"""
        stat = file_path.stat()
        permissions = oct(stat.st_mode)[-3:]
        
        issues = []
        if permissions != '600':
            issues.append(f"Incorrect permissions: {permissions} (should be 600)")
        
        if stat.st_uid != os.getuid():
            issues.append("File not owned by current user")
            
        return {
            'file': str(file_path),
            'permissions': permissions,
            'owner_uid': stat.st_uid,
            'issues': issues
        }
    
    def verify_encryption(self, file_path: Path) -> Dict:
        """Verify file is properly encrypted"""
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                
            is_encrypted = first_line.startswith('$ANSIBLE_VAULT')
            
            if not is_encrypted:
                return {
                    'file': str(file_path),
                    'encrypted': False,
                    'issue': 'File appears to be unencrypted'
                }
            
            # Parse vault header
            parts = first_line.split(';')
            if len(parts) >= 3:
                version = parts[1]
                cipher = parts[2]
                
                return {
                    'file': str(file_path),
                    'encrypted': True,
                    'version': version,
                    'cipher': cipher
                }
            else:
                return {
                    'file': str(file_path),
                    'encrypted': True,
                    'issue': 'Malformed vault header'
                }
                
        except Exception as e:
            return {
                'file': str(file_path),
                'encrypted': False,
                'issue': f'Error reading file: {str(e)}'
            }
    
    def check_file_age(self, file_path: Path) -> Dict:
        """Check file age and recommend rotation"""
        stat = file_path.stat()
        modified_time = datetime.datetime.fromtimestamp(stat.st_mtime)
        age_days = (datetime.datetime.now() - modified_time).days
        
        recommendations = []
        if age_days > 90:
            recommendations.append(f"File is {age_days} days old, consider rotation")
        if age_days > 365:
            recommendations.append("File is over 1 year old, rotation strongly recommended")
            
        return {
            'file': str(file_path),
            'last_modified': modified_time.isoformat(),
            'age_days': age_days,
            'recommendations': recommendations
        }
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity checking"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def audit_vault_structure(self) -> Dict:
        """Audit overall vault directory structure"""
        if not self.vault_dir.exists():
            return {'error': f'Vault directory not found: {self.vault_dir}'}
        
        expected_dirs = ['production', 'staging', 'development', 'shared', 'vault_ids']
        existing_dirs = [d.name for d in self.vault_dir.iterdir() if d.is_dir()]
        
        missing_dirs = set(expected_dirs) - set(existing_dirs)
        unexpected_dirs = set(existing_dirs) - set(expected_dirs)
        
        return {
            'expected_directories': expected_dirs,
            'existing_directories': existing_dirs,
            'missing_directories': list(missing_dirs),
            'unexpected_directories': list(unexpected_dirs)
        }
    
    def run_full_audit(self) -> Dict:
        """Run comprehensive audit of all vault files"""
        print("Starting comprehensive vault audit...")
        
        # Audit directory structure
        structure_audit = self.audit_vault_structure()
        self.audit_results['directory_structure'] = structure_audit
        
        # Find all vault files
        vault_files = list(self.vault_dir.rglob('*.yml'))
        print(f"Found {len(vault_files)} vault files")
        
        for vault_file in vault_files:
            print(f"Auditing: {vault_file}")
            
            file_audit = {
                'file_path': str(vault_file),
                'file_hash': self.calculate_file_hash(vault_file)
            }
            
            # Check permissions
            perm_audit = self.audit_file_permissions(vault_file)
            file_audit['permissions'] = perm_audit
            if perm_audit['issues']:
                self.audit_results['security_issues'].extend(perm_audit['issues'])
            
            # Verify encryption
            enc_audit = self.verify_encryption(vault_file)
            file_audit['encryption'] = enc_audit
            if not enc_audit.get('encrypted', False):
                self.audit_results['security_issues'].append(
                    f"Unencrypted file: {vault_file}"
                )
            
            # Check file age
            age_audit = self.check_file_age(vault_file)
            file_audit['age_analysis'] = age_audit
            if age_audit['recommendations']:
                self.audit_results['recommendations'].extend(age_audit['recommendations'])
            
            self.audit_results['vault_files'].append(file_audit)
        
        # Generate compliance status
        self.audit_results['compliance_status'] = {
            'total_files_audited': len(vault_files),
            'security_issues_found': len(self.audit_results['security_issues']),
            'recommendations_count': len(self.audit_results['recommendations']),
            'compliance_score': self._calculate_compliance_score()
        }
        
        return self.audit_results
    
    def _calculate_compliance_score(self) -> float:
        """Calculate compliance score based on audit results"""
        total_files = len(self.audit_results['vault_files'])
        if total_files == 0:
            return 0.0
        
        issues_count = len(self.audit_results['security_issues'])
        recommendations_count = len(self.audit_results['recommendations'])
        
        # Calculate score (0-100)
        deductions = (issues_count * 10) + (recommendations_count * 2)
        max_possible_deductions = total_files * 12
        
        if max_possible_deductions == 0:
            return 100.0
        
        score = max(0, 100 - (deductions / max_possible_deductions * 100))
        return round(score, 2)
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate audit report"""
        report = {
            'audit_summary': {
                'timestamp': self.audit_results['timestamp'],
                'compliance_score': self.audit_results['compliance_status']['compliance_score'],
                'total_files': self.audit_results['compliance_status']['total_files_audited'],
                'security_issues': self.audit_results['compliance_status']['security_issues_found'],
                'recommendations': self.audit_results['compliance_status']['recommendations_count']
            },
            'detailed_results': self.audit_results
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Audit report saved to: {output_file}")
        
        return json.dumps(report, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Ansible Vault Audit Tool')
    parser.add_argument('--vault-dir', default='vault', help='Vault directory path')
    parser.add_argument('--output', help='Output file for audit report')
    parser.add_argument('--format', choices=['json', 'summary'], default='json', 
                       help='Output format')
    
    args = parser.parse_args()
    
    auditor = VaultAuditor(args.vault_dir)
    results = auditor.run_full_audit()
    
    if args.format == 'summary':
        print(f"\nAudit Summary:")
        print(f"Compliance Score: {results['compliance_status']['compliance_score']}%")
        print(f"Files Audited: {results['compliance_status']['total_files_audited']}")
        print(f"Security Issues: {results['compliance_status']['security_issues_found']}")
        print(f"Recommendations: {results['compliance_status']['recommendations_count']}")
        
        if results['security_issues']:
            print("\nSecurity Issues:")
            for issue in results['security_issues']:
                print(f"  - {issue}")
                
        if results['recommendations']:
            print("\nRecommendations:")
            for rec in results['recommendations'][:5]:  # Show first 5
                print(f"  - {rec}")
    else:
        report = auditor.generate_report(args.output)
        if not args.output:
            print(report)

if __name__ == '__main__':
    main()
```

## Performance & Scalability

### Vault Caching Strategy
```yaml
# Vault caching for large-scale deployments
- name: "Setup vault caching"
  block:
    - name: "Check vault cache validity"
      stat:
        path: "/tmp/vault_cache_{{ environment }}.json"
      register: vault_cache_file
      
    - name: "Load cached vault data"
      set_fact:
        cached_vault_data: "{{ lookup('file', '/tmp/vault_cache_' + environment + '.json') | from_json }}"
      when: 
        - vault_cache_file.stat.exists
        - (ansible_date_time.epoch | int - vault_cache_file.stat.mtime) < vault_cache_ttl | default(3600)
        
    - name: "Decrypt and cache vault data"
      block:
        - name: "Decrypt all vault files"
          include_vars:
            file: "{{ item }}"
            name: "vault_data_{{ item | basename | regex_replace('\\.yml$', '') }}"
          loop: "{{ vault_files_to_cache }}"
          register: vault_decryption
          no_log: true
          
        - name: "Build consolidated vault cache"
          set_fact:
            cached_vault_data: |
              {{
                hostvars[inventory_hostname] | 
                dict2items | 
                selectattr('key', 'match', '^vault_data_.*') | 
                list | 
                items2dict(key_name='key', value_name='value')
              }}
          no_log: true
          
        - name: "Save vault cache"
          copy:
            content: "{{ cached_vault_data | to_nice_json }}"
            dest: "/tmp/vault_cache_{{ environment }}.json"
            mode: '0600'
          no_log: true
          
      when: cached_vault_data is not defined
  
  vars:
    vault_files_to_cache:
      - "vault/{{ environment }}/database_secrets.yml"
      - "vault/{{ environment }}/api_keys.yml"
      - "vault/{{ environment }}/certificates.yml"
      - "vault/shared/monitoring_keys.yml"
```

### Parallel Vault Operations
```yaml
# Parallel vault decryption for performance
- name: "Decrypt vault files in parallel"
  include_vars:
    file: "{{ item }}"
    name: "vault_{{ item | basename | regex_replace('\\.yml$', '') }}"
  loop:
    - "vault/{{ environment }}/database_secrets.yml"
    - "vault/{{ environment }}/api_keys.yml"
    - "vault/{{ environment }}/certificates.yml"
    - "vault/shared/monitoring_keys.yml"
    - "vault/shared/backup_keys.yml"
    - "vault/shared/logging_tokens.yml"
  async: 30
  poll: 0
  register: vault_decryption_jobs
  no_log: true
  
- name: "Wait for all vault decryption to complete"
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: vault_decryption_results
  until: vault_decryption_results.finished
  retries: 10
  delay: 3
  loop: "{{ vault_decryption_jobs.results }}"
  no_log: true
```

## Security Best Practices

### Enterprise Security Checklist
```yaml
# Security validation tasks
- name: "Enterprise vault security validation"
  block:
    - name: "Validate vault file permissions"
      find:
        paths: "{{ vault_base_dir }}"
        patterns: "*.yml"
        recurse: true
      register: vault_files
      
    - name: "Check file permissions"
      stat:
        path: "{{ item.path }}"
      register: file_stats
      loop: "{{ vault_files.files }}"
      
    - name: "Assert correct permissions"
      assert:
        that:
          - "item.stat.mode == '0600'"
        fail_msg: "Incorrect permissions on {{ item.stat.path }}: {{ item.stat.mode }}"
        success_msg: "Correct permissions on {{ item.stat.path }}"
      loop: "{{ file_stats.results }}"
      
    - name: "Validate vault encryption"
      shell: |
        head -1 "{{ item.path }}" | grep -q '^\$ANSIBLE_VAULT'
      register: encryption_check
      failed_when: encryption_check.rc != 0
      loop: "{{ vault_files.files }}"
      
    - name: "Check for weak encryption"
      shell: |
        head -1 "{{ item.path }}" | grep -q 'AES256'
      register: encryption_strength
      failed_when: encryption_strength.rc != 0
      loop: "{{ vault_files.files }}"
      
    - name: "Validate vault IDs exist"
      stat:
        path: "{{ vault_base_dir }}/vault_ids/{{ item }}_vault_id"
      register: vault_id_files
      failed_when: not vault_id_files.stat.exists
      loop:
        - production
        - staging
        - development
        - shared
        
    - name: "Check vault ID permissions"
      stat:
        path: "{{ vault_base_dir }}/vault_ids/{{ item }}_vault_id"
      register: vault_id_stats
      loop:
        - production
        - staging
        - development
        - shared
        
    - name: "Assert vault ID permissions"
      assert:
        that:
          - "item.stat.mode == '0600'"
        fail_msg: "Incorrect vault ID permissions: {{ item.stat.path }}"
      loop: "{{ vault_id_stats.results }}"
      
    - name: "Validate no plain text secrets in git"
      shell: |
        git log --all --full-history -p | grep -i 'password\|secret\|key\|token' | grep -v '!vault' || true
      register: git_secret_check
      failed_when: git_secret_check.stdout != ''
      
  always:
    - name: "Generate security audit report"
      template:
        src: security_audit_report.j2
        dest: "/tmp/vault_security_audit_{{ ansible_date_time.date }}.txt"
        mode: '0600'
```

This comprehensive enterprise vault guide provides production-ready security patterns, automated management tools, and compliance frameworks for protecting sensitive data in large-scale Ansible environments.