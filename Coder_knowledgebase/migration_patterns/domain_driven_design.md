# Domain-Driven Design for Microservices Migration

## Overview

Domain-Driven Design (DDD) is an approach to software development that focuses on building a deep understanding of the problem domain and using this understanding to guide the software design. When migrating from monoliths to microservices, DDD provides a valuable framework for identifying service boundaries based on business domains.

## Core Concepts

### 1. Ubiquitous Language

A shared language between developers and domain experts, used consistently in code, documentation, and conversations.

**Example:** In an e-commerce system:
- Use "Order" not "Purchase" or "Transaction" consistently
- Use "Customer" not "User" or "Buyer" consistently
- Use "Product" not "Item" or "Merchandise" consistently

### 2. Bounded Contexts

A boundary within which a particular domain model applies. Different parts of a system may have different models for the same concept.

**Example:** In an e-commerce system:
- **Product in Catalog Context**: Has description, images, categories
- **Product in Inventory Context**: Has stock level, warehouse location
- **Product in Order Context**: Has price, quantity, discounts

### 3. Context Mapping

The explicit mapping between bounded contexts, defining how they relate and communicate.

**Types of Context Relationships:**
- **Partnership**: Two contexts developed in close cooperation
- **Shared Kernel**: Common subset of the domain model shared by multiple contexts
- **Customer-Supplier**: Upstream/Downstream relationship with aligned planning
- **Conformist**: Downstream team conforms to upstream model
- **Anticorruption Layer**: Isolation layer that translates between contexts
- **Open Host Service**: Protocol to provide access to a subsystem
- **Separate Ways**: No connection between contexts
- **Published Language**: Shared, well-documented format for data exchange

### 4. Strategic Design

The process of identifying bounded contexts and their relationships within a complex domain.

### 5. Tactical Design Patterns

Specific patterns within a bounded context:

- **Entities**: Objects with identity and lifecycle (e.g., Customer)
- **Value Objects**: Immutable objects defined by their attributes (e.g., Address)
- **Aggregates**: Clusters of entities and value objects with clear boundaries
- **Domain Events**: Record of something significant that happened in the domain
- **Repositories**: Provide access to aggregates
- **Services**: Stateless operations that don't belong to entities or value objects
- **Factories**: Encapsulate complex object creation

## Application to Microservices Migration

### Identifying Service Boundaries

The most valuable aspect of DDD for microservices migration is identifying service boundaries. A well-designed microservice should:

1. **Align with a Bounded Context**: Each microservice should represent a single bounded context
2. **Have Its Own Domain Model**: Independent data model reflecting domain concepts
3. **Own Its Data**: Private database or schema that other services don't access directly
4. **Implement a Complete Business Capability**: Not just a technical function

**Example of Identifying Bounded Contexts:**

```
E-commerce System Bounded Contexts:
- Customer Management (accounts, preferences, addresses)
- Product Catalog (products, categories, search)
- Inventory Management (stock levels, warehouses)
- Order Processing (orders, line items, payments)
- Shipping & Fulfillment (shipping methods, tracking)
- Reviews & Ratings (customer reviews, ratings)
```

### Strategic Design in Spring Boot Applications

Spring Boot applications often have a structure that doesn't reflect business domains:

**Traditional Structure (Not DDD-aligned):**
```
com.example.ecommerce
  |- controller/
  |    |- CustomerController
  |    |- ProductController
  |    |- OrderController
  |
  |- service/
  |    |- CustomerService
  |    |- ProductService 
  |    |- OrderService
  |
  |- repository/
  |    |- CustomerRepository
  |    |- ProductRepository
  |    |- OrderRepository
  |
  |- model/
       |- Customer
       |- Product
       |- Order
```

**DDD-Aligned Structure:**
```
com.example.ecommerce
  |- customer/
  |    |- api/
  |    |    |- CustomerController
  |    |    |- CustomerDTO
  |    |
  |    |- domain/
  |    |    |- Customer
  |    |    |- Address
  |    |    |- CustomerService
  |    |
  |    |- infrastructure/
  |         |- CustomerRepository
  |         |- CustomerEventPublisher
  |
  |- product/
  |    |- api/
  |    |- domain/
  |    |- infrastructure/
  |
  |- order/
       |- api/
       |- domain/
       |- infrastructure/
```

