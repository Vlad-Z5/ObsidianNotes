### State File Basics

```hcl
# Terraform state stores mapping between configuration and real-world resources
# Default: terraform.tfstate (local)
# Production: Remote backend (S3, Azure Storage, GCS, Terraform Cloud)
```

### Remote State Configuration

**AWS S3 Backend:**

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**Azure Storage Backend:**

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "terraformstatestg"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}
```

**Google Cloud Storage Backend:**

```hcl
terraform {
  backend "gcs" {
    bucket = "my-terraform-state-bucket"
    prefix = "terraform/state"
  }
}
```

### State Commands

```bash
terraform show # Show current state
terraform state list # List resources in state
terraform state show aws_instance.example # Show specific resource
terraform state mv aws_instance.old_name aws_instance.new_name # Move resource in state
terraform state rm aws_instance.example # Remove resource from state (doesn't destroy)
terraform import aws_instance.example i-1234567890abcdef0 # Import existing resource into state
terraform refresh # Refresh state to match real infrastructure
terraform apply -replace=aws_instance.example # Replace specific resource
```

### State Locking

```hcl
# DynamoDB table for S3 backend locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
  
  tags = {
    Name = "Terraform State Lock Table"
  }
}
```
