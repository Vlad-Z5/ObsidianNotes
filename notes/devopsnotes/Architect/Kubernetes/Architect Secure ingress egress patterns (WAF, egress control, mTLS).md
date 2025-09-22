# Architect: Secure ingress egress patterns (WAF, egress control, mTLS)

This subtopic focuses on controlling traffic into and out of your cluster to enforce security, compliance, and resilience.

## 1. Core Concepts
- ### Traffic Types
	- Ingress: Traffic entering the cluster (external → services).
	- Egress: Traffic leaving the cluster (services → external systems).
- ### Security Components
	- WAF (Web Application Firewall): Protects against web-layer attacks (SQLi, XSS, DDoS).
	- mTLS (Mutual TLS): Encrypts traffic between services and authenticates both client and server.
	- Egress Controls: Restrict external access to only approved destinations.
- ### Goal
	- Prevent unauthorized access, enforce data confidentiality, and mitigate lateral movement risks.
## 2. Ingress Security Patterns
- ### API Gateway / Ingress Controller
	- Use Ingress controllers (NGINX, AWS ALB Ingress, GKE Ingress) to route traffic.
	- Enable TLS termination at ingress.
	- Integrate with WAF for layer-7 filtering.
- ### WAF
	- AWS WAF, Cloudflare, Azure WAF.
	- Apply rule sets for OWASP Top 10 protection.
	- Can block IP ranges, inspect headers, detect SQLi/XSS attempts.
- ### Rate Limiting & Authentication
	- Enforce rate limiting to prevent DoS attacks.
	- Use JWT/OAuth2 for service authentication.
	- Combine with RBAC and service accounts.
## 3. Egress Security Patterns
- ### Network Policies
	- Kubernetes NetworkPolicies restrict which pods can initiate connections outside the cluster.
	- Example: only allow pods to reach internal APIs, block all other external access.
- ### Proxy / Firewall
	- Use egress proxies or cloud firewall rules.
	- Inspect traffic for compliance and audit requirements.
- ### DNS & IP Whitelisting
	- Restrict egress to approved IPs or FQDNs (e.g., internal databases, SaaS services).
## 4. mTLS for Internal Traffic
- ### Encryption
	- Encrypt all pod-to-pod traffic within the cluster.
- ### Authentication
	- Authenticate both client and server to prevent unauthorized access.
- ### Automation
	- Service Mesh (Istio, Linkerd, App Mesh) handles certificate management and rotation automatically.
## 5. Best Practices
- ### Enforce TLS everywhere
	- Ingress, service-to-service, and egress.
- ### Zero-trust approach
	- Default deny all inbound/outbound; allow only what is required.
- ### Combine policies
	- WAF + network policies + service mesh.
- ### Audit & observability
	- Log all ingress/egress traffic.
	- Alert on anomalies or policy violations.
- ### Automate certificate rotation
	- Avoid expired certs causing downtime or breaches.
## 6. Tools & Automation
- ### Ingress / API Gateway
	- AWS ALB, NGINX, GKE Ingress, Istio Gateway.
- ### WAF
	- AWS WAF, Azure WAF, Cloudflare.
- ### Egress Control
	- Calico, Cilium, Istio egress policies, cloud firewall rules.
- ### mTLS
	- Istio, Linkerd, App Mesh.
- ### Monitoring & Auditing
	- Prometheus, Grafana, FluentBit, CloudTrail/Stackdriver.
