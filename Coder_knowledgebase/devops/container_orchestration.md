# Container Orchestration for Microservices

## Overview

Container orchestration automates the deployment, management, scaling, and networking of containers. When migrating from a monolith to microservices, container orchestration becomes essential for managing the increased operational complexity.

## Docker Containerization for Spring Boot

### Spring Boot Container Best Practices

#### 1. Efficient Layering

Spring Boot 2.3.0+ supports creating optimized layered Docker images:

```xml
<!-- pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
            <configuration>
                <layers>
                    <enabled>true</enabled>
                </layers>
            </configuration>
        </plugin>
    </plugins>
</build>
```

Corresponding Dockerfile:

```dockerfile
FROM eclipse-temurin:17-jdk as builder
WORKDIR /app
COPY target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./
ENTRYPOINT ["java", "org.springframework.boot.loader.JarLauncher"]
```

#### 2. Optimizing Image Size

- Use JRE instead of JDK in the runtime image
- Consider using Alpine-based images for smaller size
- Remove unnecessary files and dependencies

#### 3. Runtime Configuration

Use environment variables for configuration:

```dockerfile
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY target/*.jar app.jar
ENV JAVA_OPTS="-Xmx512m -Xms256m"
ENV SPRING_PROFILES_ACTIVE="prod"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

#### 4. Health Checks in Dockerfile

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/actuator/health || exit 1
```

## Kubernetes for Spring Boot Microservices

### Basic Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: myregistry/user-service:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
```

### Service Definition

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### ConfigMap for Spring Boot Properties

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
data:
  application.properties: |
    spring.datasource.url=jdbc:mysql://mysql-service:3306/userdb
    spring.datasource.username=${DB_USERNAME}
    spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
    spring.jpa.hibernate.ddl-auto=update
    management.endpoints.web.exposure.include=health,info,metrics
    
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  # ...
  template:
    # ...
    spec:
      containers:
      - name: user-service
        # ...
        volumeMounts:
        - name: config-volume
          mountPath: /config
        env:
        - name: SPRING_CONFIG_LOCATION
          value: file:/config/application.properties
      volumes:
      - name: config-volume
        configMap:
          name: user-service-config
```

### Secrets Management

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: user-service-secrets
type: Opaque
data:
  db-username: dXNlcm5hbWU=  # base64 encoded username
  db-password: cGFzc3dvcmQ=  # base64 encoded password
  
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  # ...
  template:
    # ...
    spec:
      containers:
      - name: user-service
        # ...
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: db-username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: db-password
```

### Helm Charts for Spring Boot Applications

Example Helm chart structure:

```
user-service/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── secret.yaml
```

`values.yaml`:

```yaml
# Default values for user-service
replicaCount: 2

image:
  repository: myregistry/user-service
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

springConfig:
  activeProfile: prod
  datasource:
    url: jdbc:mysql://mysql-service:3306/userdb
    username: user
    password: password
```

`templates/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
  labels:
    app: {{ .Release.Name }}
    chart: {{ .Chart.Name }}-{{ .Chart.Version }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
      - name: {{ .Release.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: {{ .Values.springConfig.activeProfile }}
        - name: SPRING_DATASOURCE_URL
          value: {{ .Values.springConfig.datasource.url }}
        - name: SPRING_DATASOURCE_USERNAME
          valueFrom:
            secretKeyRef:
              name: {{ .Release.Name }}-secret
              key: db-username
        - name: SPRING_DATASOURCE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ .Release.Name }}-secret
              key: db-password
        resources:
          requests:
            memory: {{ .Values.resources.requests.memory }}
            cpu: {{ .Values.resources.requests.cpu }}
          limits:
            memory: {{ .Values.resources.limits.memory }}
            cpu: {{ .Values.resources.limits.cpu }}
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: {{ .Values.service.targetPort }}
          initialDelaySeconds: 20
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: {{ .Values.service.targetPort }}
          initialDelaySeconds: 30
          periodSeconds: 30
```

## Local Development Setup

### Docker Compose for Local Microservices

```yaml
# docker-compose.yml
version: '3.8'

services:
  user-service:
    build: ./user-service
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/userdb
      - SPRING_DATASOURCE_USERNAME=root
      - SPRING_DATASOURCE_PASSWORD=rootpassword
    depends_on:
      - mysql
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  order-service:
    build: ./order-service
    ports:
      - "8082:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/orderdb
      - SPRING_DATASOURCE_USERNAME=root
      - SPRING_DATASOURCE_PASSWORD=rootpassword
    depends_on:
      - mysql
      
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=userdb
    volumes:
      - mysql-data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  mysql-data:
```

### Minikube/Kind for Local Kubernetes

```bash
# Start Minikube
minikube start --memory=4096 --cpus=4

# Build Docker image in Minikube's Docker environment
eval $(minikube docker-env)
docker build -t user-service:local ./user-service

# Deploy application
kubectl apply -f kubernetes/user-service.yaml

# Access service
minikube service user-service
```

## Migration Strategies

### 1. Parallel Running

Run both monolith and microservices in parallel during migration:

```yaml
# ingress.yaml for parallel running
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: application-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /monolith(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: monolith-service
            port:
              number: 80
      - path: /users(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 80
```

### 2. Canary Deployments

Gradually shift traffic from monolith to microservices:

```yaml
# canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service-canary
spec:
  replicas: 1
  # rest of deployment spec...
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: user-service-ingress
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "20"
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api/users
        pathType: Prefix
        backend:
          service:
            name: user-service-canary
            port:
              number: 80
```

## References

- [Spring Boot Kubernetes Deployment Guide](https://spring.io/guides/gs/spring-boot-kubernetes/)
- [9 Tips for Containerizing Your Spring Boot Code](https://www.docker.com/blog/9-tips-for-containerizing-your-spring-boot-code/)
- [Efficient Container Images in Spring Boot](https://docs.spring.io/spring-boot/reference/packaging/container-images/efficient-images.html)
- [Configuring Spring Boot on Kubernetes with ConfigMap](https://developers.redhat.com/blog/2017/10/03/configuring-spring-boot-kubernetes-configmap)
- [Deploying Spring Boot Microservices with Helm](https://josephrodriguezg.medium.com/deploying-a-spring-boot-application-in-kubernetes-using-helm-charts-5c04c2d46e16) 