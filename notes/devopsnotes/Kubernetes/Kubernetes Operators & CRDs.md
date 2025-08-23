## Operators & Custom Resource Definitions (CRDs) Guide

### Custom Resource Definitions (CRDs) Deep Dive

CRDs extend the Kubernetes API to create custom resources that behave like native Kubernetes objects.

#### Basic CRD Creation

**Simple CRD Definition:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.storage.company.com
spec:
  group: storage.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
                enum: ["mysql", "postgresql", "mongodb"]
              version:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 10
              storage:
                type: object
                properties:
                  size:
                    type: string
                  storageClass:
                    type: string
                required:
                - size
            required:
            - engine
            - version
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Running", "Failed"]
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    reason:
                      type: string
                    message:
                      type: string
                    lastTransitionTime:
                      type: string
                      format: date-time
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames:
    - db
  conversion:
    strategy: None
```

#### Advanced CRD Features

**CRD with Validation and Defaults:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.company.com
spec:
  group: apps.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              image:
                type: string
                pattern: '^[a-z0-9-._/]+:[a-z0-9-._]+$'
              replicas:
                type: integer
                minimum: 1
                maximum: 100
                default: 3
              resources:
                type: object
                properties:
                  cpu:
                    type: string
                    default: "100m"
                  memory:
                    type: string
                    default: "128Mi"
                default:
                  cpu: "100m"
                  memory: "128Mi"
              ingress:
                type: object
                properties:
                  enabled:
                    type: boolean
                    default: false
                  host:
                    type: string
                  tls:
                    type: boolean
                    default: false
                  annotations:
                    type: object
                    additionalProperties:
                      type: string
            required:
            - image
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Deploying", "Ready", "Failed"]
              readyReplicas:
                type: integer
              url:
                type: string
    additionalPrinterColumns:
    - name: Image
      type: string
      jsonPath: .spec.image
    - name: Replicas
      type: integer
      jsonPath: .spec.replicas
    - name: Ready
      type: integer
      jsonPath: .status.readyReplicas
    - name: Phase
      type: string
      jsonPath: .status.phase
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
  scope: Namespaced
  names:
    plural: webapps
    singular: webapp
    kind: WebApp
    shortNames:
    - wa
```

**CRD with Subresources:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: clusters.database.company.com
spec:
  group: database.company.com
  versions:
  - name: v1
    served: true
    storage: true
    subresources:
      status: {}
      scale:
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.replicas
        labelSelectorPath: .status.selector
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              replicas:
                type: integer
                minimum: 1
              version:
                type: string
              backup:
                type: object
                properties:
                  enabled:
                    type: boolean
                  schedule:
                    type: string
                  retention:
                    type: string
          status:
            type: object
            properties:
              replicas:
                type: integer
              readyReplicas:
                type: integer
              selector:
                type: string
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    reason:
                      type: string
                    message:
                      type: string
  scope: Namespaced
  names:
    plural: clusters
    singular: cluster
    kind: Cluster
```

#### Using Custom Resources

**Creating Custom Resource Instances:**

```yaml
apiVersion: storage.company.com/v1
kind: Database
metadata:
  name: user-database
  namespace: production
spec:
  engine: postgresql
  version: "13.7"
  replicas: 3
  storage:
    size: 100Gi
    storageClass: fast-ssd
---
apiVersion: apps.company.com/v1
kind: WebApp
metadata:
  name: frontend-app
  namespace: production
spec:
  image: company/frontend:v1.2.3
  replicas: 5
  resources:
    cpu: 200m
    memory: 256Mi
  ingress:
    enabled: true
    host: app.company.com
    tls: true
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
```

### Kubernetes Operators Deep Dive

Operators are software extensions that use custom resources to manage applications and their components.

#### Operator Development with Operator SDK

**Initialize Operator Project:**

```bash
# Install Operator SDK
curl -LO https://github.com/operator-framework/operator-sdk/releases/download/v1.28.1/operator-sdk_linux_amd64
chmod +x operator-sdk_linux_amd64 && sudo mv operator-sdk_linux_amd64 /usr/local/bin/operator-sdk

# Initialize new operator
operator-sdk init --domain=company.com --repo=github.com/company/database-operator

