Encrypt sensitive data like passwords, keys, and certificates in Ansible files.

## Basic Commands

```bash
ansible-vault create secrets.yml # Create encrypted file
ansible-vault edit secrets.yml # Edit encrypted file
ansible-vault encrypt plaintext.yml # Encrypt existing file
ansible-vault decrypt secrets.yml # Decrypt file
ansible-vault view secrets.yml # View encrypted file
ansible-vault rekey secrets.yml # Change password

```

## Using Encrypted Files

```bash
ansible-playbook -K --ask-vault-pass playbook.yml # Run playbook with sudo and vault password prompt

ansible-playbook --vault-password-file ~/.vault_pass playbook.yml # Use vault password file

export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass # Set vault password file env var
ansible-playbook playbook.yml # Run playbook using env var

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
ansible-vault create --vault-id prod@prompt secrets.yml # Create file with specific vault ID and prompt

ansible-playbook --vault-id dev@dev_pass --vault-id prod@prod_pass playbook.yml # Run playbook using multiple vault IDs
```

## Best Practices

- Store vault password files outside project directory
- Use different passwords for different environments
- Never commit vault password files to version control
- Use `ansible-vault encrypt_string` for single values