Organize and reuse automation code through structured directories and standardized components.

## Directory Structure

```
roles/
└── webserver/
    ├── tasks/main.yml        # Main task list
    ├── handlers/main.yml     # Handlers
    ├── templates/           # Jinja2 templates
    ├── files/               # Static files
    ├── vars/main.yml        # Role variables
    ├── defaults/main.yml    # Default variables
    ├── meta/main.yml        # Role metadata
    └── README.md            # Documentation
```

## Using Roles in Playbooks

```yaml
---
- name: Configure servers
  hosts: webservers
  roles:
    - common
    - webserver
    - { role: database, db_port: 3306 }
```

## Role Dependencies

```yaml
# meta/main.yml
dependencies:
  - role: common
  - role: firewall
    firewall_rules:
      - port: 80
      - port: 443
```

## Example Role Structure

### tasks/main.yml

```yaml
---
- name: Install web server
  package:
    name: "{{ web_package }}"
    state: present

- name: Configure web server
  template:
    src: config.j2
    dest: "{{ web_config_path }}"
  notify: restart web server
```

### handlers/main.yml

```yaml
---
- name: restart web server
  service:
    name: "{{ web_service }}"
    state: restarted
```

### defaults/main.yml

```yaml
---
web_package: nginx
web_service: nginx
web_config_path: /etc/nginx/nginx.conf
web_port: 80
```

## Role Creation

```bash
ansible-galaxy init role_name
```

## Ansible Galaxy

- **Install:** `ansible-galaxy install username.rolename`
- **List:** `ansible-galaxy list`
- **Remove:** `ansible-galaxy remove username.rolename`