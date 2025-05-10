# Java Code Analyzer Tool

## Overview

The Java Code Analyzer is a specialized tool built for the Observer Agent to analyze Spring Boot monolithic applications and identify potential microservice boundaries. It serves as a "code detective" that explores Java codebases to extract structural information, map dependencies, and suggest logical service boundaries based on code patterns and relationships.

## Purpose

The primary purpose of this tool is to assist in the monolith-to-microservice migration process by providing:

1. **Automated Code Structure Analysis**: Extract and visualize the structure of Spring Boot monolithic applications
2. **Dependency Mapping**: Identify relationships between classes, packages, and Spring components
3. **Boundary Detection**: Suggest logical boundaries for potential microservices based on code patterns and coupling
4. **Migration Planning Support**: Generate reports that help inform migration decisions and strategies

## Technical Design

### Architecture

The Java Analyzer is built with a modular architecture:

```
java_analyzer/
├── setup_analysis_project()  # Project structure creation
├── parse_java_code()         # Java code parsing
├── analyze_code_structure()  # Dependency analysis 
├── generate_visualization()  # Visualization generation
└── create_analysis_report()  # Report creation
```

### Component Responsibilities

1. **Project Setup**: Creates a standardized directory structure for each analysis project
2. **Code Parser**: Processes Java source files to extract class structure, package organization, and Spring annotations
3. **Structure Analyzer**: Maps dependencies between classes and packages
4. **Visualizer**: Creates dependency graphs and other visual representations
5. **Report Generator**: Produces human-readable reports with metrics and recommendations

### Data Flow

1. Java source code is uploaded/provided
2. Parser extracts structural information
3. Analyzer examines relationships and patterns
4. Visualizer creates graphical representations
5. Report Generator creates detailed analysis documents

## Implementation Details

### Technologies Used

- **Code Parsing**: `javalang` library for Java source code parsing
- **Dependency Analysis**: Custom algorithms for relationship mapping
- **Visualization**: `networkx` and `matplotlib` for graph generation
- **Data Storage**: JSON for structured data storage

### Project Structure

Each analysis project maintains the following structure:

```
analysis/
└── {project_name}/
    ├── source_code/       # Copied Java files 
    ├── parsed_structure/  # Parsed code structure (JSON)
    ├── visualizations/    # Generated graphs
    ├── reports/           # Analysis reports
    └── metadata.json      # Project metadata
```

### Key Algorithms

1. **Class Dependency Mapping**:
   - Inheritance relationships
   - Field type dependencies
   - Method parameter/return type dependencies

2. **Package Dependency Analysis**:
   - Cross-package references
   - Package coupling metrics

3. **Boundary Detection**:
   - Entity clustering
   - Service boundary identification
   - API endpoint grouping

## Usage Guide

### Setup Project

Initialize a new analysis project:

```
<mcp:tool>
name: java_analyzer
parameters: {
  "operation": "setup_project",
  "project_name": "my_spring_app"
}
</mcp:tool>
```

### Parse Java Code

Process the Java source files:

```
<mcp:tool>
name: java_analyzer
parameters: {
  "operation": "parse_code",
  "project_name": "my_spring_app",
  "source_path": "/path/to/java/src"
}
</mcp:tool>
```

### Analyze Code Structure

Examine relationships between components:

```
<mcp:tool>
name: java_analyzer
parameters: {
  "operation": "analyze_structure",
  "project_name": "my_spring_app"
}
</mcp:tool>
```

### Generate Visualizations

Create visual representations of the code structure:

```
<mcp:tool>
name: java_analyzer
parameters: {
  "operation": "generate_visualization",
  "project_name": "my_spring_app",
  "output_format": "png"
}
</mcp:tool>
```

### Create Analysis Report

Generate a comprehensive analysis report:

```
<mcp:tool>
name: java_analyzer
parameters: {
  "operation": "create_report",
  "project_name": "my_spring_app",
  "output_format": "markdown"
}
</mcp:tool>
```

## Analysis Capabilities

### Spring Boot Component Detection

The analyzer automatically identifies Spring Boot components:

- **Entities**: Classes annotated with `@Entity`
- **Services**: Classes annotated with `@Service`
- **Repositories**: Classes annotated with `@Repository`
- **Controllers**: Classes annotated with `@Controller` or `@RestController`

### Metrics Generated

The tool produces various metrics to help understand the codebase:

1. **Size Metrics**:
   - Total classes
   - Total packages
   - Lines of code

2. **Complexity Metrics**:
   - Average methods per class
   - Average fields per class
   - Inheritance depth

3. **Coupling Metrics**:
   - Average dependencies per class
   - Average dependencies per package
   - Highly coupled components

4. **Spring Component Metrics**:
   - Entity count
   - Service count
   - Repository count
   - Controller count
   - Endpoints count

### Visualization Types

1. **Package Dependency Graphs**: Shows relationships between packages
2. **Class Dependency Networks**: Details class-level dependencies
3. **Service Relationship Diagrams**: Illustrates service-to-repository connections
4. **Entity Relationship Diagrams**: Shows entity relationships
5. **Boundary Suggestion Maps**: Visualizes potential microservice boundaries

## Report Sections

A typical analysis report includes:

1. **Overview**: General statistics about the codebase
2. **Package Structure**: Details of package organization
3. **Spring Components**: Inventory of Spring-annotated classes
4. **Dependency Analysis**: Coupling and cohesion metrics
5. **Anti-Pattern Detection**: Identification of problematic code patterns
6. **Boundary Recommendations**: Suggested microservice boundaries
7. **Migration Complexity Assessment**: Estimation of migration difficulty

## Integration with Mo-To-Mi Framework

The Java Analyzer is a crucial component in the Mo-To-Mi migration framework:

1. **Observer Agent**: Uses the analyzer to understand the monolithic application
2. **Architect Agent**: Consumes analysis reports to design microservice architecture
3. **Strategist Agent**: Uses boundary suggestions to create migration strategy
4. **Builder Agent**: References the analysis for implementation guidance

## Limitations

Current limitations of the analyzer include:

1. Limited support for reflection-based dependency injection
2. No runtime behavior analysis (static analysis only)
3. Basic support for advanced Spring features (Spring Data, Spring Security)
4. Simplified boundary detection algorithms (will improve in future versions)

## Future Enhancements

Planned enhancements include:

1. Dynamic code analysis integration
2. Machine learning for boundary detection
3. Database schema analysis
4. Runtime performance metrics integration
5. Code quality and tech debt assessment
6. Automated test coverage analysis

## Conclusion

The Java Analyzer tool provides the Observer Agent with powerful code analysis capabilities that form the foundation of the Mo-To-Mi migration process. By automatically analyzing Spring Boot monoliths, it enables data-driven decisions about microservice boundaries and migration strategies.

## References

- Spring Boot Documentation: https://docs.spring.io/spring-boot/docs/current/reference/html/
- Domain-Driven Design Principles: Evans, Eric. "Domain-Driven Design: Tackling Complexity in the Heart of Software"
- Microservice Extraction Patterns: Newman, Sam. "Monolith to Microservices: Evolutionary Patterns to Transform Your Monolith" 