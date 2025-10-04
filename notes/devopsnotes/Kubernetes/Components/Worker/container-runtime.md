# Container Runtime

## Overview

The **container runtime** is the software responsible for running containers on a node. It's the lowest-level component in the Kubernetes stack that actually executes and manages container processes. Kubernetes supports multiple container runtimes through the Container Runtime Interface (CRI).

**Component Type:** Worker Node Runtime
**Common Runtimes:**
- containerd (most popular)
- CRI-O
- Docker Engine (deprecated in K8s 1.24+)

**Ports:**
- containerd: Unix socket `/run/containerd/containerd.sock`
- CRI-O: Unix socket `/var/run/crio/crio.sock`

## What Container Runtime Actually Does

The container runtime is like the engine room of a ship - it's where the actual work happens, running and managing the containers that make up your applications.

### Real-World Analogy
Think of the container runtime as a building superintendent:
- **Receives blueprints** → Gets container specs from kubelet
- **Procures materials** → Pulls container images
- **Constructs spaces** → Creates container filesystems and namespaces
- **Manages tenants** → Runs and monitors container processes
- **Handles maintenance** → Manages container lifecycle (start, stop, restart)
- **Enforces rules** → Applies resource limits and security policies

### Core Responsibilities

**1. Image Management**
- Pull container images from registries
- Store and cache images locally
- Manage image layers and storage drivers
- Garbage collect unused images

**2. Container Lifecycle**
- Create container filesystems from images
- Set up Linux namespaces (PID, network, mount, IPC, UTS)
- Create and manage cgroups for resource limiting
- Start and stop container processes
- Stream container logs

**3. Network Management**
- Create network namespaces
- Call CNI plugins to set up networking
- Configure container network interfaces

**4. Volume Management**
- Mount volumes into containers
- Handle volume permissions
- Clean up volumes on container deletion

**5. Resource Management**
- Enforce CPU and memory limits (cgroups)
- Implement QoS classes
- Monitor resource usage

## Container Runtime Landscape

### Historical Evolution

```
2013-2015: Docker Era
├── Docker is the only runtime
├── Kubernetes tightly coupled with Docker
└── docker-shim in kubelet

2016: CRI Introduction
├── Kubernetes introduces Container Runtime Interface (CRI)
├── Decouples Kubernetes from Docker
└── Allows multiple runtimes

2017-2020: Runtime Diversity
├── containerd (from Docker)
├── CRI-O (from Red Hat)
├── frakti (Kata Containers)
└── cri-dockerd (Docker adapter)

2020: Dockershim Deprecation Announced
└── Docker runtime deprecated, removal planned

2022: Kubernetes 1.24+
├── Dockershim removed from kubelet
├── containerd becomes dominant
├── CRI-O popular in enterprise (Red Hat)
└── Docker still works via cri-dockerd
```

### Runtime Architecture Comparison

```
┌─────────────────────────────────────────────────────────────┐
│                   containerd Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  kubelet                                                     │
│     ↓ (CRI gRPC)                                            │
│  containerd (daemon)                                         │
│     ↓                                                        │
│  containerd-shim (per container)                            │
│     ↓                                                        │
│  runc (OCI runtime)                                         │
│     ↓                                                        │
│  Container process                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     CRI-O Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  kubelet                                                     │
│     ↓ (CRI gRPC)                                            │
│  CRI-O (daemon)                                             │
│     ↓                                                        │
│  conmon (container monitor, per container)                  │
│     ↓                                                        │
│  runc (OCI runtime)                                         │
│     ↓                                                        │
│  Container process                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Docker (via cri-dockerd)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  kubelet                                                     │
│     ↓ (CRI gRPC)                                            │
│  cri-dockerd (adapter)                                       │
│     ↓ (Docker API)                                          │
│  dockerd (Docker daemon)                                     │
│     ↓                                                        │
│  containerd                                                  │
│     ↓                                                        │
│  runc                                                        │
│     ↓                                                        │
│  Container process                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## containerd Deep Dive

### Installation and Configuration

**Install containerd:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y containerd

# RHEL/CentOS
sudo yum install -y containerd

# Or from source
wget https://github.com/containerd/containerd/releases/download/v1.7.0/containerd-1.7.0-linux-amd64.tar.gz
sudo tar Cxzvf /usr/local containerd-1.7.0-linux-amd64.tar.gz

# Install runc
wget https://github.com/opencontainers/runc/releases/download/v1.1.7/runc.amd64
sudo install -m 755 runc.amd64 /usr/local/sbin/runc

# Install CNI plugins
wget https://github.com/containernetworking/plugins/releases/download/v1.3.0/cni-plugins-linux-amd64-v1.3.0.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.3.0.tgz
```

