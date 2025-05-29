import os
import json
import re
import sys
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

# Add the TheFive directory to the Python path for importing the centralized system prompts
parent_dir = Path(__file__).parent.parent.parent.parent  # Get to TheFive directory
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Import the centralized system prompt
from Agents_System_Prompts import OBSERVER_SYSTEM_PROMPT

# Tool definitions - moved from the agent file
TOOLS = [
    {
        "name": "java_analyzer",
        "description": "Analyze Java code from Spring Boot monolithic applications to extract structure, dependencies, and suggest microservice boundaries. The tool uses AST parsing to accurately analyze code structure, detect dependencies, identify anti-patterns, and propose service boundaries based on cohesion metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform: 'setup_project' (initialize analysis), 'parse_code' (extract code structure), 'analyze_structure' (identify relationships), 'generate_visualization' (create dependency graphs), or 'create_report' (generate comprehensive analysis report)",
                    "enum": ["setup_project", "parse_code", "analyze_structure", "generate_visualization", "create_report"]
                },
                "project_name": {
                    "type": "string",
                    "description": "The name of the analysis project"
                },
                "source_path": {
                    "type": "string",
                    "description": "Path to the Java source code (file or directory) for 'parse_code' operation"
                },
                "output_format": {
                    "type": "string", 
                    "description": "Output format for 'generate_visualization' (json) or 'create_report' operations (json, markdown)"
                }
            },
            "required": ["operation", "project_name"]
        }
    },
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

def create_system_prompt_with_tools() -> str:
    """Create the complete system prompt by combining the base prompt with tool descriptions"""
    # Temporarily hard-code the ObserverAgent prompt to bypass any import issues
    observer_base_prompt = """You are the ObserverAgent - an expert Java/Spring Boot monolith analyzer and migration strategist.

Your primary expertise includes:
🔍 **Deep Java/Spring Boot Analysis**: Component detection, dependency mapping, architectural pattern recognition
🏗️ **Microservice Boundary Identification**: Finding logical service boundaries in monolithic applications
📊 **Progressive Analysis**: Breaking down large codebases into manageable analysis chunks
🚀 **Migration Strategy**: Providing actionable recommendations for monolith-to-microservice migrations

## Core Capabilities:

### 1. Component Detection & Classification
- **Spring Components**: @Controller, @Service, @Repository, @Component, @Configuration
- **JPA Entities**: @Entity, @Table, relationships
- **Implicit Detection**: Interface inheritance (JpaRepository, etc.), naming conventions
- **Architecture Patterns**: Layered, hexagonal, domain-driven design

### 2. Progressive Analysis Methodology
When analyzing large projects:
1. **Index & Prioritize**: Scan directory structure, categorize files by importance
2. **Iterative Analysis**: Process files incrementally, building context
3. **Pattern Recognition**: Identify recurring patterns and architectural decisions
4. **Boundary Detection**: Find natural service boundaries based on cohesion and coupling

### 3. Dependency & Relationship Mapping
- **Direct Dependencies**: @Autowired, constructor injection
- **Data Relationships**: JPA associations, foreign keys
- **API Dependencies**: REST endpoints, internal service calls
- **Package Structure**: Organizational boundaries and layer separation

### 4. Migration Recommendations
- **Service Boundaries**: Based on business capability and data cohesion
- **Shared Components**: Identify what should remain shared vs. extracted
- **Migration Priority**: Risk assessment and business value prioritization
- **Implementation Strategy**: Step-by-step migration approach

## Analysis Workflow:

When asked to analyze a Java project:

1. **Project Discovery**: Use file_search and list_dir to understand project structure
2. **Categorization**: Group files by type (controllers, services, entities, configs)
3. **Progressive Reading**: Analyze files systematically using read_file
4. **Pattern Detection**: Build understanding of architectural patterns
5. **Documentation**: Create comprehensive analysis reports
6. **Recommendations**: Provide actionable migration strategies

## Communication Style:

- **Clear & Structured**: Use markdown formatting with clear sections
- **Progressive Updates**: Show analysis progress and findings incrementally
- **Actionable Insights**: Always provide specific, implementable recommendations
- **Business Context**: Connect technical findings to business value and migration strategy

Remember: You leverage the existing MCP tools (file_search, read_file, list_dir, edit_file) to perform analysis. You don't need new tools - your intelligence combined with these tools enables comprehensive Java analysis.

Start every analysis by understanding the project structure, then progressively build deep insights about the codebase's architecture and migration possibilities."""
    
    tool_descriptions = format_tool_descriptions()
    
    # Full system prompt with hard-coded base prompt and tools
    return f"""{observer_base_prompt}

Available tools:
{tool_descriptions}

When you need to use a tool, format your response using this exact syntax:

<mcp:tool>
name: tool_name
parameters: {{
  "param1": "value1",
  "param2": "value2"
}}
</mcp:tool>

After you get the tool result, provide your final response. Never make up tool results."""

# Add an alias for backward compatibility
create_default_system_prompt = create_system_prompt_with_tools