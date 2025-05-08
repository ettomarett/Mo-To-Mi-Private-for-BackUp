import os
import sys
from pathlib import Path

# Get path references
current_dir = Path(__file__).parent.parent.absolute()  # TheFiveinterFace
parent_dir = current_dir.parent.absolute()  # OurHub
project_root = parent_dir.parent.absolute()  # Mo-To-Mi root

# Project directories
PROJECTS_DIR = current_dir / "projects"
MEMORY_DIR = current_dir / "permanent_memories"

# Path to the five agents
ARCHITECT_AGENT_PATH = parent_dir / 'TheFive' / 'ArchitectAgent'
OBSERVER_AGENT_PATH = parent_dir / 'TheFive' / 'ObserverAgent'
STRATEGIST_AGENT_PATH = parent_dir / 'TheFive' / 'StrategistAgent'
BUILDER_AGENT_PATH = parent_dir / 'TheFive' / 'BuilderAgent'
VALIDATOR_AGENT_PATH = parent_dir / 'TheFive' / 'ValidatorAgent'

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
    
    # Create necessary directories
    PROJECTS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)
    
    return True

# Dict of agent types to their paths
AGENT_PATHS = {
    "architect": ARCHITECT_AGENT_PATH,
    "observer": OBSERVER_AGENT_PATH,
    "strategist": STRATEGIST_AGENT_PATH,
    "builder": BUILDER_AGENT_PATH,
    "validator": VALIDATOR_AGENT_PATH
} 