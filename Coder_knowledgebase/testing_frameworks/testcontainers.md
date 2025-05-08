# Testing with Testcontainers for Spring Boot Microservices

## Overview

Testcontainers is a Java library that provides lightweight, throwaway instances of common databases, message brokers, and other services in Docker containers for testing. It's especially valuable in microservices testing as it enables true integration tests with real dependencies rather than mocks or stubs.

## Key Benefits for Microservice Testing

1. **Realistic Testing Environment**: Test against the same database, message broker, or service implementations used in production
2. **Isolation**: Each test gets its own isolated container instances
3. **Portability**: Tests run the same way on any environment with Docker
4. **Simplicity**: No need to maintain separate test infrastructure
5. **Compatibility**: Works with JUnit 4, JUnit 5, TestNG, and other test frameworks

## Basic Setup

### Maven Dependency

```xml
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>testcontainers</artifactId>
    <version>1.17.6</version>
    <scope>test</scope>
</dependency>

<!-- Database module -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <version>1.17.6</version>
    <scope>test</scope>
</dependency>

<!-- JUnit 5 integration -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>1.17.6</version>
    <scope>test</scope>
</dependency>
```

### Simple PostgreSQL Test

```java
@Testcontainers
@SpringBootTest
public class UserRepositoryIntegrationTest {

    @Container
    public static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");
    
    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void testSaveAndFindUser() {
        // Create and save test user
        User user = new User();
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        
        User savedUser = userRepository.save(user);
        
        // Verify
        Optional<User> foundUser = userRepository.findById(savedUser.getId());
        assertTrue(foundUser.isPresent());
        assertEquals("testuser", foundUser.get().getUsername());
    }
}
```

## Advanced Testcontainers Patterns

### 1. Testing Multiple Microservices Together

This approach runs actual microservice containers for comprehensive integration testing:

```java
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class OrderServiceIntegrationTest {

    private static final Network network = Network.newNetwork();
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withNetwork(network)
            .withNetworkAliases("postgres")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static GenericContainer<?> userService = new GenericContainer<>("user-service:latest")
            .withNetwork(network)
            .withNetworkAliases("user-service")
            .withExposedPorts(8080)
            .dependsOn(postgres)
            .withEnv("SPRING_DATASOURCE_URL", "jdbc:postgresql://postgres:5432/testdb")
            .withEnv("SPRING_DATASOURCE_USERNAME", "test")
            .withEnv("SPRING_DATASOURCE_PASSWORD", "test");
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", 
                () -> String.format("jdbc:postgresql://localhost:%d/testdb", 
                        postgres.getMappedPort(5432)));
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("user-service.url", 
                () -> String.format("http://localhost:%d", 
                        userService.getMappedPort(8080)));
    }
    
    @Test
    void testCreateOrderWithValidUser() {
        // Create order for a valid user
        OrderRequest request = new OrderRequest();
        request.setUserId(1L); // Existing user in user-service
        request.setItems(List.of(new OrderItemRequest("Product1", 2)));
        
        ResponseEntity<Order> response = restTemplate.postForEntity(
                "/api/orders", request, Order.class);
        
        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(OrderStatus.CREATED, response.getBody().getStatus());
    }
}
```

### 2. Testing Message-Based Communication

Testing microservices that communicate via message brokers:

