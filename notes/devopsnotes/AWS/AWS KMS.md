Key Management Service to create, manage, and control encryption keys; can be symmetric (AES-256) and assymmetric (RSA and ECC)
- **Types**: SSE-S3, SSE-SQS, SSE-DDB (default) - owned by AWS; aws/service-name - managed by AWS, SSE-C - customer managed
- **Keys:** Customer managed or AWS managed CMKs
- **Encryption:** Integrated with most AWS services (S3, EBS, RDS, etc.)
- **Grants:** Allow temporary access to keys without modifying IAM policies
- **Key Policies:** Control access at the key level
- **Auditing:** Integrated with CloudTrail for logging key usage
- **Use cases:** Encrypt data at rest, secure secrets, sign/verify data