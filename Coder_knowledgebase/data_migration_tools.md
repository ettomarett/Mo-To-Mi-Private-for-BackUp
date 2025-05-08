# Data Migration Tools for Microservices

## Overview

Data migration is one of the most challenging aspects of transitioning from a monolith to microservices. This document outlines tools, patterns, and best practices for ensuring data consistency and reliability during the migration process.

## Database Backup and Restore Strategies

### Docker PostgreSQL Backup and Restore

When migrating from a monolithic database to microservice-specific databases, reliable backup and restore procedures are essential.

#### Backing Up PostgreSQL in Docker

```bash
# Basic backup of a single database
docker exec -t postgres pg_dump -U postgres -d mydb > backup.sql

# Compressed backup
docker exec -t postgres pg_dump -U postgres -d mydb | gzip > backup.sql.gz

# Backup with custom format (for selective restore)
docker exec -t postgres pg_dump -U postgres -Fc -d mydb > backup.custom

# Backup all databases
docker exec -t postgres pg_dumpall -U postgres > all_dbs_backup.sql
```

#### Restoring PostgreSQL in Docker

```bash
# Restore a database
cat backup.sql | docker exec -i postgres psql -U postgres -d mydb

# Restore from compressed backup
gunzip -c backup.sql.gz | docker exec -i postgres psql -U postgres -d mydb

# Restore from custom format
docker exec -i postgres pg_restore -U postgres -d mydb < backup.custom

# Create a new database and restore
docker exec -i postgres psql -U postgres -c "CREATE DATABASE newdb;"
cat backup.sql | docker exec -i postgres psql -U postgres -d newdb
```

#### Automated Backup Script

```bash
#!/bin/bash

# Configuration
CONTAINER_NAME="postgres"
DB_USER="postgres"
DB_NAME="myapp"
BACKUP_DIR="/var/backups/postgres"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

# Create backup
echo "Backing up ${DB_NAME} to ${BACKUP_FILE}"
docker exec -t ${CONTAINER_NAME} pg_dump -U ${DB_USER} -d ${DB_NAME} | gzip > ${BACKUP_FILE}

# Retain only the last 7 backups
find ${BACKUP_DIR} -name "${DB_NAME}_*.sql.gz" -type f -mtime +7 -delete
```

### Implementing Database Snapshots

Database snapshots provide a point-in-time copy that can be used for testing migrations before applying them to production.

```bash
# Create a logical replication slot (PostgreSQL 10+)
docker exec -i postgres psql -U postgres -c "SELECT pg_create_logical_replication_slot('migration_slot', 'test_decoding');"

# Use the replication slot for capturing changes
docker exec -i postgres psql -U postgres -c "SELECT * FROM pg_logical_slot_get_changes('migration_slot', NULL, NULL);"

# Remove the slot when done
docker exec -i postgres psql -U postgres -c "SELECT pg_drop_replication_slot('migration_slot');"
```

## Dual Write Patterns for Data Migration

When migrating data between services, several patterns ensure data consistency across old and new systems.

### 1. Synchronous Dual Writes

In this pattern, the application writes to both the old and new data stores in the same transaction.

```java
@Service
@Transactional
public class OrderServiceWithDualWrite {
    
    private final MonolithOrderRepository monolithRepo;
    private final MicroserviceOrderRepository microserviceRepo;
    
    public OrderServiceWithDualWrite(
            MonolithOrderRepository monolithRepo,
            MicroserviceOrderRepository microserviceRepo) {
        this.monolithRepo = monolithRepo;
        this.microserviceRepo = microserviceRepo;
    }
    
    public Order createOrder(OrderRequest request) {
        // Create in monolith DB (source of truth during migration)
        MonolithOrder monolithOrder = new MonolithOrder();
        // ... populate order
        MonolithOrder savedMonolithOrder = monolithRepo.save(monolithOrder);
        
        // Create in microservice DB
        MicroserviceOrder microserviceOrder = convertToMicroserviceOrder(savedMonolithOrder);
        microserviceRepo.save(microserviceOrder);
        
        return convertToApiOrder(savedMonolithOrder);
    }
    
    // Conversion methods between different models
    private MicroserviceOrder convertToMicroserviceOrder(MonolithOrder monolithOrder) {
        // ... conversion logic
    }
    
    private Order convertToApiOrder(MonolithOrder monolithOrder) {
        // ... conversion logic
    }
}
```

