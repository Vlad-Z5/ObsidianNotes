## Built-in Functions

### String Functions

```hcl
# String manipulation
locals {
  # Basic string operations
  upper_name     = upper(var.environment)           # "PRODUCTION"
  lower_name     = lower(var.environment)           # "production"
  title_name     = title(var.environment)           # "Production"
  trimmed        = trim(var.user_input, " \t\n")    # Remove whitespace
  
  # String formatting
  formatted_name = format("%s-%s-%03d", var.project, var.env, var.instance_count)
  padded_number  = format("%05d", var.counter)      # "00042"
  
  # String replacement and manipulation
  sanitized      = replace(var.raw_name, "/[^a-zA-Z0-9-]/", "-")
  joined_tags    = join(",", var.tag_list)
  split_string   = split(",", "red,green,blue")
  
  # Substring operations
  prefix         = substr(var.long_string, 0, 10)
  suffix         = substr(var.long_string, -5, -1)
  
  # String validation
  starts_with_prod = startswith(var.environment, "prod")
  ends_with_dev    = endswith(var.environment, "dev")
  contains_test    = contains(var.environment, "test")
}
```

### Numeric Functions

```hcl
locals {
  # Mathematical operations
  absolute_value = abs(-42)                         # 42
  ceiling_value  = ceil(4.7)                        # 5
  floor_value    = floor(4.7)                       # 4
  maximum        = max(1, 5, 3, 9, 2)              # 9
  minimum        = min(1, 5, 3, 9, 2)              # 1
  
  # Advanced math
  power_result   = pow(2, 8)                        # 256
  log_result     = log(100, 10)                     # 2
  sign_value     = signum(-42)                      # -1
  
  # Parse numbers from strings
  parsed_int     = parseint("42", 10)               # 42
  parsed_float   = tonumber("3.14")                 # 3.14
}
```

### Collection Functions

```hcl
variable "users" {
  default = ["alice", "bob", "charlie", "diana"]
}

variable "servers" {
  default = {
    web1 = { type = "t3.micro", az = "us-east-1a" }
    web2 = { type = "t3.small", az = "us-east-1b" }
    db1  = { type = "t3.medium", az = "us-east-1a" }
  }
}

locals {
  # List operations
  user_count     = length(var.users)                # 4
  first_user     = var.users[0]                     # "alice"
  last_user      = var.users[length(var.users) - 1] # "diana"
  
  # List manipulation
  reversed_users = reverse(var.users)
  sorted_users   = sort(var.users)
  unique_items   = distinct(["a", "b", "a", "c"])   # ["a", "b", "c"]
  
  # List filtering and transformation
  admin_users    = [for user in var.users : user if startswith(user, "a")]
  uppercase_users = [for user in var.users : upper(user)]
  
  # Set operations
  user_set       = toset(var.users)
  list_union     = setunion(toset(["a", "b"]), toset(["b", "c"]))
  list_intersection = setintersection(toset(["a", "b"]), toset(["b", "c"]))
  
  # Map operations
  server_types   = values(var.servers)[*].type      # Extract all types
  server_names   = keys(var.servers)                # ["web1", "web2", "db1"]
  
  # Flatten nested structures
  all_tags = flatten([
    for server_name, server in var.servers : [
      for tag_key, tag_value in server.tags : {
        server = server_name
        key    = tag_key
        value  = tag_value
      }
    ]
  ])
}
```

### Date and Time Functions

```hcl
locals {
  # Current timestamp
  current_time     = timestamp()                    # "2024-01-15T10:30:00Z"
  
  # Time formatting
  formatted_time   = formatdate("YYYY-MM-DD", timestamp())
  custom_format    = formatdate("DD/MM/YYYY hh:mm:ss", timestamp())
  
  # Time arithmetic (using timeadd)
  future_time      = timeadd(timestamp(), "24h")
  past_time        = timeadd(timestamp(), "-1h")
  
  # Time parsing
  parsed_time      = timeadd("2024-01-01T00:00:00Z", "0s")
}
```

### Encoding Functions

```hcl
locals {
  # Base64 encoding/decoding
  encoded_data     = base64encode("Hello, World!")
  decoded_data     = base64decode(local.encoded_data)
  
  # JSON operations
  json_string      = jsonencode({
    name = "example"
    tags = ["web", "production"]
  })
  parsed_json      = jsondecode(local.json_string)
  
  # URL encoding
  encoded_url      = urlencode("hello world & stuff")
  
  # YAML operations
  yaml_string      = yamlencode({
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata   = { name = "example" }
  })
  parsed_yaml      = yamldecode(local.yaml_string)
}
```

