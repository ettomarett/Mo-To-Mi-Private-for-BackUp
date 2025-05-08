# Common Patterns in Spring Boot Monoliths

This document describes frequent patterns used in Spring Boot monoliths and how they relate to microservice migration.

## Modular Monolith Patterns

### Spring Modulith

Spring Modulith is a relatively new approach from the Spring team that helps build better-structured monolithic applications. It enforces module boundaries and prepares applications for potential microservice extraction later.

```java
@org.springframework.modulith.Modulith
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

**Key Features:**
- **Module Organization**: Code is organized into logical modules reflecting business capabilities
- **Enforced Boundaries**: Inter-module dependencies are explicitly managed and documented
- **Event-Based Communication**: Encourages using events for cross-module interaction
- **Module-Level Testing**: Supports testing modules in isolation
- **Documentation Tools**: Automatically generates module structure documentation

**Example Structure:**
```
com.example.application
├── Application.java (@Modulith)
├── order/
│   ├── Order.java
│   ├── OrderController.java
│   ├── OrderRepository.java
│   └── OrderService.java
├── customer/
│   ├── Customer.java
│   ├── CustomerController.java
│   ├── CustomerRepository.java
│   └── CustomerService.java
└── payment/
    ├── Payment.java
    ├── PaymentController.java
    ├── PaymentRepository.java
    └── PaymentService.java
```

**Benefits for Migration:**
- Modules can be migrated to microservices one at a time
- Module boundaries are already established
- Event-based communication simplifies extraction
- Independent testing of modules validates extraction readiness

### Hexagonal Architecture (Ports and Adapters)

Hexagonal Architecture is a pattern that separates business logic from external concerns, making it easier to migrate to microservices.

```java
// Domain (core business logic)
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentPort paymentPort;
    
    public OrderService(OrderRepository orderRepository, PaymentPort paymentPort) {
        this.orderRepository = orderRepository;
        this.paymentPort = paymentPort;
    }
    
    public Order createOrder(Order order) {
        // Business logic
        paymentPort.processPayment(order.getPaymentDetails());
        return orderRepository.save(order);
    }
}

// Port (interface to external system)
public interface PaymentPort {
    PaymentResult processPayment(PaymentDetails details);
}

// Adapter (implementation that connects to external system)
@Service
public class PaymentAdapter implements PaymentPort {
    private final PaymentClient paymentClient;
    
    @Override
    public PaymentResult processPayment(PaymentDetails details) {
        return paymentClient.processPayment(details);
    }
}
```

**Key Elements:**
- **Domain**: Core business logic, independent of external systems
- **Ports**: Interfaces that define how the domain interacts with the outside world
- **Adapters**: Implementations of ports that connect to external systems
- **Dependency Rule**: Dependencies always point inward toward the domain

**Benefits for Migration:**
- Business logic is already isolated
- External dependencies are well-defined through ports
- Adapters can be replaced with microservice clients without changing domain code
- Testing is simplified with mockable ports

## Data Access Patterns

### Repository Pattern

The Repository pattern abstracts data access logic, providing a collection-like interface to domain objects.

```java
// Standard Spring Data JPA Repository
public interface CustomerRepository extends JpaRepository<Customer, Long> {
    Optional<Customer> findByEmail(String email);
    List<Customer> findByLastName(String lastName);
}

// Custom Repository Implementation
@Repository
public class OrderRepositoryImpl implements OrderRepositoryCustom {
    @PersistenceContext
    private EntityManager entityManager;
    
    @Override
    public List<Order> findOrdersWithItems() {
        return entityManager.createQuery(
            "SELECT o FROM Order o JOIN FETCH o.items", Order.class).getResultList();
    }
}
```

**Migration Considerations:**
- Each microservice should have its own repositories
- Queries that span multiple entities might need decomposition for microservices
- Consider CQRS (Command Query Responsibility Segregation) for complex query scenarios

### DTO Pattern

Data Transfer Objects separate domain entities from API representations, which is essential for microservices.

```java
// Entity (internal representation)
@Entity
public class Customer {
    @Id
    private Long id;
    private String firstName;
    private String lastName;
    private String email;
    private String passwordHash; // Sensitive data
    private LocalDateTime createdAt;
    // Other fields...
}

// DTO (external representation)
public class CustomerDTO {
    private Long id;
    private String firstName;
    private String lastName;
    private String email;
    // No sensitive data
}

