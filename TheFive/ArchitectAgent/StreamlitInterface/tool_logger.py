"""
Comprehensive logging system for MCP tool parsing and execution
"""
import os
import json
import datetime
from pathlib import Path

# Create dedicated log files in the StreamlitInterface directory
PARSE_LOG_FILE = Path(__file__).parent / "tool_parse_logs.json"
EXECUTE_LOG_FILE = Path(__file__).parent / "tool_execute_logs.json"

def log_tool_parse(text, extracted_tools):
    """
    Log when tool calls are parsed from text
    
    Args:
        text: The original text that was parsed
        extracted_tools: The tools that were extracted
    """
    try:
        # Create a log entry
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "text_length": len(text),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "extracted_tools": extracted_tools,
            "tool_count": len(extracted_tools)
        }
        
        # Read existing logs
        logs = []
        if os.path.exists(PARSE_LOG_FILE):
            try:
                with open(PARSE_LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add the new log
        logs.append(entry)
        
        # Save back to file
        with open(PARSE_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"Logged tool parsing: {len(extracted_tools)} tools found")
        return True
    except Exception as e:
        print(f"Error logging tool parsing: {str(e)}")
        return False

def log_tool_execution(tool_name, params, memory_dir=None, result=None):
    """
    Log when a tool is executed
    
    Args:
        tool_name: The name of the tool
        params: Tool parameters
        memory_dir: Optional memory directory
        result: Optional execution result
    """
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
        if os.path.exists(EXECUTE_LOG_FILE):
            try:
                with open(EXECUTE_LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Add the new log
        logs.append(entry)
        
        # Save back to file
        with open(EXECUTE_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"Logged tool execution: {tool_name}")
        return True
    except Exception as e:
        print(f"Error logging tool execution: {str(e)}")
        return False

def get_parse_logs():
    """Get all tool parsing logs"""
    if not os.path.exists(PARSE_LOG_FILE):
        return []
    
    try:
        with open(PARSE_LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def get_execution_logs():
    """Get all tool execution logs"""
    if not os.path.exists(EXECUTE_LOG_FILE):
        return []
    
    try:
        with open(EXECUTE_LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def clear_logs():
    """Clear all logs"""
    if os.path.exists(PARSE_LOG_FILE):
        os.remove(PARSE_LOG_FILE)
    if os.path.exists(EXECUTE_LOG_FILE):
        os.remove(EXECUTE_LOG_FILE) 