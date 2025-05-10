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

# Import the constants module
constants_path = root_dir / "config" / "constants.py"
constants = load_module("constants", constants_path)

# Import the paths module
paths_path = root_dir / "config" / "paths.py"
paths = load_module("paths", paths_path)

# Import the AgentSkeleton modules directly
import sys
sys.path.append(str(root_dir.parent.parent))  # Project root
sys.path.append(str(root_dir.parent))  # Parent dir
sys.path.append(str(root_dir.parent.parent / 'AgentSkeleton'))  # AgentSkeleton

from AgentSkeleton.core.token_management import TokenManagedConversation

# Import system prompts directly using file paths instead of imports
def load_observer_system_prompt():
    try:
        observer_protocol_path = paths.AGENT_PATHS["observer"] / "AgentSkeleton" / "mcp_framework" / "protocol.py"
        protocol_module = load_module("observer_protocol", observer_protocol_path)
        return protocol_module.create_default_system_prompt
    except Exception as e:
        print(f"Warning: Could not load Observer's system prompt: {e}")
        return None

observer_system_prompt = load_observer_system_prompt()

def create_conversation_for_agent(agent_type, client):
    """Create a conversation instance for a specific agent"""
    conversation = TokenManagedConversation(
        max_tokens=100000,
        client=client,
        model_name=constants.AZURE_DEEPSEEK_MODEL_NAME
    )
    
    # Set the system prompt based on agent type
    if agent_type == "architect":
        conversation.set_system_prompt(constants.ARCHITECT_SYSTEM_PROMPT)
    elif agent_type == "observer":
        # Use the system prompt from Observer's protocol if available
        if observer_system_prompt:
            conversation.set_system_prompt(observer_system_prompt())
        else:
            conversation.set_system_prompt(constants.OBSERVER_SYSTEM_PROMPT)
    elif agent_type == "strategist":
        conversation.set_system_prompt(constants.STRATEGIST_SYSTEM_PROMPT)
    elif agent_type == "builder":
        conversation.set_system_prompt(constants.BUILDER_SYSTEM_PROMPT)
    elif agent_type == "validator":
        conversation.set_system_prompt(constants.VALIDATOR_SYSTEM_PROMPT)
    else:
        # Default system prompt
        conversation.set_system_prompt("You are a helpful AI assistant.")
    
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
            model_name=constants.AZURE_DEEPSEEK_MODEL_NAME,
            question=prompt,
            conversation=conversation,
            memory_bank=memory_bank
        )
    else:
        # Fallback to default implementation
        from AgentSkeleton.agents.deepseek_agent import process_with_tools
        response, updated_conversation = await process_with_tools(
            client=client,
            model_name=constants.AZURE_DEEPSEEK_MODEL_NAME,
            question=prompt,
            conversation=conversation,
            memory_bank=memory_bank
        )
    
    # Check again if summarization is needed after processing
    # This is important if the response pushed us over the threshold
    await updated_conversation.maybe_summarize()
    
    return response, updated_conversation 