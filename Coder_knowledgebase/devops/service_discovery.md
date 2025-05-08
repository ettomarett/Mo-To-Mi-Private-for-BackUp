# Service Discovery in Microservices

## Overview

Service discovery is a critical component in microservices architecture that enables services to find and communicate with each other without hardcoded hostnames or ports. This is essential because, in a microservices environment, service instances come and go dynamically due to scaling, failures, or deployments.

## Service Discovery Patterns

### Client-Side Discovery

In this pattern, the client is responsible for determining the network locations of available service instances and load balancing requests across them.

```
┌─────────────┐     ┌─────────────┐
│             │     │             │
│   Client    │ ──► │  Discovery  │
│   Service   │     │   Service   │
│             │     │             │
└──────┬──────┘     └─────────────┘
       │                   ▲
       │                   │
       │             ┌─────┴─────┐
       │             │           │
       └────────────►│  Target   │
                     │  Services │
                     │           │
                     └───────────┘
```

### Server-Side Discovery

In this pattern, clients make requests to a load balancer, which queries the service registry and forwards the request to an available service instance.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│   Client    │ ──► │    Load     │ ──► │  Discovery  │
│   Service   │     │  Balancer   │     │   Service   │
│             │     │             │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │                   ▲
                           │                   │
                           │             ┌─────┴─────┐
                           │             │           │
                           └────────────►│  Target   │
                                         │  Services │
                                         │           │
                                         └───────────┘
```

## Spring Cloud Service Discovery

Spring Cloud provides several options for service discovery, with Netflix Eureka being the most commonly used solution.

### Spring Cloud Netflix Eureka

Eureka is a REST-based service discovery server and client from Netflix OSS, integrated into Spring Cloud.

#### 1. Eureka Server Setup

First, create a dedicated service for Eureka Server:

**1.1 Add dependencies to `pom.xml`:**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
</dependency>
```

**1.2 Configure the application:**

```yaml
# application.yml
server:
  port: 8761

spring:
  application:
    name: eureka-server

eureka:
  client:
    registerWithEureka: false
    fetchRegistry: false
  server:
    waitTimeInMsWhenSyncEmpty: 0
```

**1.3 Enable Eureka Server in the main class:**

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

#### 2. Eureka Client Configuration

For each microservice that needs to be discoverable:

**2.1 Add dependencies to `pom.xml`:**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
</dependency>
```

**2.2 Configure the client:**

```yaml
# application.yml
spring:
  application:
    name: user-service

server:
  port: 8081

eureka:
  client:
    serviceUrl:
      defaultZone: http://localhost:8761/eureka/
  instance:
    preferIpAddress: true
```

**2.3 Enable Eureka Client in the main class:**

```java
@SpringBootApplication
@EnableDiscoveryClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

#### 3. Service-to-Service Communication

Using Eureka with Spring Cloud's `@LoadBalanced` `RestTemplate`:

```java
@Configuration
public class RestTemplateConfig {
    
    @Bean
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class OrderService {
    
    private final RestTemplate restTemplate;
    
    public OrderService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    public User getUserForOrder(Long userId) {
        // Use the service name instead of the host and port
        return restTemplate.getForObject("http://user-service/api/users/{id}", User.class, userId);
    }
}
```

### Using Spring Cloud LoadBalancer

Spring Cloud LoadBalancer is an alternative to Ribbon that's maintained as part of the Spring Cloud project.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-loadbalancer</artifactId>
</dependency>
```

Configuration:

```yaml
spring:
  cloud:
    loadbalancer:
      ribbon:
        enabled: false
      cache:
        enabled: true
        ttl: 5s
      healthcheck:
        interval: 15s
```

### WebClient with LoadBalancing

For reactive applications, use `WebClient` with load balancing:

```java
@Configuration
public class WebClientConfig {
    
    @Bean
    @LoadBalanced
    public WebClient.Builder loadBalancedWebClientBuilder() {
        return WebClient.builder();
    }
}

@Service
public class ReactiveOrderService {
    
    private final WebClient.Builder webClientBuilder;
    
    public ReactiveOrderService(WebClient.Builder webClientBuilder) {
        this.webClientBuilder = webClientBuilder;
    }
    
    public Mono<User> getUserForOrder(Long userId) {
        return webClientBuilder.build()
            .get()
            .uri("http://user-service/api/users/{id}", userId)
            .retrieve()
            .bodyToMono(User.class);
    }
}
```

## Spring Cloud Kubernetes

For Kubernetes-based deployments, Spring Cloud Kubernetes can leverage Kubernetes' built-in service discovery:

### 1. Dependencies

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-kubernetes-client</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-kubernetes-client-loadbalancer</artifactId>
</dependency>
```

### 2. Configuration