### 2. Change Data Capture (CDC)

CDC tracks database changes and replicates them to target systems asynchronously.

#### Implementation with Debezium

Debezium configuration for PostgreSQL:

```json
{
  "name": "monolith-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname": "monolith_db",
    "database.server.name": "monolith",
    "schema.include.list": "public",
    "table.include.list": "public.orders,public.order_items",
    "plugin.name": "pgoutput"
  }
}
```

Consumer for processing CDC events:

```java
@Component
public class OrderCdcConsumer {
    
    private final MicroserviceOrderRepository orderRepository;
    
    @KafkaListener(topics = "monolith.public.orders")
    public void consumeOrderChanges(ConsumerRecord<String, String> record) {
        JsonNode payload = parsePayload(record.value());
        
        // Handle different operations
        String operation = payload.get("op").asText();
        JsonNode after = payload.get("after");
        
        switch (operation) {
            case "c": // Create
            case "u": // Update
                if (after != null) {
                    MicroserviceOrder order = convertToMicroserviceOrder(after);
                    orderRepository.save(order);
                }
                break;
            case "d": // Delete
                JsonNode before = payload.get("before");
                if (before != null) {
                    Long id = before.get("id").asLong();
                    orderRepository.deleteById(id);
                }
                break;
            default:
                // Unknown operation
        }
    }
    
    // Helper methods for parsing and conversion
    private JsonNode parsePayload(String value) {
        // ... parsing logic
    }
    
    private MicroserviceOrder convertToMicroserviceOrder(JsonNode data) {
        // ... conversion logic
    }
}
```

### 3. Outbox Pattern

The Outbox pattern ensures reliable event publishing alongside database transactions.

```java
@Entity
@Table(name = "outbox_events")
public class OutboxEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String aggregateType;
    
    @Column(nullable = false)
    private String aggregateId;
    
    @Column(nullable = false)
    private String eventType;
    
    @Column(columnDefinition = "jsonb", nullable = false)
    private String payload;
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = true)
    private LocalDateTime processedAt;
    
    // Getters and setters
}

@Service
@Transactional
public class OrderService {
    
    private final OrderRepository orderRepository;
    private final OutboxRepository outboxRepository;
    
    public Order createOrder(OrderRequest request) {
        // Create and save order
        Order order = new Order();
        // ... populate order
        Order savedOrder = orderRepository.save(order);
        
        // Create outbox event
        OutboxEvent event = new OutboxEvent();
        event.setAggregateType("Order");
        event.setAggregateId(savedOrder.getId().toString());
        event.setEventType("OrderCreated");
        event.setPayload(convertToJson(savedOrder));
        event.setCreatedAt(LocalDateTime.now());
        outboxRepository.save(event);
        
        return savedOrder;
    }
    
    private String convertToJson(Order order) {
        // ... conversion to JSON
    }
}

@Component
public class OutboxEventProcessor {
    
    private final OutboxRepository outboxRepository;
    private final KafkaTemplate<String, String> kafkaTemplate;
    
    @Scheduled(fixedRate = 5000)
    @Transactional
    public void processOutboxEvents() {
        List<OutboxEvent> unprocessedEvents = 
            outboxRepository.findByProcessedAtIsNullOrderByCreatedAt(
                PageRequest.of(0, 100));
        
        for (OutboxEvent event : unprocessedEvents) {
            String topic = event.getAggregateType().toLowerCase() + "_events";
            
            // Send to Kafka
            kafkaTemplate.send(topic, event.getAggregateId(), event.getPayload());
            
            // Mark as processed
            event.setProcessedAt(LocalDateTime.now());
            outboxRepository.save(event);
        }
    }
}
```

### 4. Saga Pattern for Cross-Service Transactions

The Saga pattern manages distributed transactions across multiple services.

