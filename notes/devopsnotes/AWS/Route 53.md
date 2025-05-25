**Domain Name System (DNS)** service

- **Key Functions:**
	- **Domain Registration:** Register and manage domain names directly in Route 53
	- **DNS Routing:** Resolve domain names to IP addresses or AWS resources
	- **Health Checks & Failover:** Monitor endpoints and route traffic away from unhealthy ones
	- **Traffic Flow:** Create routing policies with geolocation, latency, or weighted rules

- **Routing Policies:**
	- **Simple:** Standard DNS resolution
	- **Weighted:** Split traffic by percentage
	- **Latency-based:** Route to the lowest-latency region
	- **Failover:** Active-passive failover support
	- **Geolocation / Geoproximity:** Route based on user’s geographic location
	- **Multivalue Answer:** Return multiple IPs for redundancy

- **Alias Records:** Map to AWS resources (e.g., ELB, CloudFront) without extra DNS lookup