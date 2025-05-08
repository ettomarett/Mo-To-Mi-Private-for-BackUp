# Security Patterns for Microservices Migration

## Overview

Transitioning from a monolithic application to microservices introduces significant security challenges. Security boundaries that were previously internal to the monolith become exposed network boundaries in a microservices architecture. This document outlines key security patterns and implementation approaches for ensuring robust security during and after microservice migration.

## Security Challenges in Microservices

### 1. Expanded Attack Surface

Microservices expose more network interfaces and APIs, increasing the potential attack surface:

```
Monolith:                     Microservices:
┌─────────────────┐           ┌─────────────┐   ┌─────────────┐
│                 │           │   Service   │   │   Service   │
│                 │           │      A      │   │      B      │
│    Monolith     │           └──────┬──────┘   └──────┬──────┘
│                 │                  │                 │
│                 │                  │                 │
└────────┬────────┘           ┌──────┴──────┐   ┌──────┴──────┐
         │                    │   Service   │   │   Service   │
         │                    │      C      │   │      D      │
┌────────┴────────┐           └──────┬──────┘   └──────┬──────┘
│     External    │                  │                 │
│   API Gateway   │           ┌──────┴─────────────────┴──────┐
└─────────────────┘           │        API Gateway            │
                              └────────────────────────────────┘
```

### 2. Distributed Authentication and Authorization

Authentication and authorization decisions must be coordinated across multiple services.

### 3. Service-to-Service Communication

Services need secure methods to communicate with each other.

### 4. Secrets Management

Credentials and secrets must be securely distributed to multiple services.

### 5. Data Protection

Sensitive data may flow between services, requiring encryption in transit and at rest.

## Authentication Patterns

### 1. Token-Based Authentication with OAuth 2.0/OIDC

OAuth 2.0 and OpenID Connect (OIDC) provide standardized protocols for authentication and authorization in distributed systems.

#### Implementation with Spring Security OAuth2

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests(authorize -> authorize
                .antMatchers("/api/public/**").permitAll()
                .antMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt()
            );
    }
}
```

Application properties configuration:

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          keycloak:
            client-id: my-client
            client-secret: my-secret
            authorization-grant-type: authorization_code
            scope: openid,profile,email
        provider:
          keycloak:
            issuer-uri: http://keycloak:8080/auth/realms/myrealm
      resourceserver:
        jwt:
          issuer-uri: http://keycloak:8080/auth/realms/myrealm
```

### 2. API Gateway Authentication

Centralize authentication at the API Gateway to reduce duplication and ensure consistent policy enforcement.

```yaml
# Spring Cloud Gateway configuration
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - name: TokenRelay
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
```

### 3. Identity Propagation

Propagate user identity through service calls to maintain the security context.

```java
@Component
public class UserContextFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        
        // Extract JWT token from Authorization header
        String authHeader = httpRequest.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            UserContextHolder.getContext().setAuthToken(token);
        }
        
        // Extract correlation ID for tracing
        String correlationId = httpRequest.getHeader("X-Correlation-ID");
        if (correlationId != null) {
            UserContextHolder.getContext().setCorrelationId(correlationId);
        }
        
        chain.doFilter(httpRequest, response);
    }
}

@Component
public class UserContextInterceptor implements ClientHttpRequestInterceptor {
    
    @Override
    public ClientHttpResponse intercept(HttpRequest request, byte[] body,
            ClientHttpRequestExecution execution) throws IOException {
        
        HttpHeaders headers = request.getHeaders();
        
        // Propagate the authentication token
        headers.add("Authorization", "Bearer " + 
            UserContextHolder.getContext().getAuthToken());
        
        // Propagate the correlation ID
        headers.add("X-Correlation-ID", 
            UserContextHolder.getContext().getCorrelationId());
        
        return execution.execute(request, body);
    }
}
```

## Authorization Patterns

### 1. Role-Based Access Control (RBAC)

