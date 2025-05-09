import streamlit as st
from dotenv import load_dotenv
import sys
from pathlib import Path
import os
import json
import shutil

# Get absolute paths
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))  # Add to beginning of path to ensure it's found first

# Import paths module directly
from TheFiveinterFace.config.paths import setup_paths

# Run setup_paths function
setup_paths()

# Load environment variables
load_dotenv()

# Import after paths are set up
from TheFiveinterFace.utils.session import initialize_session, get_current_project_data
from TheFiveinterFace.ui.project_dashboard import display_project_dashboard
from TheFiveinterFace.ui.migration_workflow import display_migration_workflow
from TheFiveinterFace.agents import agent_loader
from TheFiveinterFace.ui.common import apply_custom_styles
from TheFiveinterFace.config.paths import MEMORY_DIR, AGENT_MEMORY_DIRS

# Function to migrate existing memories to agent-specific folders
def migrate_existing_memories():
    # Check if migration is needed
    migration_marker = MEMORY_DIR / ".migration_completed"
    if migration_marker.exists():
        return
    
    # Make sure all agent memory directories exist
    for agent_dir in AGENT_MEMORY_DIRS.values():
        agent_dir.mkdir(exist_ok=True, parents=True)
    
    # Check if index.json exists in the main memory directory
    index_path = MEMORY_DIR / "index.json"
    if not index_path.exists():
        # No memories to migrate
        migration_marker.touch()
        return
    
    try:
        # Load the main index
        with open(index_path, 'r', encoding='utf-8') as f:
            main_index = json.load(f)
        
        # Keep track of migrated memories for each agent
        agent_indices = {agent_type: {} for agent_type in AGENT_MEMORY_DIRS.keys()}
        
        # Simple strategy: distribute memories among agents based on content/keywords
        # This is a basic approach - you might want to refine this logic for your specific case
        for key, memory_data in main_index.items():
            target_agent = "architect"  # Default to architect if no specific match
            
            # Get the memory content if possible
            filename = memory_data.get("filename", "")
            memory_path = MEMORY_DIR / filename
            content = ""
            
            if memory_path.exists():
                try:
                    with open(memory_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                except:
                    pass
            
            # Try to determine the best agent based on the memory content or key
            key_lower = key.lower()
            if "code" in content or "code" in key_lower or "implementation" in content:
                target_agent = "builder"
            elif "test" in content or "validation" in key_lower or "verify" in content:
                target_agent = "validator"
            elif "plan" in content or "strategy" in key_lower or "approach" in content:
                target_agent = "strategist"
            elif "analysis" in content or "observe" in key_lower or "structure" in content:
                target_agent = "observer"
            
            # Copy the memory file to the target agent's directory
            if memory_path.exists():
                target_path = AGENT_MEMORY_DIRS[target_agent] / filename
                shutil.copy2(memory_path, target_path)
            
            # Add to the agent's index
            agent_indices[target_agent][key] = memory_data
        
        # Save each agent's index
        for agent_type, agent_index in agent_indices.items():
            agent_index_path = AGENT_MEMORY_DIRS[agent_type] / "index.json"
            with open(agent_index_path, 'w', encoding='utf-8') as f:
                json.dump(agent_index, f, indent=2)
        
        # Create migration marker
        migration_marker.touch()
    
    except Exception as e:
        st.error(f"Error during memory migration: {str(e)}")

# Set up page config
st.set_page_config(
    page_title="Mo-To-Mi TheFiveinterFace",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
apply_custom_styles()

# Migrate memories if needed
migrate_existing_memories()

# Initialize session if not already done
if 'initialized' not in st.session_state:
    initialize_session()

# Load agent modules if not already loaded
if 'agent_modules' not in st.session_state or not st.session_state.agent_modules:
    agent_modules, missing_modules = agent_loader.load_agent_modules()
    st.session_state.agent_modules = agent_modules
    
    if missing_modules:
        st.error(f"Failed to load some agent modules: {', '.join(missing_modules)}")
    else:
        st.success("✅ All agent modules imported successfully!")

# Show the appropriate interface based on state
if st.session_state.get('current_project_id') is None:
    display_project_dashboard()
else:
    display_migration_workflow(
        project_data=get_current_project_data(),
        agent_modules=st.session_state.agent_modules
    ) 