### Standard Project Structure
```
ansible-infrastructure/
├── ansible.cfg                    # Project configuration
├── requirements.yml               # External dependencies
├── site.yml                      # Main orchestration playbook
├── inventory/                    # Environment definitions
│   ├── production/
│   │   ├── hosts.yml            # Production inventory
│   │   ├── group_vars/
│   │   │   ├── all.yml          # Global production variables
│   │   │   ├── webservers.yml   # Web server group variables
│   │   │   └── databases.yml    # Database group variables
│   │   └── host_vars/
│   │       ├── web01.yml        # Host-specific variables
│   │       └── db01.yml
│   ├── staging/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   └── host_vars/
│   └── development/
│       ├── hosts.yml
│       ├── group_vars/
│       └── host_vars/
├── playbooks/                   # Environment-specific playbooks
│   ├── site-production.yml     # Production deployment
│   ├── site-staging.yml        # Staging deployment
│   ├── maintenance.yml         # Maintenance tasks
│   ├── security-hardening.yml  # Security configurations
│   ├── backup.yml              # Backup procedures
│   └── monitoring.yml          # Monitoring setup
├── roles/                      # Custom roles
│   ├── common/
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   ├── templates/
│   │   ├── files/
│   │   ├── vars/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   ├── webserver/
│   ├── database/
│   ├── loadbalancer/
│   └── monitoring/
├── collections/                # External collections
│   └── requirements.yml
├── plugins/                   # Custom plugins
│   ├── modules/
│   ├── filters/
│   └── callbacks/
├── scripts/                  # Utility scripts
│   ├── bootstrap.sh         # Environment setup
│   ├── vault-setup.sh       # Vault initialization
│   └── deploy.sh           # Deployment wrapper
├── tests/                   # Testing framework
│   ├── integration/
│   ├── molecule/           # Molecule tests
│   └── unit/
├── docs/                   # Documentation
│   ├── runbooks/
│   ├── architecture.md
│   └── deployment-guide.md
├── .gitignore
├── .ansible-lint
├── molecule.yml           # Molecule configuration
└── README.md
```

## Configuration Files

### ansible.cfg (Project Root)
```ini
[defaults]
inventory = inventory/production/hosts.yml
roles_path = roles:collections/ansible_collections
collections_paths = collections
host_key_checking = False
timeout = 30
forks = 20
gather_timeout = 30
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 86400
retry_files_enabled = False
log_path = logs/ansible.log

[inventory]
enable_plugins = host_list, script, auto, yaml, ini, toml

[ssh_connection]
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
control_path_dir = /tmp/.ansible-cp
pipelining = True

[persistent_connection]
command_timeout = 30
connect_timeout = 30

[colors]
highlight = white
verbose = blue
warn = bright purple
error = red
debug = dark gray
deprecate = purple
skip = cyan
unreachable = red
ok = green
changed = yellow
diff_add = green
diff_remove = red
diff_lines = cyan
```

### requirements.yml (Dependencies)
```yaml
# External roles from Ansible Galaxy
roles:
  - name: geerlingguy.nginx
    version: 3.1.4
  - name: geerlingguy.mysql
    version: 4.3.4
  - name: geerlingguy.docker
    version: 6.1.0

# Collections
collections:
  - name: community.general
    version: ">=4.0.0"
  - name: ansible.posix
    version: ">=1.3.0"
  - name: community.crypto
    version: ">=2.0.0"
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: amazon.aws
    version: ">=3.0.0"
```

## Environment-Specific Layouts

### Multi-Environment Structure
```
inventory/
├── production/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml              # Global prod variables
│   │   │   # - environment: production
│   │   │   # - backup_retention: 30
│   │   │   # - monitoring_enabled: true
│   │   ├── webservers.yml       # Web tier config
│   │   │   # - nginx_worker_processes: 4
│   │   │   # - ssl_certificate_path: /etc/ssl/certs/prod.crt
│   │   └── databases.yml        # DB tier config
│   │       # - mysql_innodb_buffer_pool_size: 8G
│   │       # - mysql_max_connections: 200
│   └── host_vars/
│       ├── prod-web-01.yml      # Specific host overrides
│       └── prod-db-01.yml
├── staging/
│   # Mirror production structure with staging values
└── development/
    # Simplified structure for dev environment
```

## Role Organization Patterns

### Microservice Architecture Roles
```
roles/
├── infrastructure/             # Base infrastructure
│   ├── common/                # Base system setup
│   ├── security/              # Security hardening
│   └── monitoring/            # System monitoring
├── application/               # Application-specific roles
│   ├── frontend/              # Frontend services
│   ├── api/                   # API services
│   ├── worker/                # Background workers
│   └── cache/                 # Caching layer
└── platform/                 # Platform services
    ├── database/              # Database setup
    ├── messaging/             # Message queues
    ├── logging/               # Centralized logging
    └── backup/                # Backup procedures
```

### Cloud-Native Structure
```
roles/
├── kubernetes/
│   ├── cluster/               # K8s cluster setup
│   ├── networking/            # Network policies
│   ├── ingress/               # Ingress controllers
│   └── monitoring/            # K8s monitoring
├── containers/
│   ├── docker/                # Docker configuration
│   ├── registry/              # Container registry
│   └── security/              # Container security
└── cloud/
    ├── aws/                   # AWS-specific resources
    ├── azure/                 # Azure-specific resources
    └── gcp/                   # GCP-specific resources
```

## Best Practices for Structure

### Directory Naming Conventions
- Use lowercase with hyphens for multi-word names
- Environment directories match deployment targets exactly
- Role names reflect their primary function
- Group variables files match inventory group names

### File Organization
- Keep playbooks focused on specific purposes
- Use `site.yml` as the main orchestration playbook
- Separate environment-specific configurations
- Maintain consistent variable naming across environments

### Security Considerations
- Store sensitive files in separate directories
- Use `.gitignore` to exclude sensitive data
- Implement vault password files outside project directory
- Separate vault files by environment