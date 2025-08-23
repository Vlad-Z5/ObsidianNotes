## Storage Comprehensive Deep Dive

### Volume Types Detailed Analysis

#### Persistent Volumes (PV) and Claims (PVC)

**Static Provisioning:**

```yaml
# Persistent Volume
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv
spec:
  capacity:
    storage: 10Gi
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
# Persistent Volume Claim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: manual
```

**Dynamic Provisioning with Storage Classes:**

**AWS EBS Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

**Azure Disk Storage Class:**

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
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

**GCP Persistent Disk Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  zones: us-central1-a,us-central1-b
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### CSI Drivers Deep Dive

#### AWS EBS CSI Driver

**Installation:**

```bash
# Add IAM policy to nodes
aws iam attach-role-policy \
  --role-name eksctl-cluster-nodegroup-NodeInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy

# Deploy CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

**Volume Snapshot Configuration:**

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Delete
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-snapshot
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: mysql-pvc
```

#### Azure File CSI Driver

**Configuration for Shared Storage:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-file
provisioner: file.csi.azure.com
parameters:
  storageAccount: mystorageaccount
  resourceGroup: myResourceGroup
  shareName: myshare
volumeBindingMode: Immediate
allowVolumeExpansion: true
mountOptions:
  - dir_mode=0755
  - file_mode=0755
  - uid=0
  - gid=0
  - mfsymlinks
  - cache=strict
```

### Volume Management Best Practices

**Volume Expansion:**

```yaml
# Enable in StorageClass  
allowVolumeExpansion: true

# Expand PVC
spec:
  resources:
    requests:
      storage: 20Gi  # Increased from 10Gi
```

**Backup Strategies:**

```yaml
# Using Velero for backup
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: mysql-backup
spec:
  includedNamespaces:
  - database
  includedResources:
  - persistentvolumeclaims
  - persistentvolumes
  storageLocation: aws-s3
  ttl: 720h0m0s
```

### Traditional Volume Types

#### emptyDir Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: cache-volume
      mountPath: /cache
  volumes:
  - name: cache-volume
    emptyDir: {}
```

#### hostPath Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: host-volume
      mountPath: /host-data
  volumes:
  - name: host-volume
    hostPath:
      path: /mnt/data
      type: Directory
```

### Legacy Persistent Volume Example

**Persistent Volume:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: fast
```

**Using PVC in Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: pvc-storage
```

### Storage Classes

Dynamic provisioning of persistent volumes

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  replication-type: none
allowVolumeExpansion: true
```
