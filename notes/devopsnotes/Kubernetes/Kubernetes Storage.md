# Kubernetes Storage

**Kubernetes Storage** provides persistent data management for stateful applications through persistent volumes, storage classes, and CSI drivers, enabling data persistence across pod lifecycles and supporting various storage backends across cloud providers.


## Core Storage Concepts

### Storage Architecture

Kubernetes storage consists of three main components:
- **Volumes**: Provide data persistence for containers
- **Persistent Volumes (PV)**: Cluster-wide storage resources
- **Persistent Volume Claims (PVC)**: User requests for storage
- **Storage Classes**: Dynamic provisioning templates

### Storage Access Modes

- **ReadWriteOnce (RWO)**: Volume can be mounted read-write by a single node
- **ReadOnlyMany (ROX)**: Volume can be mounted read-only by many nodes
- **ReadWriteMany (RWX)**: Volume can be mounted read-write by many nodes
- **ReadWriteOncePod (RWOP)**: Volume can be mounted read-write by a single pod

---

## Persistent Volumes & Claims

### Static Provisioning

**Local Persistent Volume:**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv
  labels:
    type: local
    tier: database
spec:
  capacity:
    storage: 50Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  local:
    path: /mnt/disks/mysql
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-1
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: database
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: manual
  selector:
    matchLabels:
      type: local
      tier: database
```

### Dynamic Provisioning

**Production PVC with Resource Management:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-pvc
  namespace: production
  labels:
    app: web-application
    tier: storage
  annotations:
    volume.beta.kubernetes.io/storage-provisioner: ebs.csi.aws.com
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
    limits:
      storage: 500Gi
  storageClassName: fast-ebs-encrypted
```

### Volume Binding Modes

```yaml
# Immediate binding - provisions immediately
volumeBindingMode: Immediate

# WaitForFirstConsumer - waits for pod creation
volumeBindingMode: WaitForFirstConsumer
```

---

## Storage Classes

### AWS EBS Storage Classes

```yaml
# High-performance encrypted EBS storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs-encrypted
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
---
# High IOPS for databases
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: database-storage
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "10000"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

### Azure Disk Storage Classes

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium-ssd
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: managed
  cachingmode: ReadOnly
  diskEncryptionSetID: "/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Compute/diskEncryptionSets/{des-name}"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
---
# Azure File for shared storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-file-premium
provisioner: file.csi.azure.com
parameters:
  storageAccount: premiumstorageaccount
  resourceGroup: myResourceGroup
  shareName: myshare
  protocol: nfs
  skuName: Premium_LRS
volumeBindingMode: Immediate
allowVolumeExpansion: true
mountOptions:
  - dir_mode=0755
  - file_mode=0644
  - uid=0
  - gid=0
  - mfsymlinks
  - cache=strict
```

### GCP Persistent Disk Storage Classes

```yaml
# High-performance SSD storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd-regional
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  zones: us-central1-a,us-central1-b,us-central1-c
  disk-encryption-key: projects/PROJECT_ID/locations/LOCATION/keyRings/RING_ID/cryptoKeys/KEY_ID
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
---
# Balanced performance and cost
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: balanced-persistent-disk
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-balanced
  zones: us-central1-a,us-central1-b
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## CSI Drivers

### AWS EBS CSI Driver

**Installation and Configuration:**

```bash
# Install EBS CSI driver via Helm
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update

helm install aws-ebs-csi-driver aws-ebs-csi-driver/aws-ebs-csi-driver \
  --namespace kube-system \
  --set image.repository=602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-ebs-csi-driver \
  --set controller.serviceAccount.create=true \
  --set controller.serviceAccount.name=ebs-csi-controller-sa \
  --set controller.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="arn:aws:iam::ACCOUNT_ID:role/AmazonEKS_EBS_CSI_DriverRole"