# Create API and controller
operator-sdk create api --group=database --version=v1 --kind=PostgreSQL --resource --controller
```

**PostgreSQL Operator CRD:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: postgresqls.database.company.com
spec:
  group: database.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              version:
                type: string
                enum: ["12", "13", "14", "15"]
              replicas:
                type: integer
                minimum: 1
                maximum: 10
              storage:
                type: object
                properties:
                  size:
                    type: string
                  storageClass:
                    type: string
                required:
                - size
              backup:
                type: object
                properties:
                  enabled:
                    type: boolean
                  schedule:
                    type: string
                  retention:
                    type: string
                  s3:
                    type: object
                    properties:
                      bucket:
                        type: string
                      region:
                        type: string
              monitoring:
                type: object
                properties:
                  enabled:
                    type: boolean
                  serviceMonitor:
                    type: boolean
            required:
            - version
            - storage
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Creating", "Running", "Failed", "Scaling"]
              readyReplicas:
                type: integer
              primaryPod:
                type: string
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    reason:
                      type: string
                    message:
                      type: string
                    lastTransitionTime:
                      type: string
    subresources:
      status: {}
      scale:
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.readyReplicas
  scope: Namespaced
  names:
    plural: postgresqls
    singular: postgresql
    kind: PostgreSQL
    shortNames:
    - pg
```

#### Operator Controller Implementation

**Go Controller Logic (Simplified):**

```go
// controllers/postgresql_controller.go
package controllers

import (
    "context"
    "fmt"
    
    appsv1 "k8s.io/api/apps/v1"
    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
    
    databasev1 "github.com/company/database-operator/api/v1"
)

type PostgreSQLReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}

func (r *PostgreSQLReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // Fetch the PostgreSQL instance
    postgresql := &databasev1.PostgreSQL{}
    err := r.Get(ctx, req.NamespacedName, postgresql)
    if err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Create or update StatefulSet
    if err := r.reconcileStatefulSet(ctx, postgresql); err != nil {
        return ctrl.Result{}, err
    }

    // Create or update Service
    if err := r.reconcileService(ctx, postgresql); err != nil {
        return ctrl.Result{}, err
    }

    // Update status
    if err := r.updateStatus(ctx, postgresql); err != nil {
        return ctrl.Result{}, err
    }

    return ctrl.Result{RequeueAfter: time.Minute * 5}, nil
}

func (r *PostgreSQLReconciler) reconcileStatefulSet(ctx context.Context, pg *databasev1.PostgreSQL) error {
    statefulSet := &appsv1.StatefulSet{
        ObjectMeta: metav1.ObjectMeta{
            Name:      pg.Name,
            Namespace: pg.Namespace,
        },
        Spec: appsv1.StatefulSetSpec{
            Replicas: &pg.Spec.Replicas,
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{
                    "app": pg.Name,
                },
            },
            Template: corev1.PodTemplateSpec{
                ObjectMeta: metav1.ObjectMeta{
                    Labels: map[string]string{
                        "app": pg.Name,
                    },
                },
                Spec: corev1.PodSpec{
                    Containers: []corev1.Container{
                        {
                            Name:  "postgresql",
                            Image: fmt.Sprintf("postgres:%s", pg.Spec.Version),
                            Env: []corev1.EnvVar{
                                {
                                    Name:  "POSTGRES_DB",
                                    Value: "app",
                                },
                                {
                                    Name: "POSTGRES_PASSWORD",
                                    ValueFrom: &corev1.EnvVarSource{
                                        SecretKeyRef: &corev1.SecretKeySelector{
                                            LocalObjectReference: corev1.LocalObjectReference{
                                                Name: pg.Name + "-secret",
                                            },
                                            Key: "password",
                                        },
                                    },
                                },
                            },
                            VolumeMounts: []corev1.VolumeMount{
                                {
                                    Name:      "data",
                                    MountPath: "/var/lib/postgresql/data",
                                },
                            },
                        },
                    },
                },
            },
            VolumeClaimTemplates: []corev1.PersistentVolumeClaim{
                {
                    ObjectMeta: metav1.ObjectMeta{
                        Name: "data",
                    },
                    Spec: corev1.PersistentVolumeClaimSpec{
                        AccessModes: []corev1.PersistentVolumeAccessMode{
                            corev1.ReadWriteOnce,
                        },
                        Resources: corev1.ResourceRequirements{
                            Requests: corev1.ResourceList{
                                corev1.ResourceStorage: resource.MustParse(pg.Spec.Storage.Size),
                            },
                        },
                        StorageClassName: &pg.Spec.Storage.StorageClass,
                    },
                },
            },
        },
    }

    // Set owner reference
    ctrl.SetControllerReference(pg, statefulSet, r.Scheme)

    // Create or update
    return r.CreateOrUpdate(ctx, statefulSet)
}

func (r *PostgreSQLReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&databasev1.PostgreSQL{}).
        Owns(&appsv1.StatefulSet{}).
        Owns(&corev1.Service{}).
        Complete(r)
}
```