```java
@Service
public class OrderSagaCoordinator {
    
    private final OrderRepository orderRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    
    @Transactional
    public void startOrderCreationSaga(OrderRequest request) {
        // Create and save order in PENDING state
        Order order = new Order();
        order.setStatus(OrderStatus.PENDING);
        // ... populate order
        Order savedOrder = orderRepository.save(order);
        
        // Start saga - Payment step
        OrderPaymentEvent paymentEvent = new OrderPaymentEvent(
            savedOrder.getId(), 
            savedOrder.getCustomerId(),
            savedOrder.getTotalAmount()
        );
        
        kafkaTemplate.send("payment-commands", paymentEvent);
    }
    
    @KafkaListener(topics = "payment-events")
    public void handlePaymentResult(PaymentResultEvent event) {
        Order order = orderRepository.findById(event.getOrderId())
            .orElseThrow();
        
        if (event.isSuccess()) {
            // Payment successful, update order and proceed to next step
            order.setStatus(OrderStatus.PAYMENT_COMPLETED);
            orderRepository.save(order);
            
            // Next saga step - Inventory
            OrderInventoryEvent inventoryEvent = new OrderInventoryEvent(
                order.getId(),
                order.getItems()
            );
            
            kafkaTemplate.send("inventory-commands", inventoryEvent);
        } else {
            // Payment failed, compensate
            order.setStatus(OrderStatus.PAYMENT_FAILED);
            orderRepository.save(order);
            
            // End saga with failure
            OrderFailedEvent failedEvent = new OrderFailedEvent(
                order.getId(),
                "Payment failed: " + event.getErrorMessage()
            );
            
            kafkaTemplate.send("order-events", failedEvent);
        }
    }
    
    @KafkaListener(topics = "inventory-events")
    public void handleInventoryResult(InventoryResultEvent event) {
        // Similar to payment handling, with compensation if needed
    }
}
```

## Data Migration Testing Tools

### 1. Data Consistency Verification

Tool for verifying data consistency between old and new databases:

```java
@Component
public class DataConsistencyVerifier {
    
    private final JdbcTemplate monolithJdbcTemplate;
    private final JdbcTemplate microserviceJdbcTemplate;
    private final MeterRegistry meterRegistry;
    
    @Scheduled(fixedRate = 60000) // Run every minute
    public void verifyOrdersConsistency() {
        // Count records in both systems
        int monolithCount = monolithJdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM orders", Integer.class);
        int microserviceCount = microserviceJdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM orders", Integer.class);
        
        // Record metrics
        meterRegistry.gauge("data.consistency.orders.count.monolith", monolithCount);
        meterRegistry.gauge("data.consistency.orders.count.microservice", microserviceCount);
        meterRegistry.gauge("data.consistency.orders.difference", 
            Math.abs(monolithCount - microserviceCount));
        
        // Sample records for detailed comparison
        List<Map<String, Object>> monolithSample = monolithJdbcTemplate.queryForList(
            "SELECT id, customer_id, status, total_amount FROM orders ORDER BY id LIMIT 100");
        
        int matchCount = 0;
        int mismatchCount = 0;
        
        for (Map<String, Object> monolithRecord : monolithSample) {
            Long id = (Long) monolithRecord.get("id");
            
            Map<String, Object> microserviceRecord = null;
            try {
                microserviceRecord = microserviceJdbcTemplate.queryForMap(
                    "SELECT id, customer_id, status, total_amount FROM orders WHERE monolith_id = ?", id);
            } catch (EmptyResultDataAccessException e) {
                // Record not found in microservice DB
                mismatchCount++;
                continue;
            }
            
            // Compare fields
            boolean matches = 
                Objects.equals(monolithRecord.get("customer_id"), microserviceRecord.get("customer_id")) &&
                Objects.equals(monolithRecord.get("status"), microserviceRecord.get("status")) &&
                compareAmounts(monolithRecord.get("total_amount"), microserviceRecord.get("total_amount"));
            
            if (matches) {
                matchCount++;
            } else {
                mismatchCount++;
            }
        }
        
        // Record metrics
        meterRegistry.gauge("data.consistency.orders.sample.matches", matchCount);
        meterRegistry.gauge("data.consistency.orders.sample.mismatches", mismatchCount);
    }
    
    private boolean compareAmounts(Object amount1, Object amount2) {
        // Compare amounts allowing for minor differences in decimal representation
        if (amount1 instanceof BigDecimal && amount2 instanceof BigDecimal) {
            return ((BigDecimal) amount1).subtract((BigDecimal) amount2).abs()
                .compareTo(new BigDecimal("0.01")) < 0;
        }
        return Objects.equals(amount1, amount2);
    }
}
```

### 2. Schema Comparison Tools

