# GitOps for Spring Boot Microservices

## Overview

GitOps is a set of practices that leverages Git as the single source of truth for declarative infrastructure and applications. This approach ensures that the Git repository contains everything needed to recreate a system, including infrastructure, configuration, application code, and deployment procedures.

## Key GitOps Principles

1. **Declarative Infrastructure**: All infrastructure and application configurations are declared in a Git repository
2. **Immutable Infrastructure**: All changes create new versions rather than modifying existing state
3. **Continuous Reconciliation**: System state is continuously compared and aligned with the desired state
4. **Pull-Based Deployments**: Agents pull desired configurations rather than having them pushed

## Benefits for Microservice Architecture

1. **Consistent Deployments**: Same deployment process across all environments
2. **Auditability**: Complete history of all changes
3. **Self-Documentation**: Infrastructure and application configurations are self-documenting
4. **Revertability**: Easy rollbacks through Git's version control
5. **Disaster Recovery**: Complete deployment state is stored in Git

## GitOps Tools for Kubernetes

### ArgoCD

ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes.

#### Setup for Spring Boot Microservices

1. **Install ArgoCD**:

```yaml
# install.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
# Apply the ArgoCD installation manifest
# This is a condensed version; in production, use the full manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-server
  namespace: argocd
spec:
  selector:
    matchLabels:
      app: argocd-server
  template:
    metadata:
      labels:
        app: argocd-server
    spec:
      containers:
      - name: argocd-server
        image: argoproj/argocd:v2.5.0
        ports:
        - containerPort: 8080
```

2. **Create Application in ArgoCD**:

```yaml
# user-service-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: user-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/microservices-gitops.git
    targetRevision: HEAD
    path: services/user-service/kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

3. **Repository Structure**:

```
microservices-gitops/
├── services/
│   ├── user-service/
│   │   ├── kubernetes/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── kustomization.yaml
│   ├── order-service/
│   │   ├── kubernetes/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── kustomization.yaml
├── environments/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── env-config.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── env-config.yaml
│   └── production/
│       ├── kustomization.yaml
│       └── env-config.yaml
```

### Flux CD

Flux is a set of continuous and progressive delivery solutions for Kubernetes.

#### Setup for Spring Boot Microservices

1. **Install Flux**:

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | bash

# Bootstrap Flux on your cluster
flux bootstrap github \
  --owner=yourusername \
  --repository=microservices-gitops \
  --branch=main \
  --path=./clusters/my-cluster \
  --personal
```

2. **Define Microservice Source**:

```yaml
# user-service-source.yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: user-service
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/yourusername/microservices-gitops
  ref:
    branch: main
```

3. **Define Kustomization**:

```yaml
# user-service-kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: user-service
  namespace: flux-system
spec:
  interval: 5m
  path: ./services/user-service/kubernetes
  prune: true
  sourceRef:
    kind: GitRepository
    name: user-service
  targetNamespace: microservices
```

## GitOps Workflow for Spring Boot Microservices

### 1. Continuous Integration Pipeline

```yaml
# .github/workflows/user-service-ci.yml
name: User Service CI

on:
  push:
    paths:
      - 'services/user-service/**'
    branches: [ main ]
  pull_request:
    paths:
      - 'services/user-service/**'
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '17'
        
    - name: Build and Test
      run: |
        cd services/user-service
        ./mvnw clean verify
        
    - name: Build Docker image
      run: |
        cd services/user-service
        docker build -t ghcr.io/${{ github.repository_owner }}/user-service:${{ github.sha }} .
        
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Push Docker image
      run: |
        docker push ghcr.io/${{ github.repository_owner }}/user-service:${{ github.sha }}
        docker tag ghcr.io/${{ github.repository_owner }}/user-service:${{ github.sha }} ghcr.io/${{ github.repository_owner }}/user-service:latest
        docker push ghcr.io/${{ github.repository_owner }}/user-service:latest
    
    - name: Update Kubernetes manifests
      run: |
        cd services/user-service/kubernetes
        sed -i "s|image: ghcr.io/.*/user-service:.*|image: ghcr.io/${{ github.repository_owner }}/user-service:${{ github.sha }}|" deployment.yaml
        
    - name: Commit and push changes
      uses: stefanzweifel/git-auto-commit-action@v4
      with:
        commit_message: "chore: Update user-service image to ${{ github.sha }}"
        file_pattern: services/user-service/kubernetes/deployment.yaml
```