### Implementing DDD in Spring Boot

#### 1. Entity Example

```java
@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue
    private OrderId id;  // Using a Value Object for ID
    
    @Embedded
    private CustomerId customerId;  // Reference to another Aggregate Root
    
    @ElementCollection
    private Set<OrderLineItem> items = new HashSet<>();
    
    @Enumerated(EnumType.STRING)
    private OrderStatus status;
    
    @Embedded
    private Money totalAmount;
    
    @Embedded
    private ShippingAddress shippingAddress;
    
    // Domain logic (not anemic!)
    public void addItem(Product product, int quantity) {
        OrderLineItem item = new OrderLineItem(product.getId(), quantity, product.getPrice());
        items.add(item);
        recalculateTotal();
    }
    
    private void recalculateTotal() {
        this.totalAmount = items.stream()
            .map(OrderLineItem::getLineTotal)
            .reduce(Money.ZERO, Money::add);
    }
    
    public void submit() {
        if (items.isEmpty()) {
            throw new OrderDomainException("Cannot submit an empty order");
        }
        this.status = OrderStatus.SUBMITTED;
        DomainEvents.publish(new OrderSubmittedEvent(this));
    }
    
    // More domain logic...
}
```

#### 2. Value Object Example

```java
@Embeddable
@Value // Lombok annotation to make it immutable
public class Money {
    public static final Money ZERO = new Money(BigDecimal.ZERO);
    
    @Column(name = "amount")
    private final BigDecimal amount;
    
    @Column(name = "currency")
    private final String currencyCode;
    
    // Constructor with validation
    public Money(BigDecimal amount, String currencyCode) {
        if (amount == null) throw new IllegalArgumentException("Amount cannot be null");
        if (currencyCode == null) throw new IllegalArgumentException("Currency cannot be null");
        
        this.amount = amount;
        this.currencyCode = currencyCode;
    }
    
    public Money add(Money other) {
        if (!this.currencyCode.equals(other.currencyCode)) {
            throw new IllegalArgumentException("Cannot add different currencies");
        }
        return new Money(this.amount.add(other.amount), this.currencyCode);
    }
    
    // More domain methods...
}
```

#### 3. Repository Example

```java
public interface OrderRepository extends JpaRepository<Order, OrderId> {
    List<Order> findByCustomerId(CustomerId customerId);
    
    @Query("SELECT o FROM Order o WHERE o.status = :status AND o.createdAt < :date")
    List<Order> findStaleOrders(@Param("status") OrderStatus status, @Param("date") LocalDateTime date);
}
```

#### 4. Domain Service Example

```java
@Service
@Transactional
public class OrderService {
    private final OrderRepository orderRepository;
    private final CustomerRepository customerRepository;
    private final ProductRepository productRepository;
    private final DomainEventPublisher eventPublisher;
    
    public OrderService(OrderRepository orderRepository, 
                       CustomerRepository customerRepository,
                       ProductRepository productRepository,
                       DomainEventPublisher eventPublisher) {
        this.orderRepository = orderRepository;
        this.customerRepository = customerRepository;
        this.productRepository = productRepository;
        this.eventPublisher = eventPublisher;
    }
    
    public Order createOrder(CustomerId customerId, List<OrderItemRequest> items) {
        Customer customer = customerRepository.findById(customerId)
            .orElseThrow(() -> new EntityNotFoundException("Customer not found"));
            
        Order order = new Order(customer.getId());
        
        for (OrderItemRequest itemRequest : items) {
            Product product = productRepository.findById(itemRequest.getProductId())
                .orElseThrow(() -> new EntityNotFoundException("Product not found"));
                
            if (!product.isAvailable(itemRequest.getQuantity())) {
                throw new InsufficientInventoryException(product.getId());
            }
            
            order.addItem(product, itemRequest.getQuantity());
        }
        
        return orderRepository.save(order);
    }
    
    // More business operations...
}
```

#### 5. Domain Events Example

