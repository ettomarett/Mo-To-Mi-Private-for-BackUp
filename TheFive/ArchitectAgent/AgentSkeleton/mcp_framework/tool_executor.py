import os
import json
import re
import glob
import asyncio
import logging
import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from math import sin, cos, tan, log, sqrt, pi, e

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='architect_tool_executor_debug.log',
                   filemode='a')
logger = logging.getLogger("architect_tool_executor")

# Import debug helper if available
try:
    from util.debug_helper import log_tool_execution
except ImportError:
    # Mock the log_tool_execution function if it's not available
    def log_tool_execution(agent_type, tool_name, params, memory_bank, result=None):
        logger.debug(f"{agent_type} - Tool call: {tool_name} with params: {params}")
        return {"tool": tool_name, "params": params}

# Try to import streamlit for web UI debug integration
try:
    import streamlit as st
except ImportError:
    # Create a mock st with a session_state that does nothing
    class MockSessionState:
        def __getattr__(self, name):
            return None
            
    class MockSt:
        def __init__(self):
            self.session_state = MockSessionState()
    
    st = MockSt()

from core import calculator

def execute_tool(tool_name: str, params: Dict[str, Any], conversation=None, memory_bank=None) -> Dict[str, Any]:
    """Execute the specified tool with the given parameters"""
    
    # Debug logging
    debug_enabled = getattr(st.session_state, 'tool_debug_enabled', False)
    if debug_enabled:
        # Log the tool call using our debug helper
        log_tool_execution(
            agent_type="Architect",
            tool_name=tool_name,
            params=params,
            memory_bank=memory_bank
        )
    
    # Execute appropriate tool based on name
    result = {"status": "unknown", "error": None}
    
    if tool_name == "calculator":
        result = calculator.execute(params)
    
    elif tool_name == "filesystem":
        operation = params.get("operation")
        path = params.get("path")
        pattern = params.get("pattern")
        
        if operation == "list_dir":
            try:
                items = os.listdir(path)
                result = {"items": items, "status": "success"}
            except Exception as e:
                result = {"error": str(e), "status": "error"}
                
        elif operation == "read_file":
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = {"content": content, "status": "success"}
            except Exception as e:
                result = {"error": str(e), "status": "error"}
                
        elif operation == "search_files":
            try:
                matches = glob.glob(os.path.join(path, pattern))
                result = {"matches": matches, "status": "success"}
            except Exception as e:
                result = {"error": str(e), "status": "error"}
        
        else:
            result = {"error": f"Invalid filesystem operation: {operation}", "status": "error"}
    
    elif tool_name == "memory" and memory_bank is not None:
        operation = params.get("operation")
        
        try:
            # Debug memory instance
            if debug_enabled:
                logger.debug(f"Architect - Memory bank instance: {memory_bank} with storage dir: {getattr(memory_bank, 'storage_dir', 'unknown')}")
            
            if operation == "store":
                content = params.get("content", "")
                key = params.get("key")
                tags = params.get("tags", [])
                store_conversation = params.get("store_conversation", False)
                has_explicit_permission = params.get("has_explicit_permission", False)
                
                # Debug the store operation
                if debug_enabled:
                    logger.debug(f"Architect - Memory store operation: key={key}, content={content[:50]}..., has_permission={has_explicit_permission}")
                
                # If storing conversation and history is available
                if store_conversation and conversation:
                    # Get conversation from token-managed history
                    if hasattr(conversation, "get_recent_conversation_text"):
                        content = conversation.get_recent_conversation_text(3)  # Last 3 exchanges
                    else:
                        # Fallback for regular history objects
                        content = "Recent conversation (could not format details)"
                
                if not content:
                    result = {"error": "No content provided for storage", "status": "error"}
                    
                    if debug_enabled:
                        logger.error("Architect - Memory store failed: No content provided")
                else:
                    # Store the memory
                    stored_key = memory_bank.store_memory(content, key, tags, has_explicit_permission)
                    
                    # Check if we got an error message instead of a key
                    if isinstance(stored_key, str) and stored_key.startswith("ERROR:"):
                        result = {
                            "success": False,
                            "error": stored_key,
                            "status": "error"
                        }
                        
                        if debug_enabled:
                            logger.error(f"Architect - Memory store failed: {stored_key}")
                    else:
                        result = {
                            "success": True,
                            "key": stored_key,
                            "message": f"Memory stored successfully with key: {stored_key}",
                            "status": "success"
                        }
                        
                        if debug_enabled:
                            logger.info(f"Architect - Memory stored successfully with key: {stored_key}")
            
            elif operation == "retrieve":
                key = params.get("key")
                if not key:
                    result = {"error": "No memory key provided", "status": "error"}
                
                # Retrieve the memory
                memory_content = memory_bank.retrieve_memory(key)
                if not memory_content:
                    result = {"error": f"No memory found with key: {key}", "status": "error"}
                else:
                    # Get metadata
                    metadata = memory_bank.memory_index.get(key, {})
                    tags = metadata.get("tags", [])
                    
                    result = {
                        "key": key,
                        "content": memory_content,
                        "tags": tags,
                        "status": "success"
                    }
            
            elif operation == "search":
                query = params.get("query", "")
                tags = params.get("tags", [])
                
                # Search memories
                results = memory_bank.search_memories(query, tags)
                if not results:
                    result = {"error": f"No memories found matching query: {query}", "status": "error"}
                else:
                    # Format results
                    formatted_results = []
                    for res in results:
                        formatted_results.append({
                            "key": res.get("key"),
                            "preview": res.get("preview", ""),
                            "tags": res.get("tags", [])
                        })
                    
                    result = {
                        "query": query,
                        "tags": tags,
                        "results": formatted_results,
                        "count": len(formatted_results),
                        "status": "success"
                    }
            
            elif operation == "delete":
                key = params.get("key")
                if not key:
                    result = {"error": "No memory key provided", "status": "error"}
                else:
                    # Delete the memory
                    delete_result = memory_bank.delete_memory(key)
                    if not delete_result:
                        result = {"error": f"No memory found with key: {key}", "status": "error"}
                    else:
                        result = {
                            "success": True,
                            "key": key,
                            "message": f"Memory with key '{key}' deleted successfully",
                            "status": "success"
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
                
                result = {
                    "memories": formatted_memories,
                    "count": len(formatted_memories),
                    "status": "success"
                }
            
            else:
                result = {"error": f"Unknown memory operation: {operation}", "status": "error"}
        
        except Exception as e:
            result = {"error": f"Error executing memory operation: {str(e)}", "status": "error"}
            
            if debug_enabled:
                logger.exception(f"Architect - Exception in memory tool: {str(e)}")
    
    elif tool_name == "token_manager" and conversation is not None:
        operation = params.get("operation")
        
        try:
            if operation == "status":
                # Get token usage status
                status = conversation.get_token_status()
                result = {
                    "current_tokens": status["current_tokens"],
                    "max_tokens": status["max_tokens"],
                    "usage_percent": status["usage_percent"],
                    "warning_threshold": status["warning_threshold"],
                    "summarize_threshold": status["summarize_threshold"],
                    "summarization_performed": status["summarization_performed"],
                    "status": "success"
                }
            
            elif operation == "reset":
                # Reset token count and clear conversation
                conversation.clear()
                result = {
                    "success": True,
                    "message": "Token count reset and conversation cleared.",
                    "status": "success"
                }
            
            elif operation == "summarize":
                # Force a summarization
                summarization_occurred = asyncio.run(conversation.maybe_summarize())
                if summarization_occurred:
                    result = {
                        "success": True,
                        "message": "Conversation was summarized successfully.",
                        "status": "success"
                    }
                else:
                    result = {
                        "success": False,
                        "message": "Summarization was not needed or not possible.",
                        "status": "error"
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
                result = {
                    "success": True,
                    "message": "Token manager settings updated successfully.",
                    "updated_status": conversation.get_token_status(),
                    "status": "success"
                }
            
            if operation not in ["status", "reset", "summarize"] and not changes_made:
                result = {"error": f"Unknown token manager operation: {operation}", "status": "error"}
            
        except Exception as e:
            result = {"error": f"Error executing token manager operation: {str(e)}", "status": "error"}
            
            if debug_enabled:
                logger.exception(f"Architect - Exception in token_manager tool: {str(e)}")
    
    else:
        result = {"error": f"Unknown tool: {tool_name}", "status": "error"}
    
    # Log the result if debugging is enabled
    if debug_enabled:
        # Update the debug log with the result
        log_tool_execution(
            agent_type="Architect",
            tool_name=tool_name,
            params=params,
            memory_bank=memory_bank,
            result=result
        )
    
    return result 