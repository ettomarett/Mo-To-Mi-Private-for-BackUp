# Data Consistency Patterns

## Overview

Maintaining data consistency across microservices is one of the most challenging aspects of a distributed architecture. Unlike monoliths, where ACID transactions can span multiple operations, microservices typically have independent databases, requiring different approaches to consistency.

## CQRS (Command Query Responsibility Segregation)

CQRS separates operations that modify data (commands) from operations that read data (queries). This pattern is particularly useful when migrating from monoliths to microservices.

### Core Concepts

1. **Command Model**: Optimized for writes, focused on business rules and validation
2. **Query Model**: Optimized for reads, potentially denormalized for performance
3. **Synchronization Mechanism**: Process to keep the models in sync

### Simple CQRS Implementation

```java
// Command side (write model)
@Service
public class OrderCommandService {
    
    private final OrderRepository orderRepository;
    private final EventPublisher eventPublisher;
    
    @Transactional
    public Order createOrder(CreateOrderCommand command) {
        // Validate command
        // Apply business rules
        Order order = new Order(command.getCustomerId(), command.getItems());
        
        // Save to database
        Order savedOrder = orderRepository.save(order);
        
        // Publish event for synchronization
        eventPublisher.publish(new OrderCreatedEvent(savedOrder));
        
        return savedOrder;
    }
}

// Query side (read model)
@Service
public class OrderQueryService {
    
    private final OrderSummaryRepository orderSummaryRepository;
    
    public List<OrderSummary> getCustomerOrders(Long customerId) {
        return orderSummaryRepository.findByCustomerId(customerId);
    }
    
    public OrderDetailsView getOrderDetails(Long orderId) {
        return orderSummaryRepository.findDetailViewById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
    }
    
    // Event handler to update read model
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        OrderSummary summary = new OrderSummary(event.getOrder());
        orderSummaryRepository.save(summary);
    }
}
```

### Advantages for Microservices Migration

1. **Separate Scaling**: Read and write workloads can scale independently
2. **Specialized Optimization**: Different data models for different access patterns
3. **Focused Services**: Services can specialize in either commands or queries
4. **Easier Extraction**: Read models can be extracted as separate microservices first

### Implementation Strategies

#### 1. Database Level

Use database views, materialized views, or read replicas:

```sql
-- Example of a materialized view for order summaries
CREATE MATERIALIZED VIEW order_summaries AS
SELECT o.id, o.customer_id, o.order_date, SUM(oi.quantity * p.price) as total_amount,
       COUNT(oi.id) as item_count
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
GROUP BY o.id, o.customer_id, o.order_date;
```

#### 2. Application Level

Use events to synchronize separate read and write databases:

```java
@Service
public class OrderEventHandler {
    
    private final OrderReadModelRepository readRepository;
    
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        OrderReadModel readModel = mapToReadModel(event.getOrder());
        readRepository.save(readModel);
    }
    
    @EventListener
    public void handleOrderUpdated(OrderUpdatedEvent event) {
        OrderReadModel readModel = readRepository.findById(event.getOrderId())
            .orElseThrow();
        updateReadModel(readModel, event);
        readRepository.save(readModel);
    }
}
```

## Event Sourcing

Event Sourcing stores all changes to application state as a sequence of events. This pattern works well with CQRS and supports microservice migration.

### Core Concepts

1. **Events as Source of Truth**: All state changes are recorded as immutable events
2. **Event Store**: Specialized database for storing the event stream
3. **Projections**: Current state is reconstructed by applying events
4. **Event Replaying**: System state can be rebuilt by replaying events

### Basic Implementation

```java
// Event base class
public abstract class DomainEvent {
    private final UUID eventId;
    private final LocalDateTime timestamp;
    private final UUID aggregateId;
    
    // Constructor, getters
}

// Concrete event
public class OrderCreatedEvent extends DomainEvent {
    private final List<OrderItem> items;
    private final Long customerId;
    
    // Constructor, getters
}

// Event store (simplified)
@Repository
public class EventStoreRepository {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    public void saveEvent(DomainEvent event) {
        String sql = "INSERT INTO event_store (event_id, aggregate_id, event_type, event_data, timestamp) " +
                     "VALUES (?, ?, ?, ?, ?)";
        
        jdbcTemplate.update(sql, 
            event.getEventId(),
            event.getAggregateId(),
            event.getClass().getSimpleName(),
            serializeEvent(event),
            event.getTimestamp()
        );
    }
    
    public List<DomainEvent> getEventsForAggregate(UUID aggregateId) {
        String sql = "SELECT * FROM event_store WHERE aggregate_id = ? ORDER BY timestamp ASC";
        
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            return deserializeEvent(rs.getString("event_data"), rs.getString("event_type"));
        }, aggregateId);
    }
}

// Aggregate root with event sourcing
public class Order {
    private UUID id;
    private Long customerId;
    private List<OrderItem> items = new ArrayList<>();
    private OrderStatus status;
    
    // Event replay constructor
    public static Order recreateFrom(List<DomainEvent> events) {
        Order order = new Order();
        events.forEach(order::apply);
        return order;
    }
    
    // Apply events to recreate state
    private void apply(DomainEvent event) {
        if (event instanceof OrderCreatedEvent) {
            OrderCreatedEvent e = (OrderCreatedEvent) event;
            this.id = e.getAggregateId();
            this.customerId = e.getCustomerId();
            this.items.addAll(e.getItems());
            this.status = OrderStatus.CREATED;
        } else if (event instanceof OrderPaidEvent) {
            this.status = OrderStatus.PAID;
        } // Handle other events
    }
}
```

### Advantages for Microservices Migration

