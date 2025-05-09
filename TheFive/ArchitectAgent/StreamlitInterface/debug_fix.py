"""
Simple direct logging utility for debugging tool execution
"""
import os
import json
import datetime
from pathlib import Path

# Create a dedicated log file in the StreamlitInterface directory
LOG_FILE = Path(__file__).parent / "tool_execution_logs.json"

def log_tool_call(tool_name, params, memory_dir=None, result=None):
    """Log a tool call to the local log file"""
    try:
        # Create a log entry
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": "Architect",
            "tool": tool_name,
            "params": params,
            "memory_dir": memory_dir,
            "status": "pending"
        }
        
        if result:
            entry["result"] = result
            entry["status"] = result.get("status", "unknown")
        
        # Read existing logs
        logs = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add the new log
        logs.append(entry)
        
        # Save back to file
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"Logged tool call: {tool_name}")
        return True
    except Exception as e:
        print(f"Error logging tool call: {str(e)}")
        return False

def get_logs():
    """Get all logged tool calls"""
    if not os.path.exists(LOG_FILE):
        return []
    
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def clear_logs():
    """Clear all logs"""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE) 