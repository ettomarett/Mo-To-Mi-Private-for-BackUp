Spring Boot Monolithic Architecture
1. Architecture and Structure
Spring Boot monoliths typically follow a layered MVC/service/repository pattern. For example, a standard architecture has Controllers at the top layer handling HTTP requests, Services with business logic in the middle, Repositories (DAO) interacting with the database, and Entities (JPA domain objects) at the bottom
tom-collings.medium.com
geeksforgeeks.org
. A typical request flows: client → Controller → Service → Repository → Database, then back through JSON response to the client
geeksforgeeks.org
. In this flow, controllers simply parse input and return output, services encapsulate business rules, and repositories perform CRUD on entities. Spring Boot’s component scanning and dependency injection streamline this setup. By default, the @SpringBootApplication on the main class (usually in the root package) enables @ComponentScan, so Spring automatically detects all @Component, @Service, @Repository, @Controller, etc., in that package and subpackages
stackoverflow.com
docs.spring.io
. All those annotated beans (by default singleton-scoped) are auto-registered and can be injected via constructor or field. The Spring IoC container manages bean lifecycles: by default each bean is a singleton (one shared instance per context)
docs.spring.io
; other scopes (prototype, request, session) are available but used less often in stateless monolith services. Typical package layouts are either layered or feature-driven. The “package-by-layer” style groups by technical role (com.example.app.controller, .service, .repository, .entity)
geeksforgeeks.org
geeksforgeeks.org
. An alternative is package-by-feature/domain, where each top-level package represents a bounded feature (e.g. com.shop.user, com.shop.product) containing its own sub-packages (controller, service, repository, dto)
medium.com
phauer.com
. Packaging by feature can increase modularity and reduce coupling, leading to higher cohesion within each package
phauer.com
dev.to
. For example, one project structures code as:
com.shop.user
    ├ controller
    ├ service
    ├ repository
    ├ model
com.shop.product
    ├ controller
    ├ service
    ├ repository
    ├ model
so all user-related classes live under com.shop.user, all product classes under com.shop.product. This approach (akin to vertical slicing) keeps related code together
phauer.com
dev.to
.
2. Spring Boot Component Breakdown
Spring Boot builds on Spring’s stereotypes. The core annotations include:
@RestController: A specialized @Controller that assumes @ResponseBody on methods. It handles HTTP requests and automatically serializes return values (usually JSON)
geeksforgeeks.org
. Use @GetMapping, @PostMapping, etc., to map REST endpoints. In contrast, a plain @Controller (with view templates) is used for MVC web pages, not typically in pure API-driven monoliths.
@Service: Marks a business logic class. It indicates the service layer and is auto-detected as a bean
geeksforgeeks.org
. Services typically call repositories and apply transactional or domain logic.
@Repository: Marks a data access layer bean, often extending JpaRepository or similar. Spring may apply exception translation on these classes. Repositories encapsulate database CRUD operations
geeksforgeeks.org
.
@Component: A generic stereotype for other beans (e.g. util or factory classes). All the above (@Service, @Repository, @Controller) are specializations of @Component.
@Entity: From JPA (Jakarta Persistence). Annotates a domain object as a persistent entity mapped to a database table. For example, a Customer class annotated with @Entity is automatically mapped to a customer table, and its @Id field becomes the primary key
spring.io
.
Bean scopes and lifecycles: by default all these beans are singletons (one instance per application)
docs.spring.io
. Prototype scope (new instance on each injection) exists, as do web-aware scopes (request, session)
docs.spring.io
docs.spring.io
, but stateless services/controllers are usually singletons. Spring manages bean initialization and destruction; important hooks like @PostConstruct or InitializingBean can customize lifecycle if needed (though not shown above). Dependencies between components are typically wired via constructor injection (recommended by Spring Boot docs
docs.spring.io
). For example, a UserController might @Autowired a UserService through its constructor; Spring will find the UserService bean from component scan and inject it. All beans (controllers, services, repositories, custom components) are picked up by the @ComponentScan that is part of @SpringBootApplication on the main class
docs.spring.io
.
3. Best Practices for Maintainable Monoliths
Modular package design (by feature/domain): Organize code so each feature or bounded context has its own package. This modularization (sometimes called a modular monolith) reduces collisions and makes the code easier to navigate
phauer.com
dev.to
. Each feature package can contain its own controllers, services, repositories, DTOs, etc. When well-designed, packages form mini-domains with clear APIs. Spring’s new Modulith support even allows marking packages as modules: by default, each package under the main is treated as a module with internal sub-packages restricted by convention
spring.io
spring.io
.
Separation of concerns & Single Responsibility Principle: Each class should have one clear responsibility. Controllers should only handle HTTP request/response and delegate business logic to services. Services should implement a single business task or use-case. High cohesion within classes and loose coupling between them make code easier to test and maintain. The Single Responsibility Principle states that “a class should only have one reason to change”
springframework.guru
; in practice this means controllers don’t mix data access logic, and services don’t manage web-specific concerns. For example, a UserController should never query the database directly or contain complex business rules – that belongs in a UserService.
Clean architecture / layering: Keep core domain code separate from web and database concerns. A typical clean/hexagonal design would have domain models and service interfaces at the core, with adapters (controllers, repositories) on the outside
dev.to
dev.to
. For instance, you might have:
com.shop.cart
   domain/model/Product.java
   domain/model/Cart.java
   domain/repository/CartRepository.java
   application/service/CartService.java    (interface)
   application/service/impl/CartServiceImpl.java
   infrastructure/adapters/controller/CartController.java
   infrastructure/adapters/repository/JpaCartRepository.java