**Configure containerd:**

```toml
# /etc/containerd/config.toml
version = 2

# ==================== Root Directory ====================
root = "/var/lib/containerd"
state = "/run/containerd"

# ==================== GRPC Configuration ====================
[grpc]
  address = "/run/containerd/containerd.sock"
  uid = 0
  gid = 0
  max_recv_message_size = 16777216
  max_send_message_size = 16777216

# ==================== Metrics ====================
[metrics]
  address = "127.0.0.1:1338"
  grpc_histogram = false

# ==================== Plugins ====================
[plugins]

  # CRI Plugin Configuration
  [plugins."io.containerd.grpc.v1.cri"]

    # Disable AppArmor (if not using)
    disable_apparmor = false

    # Disable SELinux (if not using)
    disable_selinux = false

    # Stream server configuration
    stream_server_address = "127.0.0.1"
    stream_server_port = "0"

    # Enable CNI
    enable_cni = true

    # Sandbox image (pause container)
    sandbox_image = "registry.k8s.io/pause:3.9"

    # Maximum concurrent downloads
    max_concurrent_downloads = 3

    # Max container log file size
    max_container_log_line_size = 16384

    # ==================== CNI Configuration ====================
    [plugins."io.containerd.grpc.v1.cri".cni]
      bin_dir = "/opt/cni/bin"
      conf_dir = "/etc/cni/net.d"
      max_conf_num = 1
      conf_template = ""

    # ==================== Containerd Runtime ====================
    [plugins."io.containerd.grpc.v1.cri".containerd]

      # Default runtime
      default_runtime_name = "runc"

      # Disable snapshotter
      disable_snapshot_annotations = true

      # Discard unpacked layers
      discard_unpacked_layers = false

      # ==================== runc Runtime ====================
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
        runtime_type = "io.containerd.runc.v2"

        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
          # Use systemd cgroup driver (recommended for Kubernetes)
          SystemdCgroup = true

          # Binary name
          BinaryName = "/usr/local/sbin/runc"

      # ==================== Kata Containers (Optional) ====================
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
        runtime_type = "io.containerd.kata.v2"

      # ==================== gVisor (Optional) ====================
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
        runtime_type = "io.containerd.runsc.v1"

    # ==================== Registry Configuration ====================
    [plugins."io.containerd.grpc.v1.cri".registry]
      config_path = "/etc/containerd/certs.d"

      # Mirror configuration (optional)
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
          endpoint = ["https://registry-1.docker.io"]

        # Private registry mirror
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."registry.example.com"]
          endpoint = ["https://registry.example.com"]

      # Registry credentials
      [plugins."io.containerd.grpc.v1.cri".registry.configs]
        [plugins."io.containerd.grpc.v1.cri".registry.configs."registry.example.com".auth]
          username = "user"
          password = "pass"
          # Or use auth token
          # auth = "base64-encoded-auth"

    # ==================== Image Decryption (Optional) ====================
    [plugins."io.containerd.grpc.v1.cri".image_decryption]
      key_model = "node"

  # ==================== Snapshotter ====================
  [plugins."io.containerd.snapshotter.v1.overlayfs"]
    root_path = "/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs"

# ==================== Timeouts ====================
[timeouts]
  "io.containerd.timeout.shim.cleanup" = "5s"
  "io.containerd.timeout.shim.load" = "5s"
  "io.containerd.timeout.shim.shutdown" = "3s"
  "io.containerd.timeout.task.state" = "2s"
```