### 2. Kustomize for Environment Configuration

```yaml
# services/user-service/kubernetes/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
- configmap.yaml
```

```yaml
# environments/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../services/user-service/kubernetes
- ../../services/order-service/kubernetes

namespace: microservices-dev

patchesStrategicMerge:
- env-config.yaml

images:
- name: ghcr.io/yourusername/user-service
  newTag: latest
- name: ghcr.io/yourusername/order-service
  newTag: latest
```

```yaml
# environments/dev/env-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
data:
  application.yaml: |
    spring:
      profiles: dev
      datasource:
        url: jdbc:postgresql://postgres:5432/userdb
        username: postgres
      jpa:
        hibernate:
          ddl-auto: update
    logging:
      level:
        org.springframework: INFO
        com.example: DEBUG
```

### 3. ArgoCD Application Set for Multiple Services

```yaml
# applicationset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - name: user-service
        path: services/user-service/kubernetes
      - name: order-service
        path: services/order-service/kubernetes
      - name: product-service
        path: services/product-service/kubernetes
  template:
    metadata:
      name: '{{name}}'
      namespace: argocd
    spec:
      project: default
      source:
        repoURL: https://github.com/yourusername/microservices-gitops.git
        targetRevision: HEAD
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: microservices
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

## Database Schema Management with GitOps

### Flyway with GitOps

1. **Store Migration Scripts in Git**:

```
services/user-service/
├── src/
│   ├── main/
│   │   ├── resources/
│   │   │   ├── db/
│   │   │   │   ├── migration/
│   │   │   │   │   ├── V1__Create_users_table.sql
│   │   │   │   │   ├── V2__Add_roles_table.sql
│   │   │   │   │   └── V3__Add_email_verification.sql
```

2. **Configure Spring Boot Application**:

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    validate-on-migrate: true
```

3. **Kubernetes Job for Schema Migrations**:

```yaml
# db-migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-db-migration
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
      - name: flyway-migration
        image: ghcr.io/yourusername/user-service:latest
        command: ["java", "-cp", "/app/resources:/app/classes:/app/libs/*", "org.springframework.boot.loader.JarLauncher", "--spring.profiles.active=migration"]
        env:
        - name: SPRING_DATASOURCE_URL
          valueFrom:
            configMapKeyRef:
              name: user-service-config
              key: spring.datasource.url
        - name: SPRING_DATASOURCE_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: SPRING_DATASOURCE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
      restartPolicy: Never
  backoffLimit: 3
```

## Secret Management with GitOps

### Sealed Secrets for Kubernetes

1. **Install Sealed Secrets Controller**:

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets
```

2. **Create Sealed Secret**:

```bash
# Create a regular Kubernetes secret (not stored in Git)
kubectl create secret generic db-credentials \
  --from-literal=username=postgres \
  --from-literal=password=mysecretpassword \
  --dry-run=client -o yaml > db-credentials.yaml

# Seal the secret (can be safely stored in Git)
kubeseal --format yaml < db-credentials.yaml > sealed-db-credentials.yaml
```

3. **Store Sealed Secret in Git Repository**:

```yaml
# sealed-db-credentials.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: microservices
spec:
  encryptedData:
    password: AgBy8hCF8...truncated...
    username: AgCtrIn5W...truncated...
```

### HashiCorp Vault with GitOps

1. **Install Vault Operator**:

```yaml
# vault-operator.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vault-operator
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/kubernetes-sigs/secrets-store-csi-driver.git
    targetRevision: v1.0.0
    path: charts/secrets-store-csi-driver
  destination:
    server: https://kubernetes.default.svc
    namespace: vault-system
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

