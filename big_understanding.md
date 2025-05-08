# Mo-To-Mi - Project Understanding

This document serves as a comprehensive guide to the Mo-To-Mi project, designed to help future LLMs (and developers) quickly understand its structure, components, and functional flows.

## Project Overview

Mo-To-Mi is a multi-agent project designed to help with Spring Boot monolith-to-microservices migration. It employs five specialized AI agents to orchestrate the migration process, backed by a sophisticated memory management system and a user-friendly Streamlit interface.

## Core Architecture

![Architecture Overview](https://mermaid.ink/img/pako:eNqVkl9PwjAUxb_KTR8wIcpLH3wgMDUYDAkJD8YHUrcrmra2-QfDuO9uBwPGkBj3tN6e-zu9PW1HRhtEzrU0W1VxR0RMQWhVVJ-kZmM1nJGEksaXZl4tb-1ssJr17GZa-8m0D_e7J5gNJ_ZhAYtaymHYkCXYfKYpPuxJmGP1Vkqp4JMSL32C0mxUWfZOrwnQQ4aGBMmVXi-V9LZTc1BtrXUhoB1mH6E1mV6DCFIrbB1U5GHmDJDXVOtYRa9YOQ5NSZRgQI9VBEmrQk9_CvapCbILOBcukdBSZiKQGqvdqcYMipI7m8X_5r-pnXTMl2CYEz9jgN01uE8iXcl9nqZpN4JUB-otvlGdZWfoLVEEsvUKlHfH0jfL4WZiR8NbJLnTZS5L5arXGn5u5oXIETXLRlnLBpGrVLQk8bxmtIrNIQYgaFyETYNzZfMXY32KYgeLJIuQu0vTDo5TZf2Pv8Mzlw4h?type=png)

## Project Ecosystem

The project consists of two primary repositories working together:

### TheFiveinterFace

The main application with the user interface, workflow management, and integration components. This is the primary codebase that users interact with directly.

### TheFive

The engine that powers the AI agents and their capabilities. It contains:

- **Agent Implementations**: Individual agent code organized by type
  - `/TheFive/ArchitectAgent/`: Implementation of the Architect Agent
  - `/TheFive/ObserverAgent/`: Implementation of the Observer Agent
  - `/TheFive/StrategistAgent/`: Implementation of the Strategist Agent
  - `/TheFive/BuilderAgent/`: Implementation of the Builder Agent 
  - `/TheFive/ValidatorAgent/`: Implementation of the Validator Agent

- **AgentSkeleton Framework**: The core framework that powers the agents
  - `/TheFive/ArchitectAgent/AgentSkeleton/`: Core agent framework
  - `/TheFive/ArchitectAgent/AgentSkeleton/core/`: Token management, memory bank, etc.
  - `/TheFive/ArchitectAgent/AgentSkeleton/mcp/`: MCP protocol implementation
  - `/TheFive/ArchitectAgent/AgentSkeleton/clients/`: Model-specific client implementations
  - `/TheFive/ArchitectAgent/AgentSkeleton/agents/`: Agent base classes
  - `/TheFive/ArchitectAgent/AgentSkeleton/documentation/`: Framework documentation

The relationship between the two repositories:
- TheFiveinterFace is the front-end application that provides the UI and workflow
- TheFive contains the agent implementations that TheFiveinterFace loads dynamically
- TheFiveinterFace imports functionality from TheFive via the agent_loader.py mechanism

When the application starts:
1. TheFiveinterFace initializes
2. It uses agent_loader.py to dynamically load agent modules from TheFive
3. The loaded agents utilize the AgentSkeleton framework for their core functionality

This separation allows for:
- Independent development of agent implementations
- Reuse of agent capabilities across different interfaces
- Cleaner separation of concerns between UI/workflow and agent intelligence

### Agent System

At the heart of TheFiveinterFace are five specialized agents, each handling a different aspect of the migration process:

1. **Architect Agent**: Overall orchestrator and supervisor
2. **Observer Agent**: Analyzes monolith structure to identify service boundaries
3. **Strategist Agent**: Creates migration blueprints and strategies
4. **Builder Agent**: Generates implementation code for microservices
5. **Validator Agent**: Verifies migration correctness through testing

These agents collaborate to ensure a systematic approach to the migration process.

### Memory Management

The project implements a sophisticated three-tier memory system:

1. **Token Management**: Tracks conversation token usage and provides auto-summarization
2. **Conversation Memory**: Handles saving/loading of chat sessions
3. **Permanent Memory**: Stores critical information that persists across all sessions

This memory architecture is documented in detail in `/TheFiveinterFace/MEMORY_ARCHITECTURE.md`.

### MCP Framework

The Modular Communication Protocol (MCP) framework provides the backbone for agent tool usage:

- Allows agents to execute functions through structured tool calls
- Manages the parsing and execution of tool requests
- Handles memory operations and other capabilities

The MCP framework is documented in `/TheFive/ArchitectAgent/AgentSkeleton/documentation/My_MCP_Framework.md`.

## Project Structure

```
OurHub/
├── TheFiveinterFace/       # The front-end application
│   ├── app.py              # Main application entry point
│   ├── config/             # Configuration settings
│   │   ├── constants.py    # All constants, system prompts, and UI styles
│   │   └── paths.py        # Path configuration and setup
│   ├── agents/             # Agent integration functionality
│   │   ├── agent_loader.py # Code to load agent modules
│   │   └── chat.py         # Agent chat functionality and token management
│   ├── models/             # Data models
│   │   └── project.py      # Project data model and operations
│   ├── ui/                 # User interface components
│   │   ├── common.py       # Common UI elements and styles
│   │   ├── project_dashboard.py # Project listing and creation UI
│   │   └── migration_workflow.py # Migration workflow with agent tabs
│   ├── utils/              # Utility functions
│   │   ├── session.py      # Session state management
│   │   ├── conversation_manager.py # Conversation storage/retrieval
│   │   └── formatting.py   # Message formatting utilities
│   ├── permanent_memories/ # Persistent memory storage
│   ├── saved_chats/        # Saved conversation storage
│   ├── MEMORY_ARCHITECTURE.md # Memory system documentation
│   └── README_STRUCTURE.md # Project structure documentation
│
└── TheFive/                # The agent implementations
    ├── ArchitectAgent/     # Architect agent implementation
    │   └── AgentSkeleton/  # Framework for Architect agent
    │       ├── agents/     # Agent implementation
    │       ├── core/       # Core functionality (token/memory management)
    │       ├── mcp/        # MCP protocol implementation
    │       ├── clients/    # Model clients (Azure, OpenAI)
    │       └── documentation/ # Framework documentation
    ├── ObserverAgent/      # Observer agent implementation
    │   └── AgentSkeleton/  # Framework for Observer agent
    ├── StrategistAgent/    # Strategist agent implementation
    │   └── AgentSkeleton/  # Framework for Strategist agent
    ├── BuilderAgent/       # Builder agent implementation
    │   └── AgentSkeleton/  # Framework for Builder agent
    └── ValidatorAgent/     # Validator agent implementation
        └── AgentSkeleton/  # Framework for Validator agent
```

## Key Files and Their Functions

### Entry Points

- `app.py`: Main entry point that initializes the application, sets up state, and renders UI
- `run.py`: Alternative entry point for specific configurations

### Configuration

- `config/constants.py`: Central location for all constants including:
  - Azure DeepSeek API settings
  - System prompts for each agent
  - UI styling through custom CSS

- `config/paths.py`: Manages all path configurations and system imports

### Agent Implementation

- `agents/chat.py`: Core chat functionality including:
  - Token-managed conversations
  - Auto-summarization logic
  - Message processing

- `agents/agent_loader.py`: Dynamic loading of agent modules from external sources

### Memory Management

- `utils/conversation_manager.py`: Handles saving/loading conversation files
- `utils/session.py`: Manages session state and conversation state transitions

### User Interface

- `ui/migration_workflow.py`: The main migration interface with:
  - Agent tabs for different agent interactions
  - Conversation display and input
  - Memory management UI components
  
- `ui/project_dashboard.py`: Project selection and creation interface

## Execution Flow

### Application Startup

1. `app.py` initializes session state via `initialize_session()`
2. Agent modules are loaded through `agent_loader.py`
3. UI is rendered based on current stage (project selection or workflow)

### User Interaction

1. User selects a project or creates a new one
2. Migration workflow shows tabs for each agent
3. User interacts with agents through chat interface
4. Agents process inputs using MCP tool calls
5. Responses are displayed and stored in conversation history

### Memory Operations

1. Token usage is tracked during conversations
2. Auto-summarization triggers when threshold is reached
3. Conversations can be saved/loaded through sidebar interface
4. Permanent memories are stored/retrieved through memory bank

## Important Documentation

1. **README_STRUCTURE.md**: Overview of project structure and module responsibilities
2. **MEMORY_ARCHITECTURE.md**: Detailed explanation of the memory management systems
3. **My_MCP_Framework.md**: Documentation of the MCP framework that powers agent tools

## Key Functionality Implementation

### Conversation Naming/Storage

Implemented across:
- `utils/conversation_manager.py`: Core storage functions
- `utils/session.py`: Session state management
- `ui/migration_workflow.py`: UI components

Conversations are saved as JSON files in `saved_chats/{agent_type}/` with display names preserved separately from filenames.

### Token Management

Implemented in:
- `agents/chat.py`: Via the `TokenManagedConversation` class
- `AgentSkeleton.core.token_management`: Core implementation

Auto-summarization triggers at configurable thresholds to prevent exceeding token limits.

### Permanent Memory

Implemented via:
- `AgentSkeleton.core.memory_bank`: Core implementation
- UI components in `ui/migration_workflow.py`
- Agent system prompts in `config/constants.py`

Memories are stored as text files in `permanent_memories/` with metadata tracking.

## Extending the Project

### Adding New Agents

1. Add system prompt to `config/constants.py`
2. Update agent initialization in `utils/session.py`
3. Add agent tab in `ui/migration_workflow.py`

### Adding New Tools

1. Define tool in the MCP framework
2. Implement tool executor
3. Update agent system prompts as needed

### Modifying Memory Systems

1. Update `MEMORY_ARCHITECTURE.md` with your changes
2. Modify relevant code in `utils/conversation_manager.py` or `utils/session.py`
3. Update UI components in `ui/migration_workflow.py` if interface changes are needed

## UI Structure

The UI is structured into two main screens:

1. **Project Selection**: Lists existing projects and allows creating new ones
2. **Migration Workflow**: Contains tabs for each agent with:
   - Chat interface for agent interaction
   - Agent-specific actions for migration stages
   - Sidebar with memory management tools:
     - Conversation saving/loading
     - Permanent memory creation/retrieval
     - Token status display

## Troubleshooting Common Issues

### Memory Management Issues

- Check the `saved_chats` and `permanent_memories` directories for file permissions
- Verify correct naming in `conversation_manager.py` functions
- Check token counting logic in `TokenManagedConversation`

### Agent Response Issues

- Review system prompts in `constants.py`
- Check MCP tool parsing in the AgentSkeleton framework
- Examine error messages in Streamlit logs

## Integration Between TheFiveinterFace and TheFive

This section details the exact code implementation that connects the TheFiveinterFace application with the agent implementations in the TheFive repository.

### Path Configuration in `config/paths.py`

The first step in the integration process is defining the paths to the agent implementations:

```python
# Path to the five agents
ARCHITECT_AGENT_PATH = parent_dir / 'TheFive' / 'ArchitectAgent'
OBSERVER_AGENT_PATH = parent_dir / 'TheFive' / 'ObserverAgent'
STRATEGIST_AGENT_PATH = parent_dir / 'TheFive' / 'StrategistAgent'
BUILDER_AGENT_PATH = parent_dir / 'TheFive' / 'BuilderAgent'
VALIDATOR_AGENT_PATH = parent_dir / 'TheFive' / 'ValidatorAgent'

# Dict of agent types to their paths
AGENT_PATHS = {
    "architect": ARCHITECT_AGENT_PATH,
    "observer": OBSERVER_AGENT_PATH,
    "strategist": STRATEGIST_AGENT_PATH,
    "builder": BUILDER_AGENT_PATH,
    "validator": VALIDATOR_AGENT_PATH
}
```

This mapping connects each agent type to its implementation directory in TheFive.

### Path Setup for Dynamic Imports

The `setup_paths()` function adds the necessary directories to Python's import path:

```python
def setup_paths():
    """
    Set up all necessary paths for imports
    """
    # Add paths to sys.path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(parent_dir))
    sys.path.insert(0, str(project_root / 'AgentSkeleton'))
    
    # Add agent paths to sys.path
    for agent_path in [ARCHITECT_AGENT_PATH, OBSERVER_AGENT_PATH, STRATEGIST_AGENT_PATH, 
                      BUILDER_AGENT_PATH, VALIDATOR_AGENT_PATH]:
        sys.path.insert(0, str(agent_path))
        sys.path.insert(0, str(agent_path / 'AgentSkeleton'))
        sys.path.insert(0, str(agent_path / 'AgentSkeleton' / 'agents'))
    
    # Create necessary directories
    PROJECTS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)
    
    return True
```

This ensures that Python can locate all the required modules during dynamic loading.

### ⚠️ Import Path Resolution Issues ⚠️

**CRITICAL WARNING**: The setup_paths() function adds TheFive directories to the BEGINNING of sys.path using sys.path.insert(0, path). This means Python will look for modules in TheFive BEFORE looking in TheFiveinterFace, which can cause significant import problems.

**Potential Issues**:
1. Import statements like `from agents import X` may resolve to TheFive/*/AgentSkeleton/agents instead of TheFiveinterFace/agents
2. Module name collisions between the two repositories can lead to unexpected behavior
3. Changes to TheFiveinterFace modules may not be visible if a similarly named module exists in TheFive

**Mitigation Strategies**:
1. **Use Explicit Imports**: Always use fully qualified imports when possible
   ```python
   # Instead of:
   from agents import agent_loader  # Risky
   
   # Use:
   import TheFiveinterFace.agents.agent_loader as agent_loader  # Explicit
   ```

2. **Direct Module Loading**: For critical components, use Python's module loading machinery directly
   ```python
   # Load module explicitly from a specific path
   import importlib.util
   
   module_path = TheFiveinterFace_path / "agents" / "agent_loader.py"
   spec = importlib.util.spec_from_file_location("agent_loader", module_path)
   agent_loader = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(agent_loader)
   ```

3. **Modify Path Order**: Consider modifying setup_paths() to add TheFiveinterFace paths BEFORE TheFive paths
   ```python
   # Add TheFiveinterFace paths first
   sys.path.insert(0, str(current_dir))
   
   # Then add TheFive paths
   for agent_path in [...]:
       sys.path.append(str(agent_path))  # Use append instead of insert(0)
   ```

4. **Debug Import Paths**: When facing import issues, print the current sys.path to understand the search order
   ```python
   import sys
   print("\n".join(sys.path))
   ```

### Agent Loading in `agents/agent_loader.py`

The `load_agent_modules()` function dynamically loads the agent modules from TheFive:

```python
def load_agent_modules():
    """
    Load all agent modules from their respective paths
    
    Returns:
        dict: A dictionary of agent modules keyed by agent type
    """
    agent_modules = {}
    missing_modules = []
    
    for agent_type, agent_path in paths.AGENT_PATHS.items():
        module_path = str(agent_path / "AgentSkeleton" / "agents" / "deepseek_agent.py")
        agent_module = load_module_from_path(f"{agent_type}_agent", module_path)
        
        if agent_module is None:
            missing_modules.append(agent_type.capitalize())
        else:
            agent_modules[agent_type] = agent_module
    
    return agent_modules, missing_modules
```

This function:
1. Iterates through each agent type and path
2. Constructs the full path to the implementing module (`deepseek_agent.py`)
3. Dynamically loads the module using Python's import machinery
4. Tracks any missing modules for error reporting

### Module Loading Utilities

The dynamic loading is performed by these utility functions:

```python
def load_module_from_path(module_name, file_path):
    """Load a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

### Application Integration in `app.py`

The main application loads the agent modules during initialization:

```python
# Load agent modules if not already loaded
if 'agent_modules' not in st.session_state or not st.session_state.agent_modules:
    agent_modules, missing_modules = agent_loader.load_agent_modules()
    st.session_state.agent_modules = agent_modules
    
    if missing_modules:
        st.error(f"Failed to load some agent modules: {', '.join(missing_modules)}")
    else:
        st.success("✅ All agent modules imported successfully!")
```

The loaded modules are stored in Streamlit's session state for persistence across page refreshes.

### Using Agent Modules in `agents/chat.py`

Finally, the loaded modules are used in the chat processing function:

```python
# Process the message with the appropriate agent module
if agent_type in agent_modules:
    response, updated_conversation = await agent_modules[agent_type].process_with_tools(
        client=client,
        model_name=constants.AZURE_DEEPSEEK_MODEL_NAME,
        question=prompt,
        conversation=conversation,
        memory_bank=memory_bank
    )
else:
    # Fallback to default implementation
    from AgentSkeleton.agents.deepseek_agent import process_with_tools
    response, updated_conversation = await process_with_tools(
        client=client,
        model_name=constants.AZURE_DEEPSEEK_MODEL_NAME,
        question=prompt,
        conversation=conversation,
        memory_bank=memory_bank
    )
```

This function:
1. Checks if the requested agent type is available in the loaded modules
2. If available, calls that agent's `process_with_tools` function
3. If not available, falls back to a default implementation

### Integration Flow Summary

1. `app.py` initializes the application
2. It calls `paths.setup_paths()` to add TheFive directories to the import path
3. It calls `agent_loader.load_agent_modules()` to dynamically load agent implementations
4. When a user interacts with an agent, `chat_with_agent()` in `agents/chat.py` uses the loaded module
5. The agent processes the user input and returns a response using its implementation from TheFive

This architecture provides a clean separation between UI (TheFiveinterFace) and agent intelligence (TheFive) while maintaining seamless integration.

## Conclusion

This document provides a comprehensive overview of the TheFiveinterFace project. By understanding its structure, components, and execution flows, you should be able to navigate, maintain, and extend the codebase effectively.

For more detailed information on specific components, refer to the documentation files mentioned above or explore the code directly using the structure outlined here. 