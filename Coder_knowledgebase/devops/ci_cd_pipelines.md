# CI/CD Pipelines for Microservices Migration

## Overview

Continuous Integration and Continuous Deployment (CI/CD) pipelines are essential for microservices, enabling frequent and reliable software delivery. When migrating from a monolith to microservices, the CI/CD approach must evolve from building and deploying a single application to handling multiple independent services.

## Pipeline Evolution During Migration

### Monolithic Pipeline vs. Microservice Pipelines

**Monolithic Pipeline:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Build      │ ──► │  Test       │ ──► │  Package    │ ──► │  Deploy     │
│  Monolith   │     │  Monolith   │     │  Monolith   │     │  Monolith   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Microservice Pipelines:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Build      │ ──► │  Test       │ ──► │  Package    │ ──► │  Deploy     │ Service A
│  Service A  │     │  Service A  │     │  Service A  │     │  Service A  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Build      │ ──► │  Test       │ ──► │  Package    │ ──► │  Deploy     │ Service B
│  Service B  │     │  Service B  │     │  Service B  │     │  Service B  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Transitional Pipeline Approach

During migration, implement a hybrid approach that maintains the monolith pipeline while adding pipelines for extracted microservices:

1. **Monolith Pipeline**: Continues to build and deploy the shrinking monolith
2. **Microservice Pipelines**: New pipelines for each extracted service
3. **Integration Tests**: Cross-service tests to verify the overall system behavior

## Spring Boot Microservice Pipeline Implementation

### GitHub Actions Example

`.github/workflows/microservice-pipeline.yml`:

```yaml
name: Microservice CI/CD Pipeline

on:
  push:
    branches: [ main ]
    paths:
      - 'services/user-service/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'services/user-service/**'

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./services/user-service

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        cache: maven
        
    - name: Build with Maven
      run: mvn -B package --file pom.xml
    
    - name: Run unit tests
      run: mvn test
    
    - name: Run integration tests
      run: mvn verify -P integration-test
    
    - name: Build Docker image
      run: |
        docker build -t user-service:${{ github.sha }} .
        docker tag user-service:${{ github.sha }} myregistry/user-service:${{ github.sha }}
        docker tag user-service:${{ github.sha }} myregistry/user-service:latest
    
    - name: Login to Docker Registry
      uses: docker/login-action@v2
      with:
        registry: myregistry
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Push Docker image
      run: |
        docker push myregistry/user-service:${{ github.sha }}
        docker push myregistry/user-service:latest
    
  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    environment: development
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      
    - name: Set Kubernetes context
      uses: azure/k8s-set-context@v2
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG_DEV }}
        
    - name: Deploy to development
      run: |
        cd ./services/user-service/k8s
        sed -i "s|myregistry/user-service:latest|myregistry/user-service:${{ github.sha }}|g" deployment.yaml
        kubectl apply -f deployment.yaml
        kubectl apply -f service.yaml
        kubectl rollout status deployment/user-service
        
  deploy-prod:
    needs: deploy-dev
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      
    - name: Set Kubernetes context
      uses: azure/k8s-set-context@v2
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}
        
    - name: Deploy to production
      run: |
        cd ./services/user-service/k8s
        sed -i "s|myregistry/user-service:latest|myregistry/user-service:${{ github.sha }}|g" deployment.yaml
        kubectl apply -f deployment.yaml
        kubectl apply -f service.yaml
        kubectl rollout status deployment/user-service
```

### Jenkins Pipeline Example

`Jenkinsfile` for a Spring Boot microservice:

