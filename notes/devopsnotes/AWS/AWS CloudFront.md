Content Delivery Network that achieves low latency via edge locations

- **Origins:**
	Points to an S3 bucket, ALB, EC2, or any HTTP endpoint (even non-AWS)
- **Distributions:**
	- **Web:** For websites and static/dynamic content
	- **RTMP:** For streaming media (deprecated)
- **Key Features:**
	- **Caching:** Stores content at edge locations to reduce load on origin
	- **Invalidation:** Remove cached objects before expiration
	- **Custom Domain & SSL:** Use alternate domain names (CNAMEs) and ACM/SSL certs
	- **Geo Restriction:** Allow or block content delivery based on viewer’s location
	- **Signed URLs/Cookies:** Restrict access to private content
	- **Field-Level Encryption:** Encrypt sensitive data like PII
	- **Lambda@Edge:** Run functions at edge locations for dynamic customisation
	- **OAC**: signed requests with IAM service principal to access private S3
	- **Cache invalidation** to update cache and stop using outdated info
	- DDoS protection
- **Common Use Case:**
	Speed up delivery of static assets (JS/CSS/images) hosted on S3 or behind ALB