```java
@Testcontainers
@SpringBootTest
public class OrderProcessingIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static RabbitMQContainer rabbitMQ = new RabbitMQContainer("rabbitmq:3.9-management")
            .withExposedPorts(5672, 15672);
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        
        registry.add("spring.rabbitmq.host", rabbitMQ::getHost);
        registry.add("spring.rabbitmq.port", rabbitMQ::getAmqpPort);
        registry.add("spring.rabbitmq.username", rabbitMQ::getAdminUsername);
        registry.add("spring.rabbitmq.password", rabbitMQ::getAdminPassword);
    }
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private RabbitTemplate rabbitTemplate;
    
    @Autowired
    private OrderStatusListener orderStatusListener;
    
    @Test
    void testOrderStatusUpdateViaMessage() throws Exception {
        // Create test order
        Order order = new Order();
        order.setStatus(OrderStatus.PROCESSING);
        Order savedOrder = orderRepository.save(order);
        
        // Send message to update status
        OrderStatusUpdateMessage message = new OrderStatusUpdateMessage();
        message.setOrderId(savedOrder.getId());
        message.setNewStatus(OrderStatus.COMPLETED);
        
        rabbitTemplate.convertAndSend("order-status-exchange", "order.status.update", message);
        
        // Wait for message processing using awaitility
        await().atMost(5, TimeUnit.SECONDS).until(() -> {
            Optional<Order> updatedOrder = orderRepository.findById(savedOrder.getId());
            return updatedOrder.isPresent() && 
                   updatedOrder.get().getStatus() == OrderStatus.COMPLETED;
        });
    }
}
```

### 3. Database Migration Testing

Testing Liquibase or Flyway migrations:

```java
@Testcontainers
public class DatabaseMigrationTest {

    @Container
    public static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("migration_test")
            .withUsername("test")
            .withPassword("test");
    
    @Test
    void testFlywayMigration() {
        // Create Flyway instance
        Flyway flyway = Flyway.configure()
                .dataSource(postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword())
                .load();
        
        // Execute migration
        MigrationInfo[] migrationInfo = flyway.info().all();
        flyway.migrate();
        MigrationInfo[] migratedInfo = flyway.info().all();
        
        // Verify all migrations were applied
        for (MigrationInfo info : migratedInfo) {
            assertEquals(MigrationState.SUCCESS, info.getState());
        }
        
        // Verify schema structure
        try (Connection conn = DriverManager.getConnection(
                postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword())) {
            
            // Check if users table exists with expected structure
            PreparedStatement stmt = conn.prepareStatement(
                    "SELECT column_name, data_type FROM information_schema.columns " +
                    "WHERE table_name = 'users' ORDER BY column_name");
            
            ResultSet rs = stmt.executeQuery();
            Map<String, String> columns = new HashMap<>();
            
            while (rs.next()) {
                columns.put(rs.getString("column_name"), rs.getString("data_type"));
            }
            
            assertTrue(columns.containsKey("id"));
            assertTrue(columns.containsKey("username"));
            assertTrue(columns.containsKey("email"));
        } catch (SQLException e) {
            fail("Failed to verify database structure", e);
        }
    }
}
```

## Performance Testing with Testcontainers

Testcontainers combined with JMeter for microservice performance testing:

```java
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class OrderServicePerformanceTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");
    
    @LocalServerPort
    private int port;
    
    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
    
    @Test
    void performanceTest() throws Exception {
        // Configure JMeter test plan programmatically
        StandardJMeterEngine jmeter = new StandardJMeterEngine();
        
        // JMeter configuration elements
        HashTree testPlanTree = new HashTree();
        TestPlan testPlan = new TestPlan("Order Service Performance Test");
        testPlanTree.add(testPlan);
        
        // Thread Group
        ThreadGroup threadGroup = new ThreadGroup();
        threadGroup.setNumThreads(50);
        threadGroup.setRampUp(10);
        threadGroup.setDuration(60);
        threadGroup.setProperty(TestElement.TEST_CLASS, ThreadGroup.class.getName());
        threadGroup.setProperty(TestElement.GUI_CLASS, ThreadGroupGui.class.getName());
        
        HashTree threadGroupHashTree = testPlanTree.add(testPlan, threadGroup);
        
        // HTTP Request
        HTTPSamplerProxy httpSampler = new HTTPSamplerProxy();
        httpSampler.setDomain("localhost");
        httpSampler.setPort(port);
        httpSampler.setPath("/api/orders");
        httpSampler.setMethod("POST");
        httpSampler.setContentEncoding("UTF-8");
        
        // Request body
        String jsonBody = "{\"userId\":1,\"items\":[{\"productId\":1,\"quantity\":1}]}";
        httpSampler.addNonEncodedArgument("", jsonBody, "");
        httpSampler.setPostBodyRaw(true);
        
        // HTTP headers
        HeaderManager headerManager = new HeaderManager();
        headerManager.add(new Header("Content-Type", "application/json"));
        httpSampler.setHeaderManager(headerManager);
        
        threadGroupHashTree.add(httpSampler);
        
        // Add listeners for results
        SummaryReport summaryReport = new SummaryReport();
        threadGroupHashTree.add(summaryReport);
        
        // Execute test
        jmeter.configure(testPlanTree);
        jmeter.run();
        
        // Analyze results
        Map<String, Object> results = summaryReport.getDataAsMap();
        long sampleCount = (long) results.get("sampleCount");
        double avgResponseTime = (double) results.get("average");
        double errorRate = (double) results.get("errorPercentage");
        
        // Assertions on performance metrics
        assertTrue(sampleCount > 0, "No samples were collected");
        assertTrue(avgResponseTime < 500, "Average response time exceeded threshold");
        assertTrue(errorRate < 1.0, "Error rate exceeded threshold");
    }
}
```

