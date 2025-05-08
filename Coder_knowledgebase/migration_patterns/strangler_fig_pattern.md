# Strangler Fig Pattern

## Overview

The Strangler Fig Pattern (also known as the Strangler Application Pattern) is an incremental approach to migrating a monolithic application to microservices. The pattern gets its name from strangler fig vines that grow around trees, eventually replacing them.

![Strangler Fig Visual](https://martinfowler.com/bliki/images/strangler/strangler.png)

## How It Works

1. Create a facade or proxy in front of the monolith
2. Gradually build new microservices alongside the monolith
3. Redirect specific functionality from the monolith to these new microservices
4. Eventually "strangle" (replace) the entire monolith

## Implementation Phases

### Phase 1: Setup Routing Layer

First, implement a routing mechanism (proxy, API Gateway, or load balancer) that sits in front of the monolith. All client requests go through this layer.

```
[Clients] → [Routing Layer] → [Monolith]
```

### Phase 2: Create First Microservice

Identify a bounded context or feature with minimal dependencies to extract first:
- Implement the functionality in a new microservice
- Ensure it has its own database if needed
- Deploy the microservice independently

```
                         ┌─→ [Monolith] (most functions)
[Clients] → [Routing Layer]
                         └─→ [Microservice 1] (extracted function)
```

### Phase 3: Gradually Replace Functionality

Continue the process iteratively:
- Extract a new bounded context
- Implement it as a microservice
- Update the routing layer to direct traffic to the new service
- Decommission that part of the monolith

```
                         ┌─→ [Monolith] (diminishing)
                         │
[Clients] → [Routing Layer]─→ [Microservice 1]
                         │
                         └─→ [Microservice 2]
                             ...
                             [Microservice n]
```

### Phase 4: Complete Migration

Eventually, the monolith is completely replaced by microservices:

```
                         ┌─→ [Microservice 1]
                         │
                         ├─→ [Microservice 2]
[Clients] → [Routing Layer]
                         ├─→ [Microservice 3]
                         │   ...
                         └─→ [Microservice n]
```

## Implementation in Spring Boot Applications

### 1. API Gateway Implementation

For Spring Boot applications, Spring Cloud Gateway or Netflix Zuul can be used as the routing layer:

```java
@SpringBootApplication
@EnableZuulProxy
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
```

Configuration in application.yml:

```yaml
zuul:
  routes:
    monolith:
      path: /**
      url: http://monolith-service:8080
    user-service:
      path: /api/users/**
      url: http://user-service:8081
    order-service:
      path: /api/orders/**
      url: http://order-service:8082
```

### 2. Feature Toggle Approach

Use feature toggles to gradually transition from monolith to microservices:

```java
@Service
public class OrderService {
    
    @Autowired
    private FeatureToggleService featureService;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Autowired
    private LegacyOrderService legacyOrderService;
    
    public Order processOrder(Order order) {
        if (featureService.isEnabled("use-order-microservice")) {
            // Call new microservice
            return restTemplate.postForObject(
                "http://order-service/api/orders", order, Order.class);
        } else {
            // Use legacy implementation
            return legacyOrderService.processOrder(order);
        }
    }
}
```

### 3. Database Strangling

For database migration, use one of these strategies:

1. **Database Views**: Create views in the monolith database that the microservice can access
2. **Change Data Capture**: Use tools like Debezium to capture changes in the monolith database
3. **Dual Writes**: Temporarily write to both the monolith database and the microservice database
4. **Data Migration Service**: Create a service to sync data between monolith and microservices

## Advantages of the Strangler Fig Pattern

1. **Reduced Risk**: Incremental changes are less risky than a complete rewrite
2. **Early Value Delivery**: New features can be added to microservices while migration happens
3. **Easier Rollback**: Individual services can be reverted to the monolith if issues occur
4. **Continuous Deployment**: New microservices can adopt modern CI/CD practices immediately
5. **Progressive Learning**: Team gradually adapts to microservice development practices

## Challenges and Mitigations

| Challenge | Mitigation |
|-----------|------------|
| Complex routing logic | Use mature API Gateway products; adopt standard routing patterns |
| Shared database tables | Implement read-only replicas first, then migrate writes |
| Transaction boundaries | Use saga pattern or eventual consistency for cross-service operations |
| Authentication/authorization | Implement a shared auth service or token-based auth early |
| Testing complexity | Develop comprehensive integration tests spanning monolith and microservices |

## Case Studies

1. **Amazon**: Migrated from a monolithic architecture to microservices over several years
2. **Netflix**: Famous for their migration from monolith to cloud-based microservices
3. **SoundCloud**: Used the Strangler Pattern to gradually move to microservices
4. **Guardian**: Migrated their monolithic content management system incrementally

## Best Practices

1. Start with well-bounded, less critical functionalities
2. Establish robust monitoring before beginning the migration
3. Create a clear service interface contract before extraction
4. Consider using an anti-corruption layer between old and new systems
5. Keep the team focused on one or two extractions at a time
6. Celebrate small wins to maintain momentum

## References

- Martin Fowler's article: [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html)
- Microsoft's guide: [Strangler Fig pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)
- Book: "Monolith to Microservices" by Sam Newman 