Assign roles to users and define permissions for roles.

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    
    @GetMapping
    @PreAuthorize("hasRole('USER')")
    public List<Order> getOrders() {
        // Return orders for the authenticated user
    }
    
    @GetMapping("/all")
    @PreAuthorize("hasRole('ADMIN')")
    public List<Order> getAllOrders() {
        // Return all orders (admin only)
    }
    
    @PostMapping
    @PreAuthorize("hasRole('USER')")
    public Order createOrder(@RequestBody Order order) {
        // Create a new order
    }
    
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @orderSecurity.isOrderOwner(authentication, #id)")
    public void deleteOrder(@PathVariable Long id) {
        // Delete an order
    }
}

@Component("orderSecurity")
public class OrderSecurityEvaluator {
    
    @Autowired
    private OrderRepository orderRepository;
    
    public boolean isOrderOwner(Authentication authentication, Long orderId) {
        String username = authentication.getName();
        Order order = orderRepository.findById(orderId).orElse(null);
        return order != null && order.getUsername().equals(username);
    }
}
```

### 2. Policy-Based Access Control

Define access policies centrally and enforce them across services.

```java
@Configuration
@EnableResourceServer
public class ResourceServerConfig extends ResourceServerConfigurerAdapter {
    
    @Override
    public void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
            .antMatchers(HttpMethod.GET, "/api/products/**").permitAll()
            .antMatchers(HttpMethod.POST, "/api/products").hasAuthority("SCOPE_product:write")
            .antMatchers(HttpMethod.PUT, "/api/products/**").hasAuthority("SCOPE_product:write")
            .antMatchers(HttpMethod.DELETE, "/api/products/**").hasAuthority("SCOPE_product:admin")
            .anyRequest().authenticated();
    }
}
```

### 3. Attribute-Based Access Control (ABAC)

Make access decisions based on attributes of the user, resource, action, and environment.

```java
@Component
public class AbacPermissionEvaluator implements PermissionEvaluator {
    
    @Autowired
    private PolicyEnforcementPoint pep;
    
    @Override
    public boolean hasPermission(Authentication authentication, Object targetDomainObject, 
                                 Object permission) {
        
        // Build access request with attributes
        Map<String, Object> subject = extractSubjectAttributes(authentication);
        Map<String, Object> resource = extractResourceAttributes(targetDomainObject);
        Map<String, Object> action = Map.of("name", permission);
        Map<String, Object> environment = extractEnvironmentAttributes();
        
        // Evaluate policy
        return pep.isAllowed(subject, resource, action, environment);
    }
    
    // Implementation of other methods...
}
```

## Service-to-Service Security

### 1. Mutual TLS (mTLS)

Enforce mutual authentication between services using TLS certificates.

```yaml
# application.yml
server:
  ssl:
    key-store: classpath:keystore.p12
    key-store-password: ${KEY_STORE_PASSWORD}
    key-store-type: PKCS12
    key-alias: microservice
    enabled: true
    client-auth: need
    trust-store: classpath:truststore.p12
    trust-store-password: ${TRUST_STORE_PASSWORD}
```

Spring WebClient configuration for mTLS:

```java
@Configuration
public class WebClientConfig {
    
    @Bean
    public WebClient webClient(WebClient.Builder builder, SSLContext sslContext) {
        HttpClient httpClient = HttpClient.create()
            .secure(sslSpec -> sslSpec.sslContext(sslContext));
        
        return builder
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
    
    @Bean
    public SSLContext sslContext() throws Exception {
        // Load key store with client certificate
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        keyStore.load(
            new ClassPathResource("keystore.p12").getInputStream(), 
            System.getProperty("KEY_STORE_PASSWORD").toCharArray());
        
        // Load trust store with trusted certificates
        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        trustStore.load(
            new ClassPathResource("truststore.p12").getInputStream(),
            System.getProperty("TRUST_STORE_PASSWORD").toCharArray());
        
        // Create SSL context with mutual authentication
        SSLContextBuilder sslContextBuilder = SSLContexts.custom()
            .loadKeyMaterial(keyStore, System.getProperty("KEY_STORE_PASSWORD").toCharArray())
            .loadTrustMaterial(trustStore, null);
        
        return sslContextBuilder.build();
    }
}
```

### 2. Client Credentials Flow

Use OAuth 2.0 client credentials flow for service-to-service authentication.

```java
@Configuration
public class ServiceSecurityConfig {
    
    @Bean
    public OAuth2RestTemplate oAuth2RestTemplate(OAuth2ProtectedResourceDetails details) {
        return new OAuth2RestTemplate(details);
    }
    
