# Architect: Immutable infrastructure practices (golden AMIs images, container baselines)

Immutable infrastructure is the practice of never modifying running servers or containers in production. Instead, you deploy new instances/images for every change. This eliminates configuration drift and improves repeatability.

- ### Core Concepts
	- **Immutable Infrastructure**: Once deployed, instances or containers are not updated manually. Changes require building a new image or artifact and redeploying.
	- **Golden AMIs / Images**: Pre-baked VM or container images containing OS, runtime, libraries, and security patches.
	- **Container Baselines**: Standardized container images with approved dependencies, security patches, and configurations.
	- **Benefits**:
		- Predictable deployments
		- Reduced downtime and rollback complexity
		- Enhanced security (no ad-hoc changes)
		- Easier compliance and auditing

- ### Patterns & Practices
	- **VM / Cloud Instances**
		- **Golden AMI Pipeline**:
			- Use Packer or AWS Image Builder to bake AMIs with OS patches, monitoring agents, and application dependencies.
			- Test AMIs in staging before production deployment.
		- **Immutable Deployment**:
			- Deploy new AMI via Auto Scaling Group (ASG) or instance replacement.
			- Old instances terminated after new instances are healthy.
		- **Blue/Green or Canary Deployments**:
			- Ensure zero downtime when rolling out new AMIs.
	- **Containers**
		- **Container Image Baselines**:
			- Start from minimal, official base images (e.g., Alpine, Debian slim).
			- Include only necessary dependencies.
			- Pre-install security tools and config files.
		- **Image Scanning & Signing**:
			- Scan for vulnerabilities (Trivy, Aqua, Prisma Cloud).
			- Sign images (Sigstore / Cosign) to enforce supply chain integrity.
		- **CI/CD Integration**:
			- Every commit triggers build of a new image.
			- Images tagged immutably (SHA digest) and deployed via GitOps or pipelines.

- ### Best Practices
	- **Automate Image Creation**: Packer, AWS Image Builder, Dockerfile pipelines.
	- **Version & Tag Images**: Use semantic versioning or commit SHA digests.
	- **Enforce Security Compliance**: Pre-install patches, configure logging agents, disable unused services.
	- **Replace, Don't Patch**: Rolling updates replace old instances/images rather than patching in place.
	- **Integrate Observability**: Bake monitoring and tracing agents into images to avoid manual post-deployment installs.
	- **Test Before Deployment**: Validate performance, security, and configuration in staging before production rollout.

- ### Tools & Automation
	- **VM Images**: Packer, AWS Image Builder, Terraform AMI pipelines.
	- **Containers**: Docker, BuildKit, Kaniko, Sigstore/Cosign for signing.
	- **CI/CD Integration**: Jenkins, GitHub Actions, GitLab CI, ArgoCD.
	- **Security Scanning**: Trivy, Aqua, Prisma Cloud, Clair.
	- **Configuration & Compliance**: Ansible, Chef, Puppet (baked into images), or baked scripts.