This separates the core logic (in domain and application packages) from the adapters (infrastructure). The DEV community illustrates this hexagonal approach, where “ports” (interfaces like CartService) define use cases and “adapters” (controllers, repositories) implement them
dev.to
dev.to
. Such layering ensures that business logic isn’t tangled with external APIs or frameworks.
Configuration & Profiles: Store settings in application.properties or application.yml under src/main/resources. Use Spring Profiles to manage environment-specific configs: e.g. application-dev.properties for development, application-prod.properties for production. The base application.properties contains defaults and common settings, and profile-specific files override them when that profile is active
geeksforgeeks.org
geeksforgeeks.org
. Activate a profile via spring.profiles.active in the properties or as a command-line argument. This way you can separate, say, datasource URLs or feature flags per environment without code changes. Centralizing configs in this way also makes it easy to share or override settings (even using external config servers) without touching application code.
Use meaningful layering and DTOs: For complex monoliths, avoid passing JPA entities directly to clients. Instead, map entities to Data Transfer Objects (DTOs) in the service layer. This keeps domain models encapsulated and allows different views or API versions. Tools like MapStruct or ModelMapper can reduce boilerplate. It’s also common to hide internal details by using Java access control: for example, only exposing certain methods from one package to others (as demonstrated in the spring-boot-monolith example below
github.com
).
4. Common Anti-Patterns
God Classes: These are classes that “do too much” – huge classes that bundle many responsibilities. A God class often violates SRP by centralizing unrelated logic, making maintenance and testing difficult. As one source notes, a god object “is a huge class that concentrates a lot of responsibilities, controls and oversees many different objects, and effectively does everything in the application”
linearb.io
. In Spring Boot, you might see a single service or controller handling dozens of endpoints and database operations – a red flag. God classes lead to low cohesion and high coupling.
Feature Entanglement: When a business feature’s logic is scattered across unrelated packages/modules, changes become risky. For example, if user registration logic partially lives in a user package, partly in an email package, and partly in an audit package, it becomes hard to track and modify. Each feature should ideally be encapsulated in its own package or module with clear boundaries.
Over-Shared Repositories or Entities: If you use the same JPA entity or repository class in many different contexts indiscriminately, it can cause tight coupling and unexpected side-effects. For example, a generic PersonRepository used by unrelated domains (e.g. both “customers” and “employees”) can lead to confusion. Better to have distinct repositories per aggregate or bounded context, or use package-private visibility to limit where entities/repositories can be used (see example projects below).
Tight Coupling Between Services: When services directly call each other’s implementations (instead of interfaces) or know too much about each other, the system becomes brittle. For instance, if a BillingService directly instantiates OrderService instead of depending on an interface, or if many components depend on concrete implementations, changes cascade. Monoliths are by nature more coupled than microservices, but aim for loose coupling within the monolith. In fact, a Spring Boot guide notes monoliths often exhibit “tight coupling – different components are closely integrated, making it difficult to modify or scale individual parts”
medium.com
. To avoid this, interact via well-defined interfaces and keep dependencies directional (controllers → services → repos).
Lack of Clear Boundaries/Domain Separation: In a mature monolith, you still want clear logical boundaries (sometimes called modules). Without them, code from different domains freely intermixes. The new Spring Modulith project even codifies this: by default each top-level package is an “API” module and its sub-packages are “internal”. Internal code is automatically prevented from being used by other modules
spring.io
. In contrast, an anti-pattern is when, say, the order.internal classes are directly accessed by inventory code, leading to a “distributed monolith” scenario. Proper domain separation (packages or actual modules) prevents such entanglement.
5. Code Examples
Well-Structured Example (Layered CRUD): The following simplified code shows a clean separation into layers. Each layer has a single responsibility.
// JPA Entity (domain layer)
@Entity
public class User {
    @Id @GeneratedValue
    private Long id;
    private String username;
    private String email;
    // constructors/getters/setters omitted
}

