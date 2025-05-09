#!/usr/bin/env python
"""
Script to update all MCP framework memory protocol implementations
"""
import os
import sys
import re
import json
from pathlib import Path

# Define the agents to update
AGENTS = ["Architect", "Builder", "Observer", "Strategist", "Validator"]

# Path to the base directory
BASE_DIR = Path("TheFive")

# The updated memory tool definition
UPDATED_MEMORY_TOOL = {
    "name": "memory",
    "description": "Store and retrieve permanent memories across conversations. IMPORTANT: Always ask for explicit user confirmation BEFORE storing ANY information. For preferences or personal info, set has_explicit_permission=true ONLY after user confirms.",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "The operation to perform: 'store', 'retrieve', 'search', 'delete', or 'list'",
                "enum": ["store", "retrieve", "search", "delete", "list"]
            },
            "content": {
                "type": "string",
                "description": "The content to store (for 'store' operation)"
            },
            "key": {
                "type": "string",
                "description": "The memory key (used for 'store', 'retrieve', 'delete' operations)"
            },
            "query": {
                "type": "string",
                "description": "The search query (for 'search' operation)"
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Tags for the memory (for 'store' operation or filtering results)"
            },
            "store_conversation": {
                "type": "boolean",
                "description": "Whether to store recent conversation history instead of content"
            },
            "has_explicit_permission": {
                "type": "boolean",
                "description": "REQUIRED for storing user preferences or personal information. Must ONLY be set to true if the user has EXPLICITLY granted permission to store this specific information. Always ask first, and only set this to true after user confirmation."
            }
        },
        "required": ["operation"]
    }
}

# The memory protocol section to add
MEMORY_PROTOCOL = """
MEMORY PROTOCOL: Always ask for explicit confirmation BEFORE storing any information permanently. 
Only after receiving clear confirmation should you use the memory tool with has_explicit_permission=true.
If you store without permission or with permission=false, the request will be rejected.
"""

def update_protocol_file(protocol_path):
    """Update a protocol.py file with the correct memory implementation"""
    if not protocol_path.exists():
        print(f"WARNING: {protocol_path} not found, skipping")
        return False
    
    # Read the file content
    with open(protocol_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, update the memory tool definition
    # This is a bit complex as we need to find the memory tool in TOOLS list
    tools_match = re.search(r'TOOLS\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not tools_match:
        print(f"WARNING: Could not find TOOLS list in {protocol_path}, skipping")
        return False
    
    tools_content = tools_match.group(1)
    
    # Find each tool in the list
    tools = []
    bracket_count = 0
    start_idx = 0
    
    for i, char in enumerate(tools_content):
        if char == '{':
            if bracket_count == 0:
                start_idx = i
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                tool_str = tools_content[start_idx:i+1]
                tools.append(tool_str)
    
    # Find the memory tool
    updated_tools = []
    memory_found = False
    
    for tool_str in tools:
        if '"name": "memory"' in tool_str:
            memory_found = True
            # Replace with our updated memory tool
            memory_tool_str = json.dumps(UPDATED_MEMORY_TOOL, indent=4)
            # Adapt indentation to match the file's style
            indent_match = re.search(r'^(\s+)', tool_str)
            if indent_match:
                indent = indent_match.group(1)
                memory_tool_str = memory_tool_str.replace('\n', f'\n{indent}')
            updated_tools.append(memory_tool_str)
        else:
            updated_tools.append(tool_str)
    
    if not memory_found:
        print(f"WARNING: Memory tool not found in {protocol_path}, skipping")
        return False
    
    # Replace the tools list
    updated_tools_content = ',\n    '.join(updated_tools)
    updated_content = re.sub(r'TOOLS\s*=\s*\[(.*?)\]', f'TOOLS = [\n    {updated_tools_content}\n]', content, flags=re.DOTALL)
    
    # Now update the system prompt to include the MEMORY PROTOCOL section
    prompt_match = re.search(r'def create_default_system_prompt.*?return f"""(.*?)"""', updated_content, re.DOTALL)
    if not prompt_match:
        print(f"WARNING: Could not find system prompt in {protocol_path}, skipping")
        return False
    
    prompt_content = prompt_match.group(1)
    
    # Check if memory protocol already exists
    if "MEMORY PROTOCOL" in prompt_content:
        # Replace the existing protocol with our standardized version
        updated_prompt = re.sub(
            r'(memory tool when it would be helpful.+?)\n\n(MEMORY PROTOCOL:.*?)(?=\n\nYou also have access)',
            f'\\1\n{MEMORY_PROTOCOL}',
            prompt_content,
            flags=re.DOTALL
        )
    else:
        # Add the protocol before the token_manager section
        updated_prompt = re.sub(
            r'(memory tool when it would be helpful.+?)\n\n(You also have access)',
            f'\\1\n{MEMORY_PROTOCOL}\n\\2',
            prompt_content,
            flags=re.DOTALL
        )
    
    # Replace the entire system prompt
    updated_content = re.sub(
        r'def create_default_system_prompt.*?return f"""(.*?)"""',
        f'def create_default_system_prompt.*?return f"""{updated_prompt}"""',
        updated_content,
        flags=re.DOTALL
    )
    
    # Write back the updated content
    with open(protocol_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ Updated {protocol_path}")
    return True

def main():
    """Main function to update all agent protocol files"""
    print("Updating all agent protocol files with memory enhancements...")
    
    success_count = 0
    total_count = 0
    
    for agent in AGENTS:
        protocol_path = BASE_DIR / f"{agent}Agent" / "AgentSkeleton" / "mcp_framework" / "protocol.py"
        total_count += 1
        if update_protocol_file(protocol_path):
            success_count += 1
    
    print(f"Completed: {success_count}/{total_count} agents updated successfully")

if __name__ == "__main__":
    main() 