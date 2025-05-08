# Monitoring and Observability for Microservices

## Overview

Monitoring and observability are critical for managing microservices architectures. While monitoring focuses on tracking predefined metrics, observability provides a holistic understanding of system behavior through logs, metrics, and traces. Both are essential for migration from monoliths to microservices, where debugging becomes more complex due to distributed nature.

## The Three Pillars of Observability

### 1. Metrics

Quantitative measurements collected over time, such as:

- Request rates and response times
- Error rates
- Resource utilization (CPU, memory, network)
- Business metrics (orders processed, users active)

### 2. Logs

Timestamped records of events in the system:

- Application logs
- Access logs
- Error logs
- Audit logs

### 3. Traces

Records of request flows as they traverse multiple services:

- Service calls with timing information
- Parent-child relationship between service calls
- Error propagation details

## Spring Boot Actuator

Spring Boot Actuator provides production-ready features for monitoring and managing applications.

### Basic Setup

Add the dependency to your Spring Boot application:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

### Configuration

Configure Actuator in `application.yml`:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always
  metrics:
    export:
      prometheus:
        enabled: true
```

### Key Endpoints

- `/actuator/health`: System health information
- `/actuator/info`: Application information
- `/actuator/metrics`: Metrics information
- `/actuator/prometheus`: Prometheus format metrics
- `/actuator/loggers`: Logger configuration
- `/actuator/httptrace`: Recent HTTP requests (if enabled)

### Custom Health Indicators

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {
    
    private final DataSource dataSource;
    
    public DatabaseHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }
    
    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            PreparedStatement ps = conn.prepareStatement("SELECT 1");
            ResultSet rs = ps.executeQuery();
            
            if (rs.next()) {
                return Health.up()
                    .withDetail("database", "Available")
                    .build();
            } else {
                return Health.down()
                    .withDetail("database", "No data returned")
                    .build();
            }
        } catch (SQLException e) {
            return Health.down()
                .withDetail("database", "Unavailable")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

### Custom Metrics

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    
    private final OrderService orderService;
    private final MeterRegistry meterRegistry;
    
    public OrderController(OrderService orderService, MeterRegistry meterRegistry) {
        this.orderService = orderService;
        this.meterRegistry = meterRegistry;
    }
    
    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody Order order) {
        Order createdOrder = orderService.createOrder(order);
        
        // Record business metric
        meterRegistry.counter("orders.created.count").increment();
        meterRegistry.gauge("orders.amount", createdOrder.getTotalAmount());
        
        return ResponseEntity.status(HttpStatus.CREATED).body(createdOrder);
    }
}
```

## Distributed Tracing with Spring Cloud Sleuth and Zipkin

### 1. Setup

Add dependencies:

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-sleuth-zipkin</artifactId>
</dependency>
```

### 2. Configuration

```yaml
spring:
  application:
    name: order-service
  sleuth:
    sampler:
      probability: 1.0  # Sample 100% of requests in development
  zipkin:
    base-url: http://zipkin:9411
```

### 3. Trace Propagation

Spring Cloud Sleuth automatically adds trace and span IDs to:

- HTTP headers
- Message broker messages
- Logger MDC context

```java
@Service
public class OrderService {
    
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    
    private final RestTemplate restTemplate;
    
    public OrderService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    public Order processOrder(Order order) {
        log.info("Processing order {}", order.getId());  // Trace IDs added automatically
        
        // Call user service - trace context propagated automatically
        User user = restTemplate.getForObject("http://user-service/api/users/{id}", 
                                               User.class, order.getUserId());
        
        log.info("Retrieved user {} for order {}", user.getId(), order.getId());
        
        // Process order
        return order;
    }
}
```

### 4. Zipkin Server Setup

Run Zipkin server using Docker:

```yaml
# docker-compose.yml
services:
  zipkin:
    image: openzipkin/zipkin
    ports:
      - "9411:9411"
```

## Metrics with Prometheus and Grafana

### 1. Prometheus Integration

Add Micrometer Prometheus dependency:

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

### 2. Prometheus Server Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'spring-actuator'
    metrics_path: '/actuator/prometheus'
    scrape_interval: 5s
    static_configs:
      - targets: ['user-service:8080', 'order-service:8080', 'payment-service:8080']
```

Run Prometheus with Docker:

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### 3. Grafana Dashboards

Run Grafana with Docker:

```yaml
# docker-compose.yml
services:
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
```

