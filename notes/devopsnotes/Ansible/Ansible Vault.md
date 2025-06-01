Encrypt sensitive data like passwords, keys, and certificates in Ansible files.

## Basic Commands

```bash
# Create encrypted file
ansible-vault create secrets.yml

# Edit encrypted file
ansible-vault edit secrets.yml

# Encrypt existing file
ansible-vault encrypt plaintext.yml

# Decrypt file
ansible-vault decrypt secrets.yml

# View encrypted file
ansible-vault view secrets.yml

# Change password
ansible-vault rekey secrets.yml
```

## Using Encrypted Files

```bash
# Run playbook with vault password prompt
ansible-playbook -K --ask-vault-pass playbook.yml

# Use password file
ansible-playbook --vault-password-file ~/.vault_pass playbook.yml

# Use environment variable
export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass
ansible-playbook playbook.yml
```

## Encrypting Variables

```yaml
# vars/secrets.yml
---
database_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66633839653634373264633...
          
api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          32393931313933653134626...
```

## Mixed Files (Partial Encryption)

```yaml
# Can mix encrypted and plain text
---
database_host: localhost
database_port: 3306
database_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66633839653634373264633...
```

## Vault ID Labels

```bash
# Create with specific vault ID
ansible-vault create --vault-id prod@prompt secrets.yml

# Use multiple vault IDs
ansible-playbook --vault-id dev@dev_pass --vault-id prod@prod_pass playbook.yml
```

## Best Practices

- Store vault password files outside project directory
- Use different passwords for different environments
- Never commit vault password files to version control
- Use `ansible-vault encrypt_string` for single values