```groovy
pipeline {
    agent any
    
    environment {
        SERVICE_NAME = "user-service"
        DOCKER_REGISTRY = "myregistry"
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${SERVICE_NAME}"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS_ID = "docker-credentials"
        K8S_CONFIG_ID = "k8s-config"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh 'mvn clean package -DskipTests'
                }
            }
        }
        
        stage('Test') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh 'mvn test'
                }
            }
            post {
                always {
                    junit "services/${SERVICE_NAME}/target/surefire-reports/*.xml"
                }
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    withSonarQubeEnv('SonarQube') {
                        sh 'mvn sonar:sonar'
                    }
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
                }
            }
        }
        
        stage('Push Docker Image') {
            steps {
                withCredentials([string(credentialsId: DOCKER_CREDENTIALS_ID, variable: 'DOCKER_PASSWORD')]) {
                    sh "echo ${DOCKER_PASSWORD} | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USERNAME} --password-stdin"
                    sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
        }
        
        stage('Deploy to Development') {
            steps {
                withCredentials([file(credentialsId: K8S_CONFIG_ID, variable: 'KUBECONFIG')]) {
                    dir("services/${SERVICE_NAME}/k8s") {
                        sh "sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${DOCKER_TAG}|g' deployment.yaml"
                        sh "kubectl apply -f deployment.yaml"
                        sh "kubectl apply -f service.yaml"
                        sh "kubectl rollout status deployment/${SERVICE_NAME}"
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                dir("services/${SERVICE_NAME}") {
                    sh 'mvn verify -P integration-test'
                }
            }
            post {
                always {
                    junit "services/${SERVICE_NAME}/target/failsafe-reports/*.xml"
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            input {
                message "Deploy to production?"
                ok "Yes"
            }
            steps {
                withCredentials([file(credentialsId: 'k8s-config-prod', variable: 'KUBECONFIG')]) {
                    dir("services/${SERVICE_NAME}/k8s") {
                        sh "sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${DOCKER_TAG}|g' deployment.yaml"
                        sh "kubectl apply -f deployment.yaml"
                        sh "kubectl apply -f service.yaml"
                        sh "kubectl rollout status deployment/${SERVICE_NAME}"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "Build successful!"
        }
        failure {
            echo "Build failed!"
        }
        always {
            cleanWs()
        }
    }
}
```

## Testing Strategies in Microservice Pipelines

### Unit Testing in Isolation

```java
@SpringBootTest
@AutoConfigureMockMvc
public class UserControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private UserService userService;
    
    @Test
    public void getUserById_ShouldReturnUser() throws Exception {
        // Given
        User user = new User(1L, "test@example.com", "Test User");
        when(userService.findById(1L)).thenReturn(user);
        
        // When & Then
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.email").value("test@example.com"))
            .andExpect(jsonPath("$.name").value("Test User"));
    }
}
```

### Integration Testing with TestContainers

```java
@SpringBootTest
@Testcontainers
public class UserRepositoryIntegrationTest {
    
    @Container
    public static MySQLContainer<?> mySQLContainer = new MySQLContainer<>("mysql:8.0")
            .withDatabaseName("testdb")
            .withUsername("testuser")
            .withPassword("testpass");
    
    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mySQLContainer::getJdbcUrl);
        registry.add("spring.datasource.username", mySQLContainer::getUsername);
        registry.add("spring.datasource.password", mySQLContainer::getPassword);
    }
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    public void testSaveAndFindUser() {
        // Given
        User user = new User(null, "test@example.com", "Test User");
        
        // When
        User savedUser = userRepository.save(user);
        
        // Then
        assertNotNull(savedUser.getId());
        
        User foundUser = userRepository.findById(savedUser.getId()).orElse(null);
        assertNotNull(foundUser);
        assertEquals("test@example.com", foundUser.getEmail());
    }
}
```

### Contract Testing with Spring Cloud Contract

Producer Side (`user-service`):

```groovy
// src/test/resources/contracts/shouldReturnUser.groovy
Contract.make {
    description "should return user by id=1"
    
    request {
        method GET()
        url "/api/users/1"
    }
    
    response {
        status 200
        headers {
            contentType applicationJson()
        }
        body(
            id: 1,
            email: "test@example.com",
            name: "Test User"
        )
    }
}
```

Consumer Side (`order-service`):

```java
@SpringBootTest
@AutoConfigureMockMvc
@AutoConfigureStubRunner(
    ids = {"com.example:user-service:+:stubs:8081"},
    stubsMode = StubRunnerProperties.StubsMode.LOCAL
)
public class UserServiceClientTest {
    
    @Autowired
    private UserServiceClient userServiceClient;
    
    @Test
    public void shouldReturnUserById() {
        // When
        User user = userServiceClient.getUserById(1L);
        
        // Then
        assertNotNull(user);
        assertEquals(1L, user.getId());
        assertEquals("test@example.com", user.getEmail());
        assertEquals("Test User", user.getName());
    }
}
```

