import streamlit as st
from dotenv import load_dotenv
import sys
from pathlib import Path
import importlib.util

# Get absolute paths
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))  # Add to beginning of path to ensure it's found first

# Import paths module directly
paths_module_path = current_dir / "config" / "paths.py"
spec = importlib.util.spec_from_file_location("paths", paths_module_path)
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)

# Run setup_paths function
paths.setup_paths()

# Now that paths are set up, do direct imports of other modules
agent_loader_path = current_dir / "agents" / "agent_loader.py"
spec = importlib.util.spec_from_file_location("agent_loader", agent_loader_path)
agent_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_loader)

ui_common_path = current_dir / "ui" / "common.py"
spec = importlib.util.spec_from_file_location("common", ui_common_path)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

project_dashboard_path = current_dir / "ui" / "project_dashboard.py"
spec = importlib.util.spec_from_file_location("project_dashboard", project_dashboard_path)
project_dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_dashboard)

migration_workflow_path = current_dir / "ui" / "migration_workflow.py"
spec = importlib.util.spec_from_file_location("migration_workflow", migration_workflow_path)
migration_workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_workflow)

session_path = current_dir / "utils" / "session.py"
spec = importlib.util.spec_from_file_location("session", session_path)
session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session)

# Load environment variables
load_dotenv()

# Initialize session state if not already done
session.initialize_session()

# Apply custom styles
common.apply_custom_styles()

# Load agent modules if not already loaded
if 'agent_modules' not in st.session_state or not st.session_state.agent_modules:
    agent_modules, missing_modules = agent_loader.load_agent_modules()
    st.session_state.agent_modules = agent_modules
    
    if missing_modules:
        st.error(f"Failed to load some agent modules: {', '.join(missing_modules)}")
    else:
        st.success("✅ All agent modules imported successfully!")

# Page title
st.title("Mo-To-Mi: Monolith to Microservices Migration")
st.subheader("The Five As Multi-Agent Architecture")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    
    if st.button("Projects Dashboard", key="nav_projects"):
        st.session_state.stage = "project_selection"
        st.rerun()
    
    if st.session_state.current_project_id:
        if st.button("Current Project", key="nav_current_project"):
            st.session_state.stage = "migration_workflow"
            st.rerun()
    
    st.divider()
    
    st.header("Five Agents")
    st.write("✅ **Architect Agent** (The Supervisor)")
    st.write("✅ **Observer Agent** (The Analyzer)")
    st.write("⏳ **Strategist Agent** (The Planner)")
    st.write("⏳ **Builder Agent** (The Coder)")
    st.write("⏳ **Validator Agent** (The Tester)")
    
    st.divider()
    
    # Show current project if selected
    project_data = session.get_current_project_data()
    if project_data:
        st.header("Current Project")
        st.write(f"**Name:** {project_data['name']}")
        st.write(f"**Status:** {project_data['status']}")
        
        # Show migration progress
        st.subheader("Migration Progress")
        
        # Calculate progress percentage based on stages completed
        stages = ["initiation", "analysis", "planning", "implementation", "testing", "completed"]
        current_stage_index = stages.index(project_data["stage"]) if project_data["stage"] in stages else 0
        progress_percentage = (current_stage_index / (len(stages) - 1)) * 100
        
        st.progress(progress_percentage / 100)
        st.write(f"Stage: **{project_data['stage'].capitalize()}**")

# Main content based on current stage
if st.session_state.stage == "project_selection":
    project_dashboard.display_project_dashboard()
elif st.session_state.stage == "migration_workflow":
    project_data = session.get_current_project_data()
    migration_workflow.display_migration_workflow(project_data, st.session_state.agent_modules) 