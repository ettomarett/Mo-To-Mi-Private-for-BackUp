# Database Per Service Pattern

## Overview

The Database Per Service pattern is a fundamental approach in microservices architecture where each microservice owns and manages its own database. This pattern enforces service autonomy and decouples services from each other at the data layer.

## Principles

1. **Exclusive Ownership**: Each service exclusively owns its data and database schema
2. **No Direct Database Sharing**: Services never directly access each other's databases
3. **API-Based Data Access**: Data from other services is accessed only via their APIs
4. **Independent Schema Evolution**: Each service can evolve its schema independently
5. **Technology Flexibility**: Different services can use different database technologies

## Implementation

### Basic Structure

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Service A     │     │   Service B     │     │   Service C     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Database A     │     │  Database B     │     │  Database C     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Spring Boot Implementation Examples

#### 1. Service Configuration

Each service has its own `application.yml` with database configuration:

**User Service:**
```yaml
spring:
  datasource:
    url: jdbc:mysql://user-db:3306/userdb
    username: user_service
    password: password
  jpa:
    hibernate:
      ddl-auto: update
```

**Order Service:**
```yaml
spring:
  datasource:
    url: jdbc:postgresql://order-db:5432/orderdb
    username: order_service
    password: password
  jpa:
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
```

#### 2. Entity Definitions

Each service defines only its own domain entities:

**User Service:**
```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String username;
    private String email;
    // Other user fields
}
```

**Order Service:**
```java
@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private Long userId;  // Just the ID, not the whole User entity
    private LocalDateTime orderDate;
    // Other order fields
}
```

## Data Duplication and Synchronization

### Common Approaches

1. **Event-Based Synchronization**: Services publish events when their data changes

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private EventPublisher eventPublisher;
    
    @Transactional
    public User updateUser(User user) {
        User savedUser = userRepository.save(user);
        
        // Publish event for other services that might need user data
        eventPublisher.publish(new UserUpdatedEvent(savedUser.getId(), 
                                                   savedUser.getUsername(),
                                                   savedUser.getEmail()));
        
        return savedUser;
    }
}
```

2. **Data Replication**: Maintaining read-only copies of data needed by multiple services

```java
@Service
public class OrderService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private UserInfoRepository userInfoRepository; // Contains only necessary user data
    
    @EventListener
    public void handleUserUpdatedEvent(UserUpdatedEvent event) {
        UserInfo userInfo = userInfoRepository.findById(event.getUserId())
            .orElse(new UserInfo(event.getUserId()));
        
        userInfo.setUsername(event.getUsername());
        userInfo.setEmail(event.getEmail());
        
        userInfoRepository.save(userInfo);
    }
}
```

3. **API Composition**: Aggregating data from multiple services on-demand

```java
@RestController
@RequestMapping("/api/order-details")
public class OrderDetailsController {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @GetMapping("/{orderId}")
    public OrderDetailsDTO getOrderWithUserDetails(@PathVariable Long orderId) {
        // Get order from this service's database
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new NotFoundException("Order not found"));
        
        // Get user details from User service
        UserDTO user = restTemplate.getForObject(
            "http://user-service/api/users/" + order.getUserId(),
            UserDTO.class);
        
        // Combine the data
        return new OrderDetailsDTO(order, user);
    }
}
```

## Advantages

1. **Loose Coupling**: Services are decoupled at the data layer
2. **Independent Scaling**: Each database can be scaled according to its service's needs
3. **Technology Freedom**: Teams can choose the best database type for their service
4. **Simplified Deployment**: No shared database means easier deployments
5. **Improved Fault Isolation**: Database failures impact only their respective services

## Challenges

1. **Distributed Transactions**: Maintaining consistency across multiple databases is complex
2. **Data Duplication**: Some data may need to be duplicated across services
3. **Eventual Consistency**: Services may need to deal with temporarily inconsistent data
4. **Query Complexity**: Queries that span multiple services require careful design
5. **Increased Operational Complexity**: Managing multiple databases increases ops overhead

## Mitigation Strategies

### 1. For Distributed Transactions

- Implement the Saga pattern for distributed transactions
- Use event sourcing to track state changes
- Consider the CQRS pattern for complex read/write operations

### 2. For Data Duplication

- Keep duplicated data to a minimum
- Implement robust event-based synchronization
- Consider using a shared reference data service for common data

### 3. For Query Complexity

- Implement API composition patterns
- Consider CQRS with specialized read models
- Use GraphQL for complex client data needs

## Migration Path from Monolith

1. **Analyze Data Access Patterns**: Identify how the monolith accesses the database
2. **Identify Data Boundaries**: Group tables by domain and access patterns
3. **Create Shadow Databases**: Set up new databases alongside the monolith database
4. **Implement Dual-Write**: Write to both the monolith and service database temporarily
5. **Migrate Reads**: Switch services to read from their own databases
6. **Migrate Writes**: Switch writes to the new databases and remove dual-writes
7. **Decommission Monolith DB Access**: Remove the service's code from the monolith

## Best Practices

1. Keep each database focused on a single business capability
2. Design service APIs to minimize cross-service data access
3. Use data synchronization patterns for shared data
4. Implement monitoring for data consistency issues
5. Document data ownership clearly
6. Consider data lifecycle and archiving strategies per service

## References

- Book: "Building Microservices" by Sam Newman
- Pattern: [Database per Service](https://microservices.io/patterns/data/database-per-service.html) by Chris Richardson
- Book: "Microservices Patterns" by Chris Richardson 