// Repository (data access layer)
@Repository
public interface UserRepository extends JpaRepository<User, Long> { }

// Service (business logic layer)
@Service
public class UserService {
    private final UserRepository userRepo;
    public UserService(UserRepository userRepo) {
        this.userRepo = userRepo;
    }
    public User createUser(User u) {
        // business validation can go here
        return userRepo.save(u);
    }
    public Optional<User> findUser(Long id) {
        return userRepo.findById(id);
    }
}

// REST Controller (presentation layer)
@RestController
@RequestMapping("/users")
public class UserController {
    private final UserService userSvc;
    public UserController(UserService userSvc) {
        this.userSvc = userSvc;
    }

    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User u) {
        User saved = userSvc.createUser(u);
        return ResponseEntity.ok(saved);
    }

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        return userSvc.findUser(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }
}
In this example, UserController delegates to UserService, which in turn calls UserRepository. Each class has a single concern: the controller handles HTTP, the service applies business logic, the repository accesses the DB
tom-collings.medium.com
github.com
. Poorly-Structured Example: A common anti-pattern is mixing layers. For instance, putting all logic in one controller:
@RestController
@RequestMapping("/users")
public class BadController {
    @Autowired
    private UserRepository userRepo;  // Directly injected data layer

    @PostMapping
    public User createUser(@RequestBody User u) {
        // Business logic (e.g. validation) mixed here:
        if (u.getUsername() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Username required");
        }
        // Directly calling repository from controller:
        return userRepo.save(u);
    }

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        // Converting Optional manually and throwing raw exception:
        User u = userRepo.findById(id).orElse(null);
        if (u == null) {
            throw new RuntimeException("User not found");  // poor error handling
        }
        return u;
    }
}
Here, the BadController contains both validation logic and calls the repository directly. This violates separation of concerns: there is no service layer at all, and error handling is inconsistent. Such a “giant controller” is hard to test and maintain. The well-structured version would move validation and exception logic into a UserService or global exception handler, leaving the controller thin
springframework.guru
linearb.io
.
6. Security & Configuration
Spring Security Setup: In a monolith, you typically configure Spring Security either by extending WebSecurityConfigurerAdapter (pre-5.7) or defining a SecurityFilterChain bean. A simple example using the newer lambda style:
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(authz -> authz
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .requestMatchers("/api/**").hasAnyRole("USER","ADMIN")
            .anyRequest().authenticated()
        )
        .httpBasic();  // or formLogin(), etc.
    return http.build();
}
This secures endpoints by role. By default, Spring Security requires all requests to be authenticated, so anyRequest().authenticated() is often the catch-all rule
docs.spring.io
. More specific matchers (e.g. antMatchers or requestMatchers) can restrict certain URLs to certain roles. Role-Based Access Control (RBAC): Define user roles (e.g. ROLE_USER, ROLE_ADMIN) and associate users with roles. Then use hasRole("X") or @PreAuthorize("hasRole('ROLE_ADMIN')") annotations. According to Spring Security docs, RBAC “focuses on defining roles and assigning permissions to those roles, then mapping users to roles”
geeksforgeeks.org
. In practice, you might have a User entity with a roles collection, and Spring Security loads those as GrantedAuthority. For example:
@Override
public void configure(AuthenticationManagerBuilder auth) {
    auth.inMemoryAuthentication()
        .withUser("user").password("{noop}pwd").roles("USER");
        .and()
        .withUser("admin").password("{noop}pwd").roles("USER", "ADMIN");
}
This example shows basic auth with in-memory users for illustration. JWT/Bearer Tokens: For stateless APIs, JSON Web Tokens are popular. In Spring Boot, you can use the spring-boot-starter-oauth2-resource-server dependency to enable JWT support. Example snippet:
# application.yml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://authserver  # URL of token issuer
With this, Spring will expect incoming requests to have Authorization: Bearer <token> and will decode/validate the JWT automatically. Controllers can then use @AuthenticationPrincipal to get the user details. (Configuring JWT involves setting up signing keys or issuer details, which is beyond this summary.) CORS and Filter Chains: For monolithic REST APIs accessed from browsers, configure CORS to allow cross-origin calls. This can be done via annotations or global config. For example:
@RestController
@CrossOrigin(origins = "http://localhost:3000")
@RequestMapping("/api")
public class ApiController { ... }
The @CrossOrigin above enables CORS for that controller (or method) allowing requests from the given origin
spring.io
. By default, @CrossOrigin permits all origins and methods unless specified otherwise
spring.io
. Alternatively, define a CorsConfigurationSource bean to customize CORS globally. The security filter chain may also include filters for logging, request tracing, etc. The primary chain is managed by Spring Security once you configure it (e.g. http.cors().and().csrf().disable() for stateless APIs).
7. Testing and Tooling
Unit vs Integration Tests: Use unit tests (e.g. with JUnit 5 and Mockito) for isolated classes. Mock external dependencies (e.g. mock the UserRepository when testing UserService). For Spring components, use Spring Boot’s test annotations:
@SpringBootTest loads the full application context. It’s useful for integration tests where you want most beans wired up (though usually with an in-memory DB/H2).
@WebMvcTest(SomeController.class) loads only the web layer (controllers, relevant filters) and configures MockMvc for testing HTTP requests without starting the server
spring.io
spring.io
.
@DataJpaTest loads repositories with an in-memory database for DAO layer tests.
You can narrow context with slices (e.g. @RestClientTest, @JsonTest, etc.).
The Spring guide demonstrates testing the web layer: @SpringBootTest with @AutoConfigureMockMvc lets you perform HTTP requests against the controller using MockMvc, while @WebMvcTest spins up only that controller and its immediate support beans
spring.io
. For example, a test can be:
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {
    @Autowired MockMvc mockMvc;
    @Test void testGetUser() throws Exception {
        mockMvc.perform(get("/users/1"))
               .andExpect(status().isOk())
               .andExpect(content().contentType("application/json"));
    }
}
This loads the full app but without an actual server, allowing realistic integration testing of endpoints. Testcontainers and H2: For integration tests involving databases, consider using Testcontainers to spin up real database containers. For example, instead of an in-memory H2, you can run a PostgreSQL container during tests, ensuring your SQL dialect and schema match production. The Testcontainers guide explains replacing H2 with a real DB via a special JDBC URL and a JUnit 5 extension
testcontainers.com
. This reduces differences between dev and test environments. For quick local tests or simple cases, Spring’s auto-configured H2 (in-memory) is convenient, but for confidence use Testcontainers or at least a test-specific DataSource that mirrors production. JUnit and Mockito: Write tests using JUnit 5 (@Test) and use Mockito or Spring’s @MockBean to stub dependencies. For example, to test UserService, one can mock UserRepository to return a sample user. Spring Boot supports injecting mocks in the context with @MockBean. Swagger/OpenAPI Integration: Document the monolith’s REST API with Swagger/OpenAPI. A common approach is to use springdoc-openapi (for Spring Boot 2/3) or Springfox. For instance, adding springdoc-openapi-ui to your dependencies and annotating controllers will automatically generate an OpenAPI spec and serve Swagger UI at /swagger-ui.html. This makes the API self-documenting. Many projects (see example below) integrate Swagger so consumers can see all endpoints and test calls interactively.
8. Real-World Project Examples
mzubal/spring-boot-monolith: Simple package-by-feature monolith. This GitHub project demonstrates a minimal monolithic Spring Boot app where each feature (“service”) lives in its own Java package, and internal classes are hidden via Java visibility
github.com
. The author intentionally uses package-private visibility for internal classes, showing that Spring’s component scanning still works across those boundaries. The README notes: “monolithic spring-boot project with separation of internal components via Java APIs (hiding their internals from others)”
github.com
. In this setup, the package structure might look like:
com.example.app.inventory
    InventoryController.java
    InventoryService.java
    InventoryRepository.java
    InventoryEntity.java
