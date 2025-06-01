**Core Principles:** Agentless automation using SSH, declarative YAML syntax, idempotent operations, push-based architecture, uses modules to manage systems and applications.
## [[Ansible Inventory]]
## [[Ansible Playbooks]]
## [[Ansible Modules]]
## [[Ansible Variables]]
## [[Ansible Roles]]
## [[Ansible Vault]]

## Directory Structure

- `ansible.cfg`: Configuration file
- `inventory/`: Host definitions
    - `hosts.yml`: Inventory file
    - `group_vars/`: Group variables
    - `host_vars/`: Host variables
- `playbooks/`: Playbook files
- `roles/`: Role definitions
    - `role_name/`
        - `tasks/main.yml`: Task definitions
        - `handlers/main.yml`: Handlers
        - `templates/`: Jinja2 templates
        - `files/`: Static files
        - `vars/main.yml`: Role variables
        - `defaults/main.yml`: Default variables