**Enable and start containerd:**

```bash
# Create systemd service
sudo tee /etc/systemd/system/containerd.service <<EOF
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target local-fs.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/local/bin/containerd
Type=notify
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNPROC=infinity
LimitCORE=infinity
LimitNOFILE=infinity
TasksMax=infinity
OOMScoreAdjust=-999

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable containerd
sudo systemctl start containerd
sudo systemctl status containerd
```

### crictl - containerd CLI

```bash
# Install crictl
VERSION="v1.28.0"
wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz
sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin
rm -f crictl-$VERSION-linux-amd64.tar.gz

# Configure crictl
sudo tee /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF

# List pods
sudo crictl pods

# List containers
sudo crictl ps -a

# Inspect container
sudo crictl inspect <container-id>

# View container logs
sudo crictl logs <container-id>

# Execute command in container
sudo crictl exec -it <container-id> sh

# Pull image
sudo crictl pull nginx:latest

# List images
sudo crictl images

# Remove image
sudo crictl rmi nginx:latest

# Container stats
sudo crictl stats

# Pod stats
sudo crictl statsp
```

## CRI-O Deep Dive

### Installation and Configuration

**Install CRI-O:**

```bash
# Ubuntu 22.04
OS=xUbuntu_22.04
VERSION=1.28

echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/ /" | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable:/cri-o:/$VERSION/$OS/ /" | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable:cri-o:$VERSION.list

curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/Release.key | sudo apt-key add -
curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable:/cri-o:/$VERSION/$OS/Release.key | sudo apt-key add -

sudo apt-get update
sudo apt-get install -y cri-o cri-o-runc

# RHEL/CentOS
sudo dnf module enable cri-o:$VERSION
sudo dnf install -y cri-o
```

**Configure CRI-O:**

```toml
# /etc/crio/crio.conf
[crio]
  root = "/var/lib/containers/storage"
  runroot = "/var/run/containers/storage"
  storage_driver = "overlay"
  storage_option = [
    "overlay.mountopt=nodev",
  ]

# ==================== API ====================
[crio.api]
  listen = "/var/run/crio/crio.sock"
  stream_address = "127.0.0.1"
  stream_port = "0"
  stream_enable_tls = false
  grpc_max_send_msg_size = 16777216
  grpc_max_recv_msg_size = 16777216

# ==================== Runtime ====================
[crio.runtime]
  default_runtime = "runc"
  no_pivot = false
  decryption_keys_path = "/etc/crio/keys/"
  conmon = "/usr/bin/conmon"
  conmon_cgroup = "pod"
  conmon_env = [
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
  ]
  default_env = []
  selinux = false
  seccomp_profile = ""
  apparmor_profile = "crio-default"
  default_capabilities = [
    "CHOWN",
    "DAC_OVERRIDE",
    "FSETID",
    "FOWNER",
    "SETGID",
    "SETUID",
    "SETPCAP",
    "NET_BIND_SERVICE",
    "KILL",
  ]
  default_sysctls = []
  default_ulimits = []
  pids_limit = 1024
  log_size_max = 52428800
  log_to_journald = false
  container_exits_dir = "/var/run/crio/exits"
  container_attach_socket_dir = "/var/run/crio"
  ctr_stop_timeout = 30
  manage_ns_lifecycle = false
  read_only = false
  log_level = "info"

  # Cgroup manager
  cgroup_manager = "systemd"

  # Pause image
  pause_image = "registry.k8s.io/pause:3.9"
  pause_image_auth_file = ""
  pause_command = "/pause"

  # ==================== Runtimes ====================
  [crio.runtime.runtimes.runc]
    runtime_path = "/usr/bin/runc"
    runtime_type = "oci"
    runtime_root = "/run/runc"

# ==================== Image ====================
[crio.image]
  default_transport = "docker://"
  global_auth_file = ""
  pause_image = "registry.k8s.io/pause:3.9"
  pause_image_auth_file = ""
  pause_command = "/pause"
  signature_policy = ""
  insecure_registries = []
  registries = [
    "docker.io",
  ]

# ==================== Network ====================
[crio.network]
  network_dir = "/etc/cni/net.d/"
  plugin_dirs = [
    "/opt/cni/bin/",
  ]

# ==================== Metrics ====================
[crio.metrics]
  enable_metrics = true
  metrics_port = 9090
```

