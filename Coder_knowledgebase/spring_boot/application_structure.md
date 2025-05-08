# Spring Boot Application Structure

## Standard Project Structure

A typical Spring Boot application follows a standard Maven/Gradle project structure:

```
src/
├── main/
│   ├── java/
│   │   └── com/
│   │       └── example/
│   │           └── application/
│   │               ├── ApplicationName.java (main class with @SpringBootApplication)
│   │               ├── config/
│   │               │   └── (Configuration classes)
│   │               ├── controller/
│   │               │   └── (REST controllers)
│   │               ├── model/
│   │               │   └── (Domain/entity classes)
│   │               ├── repository/
│   │               │   └── (Data access interfaces)
│   │               ├── service/
│   │               │   └── (Business logic)
│   │               └── util/
│   │                   └── (Utility classes)
│   └── resources/
│       ├── application.properties (or application.yml)
│       ├── static/
│       │   └── (static web resources)
│       └── templates/
│           └── (template files for views)
└── test/
    └── java/
        └── com/
            └── example/
                └── application/
                    └── (test classes)
```

## Key Components

### 1. Entry Point

The main application class with `@SpringBootApplication` annotation serves as the entry point:

```java
@SpringBootApplication
public class ApplicationName {
    public static void main(String[] args) {
        SpringApplication.run(ApplicationName.class, args);
    }
}
```

The `@SpringBootApplication` annotation combines:
- `@Configuration`: Tags the class as a source of bean definitions
- `@EnableAutoConfiguration`: Tells Spring Boot to start adding beans based on classpath settings
- `@ComponentScan`: Tells Spring to scan for components in the current package and below

### 2. Configuration

Spring Boot applications use either `application.properties` or `application.yml` for configuration:

```properties
# application.properties example
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.datasource.username=user
spring.datasource.password=password
spring.jpa.hibernate.ddl-auto=update
server.port=8080
```

or

```yaml
# application.yml example
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mydb
    username: user
    password: password
  jpa:
    hibernate:
      ddl-auto: update
server:
  port: 8080
```

### 3. Package Structure

Most Spring Boot monoliths follow a layered architecture with distinct packages:

- **controller**: HTTP endpoints that accept requests and return responses
- **service**: Business logic implementation
- **repository**: Data access interfaces
- **model**: Domain objects and entities
- **config**: Configuration classes
- **util**: Helper classes and utilities

## Monolithic Characteristics

In monolithic Spring Boot applications, you'll typically find:

1. **Single Application Context**: All beans are managed within a single application context
2. **Shared Database**: All modules access the same database
3. **Direct Bean Dependencies**: Services directly inject and call each other
4. **Tight Coupling**: Changes in one module may affect other modules
5. **Single Deployment Unit**: The entire application is built and deployed as a single WAR/JAR file

## Identifying Service Boundaries

When analyzing Spring Boot monoliths, look for:

1. **Package Structure**: Related controllers, services, and repositories often indicate a potential service boundary
2. **Domain Model Clusters**: Groups of related entities that are frequently used together
3. **Transaction Boundaries**: Operations that need to maintain transactional integrity
4. **Data Access Patterns**: How different parts of the application access database tables

## Common Anti-patterns in Monoliths

1. **God Classes**: Large service classes that handle too many responsibilities
2. **Circular Dependencies**: Services that depend on each other, forming circular references
3. **Inappropriate Intimacy**: Classes that know too much about each other's internals
4. **Feature Envy**: Methods that use more features from other classes than their own
5. **Deep Call Hierarchies**: Long chains of method calls across different services

These anti-patterns can help identify areas that need refactoring when migrating to microservices. 