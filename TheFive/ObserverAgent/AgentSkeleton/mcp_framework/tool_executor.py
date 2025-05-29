import os
import json
import re
import glob
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from math import sin, cos, tan, log, sqrt, pi, e

from core import calculator

def execute_tool(tool_name: str, params: Dict[str, Any], conversation=None, memory_bank=None) -> Dict[str, Any]:
    """Execute the specified tool with the given parameters"""
    
    if tool_name == "calculator":
        return calculator.execute(params)
    
    elif tool_name == "filesystem":
        operation = params.get("operation")
        path = params.get("path")
        pattern = params.get("pattern")
        
        if operation == "list_dir":
            try:
                items = os.listdir(path)
                return {"items": items}
            except Exception as e:
                return {"error": str(e)}
                
        elif operation == "read_file":
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"content": content}
            except Exception as e:
                return {"error": str(e)}
                
        elif operation == "search_files":
            try:
                matches = glob.glob(os.path.join(path, pattern))
                return {"matches": matches}
            except Exception as e:
                return {"error": str(e)}
        
        return {"error": f"Invalid filesystem operation: {operation}"}
    
    elif tool_name == "memory" and memory_bank is not None:
        operation = params.get("operation")
        
        try:
            if operation == "store":
                content = params.get("content", "")
                key = params.get("key")
                tags = params.get("tags", [])
                store_conversation = params.get("store_conversation", False)
                
                # If storing conversation and history is available
                if store_conversation and conversation:
                    # Get conversation from token-managed history
                    if hasattr(conversation, "get_recent_conversation_text"):
                        content = conversation.get_recent_conversation_text(3)  # Last 3 exchanges
                    else:
                        # Fallback for regular history objects
                        content = "Recent conversation (could not format details)"
                
                if not content:
                    return {"error": "No content provided for storage"}
                
                # Store the memory
                stored_key = memory_bank.store_memory(content, key, tags)
                return {
                    "success": True,
                    "key": stored_key,
                    "message": f"Memory stored successfully with key: {stored_key}"
                }
            
            elif operation == "retrieve":
                key = params.get("key")
                if not key:
                    return {"error": "No memory key provided"}
                
                # Retrieve the memory
                memory_content = memory_bank.retrieve_memory(key)
                if not memory_content:
                    return {"error": f"No memory found with key: {key}"}
                
                # Get metadata
                metadata = memory_bank.memory_index.get(key, {})
                tags = metadata.get("tags", [])
                
                return {
                    "key": key,
                    "content": memory_content,
                    "tags": tags
                }
            
            elif operation == "search":
                query = params.get("query", "")
                tags = params.get("tags", [])
                
                # Search memories
                results = memory_bank.search_memories(query, tags)
                if not results:
                    return {"error": f"No memories found matching query: {query}"}
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "key": result.get("key"),
                        "preview": result.get("preview", ""),
                        "tags": result.get("tags", [])
                    })
                
                return {
                    "query": query,
                    "tags": tags,
                    "results": formatted_results,
                    "count": len(formatted_results)
                }
            
            elif operation == "delete":
                key = params.get("key")
                if not key:
                    return {"error": "No memory key provided"}
                
                # Delete the memory
                result = memory_bank.delete_memory(key)
                if not result:
                    return {"error": f"No memory found with key: {key}"}
                
                return {
                    "success": True,
                    "key": key,
                    "message": f"Memory with key '{key}' deleted successfully"
                }
            
            elif operation == "list":
                # Get all memories
                all_memories = memory_bank.get_all_memories()
                
                # Format results
                formatted_memories = []
                for key, metadata in all_memories.items():
                    formatted_memories.append({
                        "key": key,
                        "preview": metadata.get("preview", ""),
                        "tags": metadata.get("tags", [])
                    })
                
                return {
                    "memories": formatted_memories,
                    "count": len(formatted_memories)
                }
            
            else:
                return {"error": f"Unknown memory operation: {operation}"}
        
        except Exception as e:
            return {"error": f"Error executing memory operation: {str(e)}"}
    
    elif tool_name == "token_manager" and conversation is not None:
        operation = params.get("operation")
        
        try:
            if operation == "status":
                # Get token usage status
                status = conversation.get_token_status()
                return {
                    "current_tokens": status["current_tokens"],
                    "max_tokens": status["max_tokens"],
                    "usage_percent": status["usage_percent"],
                    "warning_threshold": status["warning_threshold"],
                    "summarize_threshold": status["summarize_threshold"],
                    "summarization_performed": status["summarization_performed"]
                }
            
            elif operation == "reset":
                # Reset token count and clear conversation
                conversation.clear()
                return {
                    "success": True,
                    "message": "Token count reset and conversation cleared."
                }
            
            elif operation == "summarize":
                # Force a summarization
                summarization_occurred = asyncio.run(conversation.maybe_summarize())
                if summarization_occurred:
                    return {
                        "success": True,
                        "message": "Conversation was summarized successfully."
                    }
                else:
                    return {
                        "success": False,
                        "message": "Summarization was not needed or not possible."
                    }
            
            # Handle parameter updates if provided
            max_tokens = params.get("max_tokens")
            warning_threshold = params.get("warning_threshold")
            summarize_threshold = params.get("summarize_threshold")
            
            changes_made = False
            
            if max_tokens is not None and max_tokens > 1000:
                conversation.token_manager.max_tokens = max_tokens
                changes_made = True
                
            if warning_threshold is not None and 0.1 <= warning_threshold <= 0.95:
                conversation.token_manager.warning_threshold = warning_threshold
                changes_made = True
                
            if summarize_threshold is not None and 0.2 <= summarize_threshold <= 0.98:
                conversation.token_manager.summarize_threshold = summarize_threshold
                changes_made = True
            
            if changes_made:
                return {
                    "success": True,
                    "message": "Token manager settings updated successfully.",
                    "updated_status": conversation.get_token_status()
                }
            
            return {"error": f"Unknown token manager operation: {operation}"}
            
        except Exception as e:
            return {"error": f"Error executing token manager operation: {str(e)}"}
    
    return {"error": f"Unknown tool: {tool_name}"} 