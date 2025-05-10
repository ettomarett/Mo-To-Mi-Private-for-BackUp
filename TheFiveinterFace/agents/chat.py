import asyncio
import sys
from pathlib import Path
import importlib.util

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

# Add TheFive directory to the Python path for importing centralized system prompts
thefive_dir = Path(paths.project_root) / "TheFive"
if str(thefive_dir) not in sys.path:
    sys.path.append(str(thefive_dir))

# Import system prompts from centralized file
from Agents_System_Prompts import get_system_prompt

# Import the AgentSkeleton modules directly
import sys
sys.path.append(str(root_dir.parent.parent))  # Project root
sys.path.append(str(root_dir.parent))  # Parent dir
sys.path.append(str(root_dir.parent.parent / 'AgentSkeleton'))  # AgentSkeleton

from AgentSkeleton.core.token_management import TokenManagedConversation

# Import the agent protocol modules to get the full system prompts with tools
def load_agent_protocol(agent_type):
    """Load an agent's protocol module to access its create_system_prompt_with_tools function"""
    agent_path = paths.AGENT_PATHS.get(agent_type)
    if not agent_path:
        return None
        
    protocol_path = agent_path / "AgentSkeleton" / "mcp_framework" / "protocol.py"
    if not protocol_path.exists():
        print(f"Warning: Protocol file not found for {agent_type} at {protocol_path}")
        return None
        
    try:
        protocol_module = load_module(f"{agent_type}_protocol", protocol_path)
        return protocol_module
    except Exception as e:
        print(f"Warning: Could not load {agent_type}'s protocol module: {e}")
        return None

def create_conversation_for_agent(agent_type, client):
    """Create a conversation instance for a specific agent"""
    conversation = TokenManagedConversation(
        max_tokens=100000,
        client=client,
        model_name="deepseek-chat"  # Use a placeholder model name, will be overridden by actual call
    )
    
    # Load the agent's protocol module to get the full system prompt with tools
    protocol_module = load_agent_protocol(agent_type)
    
    if protocol_module and hasattr(protocol_module, "create_system_prompt_with_tools"):
        # Use the agent's protocol.py create_system_prompt_with_tools which includes tools
        print(f"Setting system prompt for {agent_type} from protocol.py")
        system_prompt = protocol_module.create_system_prompt_with_tools()
    else:
        # Fallback to centralized system prompt without tools
        print(f"Falling back to base system prompt for {agent_type} without tools")
        # Import system prompts from centralized file
        from Agents_System_Prompts import get_system_prompt
        system_prompt = get_system_prompt(agent_type)
    
    # Set the system prompt
    conversation.set_system_prompt(system_prompt)
    
    return conversation


def initialize_conversation_with_history(agent_type, messages, client):
    """
    Initialize a conversation with existing message history
    
    Args:
        agent_type (str): Type of agent
        messages (list): List of message dictionaries with role and content
        client: Azure client instance
        
    Returns:
        TokenManagedConversation: Initialized conversation with history
    """
    # Create a fresh conversation with appropriate system prompt
    conversation = create_conversation_for_agent(agent_type, client)
    
    # Add each message to the conversation
    for message in messages:
        if message["role"] != "system":  # Skip system messages as we've already set the system prompt
            conversation.add_message(
                content=message["content"],
                role=message["role"]
            )
    
    return conversation


async def chat_with_agent(agent_type, prompt, agent_modules, client, conversation, project_data=None, memory_bank=None):
    """
    Process a message with a specific agent
    
    Args:
        agent_type (str): Type of agent to chat with
        prompt (str): User prompt to process
        agent_modules (dict): Dictionary of agent modules
        client: Azure client
        conversation: Current conversation for this agent
        project_data (dict, optional): Project data to include as context
        memory_bank: Memory bank for agent to use
        
    Returns:
        str: Response from the agent
        TokenManagedConversation: Updated conversation
    """
    # Add project context if provided
    if project_data:
        project_context = f"Current project: {project_data['name']}\n"
        project_context += f"Description: {project_data['description']}\n"
        project_context += f"Status: {project_data['status']}\n"
        
        # Add project context as a system message
        conversation.add_message(
            content=project_context,
            role="system"
        )
    
    # Check if summarization is needed before processing
    # This will automatically summarize older messages if token usage is high
    await conversation.maybe_summarize()
    
    # Process the message with the appropriate agent module
    if agent_type in agent_modules:
        response, updated_conversation = await agent_modules[agent_type].process_with_tools(
            client=client,
            model_name="deepseek-chat",  # Use a placeholder model name, will be overridden by agent module
            question=prompt,
            conversation=conversation,
            memory_bank=memory_bank
        )
    else:
        # Fallback to default implementation
        from AgentSkeleton.agents.deepseek_agent import process_with_tools
        response, updated_conversation = await process_with_tools(
            client=client,
            model_name="deepseek-chat",  # Use a placeholder model name
            question=prompt,
            conversation=conversation,
            memory_bank=memory_bank
        )
    
    # Check again if summarization is needed after processing
    # This is important if the response pushed us over the threshold
    await updated_conversation.maybe_summarize()
    
    return response, updated_conversation 