#### Operator Deployment

**Operator Deployment Manifests:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-operator-controller-manager
  namespace: database-operator-system
spec:
  replicas: 1
  selector:
    matchLabels:
      control-plane: controller-manager
  template:
    metadata:
      labels:
        control-plane: controller-manager
    spec:
      serviceAccountName: database-operator-controller-manager
      containers:
      - name: manager
        image: company/database-operator:latest
        command:
        - /manager
        args:
        - --leader-elect
        env:
        - name: WATCH_NAMESPACE
          value: ""
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: database-operator-controller-manager
  namespace: database-operator-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: database-operator-manager-role
rules:
- apiGroups:
  - ""
  resources:
  - configmaps
  - persistentvolumeclaims
  - secrets
  - services
  verbs:
  - create
  - delete
  - get
  - list
  - patch
  - update
  - watch
- apiGroups:
  - apps
  resources:
  - statefulsets
  verbs:
  - create
  - delete
  - get
  - list
  - patch
  - update
  - watch
- apiGroups:
  - database.company.com
  resources:
  - postgresqls
  verbs:
  - create
  - delete
  - get
  - list
  - patch
  - update
  - watch
- apiGroups:
  - database.company.com
  resources:
  - postgresqls/status
  verbs:
  - get
  - patch
  - update
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: database-operator-manager-rolebinding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: database-operator-manager-role
subjects:
- kind: ServiceAccount
  name: database-operator-controller-manager
  namespace: database-operator-system
```

### Popular Kubernetes Operators

#### Prometheus Operator

**ServiceMonitor CRD Usage:**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: web-app-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: web-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
    honorLabels: true
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: web-app-alerts
  namespace: monitoring
spec:
  groups:
  - name: web-app.rules
    rules:
    - alert: WebAppHighErrorRate
      expr: rate(http_requests_total{job="web-app",status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate on web-app"
        description: "Error rate is {{ $value }} errors per second"
```

#### Cert-Manager Operator

**Certificate CRD Usage:**

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: app-tls-cert
  namespace: production
spec:
  secretName: app-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - app.company.com
  - api.company.com
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
    - dns01:
        route53:
          region: us-west-2
          accessKeyID: AKIAIOSFODNN7EXAMPLE
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key
```

#### Istio Operator

**VirtualService CRD Usage:**

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: web-app-vs
  namespace: production
spec:
  hosts:
  - app.company.com
  gateways:
  - app-gateway
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: api-v1-service
        port:
          number: 80
      weight: 90
    - destination:
        host: api-v2-service
        port:
          number: 80
      weight: 10
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: web-app-service
        port:
          number: 80
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-destination-rule
  namespace: production
spec:
  host: api-service
  trafficPolicy:
    circuitBreaker:
      connectionPool:
        tcp:
          maxConnections: 100
        http:
          http1MaxPendingRequests: 50
          maxRequestsPerConnection: 10
      outlierDetection:
        consecutiveErrors: 3
        interval: 30s
        baseEjectionTime: 30s
```

### Advanced Operator Patterns

#### Multi-Tenant Operator

