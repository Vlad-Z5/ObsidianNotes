### Basic Syntax

```hcl
# Comments start with #

# Resource block
resource "aws_instance" "example" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"
  
  tags = {
    Name = "HelloWorld"
  }
}

# Data source block
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

# Variable block
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

# Output block
output "instance_ip" {
  description = "The public IP address of the instance"
  value       = aws_instance.example.public_ip
}
```

### Block Types

- **`resource`** - Defines infrastructure objects
- **`data`** - Fetches information from providers
- **`variable`** - Input variables
	- `description` to provide more info about the variable
	- `type` to specify data type
	- `default` to set default
- **`output`** - Return values
	- has `description` and `values` as fields
- **`locals`** - Local values for reuse
- **`module`** - Calls to child modules
- **`provider`** - Provider configurations
	- `aws, google, azurerm, kubernetes, ...`
	- Most commonly configured at root, can be configured in child module to reuse it for multiple resources, can be configured in the required_providers to specify a version to be used
- **`terraform`** - Terraform settings

### Data Types

```hcl
# String
variable "name" {
  type    = string
  default = "example"
}

# Number
variable "count" {
  type    = number
  default = 3
}

# Boolean
variable "enabled" {
  type    = bool
  default = true
}

# List
variable "availability_zones" {
  type    = list(string)
  default = ["us-west-2a", "us-west-2b"]
}

# Map
variable "tags" {
  type = map(string)
  default = {
    Environment = "dev"
    Owner       = "team"
  }
}

# Object
variable "server_config" {
  type = object({
    name         = string
    instance_type = string
    disk_size    = number
  })
  default = {
    name         = "web-server"
    instance_type = "t2.micro"
    disk_size    = 20
  }
}
```