com.example.app.orders
    OrderController.java
    OrderService.java
    OrderRepository.java
    OrderEntity.java
Here each domain (inventory, orders) is isolated. This encourages modular thinking even in a single deployable. (See [102] for details on the philosophy and package layout.)
AlekseyBykov/pets.spring-boot-monolith: Layered architecture with full features. This example application models a multi-tier monolith. Its README explicitly describes “using Layered Architecture: API calls are processed from Controller to Persistence through Service”
github.com
. It includes common real-world concerns: Basic Authentication security, Swagger (via Springfox) for API docs, Spring Actuator, MapStruct for DTOs, and more
github.com
. For instance, it notes “Secured endpoints by using Basic Authentication” and “Springfox Swagger for generating the RESTful contract”
github.com
. The project uses controller-service-repository layers with DTO conversion. This shows a production-like monolith with monitoring and documentation built in. Its architecture diagram (omitted here) would show a typical 3-tier structure: Web (controllers), Service, and Data (repositories/entities) layers.
Spring Modulith Examples: While not a full standalone project, Spring’s modulith example (e.g. the e-commerce sample in the official Spring Blog) shows an application with two modules (inventory, order). Each has an API and internal package, with modulith tests enforcing module boundaries. This highlights best practices for domain separation in monoliths
spring.io
spring.io
. (See the Spring Modulith blog for diagrams and module rules.)
Each of these examples underscores a well-structured monolith: clearly layered code, separation of domains, and use of Spring features for configuration, security, and documentation. They can serve as models when designing or refactoring a Spring Boot monolithic application. Sources: Spring Boot and Spring Framework reference documentation, community tutorials, and real project READMEs
tom-collings.medium.com
geeksforgeeks.org
geeksforgeeks.org
stackoverflow.com
docs.spring.io
geeksforgeeks.org
geeksforgeeks.org
spring.io
docs.spring.io
spring.io
spring.io
dev.to
dev.to
geeksforgeeks.org
geeksforgeeks.org
linearb.io
medium.com
geeksforgeeks.org
docs.spring.io
spring.io
spring.io
testcontainers.com
spring.io
github.com
github.com
.
Citations
Favicon
Controller-Service-Repository. I’ve had a unique opportunity fall into… | by Tom Collings | Medium