```

**Volume Snapshots:**

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Delete
parameters:
  tags: |
    Environment: production
    Team: platform
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-snapshot-$(date +%Y%m%d)
  namespace: database
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: mysql-pvc
---
# Restore from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-restored-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: mysql-snapshot-20240101
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  storageClassName: fast-ebs-encrypted
```

### Azure Disk CSI Driver

**Installation:**

```bash
# Install Azure Disk CSI driver
helm repo add azuredisk-csi-driver https://raw.githubusercontent.com/kubernetes-sigs/azuredisk-csi-driver/master/charts
helm install azuredisk-csi-driver azuredisk-csi-driver/azuredisk-csi-driver \
  --namespace kube-system \
  --set controller.replicas=2
```

### GCP Persistent Disk CSI Driver

**Regional Persistent Disk:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: regional-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
  zones: us-central1-a,us-central1-b
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## Volume Types

### EmptyDir Volumes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cache-app
  template:
    metadata:
      labels:
        app: cache-app
    spec:
      containers:
      - name: app
        image: nginx:1.21
        volumeMounts:
        - name: cache-volume
          mountPath: /tmp/cache
        - name: shared-data
          mountPath: /shared
      - name: sidecar
        image: busybox:latest
        command: ['sh', '-c', 'while true; do date > /shared/timestamp; sleep 30; done']
        volumeMounts:
        - name: shared-data
          mountPath: /shared
      volumes:
      - name: cache-volume
        emptyDir:
          sizeLimit: 1Gi
          medium: Memory  # Use tmpfs for in-memory storage
      - name: shared-data
        emptyDir: {}
```

### ConfigMap and Secret Volumes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
spec:
  containers:
  - name: app
    image: nginx:1.21
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      defaultMode: 0644
      items:
      - key: nginx.conf
        path: nginx.conf
        mode: 0644
  - name: secret-volume
    secret:
      secretName: app-secrets
      defaultMode: 0400
      items:
      - key: database-password
        path: db-password
```

### HostPath Volumes (Use with Caution)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: collector
        image: fluentd:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: dockerlogs
          mountPath: /var/lib/docker/containers
          readOnly: true
        securityContext:
          runAsUser: 0
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
          type: Directory
      - name: dockerlogs
        hostPath:
          path: /var/lib/docker/containers
          type: Directory
      tolerations:
      - operator: Exists
```

---

## Storage Performance

### Performance Optimization

**High-Performance Database Configuration:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: admin
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: database-storage  # High IOPS storage class
      resources:
        requests:
          storage: 500Gi
```

### Storage Monitoring

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: storage-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'kubelet'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:10255'
        target_label: __address__
    - job_name: 'csi-driver'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: ebs-csi-.*
```

---

## Backup & Recovery

### Velero Backup Configuration

```yaml
# Velero backup for persistent volumes
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: daily-database-backup
  namespace: velero
spec:
  includedNamespaces:
  - database
  - application
  includedResources:
  - persistentvolumeclaims
  - persistentvolumes
  - secrets
  - configmaps
  labelSelector:
    matchLabels:
      backup: "enabled"
  snapshotVolumes: true
  storageLocation: aws-s3
  ttl: 720h0m0s  # 30 days
  hooks:
    resources:
    - name: database-backup-hook
      includedNamespaces:
      - database
      labelSelector:
        matchLabels:
          app: postgres
      pre:
      - exec:
          container: postgres
          command:
          - /bin/bash
          - -c
          - "pg_dump mydb > /tmp/backup.sql"
          onError: Fail
          timeout: 10m
---
# Scheduled backup
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  template:
    includedNamespaces:
    - production
    - database
    snapshotVolumes: true
    storageLocation: aws-s3
    ttl: 720h0m0s
```

### Volume Cloning

```yaml
# Clone existing PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cloned-mysql-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: mysql-pvc
    kind: PersistentVolumeClaim
  storageClassName: fast-ebs-encrypted
