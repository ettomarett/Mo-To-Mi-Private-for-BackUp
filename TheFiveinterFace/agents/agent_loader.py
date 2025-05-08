import importlib.util
import sys
from pathlib import Path

# Get absolute paths
current_dir = Path(__file__).parent.absolute()  # agents directory
root_dir = current_dir.parent  # TheFiveinterFace root

# Direct import of needed modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the paths module
paths_path = root_dir / "config" / "paths.py"
paths = load_module("paths", paths_path)


def load_module_from_path(module_name, file_path):
    """Load a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


# Helper function to verify all modules are loaded
def verify_agent_modules(agent_modules):
    """
    Verify that all agent modules are loaded correctly
    
    Args:
        agent_modules (dict): Dictionary of agent modules
        
    Returns:
        bool: True if all modules are loaded, False otherwise
        list: List of missing modules
    """
    expected_modules = ["architect", "observer", "strategist", "builder", "validator"]
    missing_modules = []
    
    for module_name in expected_modules:
        if module_name not in agent_modules:
            missing_modules.append(module_name.capitalize() + " Agent")
    
    return len(missing_modules) == 0, missing_modules 