1. **Complete History**: All changes are recorded, enabling full audit trails
2. **Temporal Queries**: Can determine state at any point in time
3. **Easier Debugging**: Root causes can be determined by examining event sequences
4. **Service Autonomy**: Services can subscribe to event streams they care about
5. **Safe Schema Evolution**: Events are immutable, but projections can evolve

### Implementation Considerations

#### 1. Event Schema Evolution

Event schemas may evolve over time. Strategies include:

- **Versioning**: Add version to event types
- **Upcasting**: Convert old event formats to new ones during replay
- **Snapshots**: Store occasional state snapshots to avoid full replays

#### 2. Performance Optimization

- **Snapshots**: Periodically store the current state to avoid replaying all events
- **Projections**: Maintain read-optimized views that are updated with each event
- **Event Processors**: Use background processors to update projections

## Saga Pattern

The Saga pattern manages transactions that span multiple services by breaking them into a sequence of local transactions with compensating actions.

### Types of Sagas

1. **Choreography**: Services publish events that trigger other services
2. **Orchestration**: A central coordinator manages the transaction steps

### Choreography Example

```java
// Order Service
@Service
public class OrderService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private EventPublisher eventPublisher;
    
    @Transactional
    public Order createOrder(CreateOrderCommand command) {
        Order order = new Order(command.getCustomerId(), command.getItems());
        order.setStatus(OrderStatus.PENDING);
        
        Order savedOrder = orderRepository.save(order);
        
        // Publish event for payment service
        eventPublisher.publish(new OrderCreatedEvent(savedOrder));
        
        return savedOrder;
    }
    
    @EventListener
    public void handlePaymentCompletedEvent(PaymentCompletedEvent event) {
        Order order = orderRepository.findById(event.getOrderId())
            .orElseThrow();
        
        order.setStatus(OrderStatus.PAID);
        orderRepository.save(order);
        
        // Publish event for shipping service
        eventPublisher.publish(new OrderPaidEvent(order.getId()));
    }
    
    @EventListener
    public void handlePaymentFailedEvent(PaymentFailedEvent event) {
        Order order = orderRepository.findById(event.getOrderId())
            .orElseThrow();
        
        order.setStatus(OrderStatus.PAYMENT_FAILED);
        orderRepository.save(order);
    }
}

// Payment Service
@Service
public class PaymentService {
    
    @Autowired
    private PaymentRepository paymentRepository;
    
    @Autowired
    private EventPublisher eventPublisher;
    
    @EventListener
    @Transactional
    public void handleOrderCreatedEvent(OrderCreatedEvent event) {
        try {
            Payment payment = new Payment(
                event.getOrderId(), 
                event.getCustomerId(),
                event.getTotalAmount()
            );
            
            paymentRepository.save(payment);
            
            // Process payment (external call)
            boolean paymentSuccessful = paymentProcessor.process(payment);
            
            if (paymentSuccessful) {
                payment.setStatus(PaymentStatus.COMPLETED);
                paymentRepository.save(payment);
                eventPublisher.publish(new PaymentCompletedEvent(event.getOrderId()));
            } else {
                payment.setStatus(PaymentStatus.FAILED);
                paymentRepository.save(payment);
                eventPublisher.publish(new PaymentFailedEvent(event.getOrderId()));
            }
        } catch (Exception e) {
            // Publish failure event
            eventPublisher.publish(new PaymentFailedEvent(event.getOrderId()));
        }
    }
}
```

### Orchestration Example

```java
@Service
public class OrderSagaOrchestrator {
    
    @Autowired
    private OrderService orderService;
    
    @Autowired
    private PaymentService paymentService;
    
    @Autowired
    private ShippingService shippingService;
    
    @Transactional
    public void processOrder(CreateOrderCommand command) {
        // Step 1: Create the order
        Order order = orderService.createOrder(command);
        
        try {
            // Step 2: Process payment
            boolean paymentSuccess = paymentService.processPayment(
                new ProcessPaymentCommand(order.getId(), order.getTotalAmount())
            );
            
            if (!paymentSuccess) {
                // Compensating transaction
                orderService.cancelOrder(order.getId());
                return;
            }
            
            // Step 3: Prepare shipping
            boolean shippingSuccess = shippingService.createShipment(
                new CreateShipmentCommand(order.getId(), order.getDeliveryAddress())
            );
            
            if (!shippingSuccess) {
                // Compensating transactions
                paymentService.refundPayment(order.getId());
                orderService.cancelOrder(order.getId());
                return;
            }
            
            // Complete the order
            orderService.completeOrder(order.getId());
            
        } catch (Exception e) {
            // Handle overall failure
            orderService.cancelOrder(order.getId());
            paymentService.refundPayment(order.getId());
            shippingService.cancelShipment(order.getId());
        }
    }
}
```

### Benefits for Microservices

1. **Maintains Consistency**: Ensures data consistency across services
2. **Handles Failures**: Includes compensating transactions for recovery
3. **Preserves Autonomy**: Services maintain their own data and transactions
4. **Supports Migration**: Can be implemented incrementally during monolith decomposition

## Best Practices for Data Consistency

1. **Design for Eventual Consistency**: Accept that data may not be immediately consistent
2. **Use Idempotent Operations**: Ensure operations can be safely retried
3. **Implement Compensating Transactions**: Define how to undo operations when failures occur
4. **Set Realistic Timeouts**: Consider business requirements when setting synchronization timeouts
5. **Monitor Consistency**: Implement systems to detect and resolve inconsistencies
6. **Document Consistency Guarantees**: Make it clear which operations are immediately consistent and which are eventually consistent

## References

- [CQRS Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Event Sourcing Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Decompose monoliths using CQRS and event sourcing](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/decompose-monoliths-into-microservices-by-using-cqrs-and-event-sourcing.html) 