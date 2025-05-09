"""
Debug helper utilities for tracking tool execution and memory operations
"""
import os
import datetime
import json
import logging
from pathlib import Path

# Configure logging
debug_log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_logs.json")

def log_tool_execution(agent_type, tool_name, params, memory_bank, result=None):
    """
    Log a tool execution event to both file and Streamlit session state if available
    
    Args:
        agent_type: The type of agent (Architect, Strategist, etc.)
        tool_name: The name of the tool being executed
        params: The parameters passed to the tool
        memory_bank: The memory bank instance being used
        result: Optional result from tool execution
    """
    timestamp = datetime.datetime.now().isoformat()
    
    # Create the debug entry
    debug_entry = {
        "timestamp": timestamp,
        "agent": agent_type,
        "tool": tool_name,
        "params": params,
        "memory_bank_type": str(type(memory_bank)),
        "memory_bank_dir": getattr(memory_bank, "storage_dir", "unknown") if memory_bank else "none"
    }
    
    # Add result if available
    if result:
        debug_entry["result"] = result
        debug_entry["status"] = result.get("status", "unknown")
    
    # Log to file
    try:
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(debug_log_file), exist_ok=True)
        
        # Read existing logs if file exists
        existing_logs = []
        if os.path.exists(debug_log_file):
            try:
                with open(debug_log_file, 'r') as f:
                    existing_logs = json.load(f)
            except json.JSONDecodeError:
                # File exists but is not valid JSON, start fresh
                existing_logs = []
        
        # Append new log
        existing_logs.append(debug_entry)
        
        # Write updated logs back to file
        with open(debug_log_file, 'w') as f:
            json.dump(existing_logs, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to write to debug log file: {str(e)}")
    
    # Try to update Streamlit session state if available
    try:
        import streamlit as st
        if hasattr(st, 'session_state') and 'tool_debug_log' in st.session_state:
            st.session_state.tool_debug_log.append(debug_entry)
    except Exception:
        # Streamlit may not be available in all contexts
        pass
    
    return debug_entry

def get_debug_logs():
    """
    Get all debug logs from the file
    
    Returns:
        List of debug log entries
    """
    if not os.path.exists(debug_log_file):
        return []
    
    try:
        with open(debug_log_file, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def clear_debug_logs():
    """Clear all debug logs from the file"""
    if os.path.exists(debug_log_file):
        os.remove(debug_log_file)
    
    # Try to clear Streamlit session state as well
    try:
        import streamlit as st
        if hasattr(st, 'session_state') and 'tool_debug_log' in st.session_state:
            st.session_state.tool_debug_log = []
    except Exception:
        pass 