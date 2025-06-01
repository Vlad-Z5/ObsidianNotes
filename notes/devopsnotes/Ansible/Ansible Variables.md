Store and reuse data across playbooks, roles, and tasks for dynamic configuration.

## Variable Definition Locations (Precedence Order)

1. **Command line:** `-e "var=value"`
2. **Task vars:** `vars:` in tasks
3. **Block vars:** `vars:` in blocks
4. **Role vars:** `vars/main.yml`
5. **Play vars:** `vars:` in plays
6. **Host vars:** `host_vars/hostname.yml`
7. **Group vars:** `group_vars/groupname.yml`
8. **Role defaults:** `defaults/main.yml`

## Variable Types

```yaml
# String
server_name: "web01"

# Number
http_port: 80

# Boolean
ssl_enabled: true

# List
packages:
  - nginx
  - mysql
  - php

# Dictionary
database:
  host: localhost
  port: 3306
  name: myapp
```

## Using Variables

```yaml
- name: Install {{ package_name }}
  package:
    name: "{{ package_name }}"
    state: present

- name: Configure port {{ http_port }}
  template:
    src: config.j2
    dest: /etc/app/config.conf
```

## Facts (System Variables)

- **ansible_hostname:** System hostname
- **ansible_os_family:** OS family (RedHat, Debian)
- **ansible_distribution:** OS distribution
- **ansible_memory_mb:** Memory in MB
- **ansible_processor_count:** CPU count
- **ansible_default_ipv4.address:** Primary IP

## Registered Variables

```yaml
- name: Check service status
  command: systemctl is-active nginx
  register: service_status

- name: Display result
  debug:
    msg: "Service is {{ service_status.stdout }}"
```