Used for Infrastructure as Code (IaC) on AWS

- **Templates:** Written in **YAML** or **JSON**, define **resources**, **parameters**, **outputs**, and **mappings**
- **Stacks:** A deployed instance of a template; supports **nested stacks** for modular design; **change sets** preview changes before update
- **Resources:** EC2, S3, RDS, VPC, IAM, etc.
- **Parameters:** User-defined inputs during deployment  
- **Mappings:** Key-value lookups (e.g., region to AMI)
- **Conditions:** Create resources only if specific conditions are met
- **Outputs:** Export values for cross-stack reference
- **Drift Detection:** Detect changes made outside CloudFormation
- **Rollback Triggers:** Revert stack if deployment fails
- **Stack policy**: Prevent changes to some resources
