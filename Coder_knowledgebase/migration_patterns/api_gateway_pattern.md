# API Gateway Pattern

## Overview

The API Gateway pattern provides a single entry point for clients to interact with a microservices architecture. It acts as a reverse proxy, routing requests to appropriate services, and can handle cross-cutting concerns like authentication, monitoring, and rate limiting.

In the context of microservice migration, API gateways are essential for implementing the Strangler Fig pattern, enabling gradual redirection of requests from the monolith to new microservices.

## Core Capabilities

### 1. Request Routing

Routes client requests to the appropriate backend service based on the request path, method, or other attributes.

```
Client → API Gateway → Service A/B/C
```

### 2. API Composition

Combines responses from multiple services into a single response for the client.

```
           ┌─→ Service A ─→┐
           │               │
Client → Gateway           → Response to Client
           │               │
           └─→ Service B ─→┘
```

### 3. Protocol Translation

Translates between different communication protocols (e.g., HTTP to gRPC, AMQP, or WebSockets).

### 4. Cross-Cutting Concerns

Handles common functionality that applies across services:
- Authentication and authorization
- Rate limiting and throttling
- Caching
- Logging and monitoring
- Request/response transformation
- Circuit breaking
- CORS support

## Implementation Options

### Spring Cloud Gateway

A popular API Gateway for Spring Boot applications built on top of Project Reactor, Spring WebFlux, and Spring Boot.

#### Basic Configuration

```yaml
# application.yml
spring:
  cloud:
    gateway:
      routes:
        - id: customer-service
          uri: lb://customer-service
          predicates:
            - Path=/api/customers/**
          filters:
            - StripPrefix=1
            
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
            
        - id: monolith-fallback
          uri: lb://monolith-service
          predicates:
            - Path=/**
```

#### Java Configuration

```java
@Configuration
public class GatewayConfig {
    
    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("customer-service", r -> r
                .path("/api/customers/**")
                .filters(f -> f.stripPrefix(1))
                .uri("lb://customer-service"))
            .route("order-service", r -> r
                .path("/api/orders/**")
                .filters(f -> f.stripPrefix(1))
                .uri("lb://order-service"))
            .route("monolith-fallback", r -> r
                .path("/**")
                .uri("lb://monolith-service"))
            .build();
    }
}
```

### Netflix Zuul (Legacy)

An older but still widely used API Gateway option, part of the Netflix OSS suite.

```java
@SpringBootApplication
@EnableZuulProxy
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
```

```yaml
# application.yml
zuul:
  routes:
    customers:
      path: /api/customers/**
      serviceId: customer-service
      stripPrefix: false
    orders:
      path: /api/orders/**
      serviceId: order-service
      stripPrefix: false
    monolith:
      path: /**
      serviceId: monolith-service
```

### Other Options

- **Kong**: Open-source API gateway built on NGINX
- **NGINX**: Can be configured as an API gateway
- **AWS API Gateway**: Managed service from Amazon
- **Azure API Management**: Microsoft's managed API gateway solution
- **Traefik**: Modern HTTP reverse proxy and load balancer
- **Envoy**: Cloud-native high-performance edge/service proxy

## Implementing API Gateway for Monolith Migration

When using an API Gateway for migration, there are several key patterns to consider:

### 1. Strangler Fig Pattern Implementation

```
                      ┌─→ Microservice A (New)
                      │
Clients → API Gateway ─→ Microservice B (New)
                      │
                      └─→ Monolith (Legacy)
```

The API Gateway gradually routes more traffic to new microservices as they are developed, eventually "strangling" the monolith.

#### Example Configuration (Spring Cloud Gateway)

```yaml
spring:
  cloud:
    gateway:
      routes:
        # New microservice handling customer functionality
        - id: customer-service
          uri: lb://customer-service
          predicates:
            - Path=/api/customers/**
          filters:
            - name: CircuitBreaker
              args:
                name: customerServiceCircuitBreaker
                fallbackUri: forward:/monolith-fallback/api/customers
        
        # Monolith still handling other functionality
        - id: monolith-service
          uri: lb://monolith-service
          predicates:
            - Path=/**
```

