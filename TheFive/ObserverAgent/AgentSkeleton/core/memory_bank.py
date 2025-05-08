import os
import json
import uuid
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class MemoryBank:
    """Class to manage permanent memory storage for the agent"""
    
    def __init__(self, storage_dir=None):
        """Initialize the memory bank with a storage directory"""
        # Use agent-specific directory if none provided
        if storage_dir is None:
            # Create a path within the agent's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            agent_dir = os.path.dirname(os.path.dirname(current_dir))
            storage_dir = os.path.join(agent_dir, "ObserverAgent_memories")
        
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        # Load or create the memory index
        self.memory_index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the memory index from file or create a new one"""
        index_path = os.path.join(self.storage_dir, "index.json")
        
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If the index is corrupted, start fresh
                return {}
        return {}
    
    def _save_index(self):
        """Save the memory index to file"""
        index_path = os.path.join(self.storage_dir, "index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory_index, f, indent=2)
    
    def store_memory(self, content: str, key: Optional[str] = None, tags: Optional[List[str]] = None, has_explicit_permission: bool = False) -> str:
        """
        Store a new memory
        
        Args:
            content: The content to store
            key: Optional key to use (if None, one will be generated)
            tags: Optional list of tags for categorization
            has_explicit_permission: Flag indicating if explicit permission was granted
            
        Returns:
            The key of the stored memory or error message
        """
        # Check for explicit permission for user preferences or personal information
        if not has_explicit_permission and (
            "prefer" in content.lower() or 
            "like" in content.lower() or 
            "my " in content.lower() or
            "I am" in content or
            "I'm" in content or
            "we use" in content.lower() or
            "our team" in content.lower()
        ):
            return "ERROR: Cannot store user preferences or personal information without explicit permission"
        
        # Generate key if not provided
        if not key:
            # Generate a key based on content
            content_words = re.findall(r'\w+', content.lower())
            if content_words and len(content_words) >= 2:
                # Use first few words for a readable key
                key_base = "_".join(content_words[:3])
                key = key_base[:30]  # Limit length
            else:
                # Fallback to timestamp
                key = f"memory_{int(time.time())}"
                
        # Ensure key uniqueness
        if key in self.memory_index:
            # If key exists, append a unique identifier
            key = f"{key}_{str(uuid.uuid4())[:8]}"
        
        # Create filename for storage
        timestamp = datetime.now().isoformat()
        filename = f"{key}.txt"
        file_path = os.path.join(self.storage_dir, filename)
        
        # Store the content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create a preview (first ~50 chars)
        preview = content[:50] + "..." if len(content) > 50 else content
        
        # Update the index with permission metadata
        self.memory_index[key] = {
            "created": timestamp,
            "tags": tags or [],
            "filename": filename,
            "preview": preview,
            "had_permission": has_explicit_permission
        }
        
        # Save the updated index
        self._save_index()
        
        return key
    
    def retrieve_memory(self, key: str) -> Optional[str]:
        """Retrieve a memory by key"""
        if key not in self.memory_index:
            return None
            
        filename = self.memory_index[key]["filename"]
        file_path = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(file_path):
            # File is missing, remove from index
            del self.memory_index[key]
            self._save_index()
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def search_memories(self, query: str = "", tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search memories by content or tags
        
        Args:
            query: Text to search for in memory content
            tags: List of tags to filter by
            
        Returns:
            List of matching memory metadata with previews
        """
        results = []
        query = query.lower()
        
        for key, metadata in self.memory_index.items():
            # Check if tags match (if tags provided)
            if tags and not any(tag in metadata.get("tags", []) for tag in tags):
                continue
                
            # If query is provided, check content
            if query:
                content = self.retrieve_memory(key) or ""
                if query not in content.lower() and query not in key.lower():
                    continue
            
            # Add to results
            result = {
                "key": key,
                "preview": metadata.get("preview", ""),
                "tags": metadata.get("tags", []),
                "created": metadata.get("created", ""),
                "had_permission": metadata.get("had_permission", False)
            }
            results.append(result)
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return results
    
    def delete_memory(self, key: str) -> bool:
        """Delete a memory by key"""
        if key not in self.memory_index:
            return False
            
        # Get filename from index
        filename = self.memory_index[key]["filename"]
        file_path = os.path.join(self.storage_dir, filename)
        
        # Delete file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        # Remove from index
        del self.memory_index[key]
        self._save_index()
        
        return True
    
    def get_all_memories(self) -> Dict[str, Any]:
        """Get all memories metadata"""
        return self.memory_index
    
    def format_for_context(self, max_memories: int = 3) -> str:
        """
        Format recent/relevant memories for inclusion in the system prompt
        
        Args:
            max_memories: Maximum number of memories to include
            
        Returns:
            Formatted string of memories for context
        """
        if not self.memory_index:
            return "You don't have any stored memories yet."
            
        # Get most recent memories for now (could be enhanced to get most relevant)
        recent_keys = sorted(
            self.memory_index.keys(),
            key=lambda k: self.memory_index[k].get("created", ""),
            reverse=True
        )[:max_memories]
        
        if not recent_keys:
            return "You don't have any stored memories yet."
            
        # Format the memories
        memories_text = "Your memory contains the following information:\n\n"
        
        for key in recent_keys:
            content = self.retrieve_memory(key)
            if content:
                memories_text += f"- {key}: {content}\n\n"
        
        return memories_text 