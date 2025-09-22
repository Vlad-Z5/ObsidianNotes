# Architect: Auto-scaling patterns (infra and application layers)

Autoscaling ensures your workloads adapt to demand, reducing downtime and avoiding over-provisioning.

## 1. Core Concepts
- ### Horizontal Scaling (Scale Out/In)
	- Add/remove instances, pods, or containers.
	- Examples: EC2 Auto Scaling Groups, Kubernetes HPA/VPA.
- ### Vertical Scaling (Scale Up/Down)
	- Increase/decrease resources (CPU, RAM) for a single instance/container.
	- Examples: RDS instance resize, node VM type upgrade.
- ### Predictive vs Reactive
	- Reactive: Trigger scaling based on current metrics (CPU, memory, queue length).
	- Predictive: Forecast demand and scale proactively (AWS Auto Scaling predictive policies, custom ML models).
	- Why it matters: Proper autoscaling ensures performance while optimizing cost.
## 2. Infrastructure Layer Autoscaling
- ### Cloud Instances
	- AWS Auto Scaling Groups (ASG)
        - Scale EC2 instances based on metrics (CPU, memory, custom CloudWatch metrics).
        - Supports mixed instances, spot + on-demand combinations.
	- GCP Managed Instance Groups (MIG)
	    - Autoscale VMs by metrics or schedules.
	- Patterns:
        - Multi-AZ deployment to avoid single-AZ bottlenecks.
        - Warm pool/pre-warmed instances for fast scale-out.
- ### Kubernetes Nodes
	- Cluster Autoscaler
        - Adds/removes nodes to accommodate pod scheduling.
        - Integrates with cloud provider APIs for dynamic node provisioning.
	- Karpenter (AWS)
        - Intelligent pod-based autoscaling.
        - Optimizes node types and spot instance utilization.
## 3. Application Layer Autoscaling
- ### Kubernetes HPA/VPA
	- Horizontal Pod Autoscaler (HPA)
	    - Scales pods based on CPU, memory, or custom metrics (Prometheus metrics).
	- Vertical Pod Autoscaler (VPA)
	    - Adjusts pod resource requests/limits automatically.
	- Custom Metrics
        - Queue length, request latency, throughput.
        - Tools: Prometheus Adapter, CloudWatch custom metrics.
- ### B. AWS / Cloud Services
	- RDS Aurora Autoscaling
    	- Read replicas scale automatically for read-heavy workloads.
	- SQS + Lambda
	    - Lambda concurrency scales with queue length.
	- Application Load Balancer
    	- Works with ASGs for dynamic scaling.
## 4. Best Practices
- ### Combine Horizontal + Vertical Scaling
	- Use HPA for traffic spikes, VPA for steady-state optimization.
- ### Set Safe Min/Max Boundaries
	- Avoid scaling too aggressively or under-provisioning.
- ### Use Predictive Scaling
	- Schedule scale-outs for traffic spikes (e.g., daily batch jobs).
- ### Multi-Metric Scaling
	- Don't rely only on CPU; include memory, custom app metrics.
- ### Graceful Pod/Node Draining
	- Ensure zero-downtime deployments during scale-down.
## 5. Observability & Automation
- ### Monitoring
	- Monitor scaling events (CloudWatch, Prometheus, Datadog).
	- Track SLI impact: ensure scaling maintains latency & error thresholds.
- ### Alerting
	- Alert on failures:
        - ASG failing to launch instances.
        - HPA failing to scale due to insufficient resources.
## 6. Cost Optimization
- ### Instance Types
	- Use spot instances for non-critical workloads.
- ### Resource Sizing
	- Right-size nodes & pods to avoid over-provisioning.
- ### Benefits
	- Autoscaling helps prevent paying for idle resources while maintaining performance.