    @Bean
    public OAuth2ProtectedResourceDetails clientCredentials() {
        ClientCredentialsResourceDetails details = new ClientCredentialsResourceDetails();
        details.setAccessTokenUri("http://auth-server/oauth/token");
        details.setClientId("service-client");
        details.setClientSecret("service-secret");
        details.setScope(Arrays.asList("service"));
        return details;
    }
}
```

Service client implementation:

```java
@Service
public class UserServiceClient {
    
    private final OAuth2RestTemplate oAuth2RestTemplate;
    
    public UserServiceClient(OAuth2RestTemplate oAuth2RestTemplate) {
        this.oAuth2RestTemplate = oAuth2RestTemplate;
    }
    
    public User getUserById(Long userId) {
        return oAuth2RestTemplate.getForObject(
            "http://user-service/api/users/{id}", User.class, userId);
    }
}
```

### 3. API Keys

Use API keys for simple service-to-service authentication.

```java
@Configuration
public class ServiceClientConfig {
    
    @Value("${service.api-key}")
    private String apiKey;
    
    @Bean
    public RestTemplate restTemplate() {
        RestTemplate restTemplate = new RestTemplate();
        restTemplate.getInterceptors().add((request, body, execution) -> {
            request.getHeaders().add("X-API-Key", apiKey);
            return execution.execute(request, body);
        });
        return restTemplate;
    }
}
```

API key validation filter:

```java
@Component
public class ApiKeyFilter extends OncePerRequestFilter {
    
    @Value("${service.valid-api-keys}")
    private List<String> validApiKeys;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) 
            throws ServletException, IOException {
        
        String apiKey = request.getHeader("X-API-Key");
        
        if (apiKey == null || !validApiKeys.contains(apiKey)) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
        
        filterChain.doFilter(request, response);
    }
}
```

## Secrets Management

### 1. Spring Cloud Config with Vault

Use HashiCorp Vault with Spring Cloud Config for centralized secrets management.

Dependencies:

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-vault-config</artifactId>
</dependency>
```

Configuration:

```yaml
spring:
  cloud:
    vault:
      host: vault
      port: 8200
      scheme: http
      authentication: token
      token: ${VAULT_TOKEN}
      kv:
        enabled: true
        backend: secret
        default-context: application
  config:
    import: vault://
```

Using secrets in the application:

```java
@RestController
public class SecretController {
    
    @Value("${secret.database.username}")
    private String dbUsername;
    
    @Value("${secret.database.password}")
    private String dbPassword;
    
    @GetMapping("/status")
    public String getStatus() {
        // Use secrets to connect to the database
        return "Connected with credentials";
    }
}
```

### 2. Kubernetes Secrets

Store secrets in Kubernetes and mount them as environment variables or files.

Kubernetes Secret definition:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
type: Opaque
data:
  username: dXNlcm5hbWU=  # Base64 encoded
  password: cGFzc3dvcmQ=  # Base64 encoded
```

Deployment using the secret:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
      - name: order-service
        image: order-service:1.0
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: password
```

## Traffic Encryption

### 1. Transport Layer Security (TLS)

Encrypt all service-to-service communication using TLS.

```yaml
# application.yml
server:
  port: 8443
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: ${KEY_STORE_PASSWORD}
    key-store-type: PKCS12
    key-alias: microservice
```

### 2. API Gateway TLS Termination

Terminate TLS at the API Gateway and use internal service mesh for internal communication.

```yaml
# Spring Cloud Gateway configuration
server:
  port: 8443
  ssl:
    enabled: true
    key-store: classpath:gateway-keystore.p12
    key-store-password: ${KEY_STORE_PASSWORD}
    key-store-type: PKCS12
    key-alias: api-gateway
```

## Security Patterns for Migration

### 1. Dual Authentication Strategies

Support both legacy and new authentication mechanisms during migration.

```java
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .anyRequest().authenticated()
                .and()
            .oauth2Login()  // New OAuth2 authentication
                .and()
            .formLogin()    // Legacy form-based authentication
                .loginPage("/login")
                .permitAll();
    }
}
```

### 2. Security Event Broadcasting

Broadcast security events (login, logout, etc.) to ensure consistent security state across services.