## End-to-End Testing for Migration Validation

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class MigrationValidationTest {
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Value("${monolith.base-url}")
    private String monolithBaseUrl;
    
    @Test
    public void userApiResponsesShouldMatch() {
        // Call monolith endpoint
        ResponseEntity<UserDTO> monolithResponse = 
            restTemplate.getForEntity(monolithBaseUrl + "/api/users/1", UserDTO.class);
        
        // Call microservice endpoint
        ResponseEntity<UserDTO> microserviceResponse = 
            restTemplate.getForEntity("/api/users/1", UserDTO.class);
        
        // Verify responses match
        assertEquals(HttpStatus.OK, monolithResponse.getStatusCode());
        assertEquals(HttpStatus.OK, microserviceResponse.getStatusCode());
        assertEquals(monolithResponse.getBody().getId(), microserviceResponse.getBody().getId());
        assertEquals(monolithResponse.getBody().getEmail(), microserviceResponse.getBody().getEmail());
        assertEquals(monolithResponse.getBody().getName(), microserviceResponse.getBody().getName());
    }
}
```

## Feature Flagging in CI/CD

Integration with feature flags for controlled deployment:

```java
@Component
public class FeatureFlagService {
    
    private final FFClient ffClient;
    
    public FeatureFlagService(FFClient ffClient) {
        this.ffClient = ffClient;
    }
    
    public boolean isFeatureEnabled(String featureName, String userId) {
        return ffClient.boolVariation(featureName, userId, false);
    }
}
```

Pipeline integration:

```yaml
- name: Deploy with feature flag
  run: |
    if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      # Enable feature flag for 10% of users
      curl -X PATCH \
        https://api.featureflag-service.com/flags/use-user-microservice \
        -H 'Authorization: Bearer ${{ secrets.FF_API_KEY }}' \
        -H 'Content-Type: application/json' \
        -d '{"enabled": true, "rolloutPercentage": 10}'
    fi
```

## Building a Migration-Focused Pipeline

### Migration-Specific Pipeline Steps

1. **Verify API Compatibility**: Ensure microservice APIs match monolith endpoints
2. **Data Migration Validation**: Verify data consistency between old and new databases
3. **Performance Comparison**: Compare response times between monolith and microservice
4. **Traffic Shadowing**: Route copies of production traffic to microservices
5. **Rollback Plan**: Automated rollback procedures if issues detected

Example GitHub Actions workflow:

```yaml
name: Microservice Migration Validation

on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service being migrated'
        required: true
      percentage:
        description: 'Traffic percentage to route to microservice'
        required: true
        default: '0'

jobs:
  validate-migration:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: API Compatibility Check
      run: |
        cd ./migration-tools
        ./api-compatibility-check.sh ${{ github.event.inputs.service }}
    
    - name: Data Consistency Validation
      run: |
        cd ./migration-tools
        ./data-consistency-check.sh ${{ github.event.inputs.service }}
    
    - name: Performance Comparison
      run: |
        cd ./migration-tools
        ./performance-comparison.sh ${{ github.event.inputs.service }}
    
    - name: Update Traffic Routing
      if: success()
      run: |
        cd ./migration-tools
        ./update-traffic-routing.sh ${{ github.event.inputs.service }} ${{ github.event.inputs.percentage }}
```

## Local CI/CD for Development

For local microservices development, implement lightweight CI/CD:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Git Hooks  │ ──► │  Local      │ ──► │  Local      │ ──► │  Docker     │
│  Pre-commit │     │  Build+Test │     │  Container  │     │  Compose Up │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

Example pre-commit hook (`pre-commit.sh`):

```bash
#!/bin/bash
SERVICE_PATH="./services/user-service"

echo "Running pre-commit checks for $SERVICE_PATH"

# Check code style
cd $SERVICE_PATH && ./mvnw spotless:check

# Run unit tests
cd $SERVICE_PATH && ./mvnw test

# Build to check compilation
cd $SERVICE_PATH && ./mvnw clean package -DskipTests
```

Local development script (`dev-deploy.sh`):

```bash
#!/bin/bash
SERVICE_NAME=$1

# Build service
cd ./services/$SERVICE_NAME && ./mvnw clean package -DskipTests

# Build Docker image
docker build -t $SERVICE_NAME:local ./services/$SERVICE_NAME

# Update docker-compose.yml with new image
sed -i "s|image: $SERVICE_NAME:.*|image: $SERVICE_NAME:local|g" docker-compose.yml

# Restart service
docker-compose stop $SERVICE_NAME
docker-compose up -d $SERVICE_NAME

# Show logs
docker-compose logs -f $SERVICE_NAME
```

## References

- [Building and testing Java with Maven - GitHub Actions](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-java-with-maven)
- [Spring Boot CI/CD Pipeline Tutorial](https://medium.com/@contactkumaramit9139/step-by-step-guide-to-build-ci-cd-pipeline-for-spring-boot-microservices-33ddb545f95c)
- [Spring Cloud Contract Documentation](https://spring.io/projects/spring-cloud-contract)
- [TestContainers for Java](https://www.testcontainers.org/) 