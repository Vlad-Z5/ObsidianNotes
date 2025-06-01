YAML files that define automation tasks, executed in order on specified hosts.

## Basic Structure

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  vars:
    http_port: 80
  tasks:
    - name: Install Apache
      package:
        name: httpd
        state: present
    
    - name: Start Apache service
      service:
        name: httpd
        state: started
```

## Key Components

- **hosts:** Target hosts or groups
- **become:** Run as sudo/root
- **vars:** Playbook variables
- **tasks:** List of actions to perform
- **handlers:** Tasks triggered by notifications

A Play is a single, complete execution unit within a playbook. It specifies which hosts to target and what tasks to execute on those hosts. Plays are used to group related tasks and execute them in a specific order.

Tasks are individual actions within a play that use modules to perform operations on managed nodes. Each task is executed in order and can include conditionals, loops, and handlers.
## Multiple Plays

```yaml
---
- name: Configure databases
  hosts: databases
  tasks:
    - name: Install MySQL
      package:
        name: mysql-server
        state: present

- name: Configure web servers  
  hosts: webservers
  tasks:
    - name: Install Apache
      package:
        name: httpd
        state: present
```

## Common Options

- `gather_facts: no`: Skip fact gathering
- `serial: 2`: Run on 2 hosts at a time
- `max_fail_percentage: 10`: Fail if >10% hosts fail
- `ignore_errors: yes`: Continue on task failure
- `delegate_to: localhost`: Run task locally
  
## Collections

Collections are a distribution format for Ansible content. They bundle together multiple roles, modules, plugins, and other Ansible artifacts. Collections make it easier to share and reuse Ansible content. Example

A collection structure might look like this:

```
my_collection/
├── roles/
│   └── my_role/
│       └── tasks/
│           └── main.yml
├── plugins/
│   └── modules/
│       └── my_module.py
└── README.md
```