**Enable and start CRI-O:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable crio
sudo systemctl start crio
sudo systemctl status crio
```

## Container Runtime Interface (CRI)

### CRI API Operations

```protobuf
// Runtime service
service RuntimeService {
    // Sandbox operations (pod-level)
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
    rpc PodSandboxStatus(PodSandboxStatusRequest) returns (PodSandboxStatusResponse);
    rpc ListPodSandbox(ListPodSandboxRequest) returns (ListPodSandboxResponse);

    // Container operations
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
    rpc RemoveContainer(RemoveContainerRequest) returns (RemoveContainerResponse);
    rpc ListContainers(ListContainersRequest) returns (ListContainersResponse);
    rpc ContainerStatus(ContainerStatusRequest) returns (ContainerStatusResponse);
    rpc ContainerStats(ContainerStatsRequest) returns (ContainerStatsResponse);

    // Exec/Attach
    rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse);
    rpc Exec(ExecRequest) returns (ExecResponse);
    rpc Attach(AttachRequest) returns (AttachResponse);
}

// Image service
service ImageService {
    rpc ListImages(ListImagesRequest) returns (ListImagesResponse);
    rpc ImageStatus(ImageStatusRequest) returns (ImageStatusResponse);
    rpc PullImage(PullImageRequest) returns (PullImageResponse);
    rpc RemoveImage(RemoveImageRequest) returns (RemoveImageResponse);
    rpc ImageFsInfo(ImageFsInfoRequest) returns (ImageFsInfoResponse);
}
```

### Pod Creation Flow

```
1. kubelet decides to create pod
         ↓
2. kubelet → CRI: RunPodSandbox
   - Create network namespace
   - Start pause container (holds namespaces)
   - Call CNI to setup networking
         ↓
3. kubelet → CRI: CreateContainer (for each container)
   - Prepare container filesystem (from image layers)
   - Set up mounts, environment variables
   - Configure cgroups
         ↓
4. kubelet → CRI: StartContainer (for each container)
   - Start container process
   - Attach to pod network namespace
         ↓
5. Pod running
```

## Storage Drivers and Snapsh otters

### Overlay2 (Most Common)

```bash
# Check current storage driver
sudo crictl info | grep -i storage

# Overlay2 uses:
# - Lower layers (read-only image layers)
# - Upper layer (read-write container layer)
# - Merged layer (combined view)

# Example overlay mount:
/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/123/fs

# Performance:
# ✓ Fast
# ✓ Efficient disk usage (shared layers)
# ✓ Good for most workloads
```

### Btrfs

```bash
# Uses Btrfs filesystem features
# - Copy-on-write (CoW)
# - Snapshots
# - Subvolumes

# Pros:
# ✓ Very fast snapshots
# ✓ Good for databases

# Cons:
# ✗ Requires Btrfs filesystem
# ✗ Less widely used
```

### ZFS

```bash
# Uses ZFS filesystem
# - Similar to Btrfs
# - Enterprise-grade

# Pros:
# ✓ Excellent data integrity
# ✓ Compression
# ✓ Deduplication

# Cons:
# ✗ Requires ZFS filesystem
# ✗ Higher memory usage
```

## Real-World Use Cases

### Use Case 1: Multi-Tenant Cluster with gVisor

```yaml
# RuntimeClass for secure workloads
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
overhead:
  podFixed:
    cpu: 100m
    memory: 30Mi