2. **Configure Spring Boot for Vault Integration**:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-vault-config</artifactId>
</dependency>
```

```yaml
# bootstrap.yml
spring:
  application:
    name: user-service
  cloud:
    vault:
      host: vault.vault-system
      port: 8200
      scheme: http
      authentication: KUBERNETES
      kubernetes:
        role: user-service
        service-account-token-file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kv:
        enabled: true
        backend: secret
        default-context: user-service
```

3. **Vault Configuration in Kubernetes**:

```yaml
# vault-policy.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-policy
  namespace: vault-system
data:
  user-service-policy.hcl: |
    path "secret/data/user-service/*" {
      capabilities = ["read"]
    }
```

## Monitoring and Observability with GitOps

### Prometheus and Grafana Setup

```yaml
# prometheus.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: prometheus
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/prometheus-community/helm-charts.git
    targetRevision: HEAD
    path: charts/kube-prometheus-stack
    helm:
      values: |
        prometheus:
          prometheusSpec:
            serviceMonitorSelector:
              matchLabels:
                monitoring: prometheus
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### Service Monitor for Spring Boot Applications

```yaml
# user-service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: user-service-monitor
  namespace: microservices
  labels:
    monitoring: prometheus
spec:
  selector:
    matchLabels:
      app: user-service
  endpoints:
  - port: http
    path: /actuator/prometheus
    interval: 15s
  namespaceSelector:
    matchNames:
    - microservices
```

### Grafana Dashboard Configuration

```yaml
# grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spring-boot-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "true"
data:
  spring-boot-dashboard.json: |-
    {
      "annotations": {
        "list": []
      },
      "editable": true,
      "gnetId": null,
      "graphTooltip": 0,
      "links": [],
      "panels": [
        {
          "datasource": "Prometheus",
          "fieldConfig": {
            "defaults": {
              "color": {
                "mode": "palette-classic"
              },
              "custom": {
                "axisLabel": "",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "drawStyle": "line",
                "fillOpacity": 10,
                "gradientMode": "none",
                "hideFrom": {
                  "legend": false,
                  "tooltip": false,
                  "viz": false
                },
                "lineInterpolation": "linear",
                "lineWidth": 1,
                "pointSize": 5,
                "scaleDistribution": {
                  "type": "linear"
                },
                "showPoints": "never",
                "spanNulls": true,
                "stacking": {
                  "group": "A",
                  "mode": "none"
                },
                "thresholdsStyle": {
                  "mode": "off"
                }
              },
              "mappings": [],
              "thresholds": {
                "mode": "absolute",
                "steps": [
                  {
                    "color": "green",
                    "value": null
                  },
                  {
                    "color": "red",
                    "value": 80
                  }
                ]
              },
              "unit": "short"
            },
            "overrides": []
          },
          "gridPos": {
            "h": 8,
            "w": 12,
            "x": 0,
            "y": 0
          },
          "id": 2,
          "options": {
            "legend": {
              "calcs": [],
              "displayMode": "list",
              "placement": "bottom"
            },
            "tooltip": {
              "mode": "single"
            }
          },
          "pluginVersion": "8.0.6",
          "targets": [
            {
              "expr": "jvm_memory_used_bytes{area=\"heap\", instance=~\"$instance\"}",
              "interval": "",
              "legendFormat": "{{instance}} - Heap Used",
              "refId": "A"
            }
          ],
          "title": "JVM Heap Memory Usage",
          "type": "timeseries"
        }
      ],
      "refresh": "5s",
      "schemaVersion": 30,
      "style": "dark",
      "tags": ["spring-boot", "microservices"],
      "templating": {
        "list": [
          {
            "allValue": null,
            "current": {},
            "datasource": "Prometheus",
            "definition": "label_values(jvm_memory_used_bytes, instance)",
            "description": null,
            "error": null,
            "hide": 0,
            "includeAll": false,
            "label": "Instance",
            "multi": false,
            "name": "instance",
            "options": [],
            "query": {
              "query": "label_values(jvm_memory_used_bytes, instance)",
              "refId": "Prometheus-instance-Variable-Query"
            },
            "refresh": 1,
            "regex": "",
            "skipUrlSync": false,
            "sort": 0,
            "tagValuesQuery": "",
            "tagsQuery": "",
            "type": "query",
            "useTags": false
          }
        ]
      },
      "time": {
        "from": "now-1h",
        "to": "now"
      },
      "timepicker": {},
      "timezone": "",
      "title": "Spring Boot Metrics",
      "uid": "spring-boot",
      "version": 1
    }
```