// Mapper
@Component
public class CustomerMapper {
    public CustomerDTO toDTO(Customer customer) {
        return new CustomerDTO(
            customer.getId(),
            customer.getFirstName(),
            customer.getLastName(),
            customer.getEmail()
        );
    }
}
```

**Benefits for Migration:**
- Decouples internal representations from external APIs
- Allows evolution of entities without breaking API contracts
- Enables different views of the same data for different services
- Prevents leaking sensitive information

## Communication Patterns

### Event-Driven Architecture

Event-driven architecture uses events for communication between components, which translates well to microservices.

```java
// Event
public class OrderCreatedEvent {
    private final Long orderId;
    private final Long customerId;
    private final BigDecimal amount;
    
    // Constructor, getters
}

// Publisher
@Service
public class OrderService {
    private final ApplicationEventPublisher eventPublisher;
    
    @Transactional
    public Order createOrder(Order order) {
        Order savedOrder = orderRepository.save(order);
        
        // Publish event
        eventPublisher.publishEvent(new OrderCreatedEvent(
            savedOrder.getId(),
            savedOrder.getCustomerId(),
            savedOrder.getTotalAmount()
        ));
        
        return savedOrder;
    }
}

// Listener
@Service
public class InventoryService {
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // Process inventory updates
    }
}
```

**Migration Advantages:**
- Naturally translates to microservice message-based communication
- Reduces tight coupling between components
- Enables asynchronous processing
- Simplifies eventual consistency patterns

### Circuit Breaker Pattern

Circuit breakers prevent cascading failures when services depend on each other.

```java
@Service
public class ProductService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @HystrixCommand(fallbackMethod = "getDefaultProduct")
    public Product getProduct(Long id) {
        return restTemplate.getForObject("/api/products/" + id, Product.class);
    }
    
    public Product getDefaultProduct(Long id) {
        return new Product(id, "Default Product", BigDecimal.ZERO);
    }
}
```

**Implementations:**
- Spring Cloud Circuit Breaker
- Resilience4j
- Hystrix (legacy)

**Benefits:**
- Fail fast when dependencies are unavailable
- Provide fallback behavior
- Prevent resource exhaustion
- Essential for microservice resilience

## Configuration Patterns

### Externalized Configuration

Spring Boot's externalized configuration makes environment-specific settings flexible.

```properties
# application.properties
spring.datasource.url=${DATABASE_URL:jdbc:mysql://localhost/myapp}
spring.datasource.username=${DATABASE_USER:root}
spring.datasource.password=${DATABASE_PASSWORD:password}
custom.service.url=${SERVICE_URL:http://localhost:8081/api}
```

**Configuration Sources (in order of precedence):**
1. Command-line arguments
2. JVM system properties
3. OS environment variables
4. Properties files (application.properties/yml)

**Migration Benefits:**
- Each microservice can have its own configuration
- Environment-specific settings are easily managed
- Configuration can be centralized (Spring Cloud Config)
- Secrets can be managed separately

### Feature Toggles

Feature toggles allow enabling/disabling features dynamically.

```java
@Component
public class FeatureToggleService {
    
    @Value("${features.new-payment-system:false}")
    private boolean newPaymentSystemEnabled;
    
    @Value("${features.recommendation-engine:false}")
    private boolean recommendationEngineEnabled;
    
    public boolean isNewPaymentSystemEnabled() {
        return newPaymentSystemEnabled;
    }
    
    public boolean isRecommendationEngineEnabled() {
        return recommendationEngineEnabled;
    }
}

@Service
public class PaymentService {
    
    @Autowired
    private FeatureToggleService featureToggleService;
    
    @Autowired
    private OldPaymentProcessor oldProcessor;
    
    @Autowired
    private NewPaymentProcessor newProcessor;
    
    public PaymentResult processPayment(PaymentDetails details) {
        if (featureToggleService.isNewPaymentSystemEnabled()) {
            return newProcessor.process(details);
        } else {
            return oldProcessor.process(details);
        }
    }
}
```

**Migration Benefits:**
- Can gradually transition traffic to microservices
- Allows testing new implementations with limited exposure
- Facilitates A/B testing of monolith vs. microservice functionality
- Enables emergency rollback if issues occur

## References

- [Introducing Spring Modulith](https://spring.io/blog/2022/10/21/introducing-spring-modulith)
- [Creating a Multi-Module Monolith using Spring Modulith](https://ishansoninitj.medium.com/creating-a-multi-module-monolith-using-spring-modulith-f83053736762)
- [How to build a modular monolith with Hexagonal Architecture](https://blog.artisivf.com/2024/08/29/how-to-build-a-modular-monolith-with-hexagonal-architecture/)
- [Externalized Configuration in Spring Boot](https://docs.spring.io/spring-boot/reference/features/external-config.html) 