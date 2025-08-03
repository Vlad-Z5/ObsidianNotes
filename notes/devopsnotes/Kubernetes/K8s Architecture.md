### Master Node (Control Plane)

- **API Server**: Central management hub, handles REST operations, entry point for all admin tasks
- **etcd**: Distributed key-value store, cluster state and configuration, critical for disaster recovery
- **Controller Manager**: Runs controller processes (Node, Replication, etc.), ensures desired state
- **Scheduler**: Assigns pods to nodes, considers resources and constraints

### Worker Node Components

- **kubelet**: Primary node agent, communicates with API server, manages pod lifecycle
- **kube-proxy**: Network proxy, maintains network rules, handles service load balancing
- **Container Runtime**: Docker/containerd/CRI-O, runs containers, pulls images