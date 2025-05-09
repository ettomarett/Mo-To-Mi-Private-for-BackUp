# Mo-To-Mi Application Debugging and Resolution

## Architecture Overview

The Mo-To-Mi application consists of two main repositories:

1. **TheFive** - Contains the core agent implementations
   - ArchitectAgent
   - ObserverAgent
   - StrategistAgent
   - BuilderAgent
   - ValidatorAgent
   - Each agent directory contains an `AgentSkeleton` subdirectory with shared framework code

2. **TheFiveinterFace** - Frontend/UI framework that uses the agent implementations
   - Provides the Streamlit-based user interface
   - Coordinates agent interactions
   - Handles project management and conversation history

## Critical Issues and Resolutions

### 1. Import Path Resolution Issues

#### Problem
The application showed a blank page because TheFive paths were being added to `sys.path` before TheFiveinterFace paths, causing import conflicts and incorrect module resolution.

#### Files Involved
- `app.py` (root directory)
- `TheFiveinterFace/config/paths.py`

#### Solution
We modified `paths.py` to ensure TheFiveinterFace modules are prioritized over TheFive modules:

```python
def setup_paths():
    """
    Set up all necessary paths for imports
    """
    # IMPORTANT: First add TheFiveinterFace to the path to ensure its modules are found first
    sys.path.insert(0, str(current_dir))
    
    # Then add project root and parent dir
    sys.path.append(str(project_root))
    sys.path.append(str(parent_dir))
    sys.path.append(str(project_root / 'AgentSkeleton'))
    
    # Add agent paths to sys.path using append instead of insert(0)
    # This ensures TheFive modules are found AFTER TheFiveinterFace modules
    for agent_path in [ARCHITECT_AGENT_PATH, OBSERVER_AGENT_PATH, STRATEGIST_AGENT_PATH, 
                      BUILDER_AGENT_PATH, VALIDATOR_AGENT_PATH]:
        sys.path.append(str(agent_path))
        sys.path.append(str(agent_path / 'AgentSkeleton'))
        sys.path.append(str(agent_path / 'AgentSkeleton' / 'agents'))
```

We also updated `app.py` to use normal imports after setting up the paths correctly:

```python
# Import paths module directly
from TheFiveinterFace.config.paths import setup_paths

# Run setup_paths function
setup_paths()

# Import after paths are set up
from TheFiveinterFace.utils.session import initialize_session, get_current_project_data
from TheFiveinterFace.ui.project_dashboard import display_project_dashboard
from TheFiveinterFace.ui.migration_workflow import display_migration_workflow
from TheFiveinterFace.agents import agent_loader
from TheFiveinterFace.ui.common import apply_custom_styles
```

### 2. Missing UI Styling

#### Problem
The application's UI was missing styling and appeared without proper formatting because `apply_custom_styles()` wasn't being called in `app.py`.

#### Files Involved
- `app.py`
- `TheFiveinterFace/ui/common.py`

#### Solution
We added the function call in `app.py`:

```python
# Apply custom styles
apply_custom_styles()
```

This function applies the custom CSS defined in `constants.py` to ensure the UI appears correctly with proper styling for headers, tabs, and other UI elements.

### 3. LLM Endpoint Configuration Issues

#### Problem
The application was showing "Serverless endpoint not found" errors because it was using placeholder Azure DeepSeek endpoints in `constants.py`.

#### Files Involved
- `TheFiveinterFace/config/constants.py`
- `TheFive/ArchitectAgent/AgentSkeleton/clients/azure_deepseek_client.py`

#### Solution
We updated the endpoint configuration to use the default values from TheFive's client implementation:

```python
# Azure DeepSeek settings - Update these with your actual endpoint values
AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com")
AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i")
AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1")
```

### 4. Client Initialization Architecture Issues

#### Problem
TheFiveinterFace was initializing the LLM client directly instead of inheriting from TheFive's implementation, breaking the architectural design.

#### Files Involved
- `TheFiveinterFace/utils/session.py`
- `TheFive/ArchitectAgent/AgentSkeleton/clients/azure_deepseek_client.py`

#### Solution
We modified `session.py` to import and use the client from TheFive's AgentSkeleton framework:

```python
# Import from TheFive's AgentSkeleton
# Use the relative path from our paths module to find the right client
from TheFive.ArchitectAgent.AgentSkeleton.clients.azure_deepseek_client import initialize_client
from TheFive.ArchitectAgent.AgentSkeleton.core.memory_bank import MemoryBank

# Initialize the client from AgentSkeleton
client = initialize_client(
    deployment_name=constants.AZURE_DEEPSEEK_MODEL_NAME,
    api_key=constants.AZURE_DEEPSEEK_API_KEY,
    endpoint=constants.AZURE_DEEPSEEK_ENDPOINT
)
```

### 5. Agent Module Loading Issues

#### Problem
The agent loader had syntax errors and didn't properly handle cases where agent paths didn't exist.

#### Files Involved
- `TheFiveinterFace/agents/agent_loader.py`

#### Solution
We enhanced the `agent_loader.py` with better error handling and path verification:

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
        # Ensure the agent path exists
        if not agent_path.exists():
            print(f"Agent path does not exist: {agent_path}")
            missing_modules.append(agent_type.capitalize())
            continue
            
        # Build path to the agent implementation
        module_path = agent_path / "AgentSkeleton" / "agents" / "deepseek_agent.py"
        
        if not module_path.exists():
            print(f"Agent module does not exist: {module_path}")
            missing_modules.append(agent_type.capitalize())
            continue
            
        agent_module = load_module_from_path(f"{agent_type}_agent", str(module_path))
        
        if agent_module is None:
            missing_modules.append(agent_type.capitalize())
        else:
            agent_modules[agent_type] = agent_module
    
    return agent_modules, missing_modules
```

We also added exception handling to the module loading function:

```python
def load_module_from_path(module_name, file_path):
    """Load a module from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module {module_name}: {e}")
        return None
```

## Key Architectural Principles

Understanding these key principles is crucial to maintaining the application:

1. **Layer Separation**: TheFiveinterFace should use agent implementations from TheFive, not reimplement them.
2. **Hierarchy of Imports**: TheFiveinterFace modules should have priority over TheFive modules in import resolution.
3. **Agent Structure**: Each agent tab in TheFiveinterFace should inherit from its corresponding folder in TheFive.
4. **LLM Client Initialization**: The client should be initialized using TheFive's AgentSkeleton framework.
5. **Module Loading**: Agent modules should be loaded dynamically using explicit paths to ensure correct resolution.

## Debugging Recommendations

When debugging similar issues in the future:

1. Check the `sys.path` order to ensure modules are being loaded from the correct locations.
2. Verify that TheFiveinterFace is properly inheriting from TheFive's implementations.
3. Ensure the LLM client is initialized using TheFive's AgentSkeleton framework.
4. Add adequate error handling in module loading to identify issues early.
5. Use explicit imports with full package paths to avoid ambiguity.

The Mo-To-Mi application is now working correctly with proper path resolution, error handling, and adherence to the intended architecture. 