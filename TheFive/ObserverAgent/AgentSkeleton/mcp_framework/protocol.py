import os
import json
import re
from typing import List, Dict, Any, Optional, Union, Tuple

# Tool definitions - moved from the agent file
TOOLS = [
    {
        "name": "calculator",
        "description": "Performs mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "filesystem",
        "description": "Browse files and directories on the system",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform: 'list_dir', 'read_file', or 'search_files'",
                    "enum": ["list_dir", "read_file", "search_files"]
                },
                "path": {
                    "type": "string",
                    "description": "The file or directory path (relative to the current directory or absolute)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern for search_files operation (e.g., '*.py', '*.md')"
                }
            },
            "required": ["operation", "path"]
        }
    },
    {
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
    },
    {
        "name": "token_manager",
        "description": "Manage conversation token usage and get token status",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform: 'status', 'reset', 'summarize'",
                    "enum": ["status", "reset", "summarize"]
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Set new maximum token limit (for adjusting token capacity)"
                },
                "warning_threshold": {
                    "type": "number",
                    "description": "Set new warning threshold percentage (0.0-1.0)"
                },
                "summarize_threshold": {
                    "type": "number",
                    "description": "Set new summarization threshold percentage (0.0-1.0)"
                }
            },
            "required": ["operation"]
        }
    }
]

def format_tool_descriptions() -> str:
    """Format the tool descriptions for inclusion in the system prompt"""
    formatted_tools = []
    for tool in TOOLS:
        params_str = json.dumps(tool["parameters"], indent=2)
        formatted_tools.append(f"""
Tool: {tool["name"]}
Description: {tool["description"]}
Parameters: {params_str}
""")
    return "\n".join(formatted_tools)

def extract_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    """Extract tool calls from the response text"""
    tool_pattern = r"<mcp:tool>\s*name:\s*([^\n]+)\s*parameters:\s*({[^<]+})\s*</mcp:tool>"
    matches = re.findall(tool_pattern, response_text, re.DOTALL)
    
    tool_calls = []
    for match in matches:
        tool_name = match[0].strip()
        try:
            parameters = json.loads(match[1].strip())
            tool_calls.append({"name": tool_name, "parameters": parameters})
        except json.JSONDecodeError:
            # If parameters aren't valid JSON, try to extract them as key-value pairs
            params_text = match[1].strip()
            parameters = {}
            for line in params_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    parameters[key.strip()] = value.strip()
            tool_calls.append({"name": tool_name, "parameters": parameters})
    
    return tool_calls

def create_default_system_prompt() -> str:
    """Create the default system prompt with tool descriptions"""
    return f"""You are a helpful AI assistant with access to tools and memory of the conversation history.

Available tools:
{format_tool_descriptions()}

When you need to use a tool, format your response using this exact syntax:

<mcp:tool>
name: tool_name
parameters: {{
  "param1": "value1",
  "param2": "value2"
}}
</mcp:tool>

After you get the tool result, provide your final response. Never make up tool results.

You have access to permanent memory storage. When the user mentions something important they want to remember,
or when they ask about something they've told you before, use the memory tool to store or retrieve information.
Be proactive about using the memory tool when it would be helpful, but don't overuse it for trivial details.

MEMORY PROTOCOL: Always ask for explicit confirmation BEFORE storing any information permanently. 
Only after receiving clear confirmation should you use the memory tool with has_explicit_permission=true.
If you store without permission or with permission=false, the request will be rejected.

You also have access to the token_manager tool which helps manage conversation token usage. Use it when:
- The user asks about token usage or conversation length
- The user wants to reset the conversation
- The user asks to check if summarization is needed
- The user wants to change token limit settings

The token_manager tool can show the current token usage, force summarization, or reset the conversation.
"""