## CI/CD Integration with GitOps

### Jenkins Pipeline for GitOps

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        SERVICE_NAME = "user-service"
        REPOSITORY = "https://github.com/yourusername/microservices-gitops.git"
        BRANCH = "main"
    }
    
    stages {
        stage('Checkout') {
            steps {
                git url: "${REPOSITORY}", branch: "${BRANCH}"
            }
        }
        
        stage('Build and Test') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh 'mvn clean verify'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh "docker build -t ${SERVICE_NAME}:${BUILD_NUMBER} ."
                    sh "docker tag ${SERVICE_NAME}:${BUILD_NUMBER} ${SERVICE_NAME}:latest"
                }
            }
        }
        
        stage('Push Docker Image') {
            steps {
                withCredentials([string(credentialsId: 'docker-hub-token', variable: 'DOCKER_TOKEN')]) {
                    sh "docker login -u yourusername -p ${DOCKER_TOKEN}"
                    sh "docker push yourusername/${SERVICE_NAME}:${BUILD_NUMBER}"
                    sh "docker push yourusername/${SERVICE_NAME}:latest"
                }
            }
        }
        
        stage('Update Kubernetes Manifests') {
            steps {
                dir("services/${SERVICE_NAME}/kubernetes") {
                    sh "sed -i 's|image: yourusername/${SERVICE_NAME}:.*|image: yourusername/${SERVICE_NAME}:${BUILD_NUMBER}|' deployment.yaml"
                    
                    withCredentials([sshUserPrivateKey(credentialsId: 'git-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                        sh """
                        git config user.email "jenkins@example.com"
                        git config user.name "Jenkins CI"
                        git add deployment.yaml
                        git commit -m "Update ${SERVICE_NAME} image to ${BUILD_NUMBER}"
                        GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" git push origin ${BRANCH}
                        """
                    }
                }
            }
        }
    }
}
```

## GitOps Best Practices for Spring Boot Microservices

1. **Separate Application and Configuration Repositories**:
   - Application code in one repository
   - Kubernetes manifests in a GitOps repository

2. **Environment-Specific Configuration**:
   - Use Kustomize or Helm to manage environment differences
   - Store non-sensitive configuration in ConfigMaps
   - Use sealed secrets or external secret managers for sensitive data

3. **Progressive Delivery**:
   - Use Canary deployments or Blue/Green strategies
   - Implement automatic rollbacks on failure

4. **Monitoring Integration**:
   - Include monitoring configurations in Git repository
   - Define alerts as code
   - Include dashboards as code

5. **Regular Synchronization**:
   - Set appropriate sync intervals (e.g., 3-5 minutes)
   - Configure self-healing for drift correction

6. **Security Best Practices**:
   - Use RBAC for repository access
   - Implement branch protection rules
   - Sign commits and enforce signature verification
   - Use secrets management tools

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Flux CD Documentation](https://fluxcd.io/docs/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [Spring Boot Kubernetes Deployment](https://spring.io/guides/gs/spring-boot-kubernetes/)
- [GitOps: High-Velocity CI/CD for Kubernetes](https://www.weave.works/technologies/gitops/)
- [Adopting GitOps for Kubernetes Configuration Management](https://overcast.blog/adopting-gitops-for-kubernetes-configuration-management-634975ff5d43) 