### Filesystem Functions

```hcl
locals {
  # File operations
  config_content   = file("${path.module}/config.json")
  template_content = templatefile("${path.module}/user-data.sh", {
    hostname = "web-server"
    packages = ["nginx", "htop"]
  })
  
  # File information
  file_exists      = fileexists("${path.module}/config.json")
  file_base64      = filebase64("${path.module}/binary-file.zip")
  file_md5         = filemd5("${path.module}/config.json")
  file_sha1        = filesha1("${path.module}/config.json")
  file_sha256      = filesha256("${path.module}/config.json")
  file_sha512      = filesha512("${path.module}/config.json")
  
  # Directory listing
  config_files     = fileset(path.module, "configs/*.json")
  all_tf_files     = fileset(path.module, "**/*.tf")
}
```

### Hash and Crypto Functions

```hcl
locals {
  # Hashing functions
  md5_hash         = md5("Hello, World!")
  sha1_hash        = sha1("Hello, World!")
  sha256_hash      = sha256("Hello, World!")
  sha512_hash      = sha512("Hello, World!")
  
  # UUID generation
  random_uuid      = uuidv4()
  namespace_uuid   = uuidv5("dns", "example.com")
  
  # Password generation
  random_password  = bcrypt("my-secret-password")
}
```

### IP Network Functions

```hcl
variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

locals {
  # CIDR operations
  cidr_host        = cidrhost(var.vpc_cidr, 10)     # "10.0.0.10"
  cidr_netmask     = cidrnetmask(var.vpc_cidr)      # "255.255.0.0"
  cidr_subnets     = cidrsubnets(var.vpc_cidr, 8, 8, 8, 8)
  
  # Subnet calculations
  public_subnets = [
    for i in range(2) : cidrsubnet(var.vpc_cidr, 8, i)
  ]
  
  private_subnets = [
    for i in range(2) : cidrsubnet(var.vpc_cidr, 8, i + 10)
  ]
}
```

## Expressions and Operators

### Conditional Expressions

```hcl
# Ternary operator
locals {
  environment_type = var.environment == "prod" ? "production" : "non-production"
  instance_count   = var.environment == "prod" ? 3 : 1
  
  # Complex conditionals
  instance_type = (
    var.environment == "prod" ? "t3.large" :
    var.environment == "staging" ? "t3.medium" :
    "t3.micro"
  )
  
  # Null coalescing
  final_name = coalesce(var.custom_name, "${var.project}-${var.environment}")
  
  # Try function for error handling
  parsed_value = try(tonumber(var.maybe_number), 0)
  safe_access  = try(var.complex_object.nested.value, "default")
}
```

### For Expressions

```hcl
variable "environments" {
  default = ["dev", "staging", "prod"]
}

variable "instance_configs" {
  default = {
    web = { count = 2, type = "t3.micro" }
    api = { count = 1, type = "t3.small" }
    db  = { count = 1, type = "t3.medium" }
  }
}

locals {
  # List comprehensions
  environment_buckets = [
    for env in var.environments : "${var.project}-${env}-bucket"
  ]
  
  # Conditional list comprehensions
  production_envs = [
    for env in var.environments : env if env != "dev"
  ]
  
  # Object comprehensions
  instance_tags = {
    for service, config in var.instance_configs : service => {
      Name        = "${var.project}-${service}"
      Environment = var.environment
      Type        = config.type
      Count       = config.count
    }
  }
  
  # Nested for expressions
  all_instances = flatten([
    for service, config in var.instance_configs : [
      for i in range(config.count) : {
        name    = "${var.project}-${service}-${i + 1}"
        type    = config.type
        service = service
        index   = i
      }
    ]
  ])
  
  # Grouping with for expressions
  instances_by_type = {
    for instance in local.all_instances : instance.type => instance...
  }
}
```

### Dynamic Blocks

```hcl
# Dynamic security group rules
resource "aws_security_group" "web" {
  name_prefix = "${var.project}-web-"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.allowed_ports
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidrs
    }
  }

  dynamic "ingress" {
    for_each = var.security_group_rules
    iterator = rule
    content {
      from_port       = rule.value.from_port
      to_port         = rule.value.to_port
      protocol        = rule.value.protocol
      cidr_blocks     = rule.value.cidr_blocks
      security_groups = lookup(rule.value, "security_groups", null)
      description     = lookup(rule.value, "description", null)
    }
  }
}

# Dynamic tags
resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = var.ami_id
  instance_type = var.instance_type

  dynamic "tag" {
    for_each = merge(
      var.common_tags,
      {
        Name  = "${var.project}-web-${count.index + 1}"
        Index = count.index + 1
      }
    )
    content {
      key   = tag.key
      value = tag.value
    }
  }
}
```

