# My MCP Framework

A modular, extensible framework for building AI assistants with advanced memory management and tool capabilities.

## Overview

This framework provides a modular architecture for creating AI assistants with:

- **Tool Usage**: Standardized function calling through MCP (Modular Communication Protocol)
- **Memory Management**: Both permanent storage and conversation history with token awareness
- **Modular Design**: Easily swap models, add tools, or modify components

## Architecture

The framework follows a clear separation of concerns with three main components:

### Core Components (`/core/`)

Foundation modules that are model-agnostic and provide essential services:

- `token_management.py`: Token counting, tracking, and conversation management
- `memory_bank.py`: Permanent memory storage system  
- `memory_management.py`: Conversation memory/history management
- `tool_orchestration.py`: General tool management infrastructure

### MCP Protocol (`/mcp/`)

Specific implementation of the Modular Communication Protocol:

- `protocol.py`: Defines tools, extraction patterns, and system prompts
- `tool_executor.py`: Implements the execution logic for each tool
- `processor.py`: Manages the workflow of processing messages with tools
- `__init__.py`: Provides clean exports for all MCP functionality

### Clients (`/clients/`)

Model-specific client implementations:

- `azure_chat_client.py`: Client for DeepSeek on Azure
- `openai_client.py`: Client for OpenAI models
- `direct_azure_client.py`: Alternative direct implementation

### Agents (`/agents/`)

High-level agent implementations that use the framework:

- `deepseek_mcp_agent.py`: Agent using DeepSeek model with MCP

## Key Concepts

### Token Management

The framework automatically tracks token usage to:

- Prevent exceeding model context limits
- Warn when approaching thresholds
- Summarize older parts of conversation
- Provide status information

### Memory Systems

Two complementary memory systems:

1. **Conversation Memory**: Managed by `TokenManagedConversation` to maintain context during a session
2. **Permanent Memory**: Persistent storage via `MemoryBank` that survives across sessions

### MCP Tool Protocol

A standardized way for the LLM to request tool execution:

```
<mcp:tool>
name: tool_name
parameters: {
  "param1": "value1",
  "param2": "value2"
}
</mcp:tool>
```

## Available Tools

- **calculator**: Performs mathematical calculations
- **weather**: Gets weather information (simulated)
- **filesystem**: Browses files and directories
- **memory**: Stores and retrieves information in permanent memory
- **token_manager**: Manages conversation token usage

## How To Use

### Running an Agent

```python
# Use the DeepSeek MCP agent
from agents.deepseek_mcp_agent import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Creating a New Agent

```python
import asyncio
from clients.your_client import initialize_client
from core.memory_bank import MemoryBank
from core.token_management import TokenManagedConversation
from mcp import process_with_tools

# Initialize components
client = initialize_client()
model_name = "your-model-name"
conversation = TokenManagedConversation(
    max_tokens=100000,
    client=client,
    model_name=model_name
)
memory_bank = MemoryBank("permanent_memories")

# Process messages
response, conversation = await process_with_tools(
    client=client,
    model_name=model_name,
    question="Your message here",
    conversation=conversation,
    memory_bank=memory_bank
)
```

### Adding New Tools

To add a new tool:

1. Add tool definition to `mcp/protocol.py` in the `TOOLS` list
2. Implement the tool execution in `mcp/tool_executor.py`

## Extending the Framework

### Supporting New Models

1. Create a new client implementation in the `/clients/` directory
2. Ensure it provides the required interface (especially the `complete` method)
3. Create a new agent that uses this client

### Creating Different Protocols

You can create alternatives to MCP by:

1. Creating a new protocol directory (e.g., `/my_protocol/`)
2. Implementing your own parsing/execution logic
3. Reusing the core components as needed

## Key Benefits of This Architecture

- **Modularity**: Components can be replaced or extended independently
- **Reusability**: Core functionality can be shared across different implementations
- **Maintainability**: Changes to one component don't require changes to others
- **Extensibility**: Easy to add new tools, models, or protocols

## Best Practices

- Keep tool implementations stateless where possible
- Maintain clear separation between protocol and core functionality
- Document new tools and clients thoroughly
- Use type hints to ensure interface consistency

## Future Enhancements

Potential areas for improvement:

- Response streaming for more responsive interactions
- Configuration system for easy model/setting switching
- Additional agent implementations
- Enhanced tool capabilities
- Integration with web capabilities 