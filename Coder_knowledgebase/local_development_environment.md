# Local Development Environment for Spring Boot Microservices

## Overview

A robust local development environment is essential for efficient microservice migration. This document outlines tools and configurations for setting up a productive local environment that closely resembles production while maintaining developer efficiency.

## Local Kubernetes Environments Comparison

When developing microservices locally, several lightweight Kubernetes options are available:

### 1. Minikube

Minikube creates a single-node Kubernetes cluster inside a VM on your local machine.

**Pros:**
- Well-established and thoroughly documented
- Supports multiple hypervisors (VirtualBox, HyperKit, KVM)
- Provides dashboard and other add-ons
- Supports dynamic volume provisioning

**Cons:**
- Resource-intensive (requires a VM)
- Slower startup time compared to alternatives
- Limited multi-node capabilities

**Setup:**
```bash
# Install
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-windows-amd64.exe
# Start with specific resources
minikube start --cpus=4 --memory=8192mb --disk-size=20gb
# Configure Docker to use Minikube's registry
minikube docker-env | Invoke-Expression
```

### 2. K3d

K3d creates lightweight Kubernetes clusters using k3s in Docker containers.

**Pros:**
- Extremely lightweight and fast
- Multi-node clusters are easy to create
- Runs in Docker containers (no VM needed)
- Good integration with CI pipelines

**Cons:**
- Less feature-rich than full Kubernetes
- Some advanced K8s features might not work
- Documentation isn't as extensive as Minikube

**Setup:**
```bash
# Install
curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | bash
# Create multi-node cluster
k3d cluster create microservices-cluster --servers 1 --agents 2 -p "8080:80@loadbalancer"
# Use local registry
k3d registry create registry.localhost --port 5000
k3d cluster create microservices-cluster --registry-use k3d-registry.localhost:5000
```

### 3. Kind (Kubernetes IN Docker)

Kind runs Kubernetes clusters using Docker containers as nodes.

**Pros:**
- Created for Kubernetes testing (high compatibility)
- Multi-node support
- Runs in Docker, no VM needed
- Well-supported by Kubernetes community

**Cons:**
- Limited ingress controller support
- Persistent volume setup is more complex
- Some service types may not work as expected

**Setup:**
```bash
# Install
curl.exe -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.11.1/kind-windows-amd64
move .\kind-windows-amd64.exe kind.exe
# Create cluster with config
$CONFIG=@"
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
- role: worker
"@
$CONFIG | Out-File -FilePath kind-config.yaml
kind create cluster --config kind-config.yaml
```

### 4. Feature Comparison Matrix

| Feature | Minikube | K3d | Kind |
|---------|----------|-----|------|
| Installation Complexity | Medium | Low | Low |
| Resource Usage | High | Low | Medium |
| Start-up Time | Slow | Fast | Medium |
| Multi-node Support | Limited | Good | Good |
| Ingress Support | Built-in | Limited | Limited |
| Volume Persistence | Good | Basic | Basic |
| Dashboard | Built-in | Add-on | Add-on |
| Production Similarity | High | Medium | Medium |
| Container Registry | Built-in | External | External |

## Docker Resource Constraints

When working with microservices locally, properly configuring Docker resource constraints helps avoid system-wide performance issues.

### CPU Constraints

```yaml
# docker-compose.yml with CPU constraints
version: '3.8'
services:
  user-service:
    build: ./user-service
    cpus: 0.5  # Use at most 50% of a CPU core
    cpu_shares: 512  # Relative CPU share (default: 1024)
    cpu_quota: 50000  # Microseconds per cpu_period
    cpu_period: 100000  # Default period is 100000 microseconds (100ms)
```

### Memory Constraints

```yaml
# docker-compose.yml with memory constraints
version: '3.8'
services:
  user-service:
    build: ./user-service
    mem_limit: 512m  # Maximum memory
    memswap_limit: 1g  # Total memory + swap
    mem_reservation: 256m  # Soft limit (guaranteed minimum)
    oom_kill_disable: true  # Prevent OOM killer (use carefully)
```

### Java Container Awareness

For Spring Boot applications in containers, configure JVM memory settings to respect container limits:

