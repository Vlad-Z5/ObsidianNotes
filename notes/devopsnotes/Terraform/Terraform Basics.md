Open-source Infrastructure as Code (IaC) tool by HashiCorp that enables you to define and provision infrastructure using declarative configuration files. Supports multi-cloud, has a large ecosystem with wide support, uses declarative syntax
### Key Benefits

- **Infrastructure as Code**: Version control your infrastructure
- **Execution Plans**: Preview changes before applying
- **Resource Graph**: Understands dependencies between resources
- **Change Automation**: Complex changesets with minimal human interaction
- **Multi-Cloud**: Works with multiple cloud providers

### Core Workflow

1. **Write** - Author infrastructure as code
2. **Plan** - Preview changes before applying
3. **Apply** - Provision reproducible infrastructure

### Installation

```bash
# Download from terraform.io or use package managers
brew install terraform # MacOS

choco install terraform # Windows (using Chocolatey)

# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

terraform version # Verify installation
```
