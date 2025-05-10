# Centralized System Prompts in Mo-To-Mi Framework

This document explains the centralized system prompt architecture implemented in the Mo-To-Mi framework.

## Overview

All agent system prompts are now defined in a single file:

```
TheFive/Agents_System_Prompts.py
```

This centralization offers several benefits:
- Single source of truth for all agent system prompts
- Easier maintenance and updates
- Consistent prompt format across agents
- Simplified debugging of system prompt issues

## Architecture

The centralized prompt system works as follows:

1. **Definition**: All system prompts are defined as constants in `TheFive/Agents_System_Prompts.py`

2. **Distribution**: 
   - Other parts of the codebase import prompts from this central file
   - No system prompts should be defined anywhere else in the codebase

3. **Backward Compatibility**:
   - `TheFiveinterFace/config/constants.py` still exposes the system prompts
   - It imports them from the centralized file rather than defining them

## How to Modify System Prompts

To update a system prompt:

1. Edit the corresponding prompt in `TheFive/Agents_System_Prompts.py`
2. Changes will be automatically reflected anywhere the prompt is used

Example:
```python
# In TheFive/Agents_System_Prompts.py
OBSERVER_SYSTEM_PROMPT = """
You are the Observer Agent (The Analyzer) in the Mo-To-Mi framework.
...your updated prompt here...
"""
```

## Implementation Details

### Agents_System_Prompts.py

This file contains:
- Constants for each agent's system prompt
- Helper functions to get prompts by agent type
- Agent-specific prompt creation functions for compatibility

### Importing System Prompts

Different parts of the codebase import system prompts as needed:

1. **From TheFiveinterFace/agents/chat.py**:
```python
from Agents_System_Prompts import get_system_prompt

def create_conversation_for_agent(agent_type, client):
    # ...
    system_prompt = get_system_prompt(agent_type)
    conversation.set_system_prompt(system_prompt)
```

2. **From Agent Protocol Files**:
```python
from Agents_System_Prompts import OBSERVER_SYSTEM_PROMPT

def create_default_system_prompt():
    # Use the centralized system prompt
    observer_base_prompt = OBSERVER_SYSTEM_PROMPT
    # Add tool descriptions or other augmentations
    # ...
```

3. **For Backward Compatibility**:
```python
# In TheFiveinterFace/config/constants.py
from Agents_System_Prompts import (
    ARCHITECT_SYSTEM_PROMPT,
    OBSERVER_SYSTEM_PROMPT,
    # ...
)
```

## System Prompt Augmentation

The centralized system prompts define the base behavior of each agent. Augmentations still occur in the processor.py files of each agent when necessary, following these principles:

1. The base prompt is never replaced, only augmented
2. Augmentations happen only when needed (memory retrieval, etc.)
3. Augmentations are temporary and recalculated with each new message

## MCP Tools Integration

The centralized approach separates the agent's core identity from its tool definitions:

1. **Core Identity (in Agents_System_Prompts.py)**: Who the agent is and what responsibilities it has
2. **Tool Definitions (in each agent's protocol.py)**: What tools the agent can use

### How Tools are Added to System Prompts

Each agent's protocol.py combines the base prompt with tool information using a dedicated function:

```python
def create_system_prompt_with_tools() -> str:
    """Create the complete system prompt by combining the base prompt with tool descriptions"""
    # Use the centralized system prompt instead of defining it here
    observer_base_prompt = OBSERVER_SYSTEM_PROMPT
    
    tool_descriptions = format_tool_descriptions()
    
    # Full system prompt with centralized base prompt and tools
    return f"""{observer_base_prompt}

Available tools:
{tool_descriptions}

# Tool usage instructions...
"""
```

This function:
1. Takes the base prompt from the centralized file
2. Formats all of the agent's tools into readable descriptions
3. Combines them into a complete system prompt with usage instructions

### Loading Complete System Prompts

In TheFiveinterFace, the chat.py file loads the complete system prompt (base + tools) from each agent's protocol.py file:

```python
protocol_module = load_agent_protocol(agent_type)
    
if protocol_module and hasattr(protocol_module, "create_system_prompt_with_tools"):
    # Use the agent's protocol.py create_system_prompt_with_tools which includes tools
    system_prompt = protocol_module.create_system_prompt_with_tools()
else:
    # Fallback to centralized system prompt without tools
    from Agents_System_Prompts import get_system_prompt
    system_prompt = get_system_prompt(agent_type)
```

This ensures agents have access to both their identity and their tools.

## Notes on Function Naming

For clarity, we've renamed the function that creates the complete system prompt:

1. **Old name**: `create_default_system_prompt()` (still available as an alias)
2. **New name**: `create_system_prompt_with_tools()` (clearer about what it does)

This naming makes the codebase more self-documenting and clarifies that we're not just creating a default prompt, but specifically combining the base prompt with tool descriptions.

## Resolving the System Prompt Override Issue

This centralized approach helps avoid the system prompt override issue by:

1. Eliminating duplicate prompt definitions across the codebase
2. Providing a clear ownership model for system prompts
3. Making it easier to track and debug prompt modifications

The same augmentation mechanism is preserved, but now it builds upon a centralized base prompt rather than potentially conflicting prompts from different sources. 