```dockerfile
FROM eclipse-temurin:17-jre
COPY target/*.jar app.jar
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

## Spring Boot DevTools for Local Development

Spring Boot DevTools provides automatic restart and live reload capabilities during development.

### Setup

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-devtools</artifactId>
    <scope>runtime</scope>
    <optional>true</optional>
</dependency>
```

### Configuration

```yaml
# application-dev.yml
spring:
  devtools:
    restart:
      enabled: true
      additional-paths: src/main/java
      exclude: static/**,public/**
    livereload:
      enabled: true
  thymeleaf:
    cache: false
```

## Docker Compose for Local Microservices

Docker Compose provides a simpler alternative to Kubernetes for local development:

```yaml
# docker-compose.yml
version: '3.8'
services:
  # Service discovery
  eureka-server:
    build: ./eureka-server
    ports:
      - "8761:8761"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8761/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      
  # API Gateway
  gateway:
    build: ./api-gateway
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - EUREKA_CLIENT_SERVICEURL_DEFAULTZONE=http://eureka-server:8761/eureka/
    depends_on:
      - eureka-server
      
  # Microservices
  user-service:
    build: ./user-service
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/userdb
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=postgres
      - EUREKA_CLIENT_SERVICEURL_DEFAULTZONE=http://eureka-server:8761/eureka/
    depends_on:
      - postgres
      - eureka-server
    volumes:
      - ./user-service:/app
      - maven-repo:/root/.m2
      
  order-service:
    build: ./order-service
    ports:
      - "8082:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/orderdb
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=postgres
      - EUREKA_CLIENT_SERVICEURL_DEFAULTZONE=http://eureka-server:8761/eureka/
    depends_on:
      - postgres
      - eureka-server
    volumes:
      - ./order-service:/app
      - maven-repo:/root/.m2
      
  # Database
  postgres:
    image: postgres:14-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      
  # Monitoring
  zipkin:
    image: openzipkin/zipkin
    ports:
      - "9411:9411"
      
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

volumes:
  postgres-data:
  prometheus-data:
  grafana-data:
  maven-repo:
```

## Development Workflow Tools

### Skaffold for Kubernetes Development

Skaffold automates the workflow for building, pushing, and deploying your application in Kubernetes.

```yaml
# skaffold.yaml
apiVersion: skaffold/v2beta28
kind: Config
build:
  artifacts:
  - image: user-service
    context: user-service
    docker:
      dockerfile: Dockerfile
  - image: order-service
    context: order-service
    docker:
      dockerfile: Dockerfile
  local:
    push: false
deploy:
  kubectl:
    manifests:
    - k8s-manifests/*.yaml
profiles:
- name: dev
  activation:
  - command: dev
  build:
    tagPolicy:
      sha256: {}
  deploy:
    kubectl:
      manifests:
      - k8s-manifests/dev/*.yaml
```

### Tilt for Microservice Development

Tilt unifies your team's local development processes with automated builds, deploys, and live updates.

```python
# Tiltfile
# Define resources
docker_build('user-service', './user-service')
docker_build('order-service', './order-service')

# Deploy to Kubernetes
k8s_yaml(['k8s-manifests/dev/user-service.yaml', 'k8s-manifests/dev/order-service.yaml'])

# Configure live update for faster iteration
k8s_resource('user-service', port_forwards=8081, resource_deps=['postgres'])
k8s_resource('order-service', port_forwards=8082, resource_deps=['postgres'])

# Database dependencies
k8s_yaml('k8s-manifests/dev/postgres.yaml')
k8s_resource('postgres', port_forwards=5432)
```

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Container Resource Constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [K3d Documentation](https://k3d.io/v5.4.6/)
- [Kind Documentation](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [Skaffold Documentation](https://skaffold.dev/docs/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [Spring Boot DevTools Reference](https://docs.spring.io/spring-boot/docs/current/reference/html/using.html#using.devtools)
- [Minikube vs. k3d vs. kind vs. Getdeck Comparison](https://www.blueshoe.io/blog/minikube-vs-k3d-vs-kind-vs-getdeck-beiboot/) 