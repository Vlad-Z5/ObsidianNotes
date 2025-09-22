# Architect: Use of spot preemptible instances where safe

Spot (AWS) or preemptible (GCP) instances allow running workloads at significantly lower cost than on-demand instances, with the tradeoff of possible interruption.

## 1. Core Concepts
- ### Spot/Preemptible Instances
	- Cloud provider offers unused capacity at steep discounts.
	- Instances can be terminated with short notice (e.g., 2 minutes in AWS, 30 seconds in GCP).
- ### Safe Workloads
	- Ideal for stateless, batch, or fault-tolerant workloads.
	- Not recommended for critical production services without redundancy.
- ### Key Objectives
	- Reduce infrastructure cost.
	- Maintain reliability by selecting appropriate workloads.
	- Implement interruption handling strategies.
## 2. Implementation Patterns
- ### Identify Safe Workloads
	- Batch jobs (data processing, ETL, analytics)
	- CI/CD runners and test pipelines
	- Non-critical dev/test environments
	- Compute-intensive tasks that can be retried
- ### Interruption Handling
	- Use instance termination notices to gracefully stop or checkpoint workloads.
	- Integrate with queues or orchestration platforms (Kubernetes, ECS, Dataflow).
- ### Kubernetes Integration
	- Cluster Autoscaler can provision spot nodes alongside on-demand nodes.
	- Use taints and tolerations to run safe workloads on spot nodes.
	- Implement PodDisruptionBudgets and priority classes to handle preemption.
- ### Cost Optimization Strategy
	- Mix spot/preemptible with on-demand/reserved instances for a balanced approach.
	- Schedule batch workloads during off-peak hours when spot capacity is higher.
	- Monitor historical spot pricing trends to optimize selection.
## 3. Best Practices
- ### Design for Fault Tolerance
	- Ensure workloads retry, checkpoint, or reschedule on interruption.
- ### Monitor Preemption Events
	- Track termination notices and instance replacement times.
- ### Use Multi-Zone / Multi-Region
	- Increase availability and reduce risk of capacity shortages.
- ### Automate Workload Placement
	- Use orchestration platforms to dynamically place safe workloads on spot nodes.
- ### Combine with Scheduling
	- Turn off non-critical spot instances during idle periods.
## 4. Operational Benefits
- ### Cost Savings
	- Significantly reduces compute costs (often 70–90% cheaper than on-demand).
- ### Budget Allocation
	- Frees budget for critical production workloads.
- ### Scalability
	- Increases flexibility in scaling batch and non-critical workloads.
- ### Architecture
	- Encourages resilient architecture design for cloud workloads.