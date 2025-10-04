# Terraform Cloud Providers Integration

**Cloud Providers Integration** in Terraform enables consistent infrastructure management across AWS, Azure, Google Cloud, and multi-cloud environments with provider-specific optimizations and best practices.

## AWS Provider Deep Dive

### Advanced AWS Provider Configuration

#### Provider Configuration with Assume Role
```hcl
# Advanced AWS provider configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary AWS provider
provider "aws" {
  region = var.aws_region

  # Assume role for cross-account access
  assume_role {
    role_arn     = "arn:aws:iam::${var.target_account_id}:role/TerraformExecutionRole"
    session_name = "terraform-session"
    external_id  = var.external_id
  }

  # Default tags for all resources
  default_tags {
    tags = {
      Environment   = var.environment
      Project       = var.project_name
      ManagedBy     = "terraform"
      CostCenter    = var.cost_center
      Owner         = var.owner_team
      CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
    }
  }

  # Retry configuration
  retry_mode      = "adaptive"
  max_retries     = 10

  # Custom endpoints for testing
  # endpoints {
  #   s3  = "http://localhost:4566"
  #   ec2 = "http://localhost:4566"
  # }
}

# Secondary provider for multi-region deployments
provider "aws" {
  alias  = "secondary"
  region = var.aws_secondary_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.target_account_id}:role/TerraformExecutionRole"
    session_name = "terraform-secondary-session"
    external_id  = var.external_id
  }

  default_tags {
    tags = {
      Environment   = var.environment
      Project       = var.project_name
      ManagedBy     = "terraform"
      Region        = "secondary"
    }
  }
}

# Provider for another account
provider "aws" {
  alias  = "shared_services"
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.shared_services_account_id}:role/SharedServicesRole"
    session_name = "terraform-shared-services"
  }
}
```

#### Complete AWS Infrastructure Example
```hcl
# Data sources for AWS account information
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC with advanced features
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  instance_tenancy     = "default"
  enable_dns_hostnames = true
  enable_dns_support   = true

  # IPv6 support
  assign_generated_ipv6_cidr_block = var.enable_ipv6

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# VPC Flow Logs for security monitoring
resource "aws_flow_log" "vpc_flow_log" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-flow-log"
  }
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/flow-logs/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  kms_key_id = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-flow-log"
  }
}

# EKS cluster with advanced configuration
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-${var.environment}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.allowed_cidr_blocks

    security_group_ids = [aws_security_group.eks_cluster.id]
  }

  # Encryption configuration
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  # Logging configuration
  enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Add-ons
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
    aws_cloudwatch_log_group.eks_cluster,
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-eks-cluster"
  }
}

# CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${var.project_name}-${var.environment}/cluster"
  retention_in_days = var.log_retention_days

  kms_key_id = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-eks-logs"
  }
}

# RDS with advanced features
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  # Engine configuration
  engine                      = "postgres"
  engine_version              = "14.9"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  max_allocated_storage       = var.db_max_allocated_storage
  storage_type                = "gp3"
  storage_throughput          = 125
  iops                        = 3000
  storage_encrypted           = true
  kms_key_id                  = aws_kms_key.rds.arn

  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  port                   = 5432
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period   = var.environment == "production" ? 30 : 7
  backup_window            = "03:00-04:00"
  maintenance_window       = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = var.environment != "production"

  # Monitoring and performance
  monitoring_interval    = 60
  monitoring_role_arn   = aws_iam_role.rds_enhanced_monitoring.arn
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  performance_insights_retention_period = var.environment == "production" ? 731 : 7

  # Logging
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Security
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  # Multi-AZ for production
  multi_az = var.environment == "production"

  tags = {
    Name = "${var.project_name}-${var.environment}-database"
  }
}

# Lambda function with advanced configuration
resource "aws_lambda_function" "api_handler" {
  filename         = "api_handler.zip"
  function_name    = "${var.project_name}-${var.environment}-api-handler"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  # Environment variables
  environment {
    variables = {
      ENVIRONMENT     = var.environment
      DATABASE_URL    = "postgresql://${aws_db_instance.main.username}:${var.db_password}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
      REDIS_URL       = aws_elasticache_replication_group.main.primary_endpoint_address
      S3_BUCKET       = aws_s3_bucket.app_data.bucket
      KMS_KEY_ID      = aws_kms_key.app_encryption.arn
    }
  }

  # VPC configuration
  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  # Dead letter queue
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  # Tracing
  tracing_config {
    mode = "Active"
  }

  # Reserved concurrency
  reserved_concurrency = var.environment == "production" ? 100 : 10

  tags = {
    Name = "${var.project_name}-${var.environment}-api-handler"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda,
  ]
}
```

