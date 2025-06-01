Reusable units of code that perform specific tasks on managed hosts.

## Essential Modules

### System Management

- **package:** Install/remove packages
- **service:** Manage services
- **user:** Manage user accounts
- **group:** Manage groups
- **cron:** Manage cron jobs
- **mount:** Manage filesystems

### Files and Directories

- **copy:** Copy files to remote hosts
- **file:** Set file attributes
- **template:** Process Jinja2 templates
- **fetch:** Retrieve files from remote hosts
- **synchronize:** Use rsync for file sync
- **archive/unarchive:** Handle compressed files

### Commands

- **command:** Run commands (no shell processing)
- **shell:** Run commands through shell
- **raw:** Execute raw SSH commands
- **script:** Transfer and execute scripts

### Network

- **uri:** Interact with HTTP services
- **get_url:** Download files from URLs

## Usage Examples

```yaml
- name: Install package
  package:
    name: nginx
    state: present

- name: Copy configuration
  copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart nginx

- name: Ensure service running
  service:
    name: nginx
    state: started
    enabled: yes
```

## Module Documentation

- `ansible-doc module_name`: View module documentation
- `ansible-doc -l`: List all available modules