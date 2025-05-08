# TheFiveinterFace Project Structure

This document provides a comprehensive overview of the project structure and architecture to help developers understand how the application works and how to navigate the codebase.

## Directory Structure

The application is divided into several key directories, each with a specific responsibility:

```
TheFiveinterFace/
│
├── app.py                   # Main entry point for the application
├── run.py                   # Alternative entry point with command-line options
│
├── config/                  # Configuration files
│   ├── constants.py         # System prompts, API settings, and UI styles
│   └── paths.py             # Path configuration and setup (CRITICAL)
│
├── agents/                  # Agent integration layer
│   ├── agent_loader.py      # Dynamic loading of agent modules from TheFive
│   └── chat.py              # Token-managed conversations
│
├── ui/                      # User interface components
│   ├── project_dashboard.py # Project listing and creation
│   ├── migration_workflow.py # Workflow interface with agent tabs
│   └── common.py            # Shared UI elements and styles
│
├── utils/                   # Utility functions
│   ├── conversation_manager.py # Manage saving/loading conversations
│   ├── formatting.py        # Message formatting utilities
│   └── session.py           # Session state management
│
├── models/                  # Data models
│   └── project.py           # Project data model
│
├── saved_chats/             # Directory for saved chat histories
│   └── [agent_type]/        # Subdirectories by agent type
│
└── permanent_memories/      # Directory for permanent memories
```

## Key Components and Their Relationships

### Main Entry Points

- **app.py**: The primary entry point that initializes the application, sets up paths, loads agent modules, and renders the UI.
- **run.py**: An alternative entry point that provides command-line options and manages directory creation.

### Path Configuration (**CRITICAL**)

The `config/paths.py` file is one of the most critical components in the system as it manages:

1. Path references to locate project components
2. The Python import system configuration
3. Path resolution between TheFiveinterFace and TheFive repositories

**⚠️ IMPORTANT: Import Order Considerations**

The `setup_paths()` function in `paths.py` adds various directories to the Python import path, which can cause import conflicts if not carefully managed. The current implementation adds TheFive paths to the beginning of sys.path, which means:

```python
# This ordering can cause conflicts:
sys.path.insert(0, agent_paths)  # TheFive paths are added BEFORE 
```

**Potential Issues:**
- Local imports like `from agents import agent_loader` may resolve to TheFive's agents module instead of TheFiveinterFace's
- Name clashes between modules in TheFiveinterFace and TheFive may occur

**Best Practices:**
- Always use absolute/explicit imports for shared module names
- When importing local modules, consider using direct module loading:
  ```python
  # Instead of:
  from agents import agent_loader  # Prone to path resolution issues
  
  # Use:
  from TheFiveinterFace.agents import agent_loader  # Explicit
  
  # Or load dynamically:
  agent_loader_path = current_dir / "agents" / "agent_loader.py"
  spec = importlib.util.spec_from_file_location("agent_loader", agent_loader_path)
  agent_loader = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(agent_loader)
  ```

### Integration with TheFive

TheFiveinterFace acts as a frontend interface to the agent implementations contained in the TheFive repository. The connection between these two components is managed through:

1. **agents/agent_loader.py**: Dynamically loads agent modules from TheFive
2. **config/paths.py**: Configures Python's import system to locate TheFive modules

The two repositories should be positioned as siblings in the file structure:
```
OurHub/
├── TheFiveinterFace/   # This frontend application
└── TheFive/            # The agent implementations
```

## Core Functionality

### Memory Management

The application implements a three-tier memory system:

1. **Token Management**: Tracks conversation token usage
2. **Conversation Memory**: Saves and loads entire conversations
3. **Permanent Memory**: Stores information across sessions

See the `MEMORY_ARCHITECTURE.md` document for detailed information.

### UI Components

The UI is built with Streamlit and consists of:

1. **Project Dashboard**: For creating and selecting projects
2. **Migration Workflow**: The main interface with tabs for each agent

## Development Guidelines

### Adding New Features

1. **New UI Components**: Add to the `ui/` directory and integrate with the existing pages
2. **New Utility Functions**: Add to the `utils/` directory 
3. **New Agent Capabilities**: Add to the relevant agent in TheFive, then update the integration in TheFiveinterFace

### Modifying Agent Integration

The integration with TheFive agents is handled by `agents/agent_loader.py`. When modifying:

1. Ensure path resolution is correct in `config/paths.py`
2. Test that modules load correctly
3. Update system prompts in `config/constants.py` if needed

### Debugging Import Issues

If you encounter import errors like:
```
ImportError: cannot import name 'X' from 'Y' (unexpected_path/__init__.py)
```

This usually indicates a conflict in the Python path resolution. To fix:

1. Check the import order in `setup_paths()`
2. Consider using direct module loading instead of regular imports
3. Print `sys.path` to debug the actual search order Python is using

## Further Documentation

* `MEMORY_ARCHITECTURE.md`: Detailed memory subsystem documentation
* TheFive/ArchitectAgent/AgentSkeleton/documentation/My_MCP_Framework.md: MCP framework docs 