## Azure Provider Integration

### Azure Provider Configuration

#### Complete Azure Provider Setup
```hcl
# Azure provider configuration
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
  }
}

# Primary Azure provider
provider "azurerm" {
  features {
    # Key Vault features
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }

    # Resource Group features
    resource_group {
      prevent_deletion_if_contains_resources = false
    }

    # Virtual Machine features
    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown              = false
      skip_shutdown_and_force_delete = false
    }

    # Storage Account features
    storage_account {
      prevent_deletion_if_contains_resources = false
    }
  }

  # Authentication
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id

  # Skip provider registration for faster deployment
  skip_provider_registration = true
}

# Azure AD provider for identity management
provider "azuread" {
  tenant_id = var.azure_tenant_id
}

# Secondary provider for multi-region
provider "azurerm" {
  alias = "secondary"

  features {}

  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
}
```

#### Azure Infrastructure Example
```hcl
# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.azure_location

  tags = var.common_tags
}

# Virtual Network with advanced features
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-${var.environment}-vnet"
  address_space       = [var.vnet_cidr]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  # DDoS protection
  ddos_protection_plan {
    id     = azurerm_network_ddos_protection_plan.main.id
    enable = var.enable_ddos_protection
  }

  tags = var.common_tags
}

# Network Security Group with rules
resource "azurerm_network_security_group" "web" {
  name                = "${var.project_name}-${var.environment}-web-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  # Allow HTTP
  security_rule {
    name                       = "HTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTPS
  security_rule {
    name                       = "HTTPS"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow SSH from specific subnet
  security_rule {
    name                       = "SSH"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.admin_subnet_cidr
    destination_address_prefix = "*"
  }

  tags = var.common_tags
}

# AKS cluster with advanced configuration
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project_name}-${var.environment}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${var.project_name}-${var.environment}-aks"
  kubernetes_version  = var.kubernetes_version

  # System node pool
  default_node_pool {
    name                = "system"
    node_count          = var.system_node_count
    vm_size             = var.system_node_vm_size
    type                = "VirtualMachineScaleSets"
    availability_zones  = ["1", "2", "3"]
    enable_auto_scaling = true
    min_count          = 1
    max_count          = 5
    max_pods           = 110
    os_disk_size_gb    = 100
    os_disk_type       = "Managed"
    vnet_subnet_id     = azurerm_subnet.aks.id

    # Node pool taints for system workloads
    node_taints = ["CriticalAddonsOnly=true:NoSchedule"]

    upgrade_settings {
      max_surge = "10%"
    }
  }

  # Identity configuration
  identity {
    type = "SystemAssigned"
  }

  # Network configuration
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    dns_service_ip    = "10.2.0.10"
    service_cidr      = "10.2.0.0/24"
    load_balancer_sku = "standard"
  }

  # Azure AD integration
  azure_active_directory_role_based_access_control {
    managed            = true
    azure_rbac_enabled = true
  }

  # Add-ons
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  http_application_routing_enabled = false

  azure_policy_enabled = true

  tags = var.common_tags
}

# User node pool for applications
resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size              = var.user_node_vm_size
  node_count           = var.user_node_count
  availability_zones   = ["1", "2", "3"]
  enable_auto_scaling  = true
  min_count           = 1
  max_count           = 10
  max_pods            = 110
  os_disk_size_gb     = 100
  os_disk_type        = "Managed"
  vnet_subnet_id      = azurerm_subnet.aks.id

  # Spot instances for cost optimization
  priority        = var.enable_spot_instances ? "Spot" : "Regular"
  eviction_policy = var.enable_spot_instances ? "Delete" : null
  spot_max_price  = var.enable_spot_instances ? var.spot_max_price : null

  node_labels = {
    "node-type" = "user"
  }

  upgrade_settings {
    max_surge = "33%"
  }

  tags = var.common_tags
}

# Azure SQL Database
resource "azurerm_mssql_server" "main" {
  name                         = "${var.project_name}-${var.environment}-sqlserver"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password

  # Azure AD authentication
  azuread_administrator {
    login_username = var.sql_azuread_admin_login
    object_id      = var.sql_azuread_admin_object_id
  }

  # Public network access
  public_network_access_enabled = false

  tags = var.common_tags
}

resource "azurerm_mssql_database" "main" {
  name           = "${var.project_name}-${var.environment}-db"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  max_size_gb    = var.database_max_size_gb
  sku_name       = var.database_sku_name
  zone_redundant = var.environment == "production"

  # Threat detection
  threat_detection_policy {
    state = "Enabled"
  }

  tags = var.common_tags
}
```

