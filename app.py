import streamlit as st
from dotenv import load_dotenv
import sys
from pathlib import Path

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

# Set up page config
st.set_page_config(
    page_title="Mo-To-Mi TheFiveinterFace",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
apply_custom_styles()

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