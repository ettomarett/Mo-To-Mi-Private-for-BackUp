import streamlit as st
import sys
from pathlib import Path
import importlib.util
from datetime import datetime

# Get absolute paths
current_dir = Path(__file__).parent.absolute()  # utils directory
root_dir = current_dir.parent  # TheFiveinterFace root

# Direct import of needed modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the constants and paths modules
constants_path = root_dir / "config" / "constants.py"
constants = load_module("constants", constants_path)

paths_path = root_dir / "config" / "paths.py"
paths = load_module("paths", paths_path)

# Import the conversation manager
conversation_manager_path = root_dir / "utils" / "conversation_manager.py"
conversation_manager = load_module("conversation_manager", conversation_manager_path)

# Import the AgentSkeleton modules directly
import sys
sys.path.append(str(paths.project_root))
sys.path.append(str(paths.parent_dir))
sys.path.append(str(paths.project_root / 'AgentSkeleton'))

# Import required local modules
chat_path = root_dir / "agents" / "chat.py"
chat = load_module("chat", chat_path)

project_path = root_dir / "models" / "project.py"
project = load_module("project", project_path)

def initialize_session():
    """
    Initialize the session state with default values
    
    Returns:
        bool: True if initialized, False if already initialized
    """
    if 'initialized' in st.session_state:
        return False
    
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
    
    st.session_state.client = client
    
    # Initialize separate memory banks for each agent instead of a single shared one
    st.session_state.memory_banks = {}
    for agent_type, memory_dir in paths.AGENT_MEMORY_DIRS.items():
        st.session_state.memory_banks[agent_type] = MemoryBank(str(memory_dir))
    
    # Keep the original memory_bank for backward compatibility
    st.session_state.memory_bank = st.session_state.memory_banks["architect"]
    
    st.session_state.projects = project.get_all_projects()
    
    # Initialize message history for each agent
    st.session_state.architect_messages = []
    st.session_state.observer_messages = []
    st.session_state.strategist_messages = []
    st.session_state.builder_messages = []
    st.session_state.validator_messages = []
    
    # Initialize conversations for each agent
    for agent_type in ["architect", "observer", "strategist", "builder", "validator"]:
        st.session_state[f"{agent_type}_conversation"] = chat.create_conversation_for_agent(
            agent_type, st.session_state.client
        )
    
    # Other state variables
    st.session_state.current_project_id = None
    st.session_state.stage = "project_selection"  # Stages: project_selection, migration_workflow
    st.session_state.agent_modules = {}
    st.session_state.show_token_status = {}  # Dictionary to track token status display for each agent
    
    # Conversation session management
    st.session_state.current_conversation_names = {
        "architect": "New Conversation",
        "observer": "New Conversation", 
        "strategist": "New Conversation",
        "builder": "New Conversation",
        "validator": "New Conversation"
    }
    st.session_state.last_saved_messages = {
        "architect": [],
        "observer": [],
        "strategist": [],
        "builder": [],
        "validator": []
    }
    st.session_state.show_conversation_manager = {}
    
    st.session_state.initialized = True
    return True


def check_agent_module_imports():
    """
    Check if agent modules were successfully imported
    
    Returns:
        bool: True if all modules are loaded, False otherwise
    """
    return len(st.session_state.agent_modules) == 5  # 5 agents expected


def get_agent_message_history(agent_type):
    """
    Get message history for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        list: List of messages
    """
    return st.session_state.get(f"{agent_type}_messages", [])


def add_user_message(agent_type, content):
    """
    Add a user message to the agent history
    
    Args:
        agent_type (str): Agent type
        content (str): Message content
    """
    if f"{agent_type}_messages" not in st.session_state:
        st.session_state[f"{agent_type}_messages"] = []
    
    st.session_state[f"{agent_type}_messages"].append({"role": "user", "content": content})


def add_agent_message(agent_type, content):
    """
    Add an agent message to the agent history
    
    Args:
        agent_type (str): Agent type
        content (str): Message content
    """
    if f"{agent_type}_messages" not in st.session_state:
        st.session_state[f"{agent_type}_messages"] = []
    
    st.session_state[f"{agent_type}_messages"].append({"role": "assistant", "content": content})


def get_current_project_data():
    """
    Get the current project data
    
    Returns:
        dict: Project data or None if no project is selected
    """
    if st.session_state.current_project_id:
        return st.session_state.projects.get(st.session_state.current_project_id)
    return None


def set_current_project(project_id):
    """
    Set the current project
    
    Args:
        project_id (str): Project ID
    """
    st.session_state.current_project_id = project_id
    st.session_state.stage = "migration_workflow"


def get_conversation(agent_type):
    """
    Get the conversation for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        TokenManagedConversation: Conversation for the agent
    """
    if f"{agent_type}_conversation" not in st.session_state:
        st.session_state[f"{agent_type}_conversation"] = chat.create_conversation_for_agent(
            agent_type, st.session_state.client
        )
    
    return st.session_state[f"{agent_type}_conversation"]