## Testing with Testcontainers and Locust

Integrating Testcontainers with Locust for load testing:

```java
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class LocustLoadTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static GenericContainer<?> locust = new GenericContainer<>("locustio/locust:latest")
            .withCopyFileToContainer(
                    MountableFile.forClasspathResource("locustfile.py"), 
                    "/mnt/locust/locustfile.py")
            .withEnv("TARGET_URL", "http://host.testcontainers.internal:${local.server.port}")
            .withEnv("LOCUST_MODE", "standalone")
            .withEnv("LOCUST_USERS", "100")
            .withEnv("LOCUST_SPAWN_RATE", "10")
            .withEnv("LOCUST_RUN_TIME", "1m")
            .withExposedPorts(8089)
            .withNetwork(Network.SHARED)
            .withNetworkAliases("locust")
            .withCommand("-f /mnt/locust/locustfile.py --headless");
    
    @LocalServerPort
    private int port;
    
    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("local.server.port", () -> port);
    }
    
    @Test
    void runLocustLoadTest() throws Exception {
        // Wait for Locust test to complete
        await().atMost(2, TimeUnit.MINUTES).until(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                    locust.execInContainer("cat", "/var/lib/locust/stats.csv").getStdout()))) {
                
                // Check if stats file exists and contains data
                return reader.lines().count() > 1;
            }
        });
        
        // Retrieve test results
        ExecResult statsResult = locust.execInContainer("cat", "/var/lib/locust/stats.csv");
        
        // Parse CSV results
        String[] lines = statsResult.getStdout().split("\n");
        Map<String, Map<String, String>> stats = new HashMap<>();
        
        String[] headers = lines[0].split(",");
        for (int i = 1; i < lines.length; i++) {
            String[] values = lines[i].split(",");
            if (values.length >= headers.length) {
                String endpoint = values[1].trim();
                Map<String, String> endpointStats = new HashMap<>();
                
                for (int j = 0; j < headers.length; j++) {
                    endpointStats.put(headers[j].trim(), values[j].trim());
                }
                
                stats.put(endpoint, endpointStats);
            }
        }
        
        // Analyze results for key endpoints
        Map<String, String> createOrderStats = stats.get("POST /api/orders");
        if (createOrderStats != null) {
            double avgResponseTime = Double.parseDouble(createOrderStats.get("Average Response Time"));
            double errorRate = Double.parseDouble(createOrderStats.get("Failure Rate"));
            
            assertTrue(avgResponseTime < 500, 
                    "Average response time for order creation exceeded threshold: " + avgResponseTime);
            assertTrue(errorRate < 1.0, 
                    "Error rate for order creation exceeded threshold: " + errorRate);
        }
    }
}
```

Example Locust file (`locustfile.py`):

