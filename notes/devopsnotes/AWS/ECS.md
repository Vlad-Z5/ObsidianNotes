Container orchestration service for running Docker containers on AWS

- **Clusters:** Logical grouping of tasks or services
- **Tasks:** One or more containers running together (task definition)
- **Services:** Manage long-running tasks, ensure desired count
- **Task Definitions:** JSON templates defining container specs, CPU, memory, networking
- **Launch Types:**
	- **Fargate:** Serverless, no EC2 management
	- **EC2:** Run containers on your EC2 instances
- **Service Discovery:** Integrated with Route 53
- **Auto Scaling:** Scale tasks based on demand
- **Load Balancing:** Integrates with ALB / NLB
- **IAM Roles:** Fine-grained permissions for tasks
- **Monitoring:** CloudWatch logs and metrics
- **Integration:** Works with ECR for container image