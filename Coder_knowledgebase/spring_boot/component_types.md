# Spring Boot Component Types

This document describes the main component types in Spring Boot applications and their roles in a monolithic architecture.

## Controller Layer

Controllers handle HTTP requests and return responses. They are the entry points to the application.

### REST Controllers

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    private final UserService userService;
    
    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(userService.create(user));
    }
    
    // Other endpoints
}
```

**Key Annotations:**
- `@RestController`: Combines `@Controller` and `@ResponseBody`, indicating that the class handles requests and returns objects as JSON/XML
- `@RequestMapping`: Maps requests to controller methods
- `@GetMapping`, `@PostMapping`, etc.: Shorthand for `@RequestMapping(method = RequestMethod.GET)`, etc.

**Responsibilities:**
- Request validation
- Calling appropriate service methods
- Response formatting
- Error handling

## Service Layer

Services contain the business logic of the application.

```java
@Service
public class UserServiceImpl implements UserService {
    
    private final UserRepository userRepository;
    private final EmailService emailService;
    
    @Autowired
    public UserServiceImpl(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
    
    @Override
    @Transactional(readOnly = true)
    public User findById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    }
    
    @Override
    @Transactional
    public User create(User user) {
        User savedUser = userRepository.save(user);
        emailService.sendWelcomeEmail(savedUser);
        return savedUser;
    }
    
    // Other business methods
}
```

**Key Annotations:**
- `@Service`: Indicates that the class contains business logic
- `@Transactional`: Manages database transactions

**Responsibilities:**
- Implementing business rules
- Coordinating repositories
- Managing transactions
- Calling other services

## Repository Layer

Repositories handle data access and persistence.

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    
    Optional<User> findByEmail(String email);
    
    @Query("SELECT u FROM User u WHERE u.lastLoginDate < :date")
    List<User> findInactiveUsers(@Param("date") LocalDate date);
    
    // Other data access methods
}
```

**Key Annotations:**
- `@Repository`: Indicates that the class is a data access component
- `@Query`: Defines custom JPQL/SQL queries

**Responsibilities:**
- Database CRUD operations
- Custom query execution
- Data mapping

## Entity Classes

Entities represent database tables and business objects.

```java
@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(unique = true, nullable = false)
    private String email;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<Order> orders = new ArrayList<>();
    
    // Getters, setters, constructors
}
```

**Key Annotations:**
- `@Entity`: Marks the class as a JPA entity
- `@Table`: Specifies the database table name
- `@Id`: Marks the primary key
- `@Column`: Defines column properties
- `@OneToMany`, `@ManyToOne`, etc.: Define relationships

**Relationships in Monoliths:**
- Entities in monoliths often have complex relationships
- Bidirectional relationships are common
- Eager loading might be used more frequently
- Cascade operations often span multiple entities

## Configuration Classes

Configuration classes set up beans and application settings.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
                .antMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .formLogin();
    }
    
    // Other configuration methods
}
```

**Key Annotations:**
- `@Configuration`: Indicates that the class contains bean definitions
- `@Bean`: Defines a bean to be managed by Spring
- `@EnableWebSecurity`, `@EnableAsync`, etc.: Enables various Spring features

**Types of Configuration:**
- Security configuration
- Web MVC configuration
- Database configuration
- Cache configuration
- Async task configuration

## Component Boundaries

In monolithic applications, the boundaries between components are logical rather than physical:

1. **Controllers call Services**: Direct method invocation
2. **Services call other Services**: Bean injection and direct method calls
3. **Services use Repositories**: Direct data access
4. **All components share the same context**: Global application context
5. **Configuration applies to everything**: Shared configuration

These tight couplings make it challenging to extract microservices, as many dependencies need to be identified and managed during the migration process. 