```java
@Component
public class SecurityEventPublisher {
    
    private final ApplicationEventPublisher eventPublisher;
    
    public SecurityEventPublisher(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }
    
    @EventListener
    public void handleAuthenticationSuccessEvent(AuthenticationSuccessEvent event) {
        User user = (User) event.getAuthentication().getPrincipal();
        
        // Publish user login event for other services
        eventPublisher.publishEvent(new UserLoggedInEvent(
            user.getUsername(), 
            extractAuthorities(user), 
            new Date()
        ));
    }
    
    @EventListener
    public void handleLogoutSuccessEvent(LogoutSuccessEvent event) {
        User user = (User) event.getAuthentication().getPrincipal();
        
        // Publish user logout event for other services
        eventPublisher.publishEvent(new UserLoggedOutEvent(
            user.getUsername(), 
            new Date()
        ));
    }
}
```

### 3. Backward Compatible Security Headers

Maintain backward compatibility by supporting both old and new security headers.

```java
@Component
public class SecurityHeadersFilter extends OncePerRequestFilter {
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) 
            throws ServletException, IOException {
        
        // Extract security info from request
        String legacyToken = request.getHeader("X-Auth-Token");
        String bearerToken = null;
        
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            bearerToken = authHeader.substring(7);
        }
        
        // Use new token format if available, otherwise fall back to legacy
        String token = bearerToken != null ? bearerToken : legacyToken;
        
        if (token != null) {
            // Validate token and set security context
            // ...
        }
        
        filterChain.doFilter(request, response);
    }
}
```

## Security Monitoring and Response

### 1. Centralized Logging with Security Events

Monitor security events across all services in a centralized logging system.

```java
@Component
public class SecurityEventLogger {
    
    private static final Logger log = LoggerFactory.getLogger("SECURITY_EVENTS");
    
    @EventListener
    public void handleAuthenticationEvent(AbstractAuthenticationEvent event) {
        if (event instanceof AuthenticationSuccessEvent) {
            log.info("Authentication success: {}", event.getAuthentication().getName());
        } else if (event instanceof AuthenticationFailureBadCredentialsEvent) {
            log.warn("Authentication failure: {}", event.getAuthentication().getName());
        } else if (event instanceof AuthenticationFailureLockedEvent) {
            log.warn("Authentication failure (account locked): {}", 
                     event.getAuthentication().getName());
        }
    }
    
    @EventListener
    public void handleAccessDeniedEvent(AccessDeniedEvent event) {
        log.warn("Access denied: {}, resource: {}", 
                 event.getAuthentication().getName(),
                 event.getAccessDeniedException().getMessage());
    }
}
```

### 2. Rate Limiting

Implement rate limiting to prevent abuse.

```yaml
# Spring Cloud Gateway rate limiting configuration
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
                key-resolver: "#{@ipKeyResolver}"
```

Custom rate limiter resolver:

```java
@Configuration
public class RateLimiterConfig {
    
    @Bean
    public KeyResolver ipKeyResolver() {
        return exchange -> {
            String ip = exchange.getRequest().getRemoteAddress().getAddress().getHostAddress();
            return Mono.just(ip);
        };
    }
    
    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> {
            // Extract user from JWT token if possible
            String token = exchange.getRequest().getHeaders()
                .getFirst(HttpHeaders.AUTHORIZATION);
            
            if (token != null && token.startsWith("Bearer ")) {
                try {
                    String userName = extractUserFromToken(token.substring(7));
                    return Mono.just(userName);
                } catch (Exception e) {
                    // Fall back to IP-based limiting
                    return ipKeyResolver().resolve(exchange);
                }
            }
            
            return ipKeyResolver().resolve(exchange);
        };
    }
}
```

## References

- [Spring Security Reference](https://docs.spring.io/spring-security/reference/index.html)
- [OAuth 2.0 and OpenID Connect](https://oauth.net/2/)
- [mTLS in Spring Boot](https://spring.io/guides/tutorials/spring-boot-oauth2/)
- [Spring Cloud Gateway Reference](https://docs.spring.io/spring-cloud-gateway/docs/current/reference/html/)
- [HashiCorp Vault with Spring Cloud Config](https://spring.io/guides/gs/vault-config/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) 