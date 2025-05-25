**Supports:** Java, .NET, Node.js, Python, PHP, Ruby, Go, Docker

- **How It Works:**
	- Upload your code (ZIP, WAR, etc.)
	- Beanstalk handles provisioning: EC2, ELB, ASG, RDS (optional); config for DB and LB, scaling and health monitoring
	- You retain full control over resources
- **Deployment Types:**
	- **All at once:** Fast but downtime
	- **Rolling:** Update in batches
	- **Rolling with additional batch:** Zero downtime with extra capacity
	- **Immutable:** Launch all new instances before switching traffic
- **Customization:**
	- Modify EC2 instance type, VPC, security groups
	- Add `.ebextensions/` for advanced configuration (YAML)
- **Monitoring:**
	- Integrated with CloudWatch
	- Health dashboard: green/yellow/red status
- **Storage & Logs:**
	- Store logs in S3 or stream to CloudWatch Logs
	- Environment variables configurable via console or CLI

- **Use Case:** Fast deployment for developers without deep infrastructure management