**JVM Dashboard Configuration:**

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 1,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "bytes"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "10.0.3",
      "targets": [
        {
          "datasource": "Prometheus",
          "editorMode": "code",
          "expr": "sum by (instance)(jvm_memory_used_bytes{area=\"heap\"})",
          "legendFormat": "{{instance}} - Heap Used",
          "range": true,
          "refId": "A"
        },
        {
          "datasource": "Prometheus",
          "editorMode": "code",
          "expr": "sum by (instance)(jvm_memory_committed_bytes{area=\"heap\"})",
          "hide": false,
          "legendFormat": "{{instance}} - Heap Committed",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "JVM Heap Memory",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": [
    "java",
    "spring boot"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-15m",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "JVM Metrics Dashboard",
  "version": 0,
  "weekStart": ""
}
```

## Centralized Logging with ELK Stack

### 1. Logback Configuration for Spring Boot

Add logstash encoder dependency:

```xml
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.3</version>
</dependency>
```

Configure logback.xml:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>
    
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>${CONSOLE_LOG_PATTERN}</pattern>
            <charset>utf8</charset>
        </encoder>
    </appender>
    
    <appender name="LOGSTASH" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/application.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/application.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>7</maxHistory>
        </rollingPolicy>
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <customFields>{"application":"${spring.application.name}","profile":"${spring.profiles.active}"}</customFields>
        </encoder>
    </appender>
    
    <root level="INFO">
        <appender-ref ref="CONSOLE" />
        <appender-ref ref="LOGSTASH" />
    </root>
</configuration>
```

### 2. ELK Stack Setup

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
      
  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./logs:/logs
    depends_on:
      - elasticsearch
      
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  esdata:
```

Logstash pipeline configuration:

```
# logstash/pipeline/logstash.conf
input {
  file {
    path => "/logs/application*.log"
    codec => json
    type => "logback"
  }
}

filter {
  if [type] == "logback" {
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[application]}-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
```

## Monitoring Migration Progress

During monolith to microservices migration, specific metrics and visualizations can help track progress:

### 1. Traffic Shift Metrics

Track percentage of requests handled by microservices vs. monolith:

```java
@Component
public class MigrationMetricsFilter implements Filter {
    
    private final MeterRegistry meterRegistry;
    
    public MigrationMetricsFilter(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        String uri = httpRequest.getRequestURI();
        
        // Determine if request is handled by microservice or monolith
        boolean isMicroservice = uri.startsWith("/api/v2/");
        
        // Increment counter based on destination
        if (isMicroservice) {
            meterRegistry.counter("requests.destination", "type", "microservice").increment();
        } else {
            meterRegistry.counter("requests.destination", "type", "monolith").increment();
        }
        
        chain.doFilter(request, response);
    }
}
```

### 2. Performance Comparison Dashboard

Create Grafana dashboard comparing:
- Response times between monolith and microservices implementations
- Error rates between implementations
- Resource utilization

### 3. Migration Status Metrics

```java
@Component
public class MigrationStatusReporter {
    
    private final MeterRegistry meterRegistry;
    private final Map<String, Boolean> migrationStatus;
    
    public MigrationStatusReporter(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
        this.migrationStatus = new HashMap<>();
        
        // Initialize migration status
        migrationStatus.put("users", true);
        migrationStatus.put("orders", true);
        migrationStatus.put("products", false);
        migrationStatus.put("payments", false);
        
        // Report migration status
        updateMigrationMetrics();
    }
    
    public void setMigrationStatus(String service, boolean migrated) {
        migrationStatus.put(service, migrated);
        updateMigrationMetrics();
    }
    
    private void updateMigrationMetrics() {
        int migratedServices = 0;
        int totalServices = migrationStatus.size();
        
        for (Map.Entry<String, Boolean> entry : migrationStatus.entrySet()) {
            meterRegistry.gauge("migration.status", 
                Tags.of("service", entry.getKey()), 
                entry.getValue() ? 1 : 0);
                
            if (entry.getValue()) {
                migratedServices++;
            }
        }
        
        // Overall migration progress as percentage
        double progressPercentage = (double) migratedServices / totalServices * 100;
        meterRegistry.gauge("migration.progress.percentage", progressPercentage);
    }
}
```

## Alert Configuration

### 1. Prometheus Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
- name: microservices-alerts
  rules:
  - alert: HighErrorRate
    expr: sum(rate(http_server_requests_seconds_count{status=~"5.."}[1m])) / sum(rate(http_server_requests_seconds_count[1m])) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High HTTP error rate"
      description: "Error rate is above 5% (current value: {{ $value }})"

  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[5m])) by (le, service, instance)) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Slow response time"
      description: "95th percentile of response time is above 500ms for service {{ $labels.service }} (instance {{ $labels.instance }})"

  - alert: InstanceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."

  - alert: HighMemoryUsage
    expr: sum(jvm_memory_used_bytes{area="heap"}) by (instance) / sum(jvm_memory_max_bytes{area="heap"}) by (instance) > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "JVM memory usage is above 80% for {{ $labels.instance }}"
```

### 2. Alert Integration with Slack

Configure Alertmanager:

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - channel: '#alerts'
    send_resolved: true
    title: "{{ .CommonAnnotations.summary }}"
    text: "{{ .CommonAnnotations.description }}"
    title_link: 'http://your-grafana-url/d/microservices'
```

## Local Monitoring Setup

For local development and testing:

```yaml
# docker-compose-monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/alerts.yml:/etc/prometheus/alerts.yml
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --web.console.libraries=/etc/prometheus/console_libraries
      - --web.console.templates=/etc/prometheus/consoles
      - --web.enable-lifecycle
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    depends_on:
      - prometheus
      
  alertmanager:
    image: prom/alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - --config.file=/etc/alertmanager/alertmanager.yml
      
  zipkin:
    image: openzipkin/zipkin
    ports:
      - "9411:9411"
      
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
      
  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./logs:/logs
    depends_on:
      - elasticsearch
      
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  esdata:
```

## References

- [Spring Boot Actuator](https://docs.spring.io/spring-boot/reference/actuator/index.html)
- [Observability with Spring Boot](https://docs.spring.io/spring-boot/reference/actuator/observability.html)
- [Distributed Tracing with Spring Cloud Sleuth and Zipkin](https://medium.com/@bubu.tripathy/distributed-tracing-with-spring-cloud-sleuth-and-zipkin-9106c8afd349)
- [Prometheus Spring Boot Metrics](https://grafana.com/docs/grafana-cloud/monitor-applications/asserts/enable-prom-metrics-collection/application-frameworks/springboot/)
- [Spring Boot Logs Aggregation and Monitoring Using ELK Stack](https://auth0.com/blog/spring-boot-logs-aggregation-and-monitoring-using-elk-stack/) 