---
# Pod using gVisor runtime
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  runtimeClassName: gvisor
  containers:
  - name: app
    image: untrusted-app:latest
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
```

**containerd config for gVisor:**

```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"

  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc.options]
    TypeUrl = "io.containerd.runsc.v1.options"
    ConfigPath = "/etc/containerd/runsc.toml"
```

### Use Case 2: GPU Workloads with NVIDIA Runtime

```yaml
# RuntimeClass for GPU
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: nvidia
handler: nvidia

---
# Pod with GPU
apiVersion: v1
kind: Pod
metadata:
  name: cuda-app
spec:
  runtimeClassName: nvidia
  containers:
  - name: cuda
    image: nvidia/cuda:11.8.0-base
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
```

**containerd config for NVIDIA:**

```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]
  runtime_type = "io.containerd.runc.v2"

  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]
    BinaryName = "/usr/bin/nvidia-container-runtime"
    SystemdCgroup = true
```

### Use Case 3: Private Registry with Authentication

```toml
# containerd registry config
[plugins."io.containerd.grpc.v1.cri".registry.configs."registry.company.com".auth]
  username = "deploy-user"
  password = "secret"
  # Or use auth file
  # auth_file = "/etc/containerd/registry-auth.json"

[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
  endpoint = ["https://registry.company.com", "https://registry-1.docker.io"]
```

**ImagePullSecret in Kubernetes:**

```bash
# Create docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.company.com \
  --docker-username=deploy-user \
  --docker-password=secret \
  --docker-email=deploy@company.com

# Use in pod
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  imagePullSecrets:
  - name: regcred
  containers:
  - name: app
    image: registry.company.com/private-app:v1
```

## Troubleshooting

### Common Issues

#### Issue 1: Container Fails to Start

```bash
# Check container logs
sudo crictl logs <container-id>

# Check container status
sudo crictl inspect <container-id> | jq .status

# Check containerd logs
sudo journalctl -u containerd -f

# Common causes:
# - Image pull failure
# - Insufficient resources
# - Volume mount errors
# - Network issues
```

#### Issue 2: Image Pull Errors

```bash
# Test image pull manually
sudo crictl pull nginx:latest

# Check registry configuration
sudo cat /etc/containerd/config.toml | grep -A 10 registry

# Test registry connectivity
curl -v https://registry-1.docker.io/v2/

# Check authentication
sudo cat /root/.docker/config.json

# Rate limiting (Docker Hub)
# Error: toomanyrequests: You have reached your pull rate limit
# Solution: Authenticate or use mirror registry
```

#### Issue 3: Disk Space Issues

```bash
# Check disk usage
df -h /var/lib/containerd

# List images
sudo crictl images

# Remove unused images
sudo crictl rmi --prune

# List containers
sudo crictl ps -a --state=exited

# Remove stopped containers
sudo crictl rm $(sudo crictl ps -a --state=exited -q)

# Configure garbage collection
# In containerd config.toml
[plugins."io.containerd.gc.v1.scheduler"]
  pause_threshold = 0.02
  deletion_threshold = 0
  mutation_threshold = 100
  schedule_delay = "0s"
  startup_delay = "100ms"
```

## Performance Tuning

```toml
# /etc/containerd/config.toml

# Increase concurrent downloads
[plugins."io.containerd.grpc.v1.cri"]
  max_concurrent_downloads = 10

# Tune snapshotter
[plugins."io.containerd.snapshotter.v1.overlayfs"]
  # Use faster mount options
  mount_options = ["noatime", "nodiratime"]

# Optimize grpc
[grpc]
  max_recv_message_size = 16777216
  max_send_message_size = 16777216

# Kernel parameters
# /etc/sysctl.conf
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 8192
```

## References

- [containerd Documentation](https://containerd.io/)
- [CRI-O Documentation](https://cri-o.io/)
- [Container Runtime Interface](https://kubernetes.io/docs/concepts/architecture/cri/)
- [crictl Documentation](https://github.com/kubernetes-sigs/cri-tools/blob/master/docs/crictl.md)
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)