https://tom-collings.medium.com/controller-service-repository-16e29a4684e5
Favicon
Spring Boot – Architecture | GeeksforGeeks

https://www.geeksforgeeks.org/spring-boot-architecture/
Favicon
Spring Boot – Architecture | GeeksforGeeks

https://www.geeksforgeeks.org/spring-boot-architecture/
Favicon
The controllers doens't work on my spring boot application - Stack Overflow

https://stackoverflow.com/questions/76077603/the-controllers-doenst-work-on-my-spring-boot-application
Favicon
Spring Beans and Dependency Injection :: Spring Boot

https://docs.spring.io/spring-boot/reference/using/spring-beans-and-dependency-injection.html
Favicon
Bean Scopes :: Spring Framework

https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
Favicon
Spring – Stereotype Annotations | GeeksforGeeks

https://www.geeksforgeeks.org/spring-stereotype-annotations/
Favicon
Package Structure for Modular Monolith and Microservices | by Chi Kim | Medium

https://medium.com/@chikim79/package-structure-for-modular-monolith-and-microservices-8526ad30b6a6
Package by Feature

https://phauer.com/2020/package-by-feature/
Favicon
Hexagonal Architecture in Spring Boot: A Practical Guide - DEV Community

https://dev.to/jhonifaber/hexagonal-architecture-or-port-adapters-23ed
Favicon
Spring – REST Controller | GeeksforGeeks

