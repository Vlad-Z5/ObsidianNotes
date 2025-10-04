# etcd

## Overview

**etcd** is a distributed, consistent, and highly-available key-value store that serves as Kubernetes' primary datastore. Every piece of cluster state - pods, services, secrets, configurations - is stored in etcd. It's the single source of truth for the entire cluster.

**Component Type:** Control Plane (Database)
**Process Name:** `etcd`
**Default Ports:**
- 2379 (client connections - API server)
- 2380 (peer connections - etcd cluster members)
**Runs On:** Control plane nodes (can be stacked or external)
**Stateful:** Yes (critical data, requires backup)

## What etcd Actually Does

Think of etcd as the cluster's brain - a distributed database that stores all cluster state and configuration.

### Real-World Analogy
Imagine a bank's central ledger system:
- **Distributed:** Multiple copies across different locations
- **Consistent:** All copies show the same account balances
- **Highly Available:** If one location fails, others continue operating
- **Transactional:** Changes are atomic (all-or-nothing)
- **Historical:** Complete audit trail of all changes

### Why Kubernetes Needs etcd

```
Without etcd, Kubernetes has no memory:
- Which pods exist? Where are they?
- What's the desired state vs actual state?
- What secrets and configs exist?
- Who has what permissions (RBAC)?
- Service discovery information?

etcd stores ALL of this.
```

### What Gets Stored in etcd

```bash
# View all keys in etcd
ETCDCTL_API=3 etcdctl get / --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Common paths:
/registry/pods/default/nginx-pod
/registry/services/default/kubernetes
/registry/secrets/default/my-secret
/registry/deployments/default/nginx-deployment
/registry/configmaps/kube-system/coredns
/registry/namespaces/default
/registry/nodes/worker-1
/registry/serviceaccounts/default/default
/registry/clusterrolebindings/cluster-admin
```

### How Kubernetes Uses etcd

```
1. kubectl create pod nginx
2. kubectl → API Server → Validates request
3. API Server → etcd: Write pod spec to /registry/pods/default/nginx
4. etcd → Confirms write (via Raft consensus)
5. API Server → Notifies watchers (scheduler, controllers)
6. Scheduler → API Server → Update pod with node assignment
7. API Server → etcd: Update /registry/pods/default/nginx (add nodeName)
8. Kubelet (watches etcd via API server) → Sees pod assigned to its node
9. Kubelet → Starts container
10. Kubelet → API Server → Update pod status
11. API Server → etcd: Update pod status
```

## Architecture

### Raft Consensus Algorithm

etcd uses Raft to ensure consistency across cluster members.

```
┌─────────────────────────────────────────────────────────┐
│                    etcd Cluster (3 nodes)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐        │
│  │ Leader  │◄────►│ Follower│◄────►│ Follower│        │
│  │ etcd-1  │      │ etcd-2  │      │ etcd-3  │        │
│  └────▲────┘      └─────────┘      └─────────┘        │
│       │                                                  │
│       │ All writes go to leader                        │
│       │ Leader replicates to followers                 │
│       │ Majority (quorum) must acknowledge             │
│       │                                                  │
└───────┼──────────────────────────────────────────────────┘
        │
        │ Client connections (kube-apiserver)
        │
┌───────▼──────────────────────────────────────────────────┐
│  kube-apiserver (reads/writes via 2379)                  │
└───────────────────────────────────────────────────────────┘
```

**Raft Leader Election:**
1. All nodes start as followers
2. If no heartbeat from leader, follower becomes candidate
3. Candidate requests votes from other nodes
4. Node with majority votes becomes leader
5. Leader sends heartbeats to maintain authority

**Quorum Requirements:**
```
Cluster Size    Quorum  Fault Tolerance
1               1       0 (no HA)
3               2       1 node can fail
5               3       2 nodes can fail
7               4       3 nodes can fail
```

**Why odd numbers?**
- 3 nodes: Can tolerate 1 failure (need 2/3)
- 4 nodes: Can tolerate 1 failure (need 3/4) - wastes a node
- 5 nodes: Can tolerate 2 failures (need 3/5)

