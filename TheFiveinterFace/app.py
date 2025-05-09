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

# Load environment variables
load_dotenv()

# Import after paths are set up
from utils.session import initialize_session, get_current_project_data
from ui.project_dashboard import display_project_dashboard
from ui.migration_workflow import display_migration_workflow
from ui.debug_tools import display_debug_tools
from agents import agent_loader
from ui.common import apply_custom_styles

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

# Initialize debug mode if not set
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Load agent modules if not already loaded
if 'agent_modules' not in st.session_state or not st.session_state.agent_modules:
    agent_modules, missing_modules = agent_loader.load_agent_modules()
    st.session_state.agent_modules = agent_modules
    
    if missing_modules:
        st.error(f"Failed to load some agent modules: {', '.join(missing_modules)}")
    else:
        st.success("✅ All agent modules imported successfully!")

# Debug mode toggle - placed in the sidebar to not disrupt main UI flow
with st.sidebar:
    st.session_state.debug_mode = st.checkbox("🛠️ Debug Mode", value=st.session_state.debug_mode)

# If debug mode is enabled, show debug tools instead of the normal interface
if st.session_state.debug_mode:
    display_debug_tools()
else:
    # Show the appropriate interface based on state
    if st.session_state.get('current_project_id') is None:
        display_project_dashboard()
    else:
        display_migration_workflow(
            project_data=get_current_project_data(),
            agent_modules=st.session_state.agent_modules
        ) 