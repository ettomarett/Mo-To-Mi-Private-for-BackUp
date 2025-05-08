import json
import os
from datetime import datetime
from pathlib import Path

# Define the saved chats directory
CHATS_DIR = Path("saved_chats")
CHATS_DIR.mkdir(exist_ok=True)

def save_conversation(agent_type, name, messages, timestamp=None):
    """
    Save an agent's conversation to a JSON file
    
    Args:
        agent_type (str): Agent type (architect, observer, etc.)
        name (str): Name of the conversation
        messages (list): List of conversation messages
        timestamp (str, optional): Timestamp for the save
        
    Returns:
        str: Path to the saved file
    """
    if not timestamp:
        timestamp = datetime.now().isoformat()
    
    # Create agent directory if it doesn't exist
    agent_dir = CHATS_DIR / agent_type
    agent_dir.mkdir(exist_ok=True)
    
    # Create a unique identifier for the filename
    # But preserve the user's original display name in the JSON data
    display_name = name  # Keep the original display name
    
    # Create filename from name (sanitize)
    safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)
    
    # Prepare data to save
    conversation_data = {
        "name": display_name,  # Use the original display name
        "agent_type": agent_type,
        "messages": messages,
        "timestamp": timestamp
    }
    
    file_path = agent_dir / f"{safe_name}.json"
    
    # Save to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, indent=2)
    
    return str(file_path)


def load_conversation(agent_type, name):
    """
    Load an agent's conversation from a JSON file
    
    Args:
        agent_type (str): Agent type (architect, observer, etc.)
        name (str): Name of the conversation
        
    Returns:
        dict: Conversation data or None if not found
    """
    agent_dir = CHATS_DIR / agent_type
    safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)
    file_path = agent_dir / f"{safe_name}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_conversations(agent_type=None):
    """
    List saved conversations
    
    Args:
        agent_type (str, optional): Filter by agent type
        
    Returns:
        dict: Dictionary of conversations by agent type
    """
    result = {}
    
    # If specific agent type requested
    if agent_type:
        agent_dir = CHATS_DIR / agent_type
        if agent_dir.exists():
            result[agent_type] = []
            for f in agent_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        result[agent_type].append({
                            "name": data.get("name", f.stem),
                            "timestamp": data.get("timestamp", ""),
                            "message_count": len(data.get("messages", []))
                        })
                except:
                    # Skip invalid files
                    pass
    else:
        # Get all agent types
        for agent_dir in CHATS_DIR.iterdir():
            if agent_dir.is_dir():
                agent_type = agent_dir.name
                result[agent_type] = []
                for f in agent_dir.glob("*.json"):
                    try:
                        with open(f, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            result[agent_type].append({
                                "name": data.get("name", f.stem),
                                "timestamp": data.get("timestamp", ""),
                                "message_count": len(data.get("messages", []))
                            })
                    except:
                        # Skip invalid files
                        pass
    
    return result


def delete_conversation(agent_type, name):
    """
    Delete a saved conversation
    
    Args:
        agent_type (str): Agent type (architect, observer, etc.)
        name (str): Name of the conversation
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    agent_dir = CHATS_DIR / agent_type
    safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in name)
    file_path = agent_dir / f"{safe_name}.json"
    
    if file_path.exists():
        try:
            file_path.unlink()
            return True
        except:
            pass
    return False


def get_unique_name(agent_type, base_name):
    """
    Generate a unique name for a conversation if the base name already exists
    
    Args:
        agent_type (str): Agent type (architect, observer, etc.)
        base_name (str): Base name for the conversation
        
    Returns:
        str: Unique name
    """
    agent_dir = CHATS_DIR / agent_type
    
    if not agent_dir.exists():
        return base_name
    
    safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in base_name)
    file_path = agent_dir / f"{safe_name}.json"
    
    if not file_path.exists():
        return base_name
    
    # Add numbering to make unique
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}"
        safe_new_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in new_name)
        new_path = agent_dir / f"{safe_new_name}.json"
        
        if not new_path.exists():
            return new_name
        
        counter += 1 