### Deployment Topologies

#### 1. Stacked etcd (Co-located with control plane)

```
┌─────────────────────────────────────────────────────────┐
│              Control Plane Node 1                        │
├─────────────────────────────────────────────────────────┤
│  kube-apiserver                                          │
│  kube-scheduler                                          │
│  kube-controller-manager                                 │
│  etcd  ◄──────────────────────────┐                     │
└────────────────────────────────────┼─────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────┐
│              Control Plane Node 2  │                     │
├────────────────────────────────────┼─────────────────────┤
│  kube-apiserver                    │                     │
│  kube-scheduler                    │                     │
│  kube-controller-manager           │                     │
│  etcd  ◄───────────────────────────┼─────────────────┐  │
└────────────────────────────────────┼─────────────────┼───┘
                                     │                 │
┌────────────────────────────────────┼─────────────────┼───┐
│              Control Plane Node 3  │                 │   │
├────────────────────────────────────┼─────────────────┼───┤
│  kube-apiserver                    │                 │   │
│  kube-scheduler                    │                 │   │
│  kube-controller-manager           │                 │   │
│  etcd  ◄───────────────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- Simpler setup (fewer nodes)
- Lower cost (3 nodes instead of 6)
- Easier to manage

**Cons:**
- Losing control plane node = losing etcd member
- Mixed workload (API server and etcd compete for resources)

#### 2. External etcd (Separate cluster)

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Control Plane 1 │  │ Control Plane 2 │  │ Control Plane 3 │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ kube-apiserver  │  │ kube-apiserver  │  │ kube-apiserver  │
│ kube-scheduler  │  │ kube-scheduler  │  │ kube-scheduler  │
│ controller-mgr  │  │ controller-mgr  │  │ controller-mgr  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   etcd Node 1   │  │   etcd Node 2   │  │   etcd Node 3   │
│   (dedicated)   │◄─┤   (dedicated)   │◄─┤   (dedicated)   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Pros:**
- Better isolation (etcd not affected by API server load)
- Independent scaling (scale etcd separately)
- Better fault tolerance (losing control plane ≠ losing etcd)

**Cons:**
- More complex setup (6 nodes instead of 3)
- Higher cost
- More components to manage

## Installation and Configuration

### Static Pod Manifest (Stacked etcd)

```yaml
# /etc/kubernetes/manifests/etcd.yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubeadm.kubernetes.io/etcd.advertise-client-urls: https://10.0.0.10:2379
  labels:
    component: etcd
    tier: control-plane
  name: etcd
  namespace: kube-system