def update_conversation(agent_type, conversation):
    """
    Update the conversation for a specific agent
    
    Args:
        agent_type (str): Agent type
        conversation: Updated conversation
    """
    st.session_state[f"{agent_type}_conversation"] = conversation


def get_token_status(agent_type):
    """
    Get token status for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        dict: Token status information
    """
    conversation = get_conversation(agent_type)
    if conversation:
        return conversation.get_token_status()
    return {}


def toggle_token_status(agent_type):
    """
    Toggle token status display for a specific agent
    
    Args:
        agent_type (str): Agent type
    """
    if 'show_token_status' not in st.session_state:
        st.session_state.show_token_status = {}
    
    current_status = st.session_state.show_token_status.get(agent_type, False)
    st.session_state.show_token_status[agent_type] = not current_status


def should_show_token_status(agent_type):
    """
    Check if token status should be shown for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        bool: True if token status should be shown
    """
    if 'show_token_status' not in st.session_state:
        st.session_state.show_token_status = {}
    
    return st.session_state.show_token_status.get(agent_type, False)


def toggle_conversation_manager(agent_type):
    """
    Toggle the conversation manager interface for a specific agent
    
    Args:
        agent_type (str): Agent type
    """
    if 'show_conversation_manager' not in st.session_state:
        st.session_state.show_conversation_manager = {}
    
    current_status = st.session_state.show_conversation_manager.get(agent_type, False)
    st.session_state.show_conversation_manager[agent_type] = not current_status


def should_show_conversation_manager(agent_type):
    """
    Check if conversation manager should be shown for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        bool: True if conversation manager should be shown
    """
    if 'show_conversation_manager' not in st.session_state:
        st.session_state.show_conversation_manager = {}
    
    return st.session_state.show_conversation_manager.get(agent_type, False)


def save_current_conversation(agent_type, name=None):
    """
    Save the current conversation for a specific agent
    
    Args:
        agent_type (str): Agent type
        name (str, optional): Name for the conversation
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    messages = get_agent_message_history(agent_type)
    if not messages:
        return False
    
    # Use current name if not specified
    if not name:
        name = st.session_state.current_conversation_names.get(agent_type, "New Conversation")
    
    # Generate unique name if needed
    if name == "New Conversation" or name.strip() == "":
        # Always use date-time based naming instead of project-based default
        name = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Ensure name is unique
    name = conversation_manager.get_unique_name(agent_type, name)
    
    try:
        # Save the conversation
        conversation_manager.save_conversation(agent_type, name, messages)
        
        # Update session state
        st.session_state.current_conversation_names[agent_type] = name
        st.session_state.last_saved_messages[agent_type] = messages.copy()
        
        return True
    except Exception as e:
        st.error(f"Failed to save conversation: {str(e)}")
        return False


def load_conversation_for_agent(agent_type, name):
    """
    Load a conversation for a specific agent
    
    Args:
        agent_type (str): Agent type
        name (str): Name of the conversation to load
        
    Returns:
        bool: True if loaded successfully, False otherwise
    """
    try:
        # Load the conversation data
        conversation_data = conversation_manager.load_conversation(agent_type, name)
        
        if not conversation_data or not conversation_data.get("messages"):
            return False
        
        # Clear current conversation
        st.session_state[f"{agent_type}_messages"] = []
        
        # Initialize a new conversation with loaded messages
        conversation_messages = conversation_data.get("messages", [])
        conversation = chat.initialize_conversation_with_history(
            agent_type, 
            conversation_messages, 
            st.session_state.client
        )
        
        # Update session state
        st.session_state[f"{agent_type}_messages"] = conversation_messages
        st.session_state[f"{agent_type}_conversation"] = conversation
        st.session_state.current_conversation_names[agent_type] = name
        st.session_state.last_saved_messages[agent_type] = conversation_messages.copy()
        
        return True
    except Exception as e:
        st.error(f"Failed to load conversation: {str(e)}")
        return False


def start_new_conversation(agent_type):
    """
    Start a new conversation for a specific agent
    
    Args:
        agent_type (str): Agent type
        
    Returns:
        bool: True if successfully created, False otherwise
    """
    try:
        # Clear messages
        st.session_state[f"{agent_type}_messages"] = []
        
        # Create fresh conversation
        st.session_state[f"{agent_type}_conversation"] = chat.create_conversation_for_agent(
            agent_type, st.session_state.client
        )
        
        # Update session state
        st.session_state.current_conversation_names[agent_type] = "New Conversation"
        st.session_state.last_saved_messages[agent_type] = []
        
        return True
    except Exception as e:
        st.error(f"Failed to start new conversation: {str(e)}")
        return False 