```python
from locust import HttpUser, task, between

class MicroserviceUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def create_order(self):
        self.client.post("/api/orders", json={
            "userId": 1,
            "items": [
                {"productId": 1, "quantity": 2},
                {"productId": 2, "quantity": 1}
            ]
        }, headers={"Content-Type": "application/json"})
    
    @task(1)
    def get_orders(self):
        self.client.get("/api/orders", 
                        headers={"Authorization": "Bearer test-token"})
    
    @task(2)
    def get_products(self):
        self.client.get("/api/products")
```

## Multiple Containers in Testcontainers

Testing a complete microservice ecosystem:

```java
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class MicroserviceEcosystemTest {

    private static final Network network = Network.newNetwork();
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14-alpine")
            .withNetwork(network)
            .withNetworkAliases("postgres")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:6-alpine")
            .withNetwork(network)
            .withNetworkAliases("redis")
            .withExposedPorts(6379);
    
    @Container
    static RabbitMQContainer rabbitMQ = new RabbitMQContainer("rabbitmq:3.9-management")
            .withNetwork(network)
            .withNetworkAliases("rabbitmq")
            .withExposedPorts(5672);
    
    @Container
    static GenericContainer<?> userService = new GenericContainer<>("user-service:latest")
            .withNetwork(network)
            .withNetworkAliases("user-service")
            .withExposedPorts(8080)
            .dependsOn(postgres, redis)
            .withEnv("SPRING_DATASOURCE_URL", "jdbc:postgresql://postgres:5432/testdb")
            .withEnv("SPRING_DATASOURCE_USERNAME", "test")
            .withEnv("SPRING_DATASOURCE_PASSWORD", "test")
            .withEnv("SPRING_REDIS_HOST", "redis")
            .withEnv("SPRING_RABBITMQ_HOST", "rabbitmq");
    
    @Container
    static GenericContainer<?> productService = new GenericContainer<>("product-service:latest")
            .withNetwork(network)
            .withNetworkAliases("product-service")
            .withExposedPorts(8080)
            .dependsOn(postgres, redis)
            .withEnv("SPRING_DATASOURCE_URL", "jdbc:postgresql://postgres:5432/testdb")
            .withEnv("SPRING_DATASOURCE_USERNAME", "test")
            .withEnv("SPRING_DATASOURCE_PASSWORD", "test")
            .withEnv("SPRING_REDIS_HOST", "redis")
            .withEnv("SPRING_RABBITMQ_HOST", "rabbitmq");
    
    @LocalServerPort
    private int port;
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", 
                () -> String.format("jdbc:postgresql://localhost:%d/testdb", 
                        postgres.getMappedPort(5432)));
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.redis.host", redis::getHost);
        registry.add("spring.redis.port", redis::getFirstMappedPort);
        registry.add("spring.rabbitmq.host", rabbitMQ::getHost);
        registry.add("spring.rabbitmq.port", rabbitMQ::getAmqpPort);
        registry.add("service.user.url", 
                () -> String.format("http://localhost:%d", 
                        userService.getMappedPort(8080)));
        registry.add("service.product.url", 
                () -> String.format("http://localhost:%d", 
                        productService.getMappedPort(8080)));
    }
    
    @Test
    void testCreateOrderWithValidUserAndProducts() {
        // Create test user if needed
        UserDTO user = new UserDTO();
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        
        ResponseEntity<UserDTO> userResponse = restTemplate.postForEntity(
                "http://localhost:" + userService.getMappedPort(8080) + "/api/users", 
                user, UserDTO.class);
        assertEquals(HttpStatus.CREATED, userResponse.getStatusCode());
        
        // Create test product if needed
        ProductDTO product = new ProductDTO();
        product.setName("Test Product");
        product.setPrice(BigDecimal.valueOf(29.99));
        product.setQuantity(100);
        
        ResponseEntity<ProductDTO> productResponse = restTemplate.postForEntity(
                "http://localhost:" + productService.getMappedPort(8080) + "/api/products", 
                product, ProductDTO.class);
        assertEquals(HttpStatus.CREATED, productResponse.getStatusCode());
        
        // Create order using both services
        OrderRequest orderRequest = new OrderRequest();
        orderRequest.setUserId(userResponse.getBody().getId());
        orderRequest.setItems(List.of(
                new OrderItemRequest(productResponse.getBody().getId(), 2)));
        
        ResponseEntity<OrderDTO> orderResponse = restTemplate.postForEntity(
                "/api/orders", orderRequest, OrderDTO.class);
        
        assertEquals(HttpStatus.CREATED, orderResponse.getStatusCode());
        assertNotNull(orderResponse.getBody());
        assertNotNull(orderResponse.getBody().getId());
        assertEquals(OrderStatus.CREATED, orderResponse.getBody().getStatus());
    }
}
```

