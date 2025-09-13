# Architect: Artifact Management (Signing, Provenance, SBOM)

Artifacts include container images, binaries, libraries, and Helm charts. Proper management ensures that all deployed components are trusted, verified, and traceable.

## 1. Core Concepts

### Artifact Repository

Centralized storage for all build artifacts.

Examples: Harbor, Artifactory, Nexus, AWS ECR, GCP Artifact Registry.

### Provenance

Metadata about who built the artifact, when, and from which source code/revision.

Ensures reproducibility and accountability.

### Signing

Cryptographic signatures verify artifact integrity and authenticity.

Tools: cosign, GPG, sigstore.

### SBOM (Software Bill of Materials)

Lists all dependencies and components in the artifact.

Essential for security audits, compliance (e.g., SLSA, ISO, SOC2), and vulnerability scanning.

## 2. Pipeline Integration Patterns

### Build Stage

Build artifact in CI/CD, generate SBOM automatically.

Sign artifact using cosign or GPG.

### Storage & Versioning

Push artifact to repository with version tags.

Maintain immutability: no artifact overwrite.

### Deployment Stage

Validate signatures and SBOM before deployment.

Ensure only approved artifacts enter production.

### Security Integration

Scan artifacts for known CVEs before push/deploy.

Integrate with vulnerability scanners (Trivy, Clair, Anchore).

## 3. Best Practices

### Immutable Artifacts

Never overwrite tags; use semantic versioning.

### Signed & Verified

Sign all artifacts; verify signature at deployment.

### SBOM Automation

Include SBOM generation in every CI build.

### Provenance Tracking

Store metadata: Git commit, build ID, pipeline, author.

### Integrate Scanning

Automated vulnerability scanning before artifacts are deployed.

### Central Repository Governance

RBAC and audit logging for artifact repositories.

## 4. Observability & Compliance

Audit Logs: Who built, signed, or promoted an artifact.

Metrics: Build success rate, SBOM coverage, signature validation failures.

Security Alerts: CVE detection or invalid signatures trigger alerts.