```java
@Component
public class SchemaComparisonTool {
    
    private final DataSource monolithDataSource;
    private final DataSource microserviceDataSource;
    
    @Scheduled(cron = "0 0 * * * *") // Run hourly
    public void compareSchemas() {
        try (
            Connection monolithConn = monolithDataSource.getConnection();
            Connection microserviceConn = microserviceDataSource.getConnection();
        ) {
            DatabaseMetaData monolithMeta = monolithConn.getMetaData();
            DatabaseMetaData microserviceMeta = microserviceConn.getMetaData();
            
            // Compare tables
            ResultSet monolithTables = monolithMeta.getTables(
                null, "public", "order%", new String[]{"TABLE"});
            
            Set<String> monolithTableNames = new HashSet<>();
            while (monolithTables.next()) {
                monolithTableNames.add(monolithTables.getString("TABLE_NAME"));
            }
            
            ResultSet microserviceTables = microserviceMeta.getTables(
                null, "public", "order%", new String[]{"TABLE"});
            
            Set<String> microserviceTableNames = new HashSet<>();
            while (microserviceTables.next()) {
                microserviceTableNames.add(microserviceTables.getString("TABLE_NAME"));
            }
            
            // Tables in monolith but not in microservice
            Set<String> missingTables = new HashSet<>(monolithTableNames);
            missingTables.removeAll(microserviceTableNames);
            
            // Compare columns for common tables
            Set<String> commonTables = new HashSet<>(monolithTableNames);
            commonTables.retainAll(microserviceTableNames);
            
            for (String table : commonTables) {
                ResultSet monolithColumns = monolithMeta.getColumns(
                    null, "public", table, null);
                
                Map<String, String> monolithColumnTypes = new HashMap<>();
                while (monolithColumns.next()) {
                    monolithColumnTypes.put(
                        monolithColumns.getString("COLUMN_NAME"),
                        monolithColumns.getString("TYPE_NAME")
                    );
                }
                
                ResultSet microserviceColumns = microserviceMeta.getColumns(
                    null, "public", table, null);
                
                Map<String, String> microserviceColumnTypes = new HashMap<>();
                while (microserviceColumns.next()) {
                    microserviceColumnTypes.put(
                        microserviceColumns.getString("COLUMN_NAME"),
                        microserviceColumns.getString("TYPE_NAME")
                    );
                }
                
                // Columns in monolith but not in microservice
                Set<String> missingColumns = new HashMap<>(monolithColumnTypes).keySet();
                missingColumns.removeAll(microserviceColumnTypes.keySet());
                
                // Column type differences
                Set<String> commonColumns = new HashMap<>(monolithColumnTypes).keySet();
                commonColumns.retainAll(microserviceColumnTypes.keySet());
                
                for (String column : commonColumns) {
                    String monolithType = monolithColumnTypes.get(column);
                    String microserviceType = microserviceColumnTypes.get(column);
                    
                    if (!monolithType.equals(microserviceType)) {
                        System.out.println("Type mismatch for " + table + "." + column + 
                                          ": monolith=" + monolithType + 
                                          ", microservice=" + microserviceType);
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
```

## GitOps for Database Schema Migration

GitOps principles can be applied to database migrations, treating schema changes as code.

### Flyway with GitOps Integration

```java
@Configuration
public class FlywayConfig {
    
    @Bean
    public FlywayMigrationStrategy flywayMigrationStrategy() {
        return flyway -> {
            // Before migration, check Git state
            String currentGitCommit = getCurrentGitCommit();
            
            // Execute migration
            flyway.migrate();
            
            // Record migration in audit table
            recordMigration(currentGitCommit, flyway.info().current().getVersion().toString());
        };
    }
    
    private String getCurrentGitCommit() {
        try {
            Process process = Runtime.getRuntime().exec("git rev-parse HEAD");
            process.waitFor();
            
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                return reader.readLine();
            }
        } catch (Exception e) {
            return "unknown";
        }
    }
    
    private void recordMigration(String gitCommit, String schemaVersion) {
        // Record migration details in audit table
    }
}
```

## References

- [Docker Postgres Backup/Restore Guide](https://simplebackups.com/blog/docker-postgres-backup-restore-guide-with-examples/)
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)
- [5 Patterns for Dual Writes in Microservices](https://developers.redhat.com/articles/2021/09/21/distributed-transaction-patterns-microservices-compared)
- [Flyway Documentation](https://flywaydb.org/documentation/)
- [GitOps for Kubernetes Configuration Management](https://overcast.blog/adopting-gitops-for-kubernetes-configuration-management-634975ff5d43) 