## Migration Testing with Testcontainers

Using Testcontainers to validate migration from monolith to microservices:

```java
@Testcontainers
public class DatabaseMigrationValidationTest {

    @Container
    static PostgreSQLContainer<?> monolithDb = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("monolith")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static PostgreSQLContainer<?> microserviceDb = new PostgreSQLContainer<>("postgres:14-alpine")
            .withDatabaseName("microservice")
            .withUsername("test")
            .withPassword("test");
    
    @Test
    void testOrderDataMigration() throws Exception {
        // Set up JDBC templates
        JdbcTemplate monolithJdbc = new JdbcTemplate(new SingleConnectionDataSource(
                monolithDb.getJdbcUrl(), monolithDb.getUsername(), monolithDb.getPassword(), true));
        
        JdbcTemplate microserviceJdbc = new JdbcTemplate(new SingleConnectionDataSource(
                microserviceDb.getJdbcUrl(), microserviceDb.getUsername(), microserviceDb.getPassword(), true));
        
        // Create schema in monolith DB
        monolithJdbc.execute("CREATE TABLE customers (" +
                "id SERIAL PRIMARY KEY, " +
                "name VARCHAR(255), " +
                "email VARCHAR(255))");
        
        monolithJdbc.execute("CREATE TABLE orders (" +
                "id SERIAL PRIMARY KEY, " +
                "customer_id INTEGER REFERENCES customers(id), " +
                "total DECIMAL(10,2), " +
                "status VARCHAR(50))");
        
        monolithJdbc.execute("CREATE TABLE order_items (" +
                "id SERIAL PRIMARY KEY, " +
                "order_id INTEGER REFERENCES orders(id), " +
                "product_name VARCHAR(255), " +
                "quantity INTEGER, " +
                "price DECIMAL(10,2))");
        
        // Create schema in microservice DB
        microserviceJdbc.execute("CREATE TABLE orders (" +
                "id SERIAL PRIMARY KEY, " +
                "original_id INTEGER, " +
                "customer_id INTEGER, " +
                "total DECIMAL(10,2), " +
                "status VARCHAR(50))");
        
        microserviceJdbc.execute("CREATE TABLE order_items (" +
                "id SERIAL PRIMARY KEY, " +
                "order_id INTEGER REFERENCES orders(id), " +
                "product_id INTEGER, " +
                "product_name VARCHAR(255), " +
                "quantity INTEGER, " +
                "price DECIMAL(10,2))");
        
        // Insert test data in monolith DB
        monolithJdbc.update("INSERT INTO customers (name, email) VALUES (?, ?)", 
                "Test Customer", "test@example.com");
        
        Long customerId = monolithJdbc.queryForObject(
                "SELECT id FROM customers WHERE email = ?", Long.class, "test@example.com");
        
        monolithJdbc.update("INSERT INTO orders (customer_id, total, status) VALUES (?, ?, ?)",
                customerId, 99.99, "COMPLETED");
        
        Long orderId = monolithJdbc.queryForObject(
                "SELECT id FROM orders WHERE customer_id = ?", Long.class, customerId);
        
        monolithJdbc.update("INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                orderId, "Test Product", 2, 49.99);
        
        // Run migration (simulated here)
        List<Map<String, Object>> monolithOrders = monolithJdbc.queryForList(
                "SELECT id, customer_id, total, status FROM orders");
        
        for (Map<String, Object> order : monolithOrders) {
            Long monolithOrderId = ((Number) order.get("id")).longValue();
            Long monolithCustomerId = ((Number) order.get("customer_id")).longValue();
            BigDecimal total = (BigDecimal) order.get("total");
            String status = (String) order.get("status");
            
            microserviceJdbc.update(
                    "INSERT INTO orders (original_id, customer_id, total, status) VALUES (?, ?, ?, ?)",
                    monolithOrderId, monolithCustomerId, total, status);
            
            Long microserviceOrderId = microserviceJdbc.queryForObject(
                    "SELECT id FROM orders WHERE original_id = ?", Long.class, monolithOrderId);
            
            List<Map<String, Object>> orderItems = monolithJdbc.queryForList(
                    "SELECT product_name, quantity, price FROM order_items WHERE order_id = ?",
                    monolithOrderId);
            
            for (Map<String, Object> item : orderItems) {
                String productName = (String) item.get("product_name");
                Integer quantity = ((Number) item.get("quantity")).intValue();
                BigDecimal price = (BigDecimal) item.get("price");
                
                // In real migration, would look up product_id from product service
                Long productId = 1L; 
                
                microserviceJdbc.update(
                        "INSERT INTO order_items (order_id, product_id, product_name, quantity, price) " +
                        "VALUES (?, ?, ?, ?, ?)",
                        microserviceOrderId, productId, productName, quantity, price);
            }
        }
        
        // Validate migration
        List<Map<String, Object>> monolithOrdersList = monolithJdbc.queryForList(
                "SELECT o.id, o.customer_id, o.total, o.status, COUNT(oi.id) as item_count " +
                "FROM orders o " +
                "JOIN order_items oi ON o.id = oi.order_id " +
                "GROUP BY o.id, o.customer_id, o.total, o.status");
        
        List<Map<String, Object>> microserviceOrdersList = microserviceJdbc.queryForList(
                "SELECT o.id, o.original_id, o.customer_id, o.total, o.status, COUNT(oi.id) as item_count " +
                "FROM orders o " +
                "JOIN order_items oi ON o.id = oi.order_id " +
                "GROUP BY o.id, o.original_id, o.customer_id, o.total, o.status");
        
        assertEquals(monolithOrdersList.size(), microserviceOrdersList.size(), 
                "Number of orders should match");
        
        for (Map<String, Object> monolithOrder : monolithOrdersList) {
            Long monolithId = ((Number) monolithOrder.get("id")).longValue();
            
            Optional<Map<String, Object>> matchingOrder = microserviceOrdersList.stream()
                    .filter(o -> ((Number) o.get("original_id")).longValue() == monolithId)
                    .findFirst();
            
            assertTrue(matchingOrder.isPresent(), 
                    "Could not find matching order with original_id = " + monolithId);
            
            Map<String, Object> microserviceOrder = matchingOrder.get();
            
            assertEquals(monolithOrder.get("customer_id"), microserviceOrder.get("customer_id"), 
                    "Customer ID should match");
            assertEquals(monolithOrder.get("total"), microserviceOrder.get("total"), 
                    "Order total should match");
            assertEquals(monolithOrder.get("status"), microserviceOrder.get("status"), 
                    "Order status should match");
            assertEquals(monolithOrder.get("item_count"), microserviceOrder.get("item_count"), 
                    "Order item count should match");
        }
    }
}
```

## References

- [Testcontainers Documentation](https://www.testcontainers.org/)
- [Getting started with Testcontainers in a Java Spring Boot Project](https://testcontainers.com/guides/testing-spring-boot-rest-api-using-testcontainers/)
- [Testcontainers: Integration Tests for Spring Boot and Databases](https://www.baeldung.com/spring-boot-testcontainers-integration-test)
- [Locust - A modern load testing framework](https://locust.io/)
- [Spring Boot Testing Documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.testing) 