### 2. Feature Flagging and Canary Releases

API gateways can implement feature flags to control which users are routed to new microservices:

```java
@Component
public class CustomRoutePredicateFactory extends AbstractRoutePredicateFactory<CustomRoutePredicateFactory.Config> {
    
    private final FeatureFlagService featureFlagService;
    
    // Constructor and config class omitted for brevity
    
    @Override
    public Predicate<ServerWebExchange> apply(Config config) {
        return exchange -> {
            // Extract user info from request
            String userId = extractUserIdFromRequest(exchange);
            
            // Check if user should be routed to new service
            return featureFlagService.isFeatureEnabledForUser(
                "use-new-customer-service", userId);
        };
    }
}
```

### 3. A/B Testing Between Monolith and Microservices

```java
@Component
public class AbTestingFilter implements GlobalFilter {
    
    private final AbTestingService abTestingService;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Get the current route
        Route route = exchange.getAttribute(ServerWebExchangeUtils.GATEWAY_ROUTE_ATTR);
        
        // Check if this request should be part of A/B test
        if (route.getId().equals("customer-service") && 
            abTestingService.shouldRouteToLegacy()) {
            
            // Create a new exchange pointing to monolith
            ServerWebExchange newExchange = createExchangeForMonolith(exchange);
            return chain.filter(newExchange);
        }
        
        return chain.filter(exchange);
    }
}
```

### 4. API Transformation for Microservices

During migration, you may need to transform requests/responses between the old and new formats:

```java
@Component
public class ApiTransformationFilter implements GatewayFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Transform request before sending to service
        ServerWebExchange modifiedExchange = transformRequest(exchange);
        
        return chain.filter(modifiedExchange)
            .then(Mono.fromRunnable(() -> {
                // Transform response before returning to client
                transformResponse(exchange);
            }));
    }
    
    private ServerWebExchange transformRequest(ServerWebExchange exchange) {
        // Transform request payload or headers as needed
        // For example, convert between API versions or formats
        return exchange.mutate()
            // Transformation logic here
            .build();
    }
    
    private void transformResponse(ServerWebExchange exchange) {
        // Transform response payload or headers as needed
    }
    
    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 100;
    }
}
```

### 5. Handling Authentication and Authorization

API Gateways often centralize authentication for all services:

```java
@Component
public class AuthenticationFilter implements GatewayFilter, Ordered {
    
    private final AuthenticationService authService;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Extract token from request
        String token = extractToken(exchange.getRequest());
        
        if (token == null) {
            return onError(exchange, "No authorization token", HttpStatus.UNAUTHORIZED);
        }
        
        // Validate token
        return authService.validateToken(token)
            .flatMap(claims -> {
                // Add user info to headers for downstream services
                ServerHttpRequest request = exchange.getRequest().mutate()
                    .header("X-User-Id", claims.getSubject())
                    .header("X-User-Role", claims.get("role").toString())
                    .build();
                
                return chain.filter(exchange.mutate().request(request).build());
            })
            .onErrorResume(error -> 
                onError(exchange, "Invalid token", HttpStatus.UNAUTHORIZED));
    }
    
    // Helper methods omitted for brevity
    
    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }
}
```

## Deployment Strategies

### 1. Single Gateway

A single API Gateway handles all traffic:

```
Clients → API Gateway → Microservices
```

**Pros:**
- Simple architecture
- Centralized control
- Easier to manage

**Cons:**
- Single point of failure
- Potential bottleneck
- May become complex over time

### 2. Gateway per Client Type

Different gateways for different client types (web, mobile, IoT, etc.):

```
Web Clients → Web API Gateway → Microservices
Mobile Clients → Mobile API Gateway → Microservices
```

**Pros:**
- Optimized for specific client needs
- Better separation of concerns
- Reduced complexity per gateway

**Cons:**
- More components to manage
- Potential duplication of functionality

### 3. Backend for Frontend (BFF) Pattern

Dedicated gateways for each frontend application:

```
Web App → Web BFF → Microservices
Mobile App → Mobile BFF → Microservices
```