```

---

## Production Best Practices

### Storage Security

```yaml
# Encrypted storage with security context
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: secure-database
spec:
  serviceName: secure-db
  replicas: 1
  selector:
    matchLabels:
      app: secure-database
  template:
    metadata:
      labels:
        app: secure-database
    spec:
      securityContext:
        fsGroup: 999
        runAsUser: 999
        runAsNonRoot: true
      containers:
      - name: database
        image: postgres:14
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: tmp
          mountPath: /tmp
        - name: run
          mountPath: /var/run/postgresql
      volumes:
      - name: tmp
        emptyDir: {}
      - name: run
        emptyDir: {}
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: encrypted-ssd
      resources:
        requests:
          storage: 100Gi
```

### Resource Quotas for Storage

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: application
spec:
  hard:
    persistentvolumeclaims: "10"
    requests.storage: "500Gi"
    fast-ebs-encrypted.storageclass.storage.k8s.io/requests.storage: "200Gi"
    database-storage.storageclass.storage.k8s.io/requests.storage: "100Gi"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: storage-limits
  namespace: application
spec:
  limits:
  - type: PersistentVolumeClaim
    min:
      storage: 1Gi
    max:
      storage: 1Ti
    default:
      storage: 10Gi
    defaultRequest:
      storage: 5Gi
```

### Volume Expansion

```bash
# Check if storage class supports expansion
kubectl get storageclass fast-ebs-encrypted -o yaml | grep allowVolumeExpansion

# Expand PVC
kubectl patch pvc mysql-pvc -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Check expansion status
kubectl get pvc mysql-pvc -w

# For filesystem expansion, restart the pod
kubectl rollout restart deployment/mysql
```

---

## Troubleshooting

### Common Storage Issues

```bash
# Check PV and PVC status
kubectl get pv,pvc --all-namespaces
kubectl describe pvc <pvc-name> -n <namespace>

# Check storage class
kubectl get storageclass
kubectl describe storageclass <storage-class-name>

# Check CSI driver pods
kubectl get pods -n kube-system | grep csi
kubectl logs -n kube-system <csi-driver-pod>

# Check volume attachments
kubectl get volumeattachments
kubectl describe volumeattachment <attachment-name>

# Check node storage capacity
kubectl top nodes
kubectl describe node <node-name> | grep -A 10 "Allocated resources"
```

### Debug Volume Mount Issues

```yaml
# Debug pod for volume testing
apiVersion: v1
kind: Pod
metadata:
  name: volume-debug
spec:
  containers:
  - name: debug
    image: busybox:latest
    command: ['sleep', '3600']
    volumeMounts:
    - name: test-volume
      mountPath: /mnt/test
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: problematic-pvc
```

### Performance Monitoring

```bash
# Check I/O performance
kubectl exec -it <pod-name> -- iostat -x 1

# Monitor disk usage
kubectl exec -it <pod-name> -- df -h

# Check mount points
kubectl exec -it <pod-name> -- mount | grep -E "^/dev"

# Test disk performance
kubectl exec -it <pod-name> -- dd if=/dev/zero of=/mnt/test/testfile bs=1M count=1000 oflag=direct
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Storage security and production deployment patterns
- [Kubernetes Workload Controllers](Kubernetes%20Workload%20Controllers.md) - StatefulSet and persistent application patterns
- [Kubernetes Cloud Provider Integrations](Kubernetes%20Cloud%20Provider%20Integrations.md) - Cloud-specific storage implementations
- [Kubernetes Security](Kubernetes%20Security.md) - Storage encryption and access control

**Storage Patterns:**
- **Persistent Applications**: StatefulSet with persistent volumes for databases
- **Shared Storage**: ReadWriteMany volumes for multi-pod access
- **High Performance**: IOPS optimization for database workloads
- **Backup Strategies**: Volume snapshots and Velero integration

**Best Practices Summary:**
- Use appropriate storage classes for workload requirements
- Implement encryption for sensitive data
- Configure proper backup and disaster recovery procedures
- Monitor storage performance and capacity
- Use volume snapshots for point-in-time recovery
- Apply resource quotas to prevent storage exhaustion
- Test volume expansion procedures in non-production environments