# The Five: Mo-To-Mi Multi-Agent Architecture

## Overview

The Five is our specialized multi-agent architecture for migrating Spring Boot monoliths to microservices. Each "A" represents a specialized agent focused on a specific aspect of the migration process.

![The Five Architecture](https://via.placeholder.com/800x400.png?text=The+Five+As+Architecture)

## The Agents

### 1. Architect Agent (The Supervisor)
- **Location**: [ArchitectAgent](./ArchitectAgent/)
- **Role**: Orchestrates the entire migration process
- **Responsibilities**: Coordinates all other agents, tracks progress, handles failures, learns from experience

### 2. Observer Agent (The Analyzer)
- **Location**: [ObserverAgent](./ObserverAgent/)
- **Role**: Analyzes the monolith's structure
- **Responsibilities**: Detects dependencies, identifies service boundaries, maps data access patterns

### 3. Strategist Agent (The Planner)
- **Location**: [StrategistAgent](./StrategistAgent/)
- **Role**: Creates the migration blueprint
- **Responsibilities**: Designs service decomposition, defines interfaces, plans database splitting

### 4. Builder Agent (The Coder)
- **Location**: [BuilderAgent](./BuilderAgent/)
- **Role**: Generates implementation code
- **Responsibilities**: Creates service scaffolds, configures infrastructure, implements migrations

### 5. Validator Agent (The Tester)
- **Location**: [ValidatorAgent](./ValidatorAgent/)
- **Role**: Verifies migration correctness
- **Responsibilities**: Generates tests, ensures functional equivalence, validates implementation

## Workflow

The migration process follows this workflow:

1. The **Architect** initializes the migration and coordinates all steps
2. The **Observer** analyzes the monolith and produces an analysis report
3. The **Strategist** creates a migration plan based on the analysis
4. The **Builder** generates implementation code following the plan
5. The **Validator** tests the implementation against the original monolith
6. The **Architect** oversees the process, handles errors, and learns from the experience

## Installation & Usage

Each agent can be installed and run independently, or the entire system can be orchestrated through the Architect Agent:

```bash
# Install all agents
cd TheFiveAs/ArchitectAgent && pip install -e .
cd ../ObserverAgent && pip install -e .
cd ../StrategistAgent && pip install -e .
cd ../BuilderAgent && pip install -e .
cd ../ValidatorAgent && pip install -e .

# Run a complete migration (via the Architect)
python -c "from architect_agent import SupervisorAgent; \
           architect = SupervisorAgent({'model': 'gpt-4'}); \
           architect.coordinate_migration('/path/to/monolith')"
```

## Dependencies

- Python 3.8+
- OpenAI API access (or compatible LLM API)
- Docker and Kubernetes for testing
- Java/Maven for Spring Boot operations

## Documentation

Each agent has its own detailed documentation in its respective folder. See the architecture documentation in the [ultimate_docs](../ultimate_docs/) folder for more details on the overall approach.

## Contributing

To contribute to a specific agent, please see the README in that agent's directory for development guidelines. 