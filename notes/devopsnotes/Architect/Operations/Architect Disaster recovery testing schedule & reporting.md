# Disaster recovery testing schedule & reporting

# Content from previous subtopic: [[Cloud-native cost control tools (AWS Cost Explorer, GCP Billing, Kubecost)

What they’re testing: tradeoffs between security vs. cost vs. isolation; multi-account vs multi-namespace; runtime isolation techniques.
Good follow-ups to ask: expected scale (# clusters, pods), compliance requirements, CI/CD model, cost sensitivity.
Checklist bullets: RBAC least privilege, network policy deny-all, quotas, taints/tolerations, separate node pools, observability & quotas on logging/metrics.

Q: What’s your approach to managing 10+ Kustomize overlays without drift or duplication?

Model answer:

Adopt a base + overlay pattern: one canonical base per app, overlays per environment.

Don’t duplicate resources — use Kustomize patches/vars and generators.

Keep environment config minimal (only environment-specific values).

Use templating for secrets/configMaps via sealed-secrets/External Secrets; store overlays in Git as branches or directories with clear naming convention.

Validate overlays in CI: kustomize build + kubectl apply --server-dry-run=client + schema validation (kubeval/custom schema).

Periodic automated drift detection: generate manifests from each overlay and compare to canonical base or golden images.
What they’re testing: reproducibility, GitOps hygiene, drift detection.
Keywords to use: base/overlay, kustomize patchesStrategicPatch, sealed-secrets, CI validation, schema validation, GitOps.

Q: Explain how you’d secure cross-region S3 replication and validate data integrity at scale.

Model answer:

Secure replication:

Use S3 Replication (CRR/Cross-Region Replication) with AWS KMS — use separate CMKs in source/dest and grant replication role permissions.

Enforce bucket policies & VPC endpoints, block public access.

Use IAM replication role restricted to necessary actions.

Use S3 Object Lock (if immutability required).

Validate integrity:

Rely on S3 ETag/Checksum support (S3 supports MD5/CRC/sha256 depending on upload type).

Enable S3 Replication Time Control + Replication metrics & notifications for failures.

Periodic validation: use S3 Inventory + manifest to compare object checksums between source and destination (or use AWS SDK to compute/check checksums).

For very large scales: use checksumming pipeline (Lambda/EMR) that samples or parallel compares objects; use Batch Operations to trigger validation jobs.
What they’re testing: KMS & IAM, practical integrity checks at scale, monitoring/alerts.
Checklist bullets: KMS keys & grants, replication config, S3 Inventory, metrics & alerts, batch validation jobs.

Q: What happens when systemd hits a failing unit in a containerized node? How would you auto-recover?