Managed Kubernetes service on AWS

- **Clusters:** Control plane managed by AWS, worker nodes managed by you or AWS
- **Node Groups:** Managed or self-managed EC2 instances running Kubernetes nodes
- **Fargate:** Serverless compute for Kubernetes pods
- **Add-ons:** Managed services like CoreDNS, kube-proxy, VPC CNI plugin
- **Networking:** Uses VPC, supports CNI for pod networking
- **IAM for Service Accounts:** Fine-grained permissions per pod using IAM roles
- **Integration:** Works with CloudWatch, ALB Ingress Controller, EBS CSI Driver
- **CLI Tools:** `eksctl` for cluster creation; `kubectl` for cluster management
- **Scaling:** Supports Cluster Autoscaler and Horizontal Pod Autoscaler
- **Security:** Uses AWS IAM, Security Groups, Network Policies, and Secrets Manager