## Advanced Expression Patterns

### Complex Data Transformations

```hcl
variable "raw_data" {
  default = [
    { name = "web1", env = "prod", type = "t3.large", port = 80 },
    { name = "web2", env = "prod", type = "t3.large", port = 80 },
    { name = "api1", env = "prod", type = "t3.medium", port = 8080 },
    { name = "db1", env = "prod", type = "t3.xlarge", port = 5432 },
  ]
}

locals {
  # Group by type and create load balancer target groups
  targets_by_port = {
    for item in var.raw_data : item.port => {
      port     = item.port
      protocol = item.port == 443 ? "HTTPS" : "HTTP"
      targets = [
        for target in var.raw_data : {
          id   = target.name
          port = target.port
        } if target.port == item.port
      ]
    }...
  }
  
  # Create security group rules matrix
  service_communication = {
    for service in ["web", "api", "db"] : service => {
      ingress_rules = flatten([
        for other_service in ["web", "api", "db"] : [
          for rule in lookup(var.service_rules, "${other_service}_to_${service}", []) : {
            from_service = other_service
            to_service   = service
            port         = rule.port
            protocol     = rule.protocol
          }
        ]
      ])
    }
  }
}
```

### Validation Expressions

```hcl
variable "environment" {
  type        = string
  description = "Environment name"
  
  validation {
    condition = contains([
      "development", "staging", "production"
    ], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  
  validation {
    condition = can(regex("^[tm][0-9]+\\.(nano|micro|small|medium|large|xlarge|[0-9]+xlarge)$", var.instance_type))
    error_message = "Instance type must be a valid EC2 instance type."
  }
}

variable "cidr_blocks" {
  type        = list(string)
  description = "List of CIDR blocks"
  
  validation {
    condition = alltrue([
      for cidr in var.cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid."
  }
}
```

### Error Handling Patterns

```hcl
locals {
  # Safe property access
  database_config = try(var.services.database, {
    engine   = "mysql"
    version  = "8.0"
    instance = "db.t3.micro"
  })
  
  # Multiple fallback attempts
  api_endpoint = coalesce(
    try(var.custom_endpoints.api, null),
    try("${var.load_balancer_dns}/api", null),
    "http://localhost:8080/api"
  )
  
  # Conditional resource creation
  create_monitoring = alltrue([
    var.enable_monitoring,
    var.environment == "production",
    can(var.monitoring_config.retention_days)
  ])
  
  # Graceful degradation
  backup_schedule = try(
    var.backup_config.schedule,
    var.environment == "production" ? "0 2 * * *" : "0 3 * * 0"
  )
}
```

## Custom Function Patterns

### Reusable Logic with Locals

```hcl
locals {
  # Function-like locals for reusable logic
  format_resource_name = {
    for key, config in var.resources : key => format(
      "%s-%s-%s",
      var.project,
      var.environment,
      config.name
    )
  }
  
  # Complex validation logic
  validate_config = {
    for service, config in var.services : service => merge(config, {
      valid = alltrue([
        can(tonumber(config.replicas)),
        contains(["http", "https", "tcp"], config.protocol),
        config.port >= 1 && config.port <= 65535
      ])
    })
  }
  
  # Resource dependency resolution
  dependency_order = [
    for service in keys(var.services) : service
    if length([
      for dep in lookup(var.services[service], "depends_on", []) :
      dep if !contains(keys(var.services), dep)
    ]) == 0
  ]
}
```

### Template Functions

```hcl
# Using templatefile for complex configurations
locals {
  nginx_config = templatefile("${path.module}/templates/nginx.conf.tpl", {
    server_name    = var.domain_name
    upstream_servers = [
      for i in range(var.backend_count) : {
        host = "backend-${i + 1}"
        port = 8080
      }
    ]
    ssl_enabled    = var.ssl_certificate_arn != null
    client_max_body_size = var.max_upload_size
  })
  
  docker_compose = templatefile("${path.module}/templates/docker-compose.yml.tpl", {
    services = {
      for name, config in var.services : name => merge(config, {
        environment = merge(
          var.common_env_vars,
          lookup(config, "environment", {})
        )
        labels = merge(
          var.common_labels,
          lookup(config, "labels", {})
        )
      })
    }
  })
}
```