## Google Cloud Provider Integration

### GCP Provider Configuration

#### Complete GCP Provider Setup
```hcl
# Google Cloud provider configuration
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

# Primary Google Cloud provider
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone

  # Default labels for all resources
  default_labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
    team        = var.team_name
  }
}

# Google Cloud Beta provider for preview features
provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone

  default_labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
    team        = var.team_name
  }
}
```

#### GCP Infrastructure Example
```hcl
# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"

  description = "VPC network for ${var.project_name} ${var.environment}"
}

# Subnets
resource "google_compute_subnetwork" "private" {
  count = length(var.private_subnet_cidrs)

  name          = "${var.project_name}-${var.environment}-private-${count.index + 1}"
  ip_cidr_range = var.private_subnet_cidrs[count.index]
  region        = var.gcp_region
  network       = google_compute_network.main.id

  # Secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pod_subnet_cidrs[count.index]
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.service_subnet_cidrs[count.index]
  }

  # Private Google Access
  private_ip_google_access = true

  # VPC Flow Logs
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

# GKE cluster with advanced configuration
resource "google_container_cluster" "main" {
  name     = "${var.project_name}-${var.environment}-gke"
  location = var.gcp_region

  # Network configuration
  network    = google_compute_network.main.id
  subnetwork = google_compute_subnetwork.private[0].id

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Cluster configuration
  min_master_version = var.kubernetes_version

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "10.0.0.0/8"
      display_name = "Private networks"
    }
    cidr_blocks {
      cidr_block   = "172.16.0.0/12"
      display_name = "Private networks"
    }
    cidr_blocks {
      cidr_block   = "192.168.0.0/16"
      display_name = "Private networks"
    }
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block = "172.16.0.0/28"
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled = true
  }

  # Add-ons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    dns_cache_config {
      enabled = true
    }
  }

  # Maintenance policy
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T02:00:00Z"
      end_time   = "2023-01-01T06:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA"
    }
  }

  # Cluster autoscaling
  cluster_autoscaling {
    enabled = true
    resource_limits {
      resource_type = "cpu"
      minimum       = 1
      maximum       = 100
    }
    resource_limits {
      resource_type = "memory"
      minimum       = 1
      maximum       = 1000
    }
  }

  # Binary authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }
}

# GKE node pool
resource "google_container_node_pool" "main" {
  name       = "${var.project_name}-${var.environment}-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.main.name
  node_count = var.node_count

  # Autoscaling
  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  # Management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  # Node configuration
  node_config {
    preemptible  = var.enable_preemptible_nodes
    machine_type = var.node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    image_type   = "COS_CONTAINERD"

    # Service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Labels
    labels = {
      environment = var.environment
      node-pool   = "main"
    }

    # Taints
    dynamic "taint" {
      for_each = var.node_taints
      content {
        key    = taint.value.key
        value  = taint.value.value
        effect = taint.value.effect
      }
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Workload metadata config
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# Cloud SQL instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-${var.environment}-db"
  database_version = "POSTGRES_14"
  region           = var.gcp_region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size
    disk_autoresize   = true

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
        retention_unit   = "COUNT"
      }
    }

    # IP configuration
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
      require_ssl     = true
    }

    # Database flags
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    # Maintenance window
    maintenance_window {
      day  = 7
      hour = 2
    }
  }

  deletion_protection = var.environment == "production"
}
```