**Pros:**
- Tailored to each frontend's needs
- Team alignment (frontend team owns the BFF)
- Reduced data transfer

**Cons:**
- More infrastructure to maintain
- Potential code duplication

## Best Practices

### 1. Design for Resilience

- Implement circuit breakers for failing services
- Configure reasonable timeouts
- Provide fallback responses
- Use bulkheads to isolate failures

```java
// Spring Cloud Gateway circuit breaker example
.route("customer-service", r -> r
    .path("/api/customers/**")
    .filters(f -> f
        .circuitBreaker(c -> c
            .setName("customerServiceCircuitBreaker")
            .setFallbackUri("forward:/fallback/customers")))
    .uri("lb://customer-service"))
```

### 2. Consider Performance and Scalability

- Keep gateway logic lightweight
- Avoid blocking operations
- Consider caching frequently accessed data
- Scale gateways horizontally
- Monitor performance metrics

### 3. Versioning Strategy

- Implement a consistent API versioning strategy
- Support multiple versions during migration
- Consider using headers, URL paths, or query parameters for versioning

```
/api/v1/customers → Monolith
/api/v2/customers → Microservice
```

### 4. Security Considerations

- Implement rate limiting to prevent abuse
- Use HTTPS for all communications
- Consider using OAuth2 for authentication
- Validate and sanitize all inputs
- Implement proper logging for security events

```yaml
spring:
  cloud:
    gateway:
      default-filters:
        - name: RequestRateLimiter
          args:
            redis-rate-limiter.replenishRate: 10
            redis-rate-limiter.burstCapacity: 20
```

### 5. Monitoring and Observability

- Implement comprehensive logging
- Add request tracing (e.g., with Spring Cloud Sleuth or OpenTelemetry)
- Monitor gateway health and performance
- Set up alerts for failures
- Create dashboards for key metrics

## Common Challenges During Migration

### 1. Service Discovery Integration

Ensure the gateway can discover both the monolith and new microservices:

```yaml
spring:
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true
```

### 2. Authentication Differences

Handle authentication differences between monolith and microservices:

```java
@Component
public class AuthenticationBridgeFilter implements GatewayFilter {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String targetService = getTargetService(exchange);
        
        if ("monolith-service".equals(targetService)) {
            // Transform modern token to legacy session cookie
            return transformToLegacyAuth(exchange, chain);
        } else {
            // Use modern token-based auth
            return chain.filter(exchange);
        }
    }
    
    // Helper methods omitted for brevity
}
```

### 3. Transaction Boundaries

Be aware of transaction boundaries when splitting functionalities:

```java
// Original monolithic transaction
@Transactional
public void processPurchase(Long customerId, Long productId) {
    Customer customer = customerRepository.findById(customerId).orElseThrow();
    Product product = productRepository.findById(productId).orElseThrow();
    
    // Update inventory
    product.decreaseStock(1);
    productRepository.save(product);
    
    // Create order
    Order order = new Order(customer, product);
    orderRepository.save(order);
    
    // Process payment
    paymentService.charge(customer, product.getPrice());
}

// After split - need coordination between services
// API Gateway might need to orchestrate this as a saga
```

### 4. Data Consistency

Handle data that might exist in both the monolith and microservices during migration:

```java
@Component
public class DataConsistencyFilter implements GatewayFilter {
    
    private final DataSyncService dataSyncService;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        return chain.filter(exchange)
            .then(Mono.fromRunnable(() -> {
                // After request is processed, check if we need to sync data
                if (isWriteOperation(exchange)) {
                    String resource = extractResourceFromPath(exchange);
                    dataSyncService.scheduleSync(resource);
                }
            }));
    }
    
    // Helper methods omitted for brevity
}
```

## References

- [Securing Services with Spring Cloud Gateway](https://spring.io/blog/2019/08/16/securing-services-with-spring-cloud-gateway)
- [Getting Started with Spring Cloud Gateway](https://spring.io/guides/gs/gateway/)
- [Pattern: API Gateway](https://microservices.io/patterns/apigateway.html)
- [Backend for Frontend (BFF) Pattern](https://samnewman.io/patterns/architectural/bff/) 