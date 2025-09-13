# Architect: Supply Chain Security (SLSA, Sigstore, Container Scanning)

Software supply chain attacks are increasing, so ensuring that every artifact is verified, signed, and scanned is essential for production safety.

## 1. Core Concepts

### Supply Chain Security

Protects the entire software lifecycle from code commit → build → artifact → deployment.

Prevents malicious code, tampering, or unverified dependencies from entering production.

### SLSA (Supply-chain Levels for Software Artifacts)

A framework for provenance and integrity of artifacts.

Levels:

Level 1: Basic build process documented

Level 2: Tamper-evident logs

Level 3: Provenance attestation signed

Level 4: Fully auditable and verifiable builds

### Sigstore

Tool for cryptographically signing software artifacts.

Ensures authenticity and provenance of container images, binaries, and scripts.

Works with SLSA attestation workflows.

### Container Scanning

Detects vulnerabilities in container images before deployment.

Tools: Trivy, Clair, Aqua, Prisma Cloud, Anchore.

## 2. Implementation Patterns
### A. CI/CD Integration

Sign artifacts automatically during build:

Git commit → build → container → sign with Sigstore → push to registry.

Store provenance metadata for auditing.

### B. Container Scanning

Scan images at build time and registry scan before deploy.

Integrate with pipeline to fail builds on critical CVEs.

### C. Dependency Management

Verify third-party libraries via hash checks, SBOM (Software Bill of Materials).

Use SLSA-compliant pipelines to ensure reproducibility.

### D. Artifact Attestation

Attach signatures to all production artifacts.

Verify signatures at deploy time using tools like Sigstore Cosign.

## 3. Best Practices

### Enforce Signing

All production artifacts must be signed and verifiable.

### SBOM Generation

Produce Software Bill of Materials for each build; verify dependencies.

### Continuous Scanning

Integrate CVE scanning into CI/CD pipelines.

Fail fast for critical vulnerabilities.

### Immutable Artifacts

Push signed images to immutable registries; avoid rebuilds in production.

### Audit and Compliance

Maintain logs of artifact signing, verification, and scanning for audits.

### Automated Attestation

Integrate Sigstore or Cosign to automatically verify provenance at deployment.

## 4. Operational Benefits

Reduces risk of supply chain attacks like malicious dependencies or image tampering.

Ensures auditable, reproducible builds.

Provides confidence to leadership and compliance teams.

Integrates seamlessly with DevOps automation and CI/CD pipelines.