https://www.geeksforgeeks.org/spring-rest-controller/
Favicon
Getting Started | Accessing Data with JPA

https://spring.io/guides/gs/accessing-data-jpa
Favicon
Bean Scopes :: Spring Framework

https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
Favicon
Introducing Spring Modulith

https://spring.io/blog/2022/10/21/introducing-spring-modulith
Favicon
Introducing Spring Modulith

https://spring.io/blog/2022/10/21/introducing-spring-modulith
Favicon
Single Responsibility Principle - Spring Framework Guru

https://springframework.guru/principles-of-object-oriented-design/single-responsibility-principle/
Favicon
Hexagonal Architecture in Spring Boot: A Practical Guide - DEV Community

https://dev.to/jhonifaber/hexagonal-architecture-or-port-adapters-23ed
Favicon
Hexagonal Architecture in Spring Boot: A Practical Guide - DEV Community

https://dev.to/jhonifaber/hexagonal-architecture-or-port-adapters-23ed
Favicon
Spring Boot – Managing Application Properties with Profiles | GeeksforGeeks

https://www.geeksforgeeks.org/spring-boot-managing-application-properties-with-profiles/
Favicon
Spring Boot – Managing Application Properties with Profiles | GeeksforGeeks

https://www.geeksforgeeks.org/spring-boot-managing-application-properties-with-profiles/
Favicon
GitHub - mzubal/spring-boot-monolith: Simple example of monolithic spring-boot app with components isolated using Java visibility modifiers.

https://github.com/mzubal/spring-boot-monolith
Favicon
What Is a God Class and Why Should We Avoid It? | LinearB Blog

https://linearb.io/blog/what-is-a-god-class
Favicon
Monolithic and Microservice Architectures in Spring Boot | by Vinotech | Medium

https://medium.com/@vino7tech/monolithic-and-microservice-architectures-in-spring-boot-6a294e507dea
Favicon
GitHub - AlekseyBykov/pets.spring-boot-monolith: An example of Spring Boot monolith application with using Layered Architecture. Includes decoupled backend only.

https://github.com/AlekseyBykov/pets.spring-boot-monolith
Favicon
Authorize HttpServletRequests :: Spring Security

https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html
Favicon
Example of RBAC in Spring Security | GeeksforGeeks

https://www.geeksforgeeks.org/example-of-rbac-in-spring-security/
Favicon
Getting Started | Enabling Cross Origin Requests for a RESTful Web Service

https://spring.io/guides/gs/rest-service-cors
Favicon
Getting Started | Enabling Cross Origin Requests for a RESTful Web Service

https://spring.io/guides/gs/rest-service-cors
Favicon
Getting Started | Testing the Web Layer

https://spring.io/guides/gs/testing-web
Favicon
Getting Started | Testing the Web Layer

https://spring.io/guides/gs/testing-web
Favicon
The simplest way to replace H2 with a real database for testing

https://testcontainers.com/guides/replace-h2-with-real-database-for-testing/
Favicon
GitHub - AlekseyBykov/pets.spring-boot-monolith: An example of Spring Boot monolith application with using Layered Architecture. Includes decoupled backend only.

https://github.com/AlekseyBykov/pets.spring-boot-monolith
Favicon
GitHub - AlekseyBykov/pets.spring-boot-monolith: An example of Spring Boot monolith application with using Layered Architecture. Includes decoupled backend only.

https://github.com/AlekseyBykov/pets.spring-boot-monolith
All Sources
Favicontom-collings.medium
Favicongeeksforgeeks
Faviconstackoverflow
Favicondocs.spring
Faviconmedium
phauer
Favicondev
Faviconspring
Faviconspringframework
Favicongithub
Faviconlinearb
Favicontestcontainers