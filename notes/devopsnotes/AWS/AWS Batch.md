Fully managed batch processing service that efficiently runs batch computing workloads. Jobs are Docker images that run on ECS, we can utilize Spot instances for cost reduction, has no limitations apart from storage and EC2 to run on

- **Job Definitions:** Specify how jobs are to be run (container image, vCPU, memory)
- **Job Queues:** Hold submitted jobs until compute resources are available
- **Compute Environments:** Managed or unmanaged EC2 or Spot instances for running jobs
- **Scheduling:** Automatically places jobs based on resource requirements and priorities
- **Integration:** Supports Docker containers, IAM roles, CloudWatch monitoring
- **Use Cases:** Large-scale parallel jobs, HPC, ETL, ML training