KInd, Helm, Kubectl, Argo cli, jq/yq

K8 Controllers are responsible for drift detection
K8 Operator is built upon controller, main function is to work with CRD based on the state of the cluster

Custom Resources:
- Applications
- AppProjects
- ApplicationSets
K8 Operators:
- Application Controller monitors first CRD
- ApplicationSet Controller monitors third CRD
Repository Server maintains local cache of remote content source, that will be translated into k8 manifests. Responsible for generating resources based on repo type, repo source location, repo path, template.
API Server is a gRPC/REST based server that exposes svc for managing configs (RBAC, cluster and repo memory management, Invocations of App operations like sync, rollback, App management and status reporting, UI, CLI)
Redis
CLI
SSO through Dex
Notifications to Slack, email, etc.
