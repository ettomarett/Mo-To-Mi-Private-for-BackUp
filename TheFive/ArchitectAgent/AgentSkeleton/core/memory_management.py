import os
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

class Message:
    """Representation of a message in a conversation"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[float] = None):
        """
        Initialize a message
        
        Args:
            role: The role of the message sender (system, user, assistant, tool)
            content: The content of the message
            timestamp: Unix timestamp when the message was created
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary format
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from dictionary data
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            Message object
        """
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time())
        )
    
    def __str__(self) -> str:
        """String representation of the message"""
        time_str = datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return f"[{time_str}] {self.role.upper()}: {self.content}"


class Conversation:
    """Represents a conversation with message history"""
    
    def __init__(self, id: str = None, system_prompt: Optional[str] = None):
        """
        Initialize a conversation
        
        Args:
            id: Unique identifier for the conversation
            system_prompt: Optional system prompt to initialize the conversation
        """
        self.id = id or self._generate_id()
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        # Add system prompt if provided
        if system_prompt:
            self.add_message("system", system_prompt)
    
    def _generate_id(self) -> str:
        """Generate a unique conversation ID"""
        return f"conv_{int(time.time())}_{os.urandom(4).hex()}"
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation
        
        Args:
            role: The role of the message sender
            content: The content of the message
        """
        message = Message(role, content)
        self.messages.append(message)
        self.metadata["last_updated"] = time.time()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the conversation
        
        Returns:
            List of messages in dictionary format suitable for LLM API
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self) -> None:
        """Clear all messages except system messages"""
        self.messages = [msg for msg in self.messages if msg.role == "system"]
        self.metadata["last_updated"] = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert conversation to dictionary format
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Create a conversation from dictionary data
        
        Args:
            data: Dictionary containing conversation data
            
        Returns:
            Conversation object
        """
        conversation = cls(id=data["id"])
        conversation.messages = [Message.from_dict(msg_data) for msg_data in data["messages"]]
        conversation.metadata = data["metadata"]
        return conversation


class ConversationMemory:
    """Manages the persistence of conversations"""
    
    def __init__(self, storage_dir: str = "./memory"):
        """
        Initialize the conversation memory
        
        Args:
            storage_dir: Directory to store conversation files
        """
        self.storage_dir = storage_dir
        self.ensure_storage_dir_exists()
        
        # Cache of loaded conversations
        self.conversations: Dict[str, Conversation] = {}
    
    def ensure_storage_dir_exists(self) -> None:
        """Ensure the storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_conversation_path(self, conversation_id: str) -> str:
        """
        Get the file path for a conversation
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Path to the conversation file
        """
        return os.path.join(self.storage_dir, f"{conversation_id}.json")
    
    def save_conversation(self, conversation: Conversation) -> None:
        """
        Save a conversation to disk
        
        Args:
            conversation: Conversation to save
        """
        file_path = self._get_conversation_path(conversation.id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Update cache
        self.conversations[conversation.id] = conversation
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from disk
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            Loaded conversation or None if not found
        """
        # Check cache first
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        file_path = self._get_conversation_path(conversation_id)
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = Conversation.from_dict(data)
            
            # Add to cache
            self.conversations[conversation_id] = conversation
            
            return conversation
        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {str(e)}")
            return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_conversation_path(conversation_id)
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            
            # Remove from cache
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
            
            return True
        except Exception as e:
            print(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations with metadata
        
        Returns:
            List of conversation metadata dictionaries
        """
        conversations = []
        
        # Ensure the directory exists
        self.ensure_storage_dir_exists()
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.storage_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract basic information
                    conversation_info = {
                        "id": data["id"],
                        "created_at": data["metadata"]["created_at"],
                        "last_updated": data["metadata"]["last_updated"],
                        "message_count": len(data["messages"]),
                        # Add first non-system message as a preview
                        "preview": next(
                            (msg["content"][:100] + "..." 
                             for msg in data["messages"] 
                             if msg["role"] != "system"), 
                            "No messages"
                        )
                    }
                    
                    conversations.append(conversation_info)
                except Exception as e:
                    print(f"Error reading conversation file {filename}: {str(e)}")
        
        # Sort by last updated timestamp (newest first)
        conversations.sort(key=lambda x: x["last_updated"], reverse=True)
        
        return conversations


class MemoryManager:
    """
    Manages conversation memory and provides a simplified interface for 
    storing, retrieving, and manipulating conversation history
    """
    
    def __init__(self, memory_dir: str = "./memory"):
        """
        Initialize the memory manager
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory = ConversationMemory(storage_dir=memory_dir)
        self.active_conversation: Optional[Conversation] = None
    
    def create_conversation(self, system_prompt: Optional[str] = None) -> str:
        """
        Create a new conversation and set it as active
        
        Args:
            system_prompt: Optional system prompt to initialize the conversation
            
        Returns:
            ID of the new conversation
        """
        self.active_conversation = Conversation(system_prompt=system_prompt)
        self.memory.save_conversation(self.active_conversation)
        return self.active_conversation.id
    
    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load a conversation and set it as active
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.memory.load_conversation(conversation_id)
        if conversation:
            self.active_conversation = conversation
            return True
        return False
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the active conversation
        
        Args:
            role: The role of the message sender
            content: The content of the message
            
        Raises:
            ValueError: If no active conversation
        """
        if not self.active_conversation:
            raise ValueError("No active conversation")
        
        self.active_conversation.add_message(role, content)
        self.memory.save_conversation(self.active_conversation)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get messages from the active conversation
        
        Returns:
            List of messages in dictionary format
            
        Raises:
            ValueError: If no active conversation
        """
        if not self.active_conversation:
            raise ValueError("No active conversation")
        
        return self.active_conversation.get_messages()
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations with metadata
        
        Returns:
            List of conversation metadata dictionaries
        """
        return self.memory.list_conversations()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Reset active conversation if it's the one being deleted
        if self.active_conversation and self.active_conversation.id == conversation_id:
            self.active_conversation = None
        
        return self.memory.delete_conversation(conversation_id)
    
    def clear_active_conversation(self) -> None:
        """
        Clear all messages from the active conversation except system messages
        
        Raises:
            ValueError: If no active conversation
        """
        if not self.active_conversation:
            raise ValueError("No active conversation")
        
        self.active_conversation.clear()
        self.memory.save_conversation(self.active_conversation) 