**Tenant CRD:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tenants.multi-tenant.company.com
spec:
  group: multi-tenant.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              name:
                type: string
              namespaces:
                type: array
                items:
                  type: string
              resourceQuota:
                type: object
                properties:
                  cpu:
                    type: string
                  memory:
                    type: string
                  storage:
                    type: string
              networkPolicies:
                type: boolean
              rbac:
                type: object
                properties:
                  users:
                    type: array
                    items:
                      type: string
                  groups:
                    type: array
                    items:
                      type: string
            required:
            - name
          status:
            type: object
            properties:
              phase:
                type: string
              namespacesCreated:
                type: array
                items:
                  type: string
  scope: Cluster
  names:
    plural: tenants
    singular: tenant
    kind: Tenant
```

**Tenant Instance:**

```yaml
apiVersion: multi-tenant.company.com/v1
kind: Tenant
metadata:
  name: team-alpha
spec:
  name: team-alpha
  namespaces:
  - team-alpha-dev
  - team-alpha-staging
  - team-alpha-prod
  resourceQuota:
    cpu: "10"
    memory: "20Gi"
    storage: "100Gi"
  networkPolicies: true
  rbac:
    users:
    - alice@company.com
    - bob@company.com
    groups:
    - team-alpha-developers
```

#### Backup Operator

**Backup CRD:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.backup.company.com
spec:
  group: backup.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              target:
                type: object
                properties:
                  kind:
                    type: string
                    enum: ["StatefulSet", "Deployment", "PersistentVolumeClaim"]
                  name:
                    type: string
                  namespace:
                    type: string
                required:
                - kind
                - name
              schedule:
                type: string
              retention:
                type: string
              storage:
                type: object
                properties:
                  provider:
                    type: string
                    enum: ["s3", "gcs", "azure"]
                  bucket:
                    type: string
                  region:
                    type: string
                  credentialsSecret:
                    type: string
                required:
                - provider
                - bucket
            required:
            - target
            - schedule
            - storage
          status:
            type: object
            properties:
              lastBackup:
                type: string
                format: date-time
              nextBackup:
                type: string
                format: date-time
              phase:
                type: string
  scope: Namespaced
  names:
    plural: backups
    singular: backup
    kind: Backup
```

### Operator Lifecycle Manager (OLM)

#### OLM Installation and Usage

**Install OLM:**

```bash
# Install OLM
curl -sL https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.24.0/install.sh | bash -s v0.24.0

# Verify installation
kubectl get csv -A
kubectl get catalogsource -n olm
```

**Custom Catalog Source:**

```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: company-operators
  namespace: olm
spec:
  sourceType: grpc
  image: company/operator-catalog:latest
  displayName: Company Operators
  publisher: Company DevOps Team
  updateStrategy:
    registryPoll:
      interval: 10m
```

**Subscription and OperatorGroup:**

```yaml
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: database-operators
  namespace: database-system
spec:
  targetNamespaces:
  - database-system
  - production
  - staging
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: postgresql-operator
  namespace: database-system
spec:
  channel: stable
  name: postgresql-operator
  source: company-operators
  sourceNamespace: olm
  installPlanApproval: Automatic
  startingCSV: postgresql-operator.v1.0.0
```

### Operator Testing and Validation

#### Unit Testing

**Controller Test (Go):**

```go
// controllers/postgresql_controller_test.go
package controllers

import (
    "context"
    "time"
    
    . "github.com/onsi/ginkgo"
    . "github.com/onsi/gomega"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    
    databasev1 "github.com/company/database-operator/api/v1"
)

var _ = Describe("PostgreSQL Controller", func() {
    Context("When creating a PostgreSQL instance", func() {
        It("Should create a StatefulSet", func() {
            ctx := context.Background()
            
            postgresql := &databasev1.PostgreSQL{
                ObjectMeta: metav1.ObjectMeta{
                    Name:      "test-postgres",
                    Namespace: "default",
                },
                Spec: databasev1.PostgreSQLSpec{
                    Version:  "13",
                    Replicas: 3,
                    Storage: databasev1.StorageSpec{
                        Size:         "10Gi",
                        StorageClass: "standard",
                    },
                },
            }
            
            Expect(k8sClient.Create(ctx, postgresql)).Should(Succeed())
            
            // Wait for StatefulSet creation
            Eventually(func() bool {
                statefulSet := &appsv1.StatefulSet{}
                err := k8sClient.Get(ctx, types.NamespacedName{
                    Name:      "test-postgres",
                    Namespace: "default",
                }, statefulSet)
                return err == nil
            }, time.Second*10, time.Millisecond*250).Should(BeTrue())
        })
    })
})
```