## Multi-Cloud Patterns

### Cross-Provider Resource Management

#### Multi-Cloud Deployment Pattern
```hcl
# Multi-cloud infrastructure deployment
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = var.common_tags
  }
}

# Azure Provider
provider "azurerm" {
  features {}
}

# Google Cloud Provider
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Local values for multi-cloud configuration
locals {
  cloud_configs = {
    aws = {
      enabled = var.deploy_to_aws
      region  = var.aws_region
    }
    azure = {
      enabled = var.deploy_to_azure
      region  = var.azure_location
    }
    gcp = {
      enabled = var.deploy_to_gcp
      region  = var.gcp_region
    }
  }

  # Filter enabled clouds
  enabled_clouds = {
    for cloud, config in local.cloud_configs : cloud => config if config.enabled
  }
}

# AWS Resources (conditional)
module "aws_infrastructure" {
  count = local.cloud_configs.aws.enabled ? 1 : 0

  source = "./modules/aws"

  project_name = var.project_name
  environment  = var.environment
  region       = var.aws_region
  vpc_cidr     = var.aws_vpc_cidr

  providers = {
    aws = aws
  }
}

# Azure Resources (conditional)
module "azure_infrastructure" {
  count = local.cloud_configs.azure.enabled ? 1 : 0

  source = "./modules/azure"

  project_name = var.project_name
  environment  = var.environment
  location     = var.azure_location
  vnet_cidr    = var.azure_vnet_cidr

  providers = {
    azurerm = azurerm
  }
}

# GCP Resources (conditional)
module "gcp_infrastructure" {
  count = local.cloud_configs.gcp.enabled ? 1 : 0

  source = "./modules/gcp"

  project_name = var.project_name
  environment  = var.environment
  project_id   = var.gcp_project_id
  region       = var.gcp_region
  vpc_cidr     = var.gcp_vpc_cidr

  providers = {
    google = google
  }
}

# Global DNS management with Route 53
resource "aws_route53_zone" "main" {
  count = var.manage_global_dns ? 1 : 0

  name = var.domain_name

  tags = merge(var.common_tags, {
    Name = "Global DNS Zone"
  })
}

# Global DNS records pointing to multiple clouds
resource "aws_route53_record" "app" {
  count = var.manage_global_dns ? 1 : 0

  zone_id = aws_route53_zone.main[0].zone_id
  name    = "app.${var.domain_name}"
  type    = "A"

  set_identifier = "multicloud"

  # Geolocation routing policy
  geolocation_routing_policy {
    continent = "NA"
  }

  # Health check
  health_check_id = aws_route53_health_check.app[0].id

  # AWS load balancer
  dynamic "alias" {
    for_each = local.cloud_configs.aws.enabled ? [1] : []
    content {
      name                   = module.aws_infrastructure[0].load_balancer_dns_name
      zone_id               = module.aws_infrastructure[0].load_balancer_zone_id
      evaluate_target_health = true
    }
  }

  ttl = 60
}
```

This comprehensive Cloud Providers Integration file provides detailed configurations for AWS, Azure, and Google Cloud providers with real-world examples, advanced features, and multi-cloud deployment patterns that enable teams to manage infrastructure consistently across different cloud platforms.