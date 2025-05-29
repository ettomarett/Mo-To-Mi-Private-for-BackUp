"""
System Prompt Logger Configuration

This module provides centralized configuration for logging final system prompts
that get sent to LLMs across all agents in the Mo-To-Mi framework.
"""

import os
from datetime import datetime
from pathlib import Path

# Configuration settings
ENABLE_SYSTEM_PROMPT_LOGGING = True  # Set to False to disable all logging
ENABLE_FILE_LOGGING = True  # Set to True to write logs to files - ENABLED FOR DEBUGGING
LOG_DIRECTORY = Path("./system_prompt_logs")  # Directory for log files
MAX_PROMPT_LENGTH_CONSOLE = 2000  # Truncate console output after this length
SAVE_FULL_PROMPT_TO_FILE = True  # Save full prompt to file even if console is truncated

def ensure_log_directory():
    """Ensure the log directory exists if file logging is enabled"""
    if ENABLE_FILE_LOGGING:
        LOG_DIRECTORY.mkdir(exist_ok=True)

def log_system_prompt(agent_name, system_prompt):
    """
    Log the final system prompt for an agent
    
    Args:
        agent_name (str): Name of the agent (e.g., "ARCHITECT", "OBSERVER")
        system_prompt (str): The final system prompt being sent to LLM
    """
    if not ENABLE_SYSTEM_PROMPT_LOGGING:
        return
    
    # Console logging
    print("=" * 80)
    print(f"🚀 {agent_name} AGENT - FINAL SYSTEM PROMPT BEING SENT TO LLM:")
    print("=" * 80)
    
    if system_prompt:
        # Truncate for console if needed
        if len(system_prompt) > MAX_PROMPT_LENGTH_CONSOLE:
            truncated_prompt = system_prompt[:MAX_PROMPT_LENGTH_CONSOLE]
            print(truncated_prompt)
            print(f"\n... [TRUNCATED - {len(system_prompt) - MAX_PROMPT_LENGTH_CONSOLE} more characters]")
            if ENABLE_FILE_LOGGING:
                # Create filename separately to avoid nested f-string
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'{agent_name.lower()}_prompt_{timestamp}.txt'
                print(f"💾 Full prompt saved to: {LOG_DIRECTORY / filename}")
        else:
            print(system_prompt)
    else:
        print("⚠️ No system prompt found!")
    
    print("=" * 80)
    
    # File logging
    if ENABLE_FILE_LOGGING and system_prompt:
        try:
            ensure_log_directory()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = LOG_DIRECTORY / f"{agent_name.lower()}_prompt_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Agent: {agent_name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Prompt Length: {len(system_prompt)} characters\n")
                f.write("=" * 80 + "\n")
                f.write(system_prompt)
                f.write("\n" + "=" * 80 + "\n")
                
        except Exception as e:
            print(f"⚠️ Error saving log file: {e}")

def log_system_prompt_from_messages(agent_name, messages):
    """
    Extract and log system prompt from a messages array
    
    Args:
        agent_name (str): Name of the agent
        messages (list): List of message dictionaries with role and content
    """
    if not ENABLE_SYSTEM_PROMPT_LOGGING:
        return
    
    # Find the system message
    system_prompt = None
    
    for msg in messages:
        if msg.get('role') == 'system':
            system_prompt = msg.get('content', '')
            break
    
    if system_prompt:
        log_system_prompt(agent_name, system_prompt)
    else:
        print("=" * 80)
        print(f"⚠️ {agent_name} AGENT - NO SYSTEM MESSAGE FOUND IN CONVERSATION!")
        print("=" * 80)

# Quick toggle functions for debugging
def enable_logging():
    """Enable system prompt logging"""
    global ENABLE_SYSTEM_PROMPT_LOGGING
    ENABLE_SYSTEM_PROMPT_LOGGING = True
    print("✅ System prompt logging ENABLED")

def disable_logging():
    """Disable system prompt logging"""
    global ENABLE_SYSTEM_PROMPT_LOGGING
    ENABLE_SYSTEM_PROMPT_LOGGING = False
    print("❌ System prompt logging DISABLED")

def enable_file_logging():
    """Enable file logging for system prompts"""
    global ENABLE_FILE_LOGGING
    ENABLE_FILE_LOGGING = True
    ensure_log_directory()
    print(f"💾 File logging ENABLED - logs will be saved to: {LOG_DIRECTORY}")

def disable_file_logging():
    """Disable file logging for system prompts"""
    global ENABLE_FILE_LOGGING
    ENABLE_FILE_LOGGING = False
    print("💾 File logging DISABLED")

def get_status():
    """Get current logging configuration status"""
    return {
        "console_logging": ENABLE_SYSTEM_PROMPT_LOGGING,
        "file_logging": ENABLE_FILE_LOGGING,
        "log_directory": str(LOG_DIRECTORY),
        "max_console_length": MAX_PROMPT_LENGTH_CONSOLE
    } 