```java
// Base event class
public abstract class DomainEvent {
    private final UUID eventId;
    private final LocalDateTime occurredOn;
    
    protected DomainEvent() {
        this.eventId = UUID.randomUUID();
        this.occurredOn = LocalDateTime.now();
    }
    
    // Getters...
}

// Concrete event
public class OrderSubmittedEvent extends DomainEvent {
    private final OrderId orderId;
    private final CustomerId customerId;
    private final Money totalAmount;
    
    public OrderSubmittedEvent(Order order) {
        super();
        this.orderId = order.getId();
        this.customerId = order.getCustomerId();
        this.totalAmount = order.getTotalAmount();
    }
    
    // Getters...
}

// Event publisher
@Service
public class DomainEventPublisher {
    private final ApplicationEventPublisher publisher;
    
    public DomainEventPublisher(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }
    
    public void publish(DomainEvent event) {
        publisher.publishEvent(event);
    }
}

// Event handler
@Component
public class OrderEventHandler {
    private final InventoryService inventoryService;
    
    @EventListener
    public void on(OrderSubmittedEvent event) {
        // Handle the event
        inventoryService.reserveInventory(event.getOrderId());
    }
}
```

### Using DDD to Identify Microservice Boundaries

1. **Domain Discovery Workshop**: Gather domain experts and developers to identify bounded contexts
2. **Context Mapping**: Document relationships between contexts
3. **Identify Aggregates**: Define clear boundaries around entity clusters
4. **Refactor Monolith**: Gradually reorganize code along bounded context lines
5. **Extract Services**: Extract bounded contexts as separate microservices

### Strategic Migration Pattern

1. **Domain Analysis**: Map the existing monolith using DDD concepts
2. **Bounded Context Identification**: Identify boundaries based on business capabilities
3. **Strangler Pattern Implementation**: 
   - Create an API gateway/facade in front of the monolith
   - Extract bounded contexts one by one
   - Gradually redirect traffic from monolith to new services
4. **Implement Anti-Corruption Layers**: Where necessary between services
5. **Evolve Domain Model**: Refine each service's domain model independently

## DDD with Spring Modulith

Spring Modulith provides built-in support for implementing DDD principles:

```java
@org.springframework.modulith.Modulith
public class Application {
    // Application bootstrap
}

// Module definition with explicit module dependencies
@Module(allowedDependencies = "order")
package com.example.ecommerce.shipping;

// Application events for domain events
@Component
class OrderEventListener {
    private final ShippingService shippingService;
    
    @EventListener
    void on(OrderCompletedEvent event) {
        shippingService.scheduleShipment(event.getOrderId());
    }
}
```

Spring Modulith provides:
- Module boundaries verification
- Documentation of module structures
- Event publication infrastructure
- Testing support for modules in isolation

## Common Pitfalls in DDD Migrations

1. **Picking Wrong Boundaries**: Decomposing along technical boundaries instead of business domains
2. **Ignoring Legacy Integration**: Not properly designing anti-corruption layers
3. **Distributed Monolith**: Creating tightly coupled microservices
4. **Premature Decomposition**: Breaking apart before understanding the domain
5. **Neglecting Data Concerns**: Not addressing data consistency challenges
6. **Missing Shared Kernel**: Duplicating core domain concepts

## Benefits of DDD for Microservices Migration

1. **Business Alignment**: Services map directly to business capabilities
2. **Clear Boundaries**: Well-defined boundaries facilitate decomposition
3. **Reduced Coupling**: Explicit context boundaries minimize dependencies
4. **Independent Evolution**: Services can evolve at different rates
5. **Focused Teams**: Teams can specialize in specific business domains
6. **Incremental Migration**: Progressive transition from monolith to microservices

## References

- [Domain-Driven Design: Tackling Complexity in the Heart of Software](https://www.domainlanguage.com/ddd/) by Eric Evans
- [Implementing Domain-Driven Design](https://www.amazon.com/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577) by Vaughn Vernon
- [Domain-Driven Design and Spring](https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html)
- [Spring Modulith Documentation](https://spring.io/blog/2022/10/21/introducing-spring-modulith)
- [How to build a modular monolith with Hexagonal Architecture](https://blog.artisivf.com/2024/08/29/how-to-build-a-modular-monolith-with-hexagonal-architecture/) 