#### Integration Testing

**E2E Test with Ginkgo:**

```go
// test/e2e/postgresql_test.go
package e2e

import (
    "context"
    "time"
    
    . "github.com/onsi/ginkgo"
    . "github.com/onsi/gomega"
    
    databasev1 "github.com/company/database-operator/api/v1"
)

var _ = Describe("PostgreSQL E2E", func() {
    It("Should create a functional PostgreSQL cluster", func() {
        ctx := context.Background()
        
        // Create PostgreSQL instance
        postgresql := &databasev1.PostgreSQL{
            ObjectMeta: metav1.ObjectMeta{
                Name:      "e2e-postgres",
                Namespace: testNamespace,
            },
            Spec: databasev1.PostgreSQLSpec{
                Version:  "13",
                Replicas: 2,
                Storage: databasev1.StorageSpec{
                    Size:         "1Gi",
                    StorageClass: "standard",
                },
            },
        }
        
        Expect(k8sClient.Create(ctx, postgresql)).Should(Succeed())
        
        // Wait for Ready status
        Eventually(func() string {
            Expect(k8sClient.Get(ctx, types.NamespacedName{
                Name:      "e2e-postgres",
                Namespace: testNamespace,
            }, postgresql)).Should(Succeed())
            return postgresql.Status.Phase
        }, time.Minute*5, time.Second*5).Should(Equal("Running"))
        
        // Test database connectivity
        By("Testing database connectivity")
        testPod := createTestPod(testNamespace)
        Expect(k8sClient.Create(ctx, testPod)).Should(Succeed())
        
        Eventually(func() bool {
            return testDatabaseConnection(testPod.Name, testNamespace)
        }, time.Minute*2, time.Second*10).Should(BeTrue())
    })
})
```

### DevOps Best Practices for Operators

#### Operator Development Checklist

**✅ Design:**
- Clear API design with proper validation
- Comprehensive status reporting
- Idempotent reconciliation logic
- Proper error handling and recovery

**✅ Security:**
- Minimal RBAC permissions
- Secure defaults in CRDs
- Input validation and sanitization
- Secret management best practices

**✅ Operations:**
- Comprehensive logging and metrics
- Health checks and readiness probes
- Graceful shutdown handling
- Upgrade and migration strategies

**✅ Testing:**
- Unit tests for controller logic
- Integration tests with real Kubernetes
- E2E tests for complete workflows
- Performance and stress testing

**✅ Documentation:**
- Clear API documentation
- Installation and upgrade guides
- Troubleshooting procedures
- Example configurations

#### Operator Monitoring

**Operator Metrics:**

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: database-operator-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      control-plane: controller-manager
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**Custom Metrics in Controller:**

```go
// Add to controller
import (
    "github.com/prometheus/client_golang/prometheus"
    "sigs.k8s.io/controller-runtime/pkg/metrics"
)

var (
    postgresqlReconcileTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "postgresql_reconcile_total",
            Help: "Total number of PostgreSQL reconciles",
        },
        []string{"namespace", "name", "result"},
    )
    
    postgresqlReconcileDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "postgresql_reconcile_duration_seconds",
            Help: "Duration of PostgreSQL reconciles",
        },
        []string{"namespace", "name"},
    )
)

func init() {
    metrics.Registry.MustRegister(postgresqlReconcileTotal)
    metrics.Registry.MustRegister(postgresqlReconcileDuration)
}

func (r *PostgreSQLReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    start := time.Now()
    defer func() {
        duration := time.Since(start).Seconds()
        postgresqlReconcileDuration.WithLabelValues(req.Namespace, req.Name).Observe(duration)
    }()
    
    // Reconciliation logic...
    
    postgresqlReconcileTotal.WithLabelValues(req.Namespace, req.Name, "success").Inc()
    return ctrl.Result{}, nil
}
```