spec:
  containers:
  - command:
    - etcd

    # ==================== Cluster Configuration ====================
    # Node name (unique per member)
    - --name=etcd-1

    # Data directory (persistent storage)
    - --data-dir=/var/lib/etcd

    # Client URLs (API server connects here)
    - --listen-client-urls=https://127.0.0.1:2379,https://10.0.0.10:2379
    - --advertise-client-urls=https://10.0.0.10:2379

    # Peer URLs (etcd members communicate here)
    - --listen-peer-urls=https://10.0.0.10:2380
    - --initial-advertise-peer-urls=https://10.0.0.10:2380

    # Initial cluster configuration (all members)
    - --initial-cluster=etcd-1=https://10.0.0.10:2380,etcd-2=https://10.0.0.11:2380,etcd-3=https://10.0.0.12:2380

    # Initial cluster state (new or existing)
    - --initial-cluster-state=new

    # Cluster token (must be same for all members)
    - --initial-cluster-token=etcd-cluster-1

    # ==================== TLS Configuration ====================
    # Client TLS (API server ← → etcd)
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --client-cert-auth=true

    # Peer TLS (etcd ← → etcd)
    - --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
    - --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
    - --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --peer-client-cert-auth=true

    # ==================== Performance Tuning ====================
    # Snapshot settings (write to disk periodically)
    - --snapshot-count=10000

    # Heartbeat interval (default: 100ms)
    - --heartbeat-interval=100

    # Election timeout (default: 1000ms)
    - --election-timeout=1000

    # Backend database size quota (default: 2GB)
    - --quota-backend-bytes=8589934592  # 8GB for large clusters

    # Auto compaction (keep history for 1 hour)
    - --auto-compaction-mode=periodic
    - --auto-compaction-retention=1h

    # ==================== Logging & Metrics ====================
    # Log level (debug, info, warn, error, panic, fatal)
    - --log-level=info

    # Log outputs
    - --log-outputs=stderr

    # Metrics (Prometheus format)
    - --listen-metrics-urls=http://127.0.0.1:2381

    # ==================== Limits & Timeouts ====================
    # Max request size (default: 1.5MB)
    - --max-request-bytes=1572864

    # Max snapshot files to retain
    - --max-snapshots=5

    # Max WAL files to retain
    - --max-wals=5

    # gRPC max concurrent streams
    - --max-concurrent-streams=4294967295

    image: registry.k8s.io/etcd:3.5.9-0
    imagePullPolicy: IfNotPresent

    # ==================== Health Probes ====================
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 127.0.0.1
        path: /health?serializable=true
        port: 2381
        scheme: HTTP
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 127.0.0.1
        path: /health?serializable=true
        port: 2381
        scheme: HTTP
      periodSeconds: 1
      timeoutSeconds: 15

    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 127.0.0.1
        path: /health?serializable=true
        port: 2381
        scheme: HTTP
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    name: etcd

    # ==================== Resource Limits ====================
    resources:
      requests:
        cpu: 100m
        memory: 512Mi
      limits:
        # No CPU limit (avoid throttling)
        memory: 2Gi

    # ==================== Volume Mounts ====================
    volumeMounts:
    - mountPath: /var/lib/etcd
      name: etcd-data
    - mountPath: /etc/kubernetes/pki/etcd
      name: etcd-certs
      readOnly: true

  hostNetwork: true
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault

  # ==================== Volumes ====================
  volumes:
  - hostPath:
      path: /var/lib/etcd
      type: DirectoryOrCreate
    name: etcd-data
  - hostPath:
      path: /etc/kubernetes/pki/etcd
      type: DirectoryOrCreate
    name: etcd-certs
```

### External etcd Cluster Setup

```bash
# ==================== On etcd Node 1 (10.0.0.20) ====================

# 1. Download etcd
ETCD_VER=v3.5.9
wget https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz
tar xzvf etcd-${ETCD_VER}-linux-amd64.tar.gz
sudo mv etcd-${ETCD_VER}-linux-amd64/etcd* /usr/local/bin/

# 2. Create etcd user
sudo useradd -r -s /bin/false etcd

# 3. Create directories
sudo mkdir -p /var/lib/etcd /etc/etcd
sudo chown -R etcd:etcd /var/lib/etcd
sudo chmod 700 /var/lib/etcd