```yaml
spring:
  cloud:
    kubernetes:
      discovery:
        enabled: true
      loadbalancer:
        enabled: true
```

### 3. Usage

The usage is the same as with Eureka, but it now uses Kubernetes' service discovery:

```java
@Service
public class OrderService {
    
    private final RestTemplate restTemplate;
    
    public OrderService(@LoadBalanced RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    public User getUserForOrder(Long userId) {
        // Uses Kubernetes service name
        return restTemplate.getForObject("http://user-service/api/users/{id}", User.class, userId);
    }
}
```

## Service Discovery during Migration

During migration from monolith to microservices, service discovery plays a crucial role in enabling new microservices to register themselves and be discovered by clients.

### Hybrid Discovery Strategy

1. **API Gateway Routing**: Use API Gateway to route requests to either the monolith or new microservices
2. **Service Discovery for New Services**: Only new microservices register with the discovery server
3. **Feature Flags**: Control which implementation (monolith or microservice) handles requests

Example API Gateway Configuration (Spring Cloud Gateway):

```yaml
spring:
  cloud:
    gateway:
      routes:
        # Route to monolith for legacy paths
        - id: monolith-route
          uri: http://monolith-service:8080
          predicates:
            - Path=/legacy/**
          
        # Route to microservices via service discovery
        - id: user-service-route
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
            
        - id: order-service-route
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
```

### Progressive Migration with Service Discovery

1. **Register Monolith as a Service**: Initially register the monolith in the service registry
2. **Extract Microservices**: Gradually extract services and register them
3. **Dual Registration**: During transition, maintain registration for both implementations
4. **Traffic Shifting**: Gradually shift traffic from monolith to microservices

## Service Health Monitoring

Service discovery is closely tied to health checking to ensure only healthy instances receive traffic.

### Spring Boot Actuator Health Indicators

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

Configuration:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      show-details: always
  health:
    diskspace:
      enabled: true
    db:
      enabled: true
```

Custom Health Indicator:

```java
@Component
public class ExternalServiceHealthIndicator implements HealthIndicator {
    
    private final RestTemplate restTemplate;
    
    public ExternalServiceHealthIndicator(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    @Override
    public Health health() {
        try {
            // Check external dependency health
            ResponseEntity<String> response = restTemplate.getForEntity(
                "http://external-service/health", String.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                return Health.up()
                    .withDetail("externalService", "UP")
                    .build();
            }
            
            return Health.down()
                .withDetail("externalService", "DOWN")
                .withDetail("status", response.getStatusCode())
                .build();
                
        } catch (Exception e) {
            return Health.down()
                .withDetail("externalService", "DOWN")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

## Local Development Setup

For local development with service discovery:

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  eureka-server:
    build: ./eureka-server
    ports:
      - "8761:8761"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8761/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  user-service:
    build: ./user-service
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_APPLICATION_NAME=user-service
      - EUREKA_CLIENT_SERVICEURL_DEFAULTZONE=http://eureka-server:8761/eureka/
    depends_on:
      - eureka-server
      
  order-service:
    build: ./order-service
    ports:
      - "8082:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_APPLICATION_NAME=order-service
      - EUREKA_CLIENT_SERVICEURL_DEFAULTZONE=http://eureka-server:8761/eureka/
    depends_on:
      - eureka-server
      - user-service
```

### Service Startup Order

When using service discovery, the order of service startup becomes important. Services should ideally start after the discovery server is available. In Docker Compose, use `depends_on` with health checks.

## Troubleshooting Service Discovery

### Common Issues and Solutions

1. **Services Not Registering**:
   - Verify network connectivity to discovery server
   - Check correct configuration of service URLs
   - Validate service name and instance ID

2. **Services Cannot Discover Each Other**:
   - Ensure client configs have correct discovery server URL
   - Check network policies or security groups
   - Verify cache TTL settings

3. **Load Balancing Issues**:
   - Validate correct annotation of clients with `@LoadBalanced`
   - Check service instance health
   - Review load balancer configuration

Diagnostic Commands:

```bash
# Check Eureka server status
curl http://localhost:8761/eureka/apps

# Check specific service registration
curl http://localhost:8761/eureka/apps/USER-SERVICE

# Check service instance health
curl http://localhost:8081/actuator/health
```

## References

- [Service Discovery in a Microservices Architecture](https://www.nginx.com/blog/service-discovery-in-a-microservices-architecture/)
- [Spring Cloud Netflix Documentation](https://cloud.spring.io/spring-cloud-netflix/reference/html/)
- [Service Discovery: Eureka Clients](https://cloud.spring.io/spring-cloud-netflix/multi/multi__service_discovery_eureka_clients.html)
- [Spring Cloud Kubernetes Documentation](https://spring.io/projects/spring-cloud-kubernetes) 