# 4. Copy certificates
sudo cp ca.crt etcd-server.crt etcd-server.key /etc/etcd/
sudo cp etcd-peer.crt etcd-peer.key /etc/etcd/
sudo chown -R etcd:etcd /etc/etcd
sudo chmod 600 /etc/etcd/*.key

# 5. Create systemd service
cat <<EOF | sudo tee /etc/systemd/system/etcd.service
[Unit]
Description=etcd key-value store
Documentation=https://github.com/etcd-io/etcd
After=network.target

[Service]
Type=notify
User=etcd
ExecStart=/usr/local/bin/etcd \\
  --name=etcd-1 \\
  --data-dir=/var/lib/etcd \\
  --listen-client-urls=https://10.0.0.20:2379,https://127.0.0.1:2379 \\
  --advertise-client-urls=https://10.0.0.20:2379 \\
  --listen-peer-urls=https://10.0.0.20:2380 \\
  --initial-advertise-peer-urls=https://10.0.0.20:2380 \\
  --initial-cluster=etcd-1=https://10.0.0.20:2380,etcd-2=https://10.0.0.21:2380,etcd-3=https://10.0.0.22:2380 \\
  --initial-cluster-state=new \\
  --initial-cluster-token=etcd-cluster \\
  --cert-file=/etc/etcd/etcd-server.crt \\
  --key-file=/etc/etcd/etcd-server.key \\
  --trusted-ca-file=/etc/etcd/ca.crt \\
  --client-cert-auth=true \\
  --peer-cert-file=/etc/etcd/etcd-peer.crt \\
  --peer-key-file=/etc/etcd/etcd-peer.key \\
  --peer-trusted-ca-file=/etc/etcd/ca.crt \\
  --peer-client-cert-auth=true \\
  --snapshot-count=10000 \\
  --quota-backend-bytes=8589934592 \\
  --auto-compaction-mode=periodic \\
  --auto-compaction-retention=1h \\
  --log-level=info

Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 6. Start etcd
sudo systemctl daemon-reload
sudo systemctl enable etcd
sudo systemctl start etcd

# 7. Verify
sudo systemctl status etcd
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/etcd/ca.crt \
  --cert=/etc/etcd/etcd-server.crt \
  --key=/etc/etcd/etcd-server.key

# Repeat for etcd-2 and etcd-3 with appropriate IP addresses
```

### kubeadm HA Setup with External etcd

```bash
# 1. Setup external etcd cluster first (3 nodes)

# 2. Initialize first control plane node
sudo kubeadm init \
  --control-plane-endpoint="10.0.0.100:6443" \
  --upload-certs \
  --external-etcd-endpoints=https://10.0.0.20:2379,https://10.0.0.21:2379,https://10.0.0.22:2379 \
  --external-etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt \
  --external-etcd-certfile=/etc/kubernetes/pki/etcd/server.crt \
  --external-etcd-keyfile=/etc/kubernetes/pki/etcd/server.key

# 3. Join additional control plane nodes
sudo kubeadm join 10.0.0.100:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash> \
  --control-plane \
  --certificate-key <cert-key>
```

## Backup and Restore

### Backup etcd (Critical Operation)

```bash
# ==================== Snapshot Backup ====================

# Basic snapshot
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify snapshot
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-snapshot-*.db --write-out=table

# Output:
# +----------+----------+------------+------------+
# |   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
# +----------+----------+------------+------------+
# | 8e6c6f8f |   123456 |       1234 |     5.2 MB |
# +----------+----------+------------+------------+

# ==================== Automated Backup Script ====================

cat > /usr/local/bin/backup-etcd.sh <<'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR=/backup/etcd
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_FILE="${BACKUP_DIR}/etcd-snapshot-${TIMESTAMP}.db"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Create snapshot
ETCDCTL_API=3 etcdctl snapshot save ${SNAPSHOT_FILE} \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify snapshot
ETCDCTL_API=3 etcdctl snapshot status ${SNAPSHOT_FILE} --write-out=table

# Compress snapshot
gzip ${SNAPSHOT_FILE}

# Delete old backups
find ${BACKUP_DIR} -name "etcd-snapshot-*.db.gz" -mtime +${RETENTION_DAYS} -delete

# Upload to S3 (optional)
# aws s3 cp ${SNAPSHOT_FILE}.gz s3://my-bucket/etcd-backups/

echo "Backup completed: ${SNAPSHOT_FILE}.gz"
EOF

chmod +x /usr/local/bin/backup-etcd.sh

# ==================== Cron Job (Daily at 2 AM) ====================

cat > /etc/cron.d/backup-etcd <<EOF
0 2 * * * root /usr/local/bin/backup-etcd.sh >> /var/log/etcd-backup.log 2>&1
EOF

# ==================== Kubernetes CronJob for Backup ====================

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etcd-backup
  namespace: kube-system
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: etcd-backup
            image: registry.k8s.io/etcd:3.5.9-0
            command:
            - /bin/sh
            - -c
            - |
              ETCDCTL_API=3 etcdctl snapshot save /backup/snapshot-\$(date +%Y%m%d-%H%M%S).db \\
                --endpoints=https://127.0.0.1:2379 \\
                --cacert=/etc/kubernetes/pki/etcd/ca.crt \\
                --cert=/etc/kubernetes/pki/etcd/server.crt \\
                --key=/etc/kubernetes/pki/etcd/server.key

              # Clean old backups
              find /backup -name "snapshot-*.db" -mtime +7 -delete
            volumeMounts:
            - name: etcd-certs
              mountPath: /etc/kubernetes/pki/etcd
              readOnly: true
            - name: backup
              mountPath: /backup
          restartPolicy: OnFailure
          hostNetwork: true
          volumes:
          - name: etcd-certs
            hostPath:
              path: /etc/kubernetes/pki/etcd
          - name: backup
            hostPath:
              path: /var/backups/etcd
EOF
```

### Restore from Backup

```bash
# ==================== Complete Cluster Restore ====================

# SCENARIO: Complete cluster failure, restore from backup

# 1. Stop all control plane components
sudo mv /etc/kubernetes/manifests/*.yaml /tmp/

# 2. Verify etcd is stopped
ps aux | grep etcd

# 3. Restore snapshot (on each etcd node)
# Node 1:
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-20231015.db \
  --name=etcd-1 \
  --initial-cluster=etcd-1=https://10.0.0.10:2380,etcd-2=https://10.0.0.11:2380,etcd-3=https://10.0.0.12:2380 \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://10.0.0.10:2380 \
  --data-dir=/var/lib/etcd-restore

# Node 2:
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-20231015.db \
  --name=etcd-2 \
  --initial-cluster=etcd-1=https://10.0.0.10:2380,etcd-2=https://10.0.0.11:2380,etcd-3=https://10.0.0.12:2380 \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://10.0.0.11:2380 \
  --data-dir=/var/lib/etcd-restore

# Node 3:
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-20231015.db \
  --name=etcd-3 \
  --initial-cluster=etcd-1=https://10.0.0.10:2380,etcd-2=https://10.0.0.11:2380,etcd-3=https://10.0.0.12:2380 \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://10.0.0.12:2380 \
  --data-dir=/var/lib/etcd-restore

# 4. Update etcd manifest to use new data directory (on all nodes)
sudo sed -i 's|/var/lib/etcd|/var/lib/etcd-restore|g' /tmp/etcd.yaml
sudo sed -i 's|--initial-cluster-state=new|--initial-cluster-state=existing|g' /tmp/etcd.yaml

# 5. Set permissions
sudo chown -R etcd:etcd /var/lib/etcd-restore

# 6. Start etcd (on all nodes)
sudo mv /tmp/etcd.yaml /etc/kubernetes/manifests/

# 7. Wait for etcd cluster to form
sleep 30
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 8. Start control plane components
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
sudo mv /tmp/kube-controller-manager.yaml /etc/kubernetes/manifests/
sudo mv /tmp/kube-scheduler.yaml /etc/kubernetes/manifests/

# 9. Verify cluster
kubectl get nodes
kubectl get pods --all-namespaces

# 10. Clean up old data (after verification)
sudo rm -rf /var/lib/etcd
sudo mv /var/lib/etcd-restore /var/lib/etcd
# Update manifest back to /var/lib/etcd
```

### Disaster Recovery Scenarios

#### Scenario 1: Single etcd Member Failed

```bash
# 1. Check cluster health
ETCDCTL_API=3 etcdctl endpoint health --cluster \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Output:
# https://10.0.0.10:2379 is healthy
# https://10.0.0.11:2379 is healthy
# https://10.0.0.12:2379 is unhealthy (FAILED)

# 2. Remove failed member
ETCDCTL_API=3 etcdctl member remove <member-id> \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 3. Clean up failed node
ssh 10.0.0.12
sudo rm -rf /var/lib/etcd/*

# 4. Add member back
ETCDCTL_API=3 etcdctl member add etcd-3 \
  --peer-urls=https://10.0.0.12:2380 \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 5. Update etcd manifest on node 3
# Change: --initial-cluster-state=new
# To: --initial-cluster-state=existing

# 6. Start etcd on node 3
sudo mv /etc/kubernetes/manifests/etcd.yaml /tmp/
sudo mv /tmp/etcd.yaml /etc/kubernetes/manifests/

# 7. Verify member rejoined
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

#### Scenario 2: Lost Quorum (2 out of 3 nodes failed)

```bash
# CRITICAL: Cannot recover without backup
# Must restore from snapshot

# Follow "Complete Cluster Restore" procedure above
```

## Maintenance Operations

### Defragmentation

```bash
# etcd database can become fragmented over time
# Defragmentation reclaims disk space

# Check database size
ETCDCTL_API=3 etcdctl endpoint status --cluster -w table \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Defragment each member (one at a time)
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Wait 5 minutes, then defrag next node
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://10.0.0.11:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Defrag all at once (more disruptive)
ETCDCTL_API=3 etcdctl defrag --cluster \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Automated defragmentation script
cat > /usr/local/bin/defrag-etcd.sh <<'EOF'
#!/bin/bash
ENDPOINTS="https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379"

for endpoint in $(echo $ENDPOINTS | tr ',' ' '); do
  echo "Defragmenting $endpoint..."
  ETCDCTL_API=3 etcdctl defrag \
    --endpoints=$endpoint \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key
  sleep 300  # Wait 5 minutes between nodes
done
EOF

chmod +x /usr/local/bin/defrag-etcd.sh

# Schedule monthly defragmentation
echo "0 3 1 * * root /usr/local/bin/defrag-etcd.sh" > /etc/cron.d/etcd-defrag
```

### Compaction

```bash
# etcd keeps historical revisions for watch functionality
# Compaction removes old revisions to save space

# Check current revision
ETCDCTL_API=3 etcdctl endpoint status -w table \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Manual compaction (compact everything before revision 1000000)
ETCDCTL_API=3 etcdctl compact 1000000 \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Automatic compaction (already configured in manifest)
# --auto-compaction-mode=periodic
# --auto-compaction-retention=1h  # Keep 1 hour of history
```

### Alarm Management

```bash
# Check for alarms
ETCDCTL_API=3 etcdctl alarm list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Common alarm: NOSPACE (database size exceeded quota)

# 1. Check database size
ETCDCTL_API=3 etcdctl endpoint status -w table \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 2. Get current revision
rev=$(ETCDCTL_API=3 etcdctl endpoint status \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  -w json | jq -r '.[0].Status.header.revision')

# 3. Compact old revisions
ETCDCTL_API=3 etcdctl compact $rev \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 4. Defragment
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 5. Disarm alarm
ETCDCTL_API=3 etcdctl alarm disarm \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 6. Increase quota (if needed)
# Edit etcd manifest:
# --quota-backend-bytes=16106127360  # 15GB
```

## Upgrading etcd

### Pre-Upgrade Checklist

```bash
# 1. Check current version
ETCDCTL_API=3 etcdctl version

# 2. Review release notes
# https://github.com/etcd-io/etcd/releases

# 3. BACKUP FIRST (critical!)
ETCDCTL_API=3 etcdctl snapshot save /backup/pre-upgrade-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 4. Check cluster health
ETCDCTL_API=3 etcdctl endpoint health --cluster \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 5. Verify all members are synced
ETCDCTL_API=3 etcdctl member list -w table \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### Upgrade Process (Rolling Upgrade)

```bash
# ==================== Upgrade Node 1 ====================

# 1. Backup configuration
sudo cp /etc/kubernetes/manifests/etcd.yaml /backup/etcd-manifest-node1.yaml

# 2. Edit manifest, update image version
sudo vi /etc/kubernetes/manifests/etcd.yaml
# Change: image: registry.k8s.io/etcd:3.5.9-0
# To: image: registry.k8s.io/etcd:3.5.10-0

# 3. Kubelet automatically restarts pod with new version
# Watch the process
kubectl get pods -n kube-system -w | grep etcd

# 4. Verify new version
ETCDCTL_API=3 etcdctl version

# 5. Check cluster health
ETCDCTL_API=3 etcdctl endpoint health --cluster \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# ==================== Wait 10-15 Minutes ====================
# Ensure stability before proceeding

# ==================== Upgrade Node 2 ====================
# Repeat same process on node 2

# ==================== Wait 10-15 Minutes ====================

# ==================== Upgrade Node 3 ====================
# Repeat same process on node 3

# ==================== Final Verification ====================

# Verify all nodes upgraded
ETCDCTL_API=3 etcdctl member list -w table \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Test cluster operations
kubectl get nodes
kubectl get pods --all-namespaces
```

## Monitoring and Metrics

### Prometheus Integration

```yaml
# ServiceMonitor for etcd
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: etcd
  namespace: kube-system
spec:
  jobLabel: component
  selector:
    matchLabels:
      component: etcd
  namespaceSelector:
    matchNames:
    - kube-system
  endpoints:
  - port: metrics
    interval: 30s
    scheme: https
    tlsConfig:
      caFile: /etc/prometheus/secrets/etcd-certs/ca.crt
      certFile: /etc/prometheus/secrets/etcd-certs/client.crt
      keyFile: /etc/prometheus/secrets/etcd-certs/client.key
      insecureSkipVerify: false
```

### Key Metrics to Monitor

```promql
# Cluster health
up{job="etcd"}

# Has leader
etcd_server_has_leader

# Leader changes (should be stable)
rate(etcd_server_leader_changes_seen_total[5m])

# Disk backend commit duration (should be < 25ms)
histogram_quantile(0.99, rate(etcd_disk_backend_commit_duration_seconds_bucket[5m]))

# Database size
etcd_mvcc_db_total_size_in_bytes

# RPC rate
rate(grpc_server_handled_total{job="etcd"}[5m])

# RPC latency
histogram_quantile(0.99, rate(grpc_server_handling_seconds_bucket{job="etcd"}[5m]))

# Network latency (peer communication)
histogram_quantile(0.99, rate(etcd_network_peer_round_trip_time_seconds_bucket[5m]))

# Slow operations
rate(etcd_server_slow_apply_total[5m])
rate(etcd_server_slow_read_indexes_total[5m])

# Failed proposals
rate(etcd_server_proposals_failed_total[5m])

# Snapshot save duration
histogram_quantile(0.99, rate(etcd_snapshot_save_total_duration_seconds_bucket[5m]))
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "etcd Cluster Monitoring",
    "panels": [
      {
        "title": "Cluster Health",
        "targets": [{
          "expr": "up{job=\"etcd\"}"
        }]
      },
      {
        "title": "DB Size",
        "targets": [{
          "expr": "etcd_mvcc_db_total_size_in_bytes"
        }]
      },
      {
        "title": "Disk Sync Duration (P99)",
        "targets": [{
          "expr": "histogram_quantile(0.99, rate(etcd_disk_wal_fsync_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Leader Changes",
        "targets": [{
          "expr": "rate(etcd_server_leader_changes_seen_total[5m])"
        }]
      }
    ]
  }
}
```

## Troubleshooting

### etcd Won't Start

```bash
# 1. Check kubelet logs
sudo journalctl -u kubelet -f | grep etcd

# 2. Check container logs
sudo crictl ps -a | grep etcd
sudo crictl logs <container-id>

# 3. Common issues:

# Issue: Data directory corruption
# Solution: Restore from backup

# Issue: Certificate errors
# Solution: Verify certificates
sudo ls -l /etc/kubernetes/pki/etcd/
openssl x509 -in /etc/kubernetes/pki/etcd/server.crt -text -noout

# Issue: Port already in use
sudo netstat -tulpn | grep 2379
sudo netstat -tulpn | grep 2380

# Issue: Disk full
df -h /var/lib/etcd

# Issue: Wrong initial-cluster-state
# If adding to existing cluster, must use: --initial-cluster-state=existing
```

### Split Brain / Multiple Leaders

```bash
# Symptoms: Multiple leaders elected

# 1. Check network connectivity between members
ping 10.0.0.11
ping 10.0.0.12

# 2. Check for network partition
ETCDCTL_API=3 etcdctl member list -w table \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 3. Check firewall rules
sudo iptables -L -n | grep 2380
sudo firewall-cmd --list-ports

# 4. Resolution: Force new election
# Stop etcd on all nodes except one
# Let single node become leader
# Restart other nodes one by one
```

### Performance Issues

```bash
# 1. Check disk I/O latency (most common issue)
ETCDCTL_API=3 etcdctl check perf \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Healthy output:
# 60 / 60 Boooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooom !
# PASS: Throughput is 150 writes/s
# PASS: Slowest request took 0.015s
# PASS: Stddev is 0.001s

# Unhealthy (slow disk):
# FAIL: Slowest request took 0.156s (should be < 0.1s)

# 2. Check database size
ETCDCTL_API=3 etcdctl endpoint status -w table \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 3. If database too large, compact and defragment
# (See Maintenance Operations section)

# 4. Check for slow apply operations
kubectl get --raw /metrics | grep etcd_server_slow_apply_total

# 5. Solutions:
# - Use faster disks (SSD recommended, NVMe better)
# - Increase --quota-backend-bytes
# - Enable auto-compaction
# - Regular defragmentation
# - Separate etcd from API server (external etcd)
```

### Lost Quorum

```bash
# CRITICAL: Cannot write to cluster without quorum

# Example: 3-node cluster, 2 nodes failed

# 1. Check cluster status
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://10.0.0.10:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 2. If quorum lost, MUST restore from backup
# (See Restore from Backup section)

# PREVENTION:
# - Always maintain odd number of members (3, 5, 7)
# - Monitor etcd health continuously
# - Automated backups (hourly/daily)
# - Test restore procedure regularly
```

## Security Best Practices

```bash
# 1. Enable client certificate authentication
--client-cert-auth=true
--trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt

# 2. Enable peer certificate authentication
--peer-client-cert-auth=true
--peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt

# 3. Disable HTTP (use HTTPS only)
# Don't use --listen-client-urls=http://...

# 4. Restrict network access (firewall)
sudo iptables -A INPUT -p tcp --dport 2379 -s 10.0.0.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2379 -j DROP
sudo iptables -A INPUT -p tcp --dport 2380 -s 10.0.0.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2380 -j DROP

# 5. Regular backups
# (See Backup section)

# 6. Encrypt data at rest (API server feature)
# --encryption-provider-config in kube-apiserver

# 7. RBAC for etcd access (via API server)
# Don't allow direct etcd access to users

# 8. Monitor and alert
# Alert on: leader changes, slow operations, disk space

# 9. Use dedicated disks for etcd
# Isolate etcd I/O from other workloads

# 10. Regular certificate rotation
kubeadm certs check-expiration
kubeadm certs renew etcd-server
kubeadm certs renew etcd-peer
```

## Quick Reference Commands

```bash
# Member list
ETCDCTL_API=3 etcdctl member list -w table \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Cluster health
ETCDCTL_API=3 etcdctl endpoint health --cluster \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Cluster status
ETCDCTL_API=3 etcdctl endpoint status --cluster -w table \
  --endpoints=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Backup
ETCDCTL_API=3 etcdctl snapshot save /backup/snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Restore
ETCDCTL_API=3 etcdctl snapshot restore /backup/snapshot.db \
  --name=etcd-1 \
  --initial-cluster=etcd-1=https://10.0.0.10:2380 \
  --initial-advertise-peer-urls=https://10.0.0.10:2380 \
  --data-dir=/var/lib/etcd-restore

# Get specific key
ETCDCTL_API=3 etcdctl get /registry/pods/default/nginx --prefix \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# List all keys
ETCDCTL_API=3 etcdctl get / --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Defragment
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Compact
ETCDCTL_API=3 etcdctl compact <revision> \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Check performance
ETCDCTL_API=3 etcdctl check perf \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Alarm list
ETCDCTL_API=3 etcdctl alarm list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

## References

- [Official etcd Documentation](https://etcd.io/docs/)
- [etcd Operations Guide](https://etcd.io/docs/v3.5/op-guide/)
- [Kubernetes etcd Documentation](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [etcd Performance Benchmarking](https://etcd.io/docs/v3.5/op-guide/performance/)
