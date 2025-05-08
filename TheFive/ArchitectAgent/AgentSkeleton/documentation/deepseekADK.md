# DeepSeek R1 on Azure - Integration Guide

This document explains how we integrated DeepSeek R1 running on Azure with our MCP framework, creating an AI assistant with tool capabilities, memory management, and token awareness.

## Overview

We created a direct integration with DeepSeek R1 hosted on Azure AI Foundry using the Azure AI Inference SDK. This approach gives us more control and simpler implementation while maintaining all the assistant functionality.

## Requirements

- Python 3.8+ environment
- Azure AI Foundry account with DeepSeek R1 deployment
- API key for authentication

## Implementation Steps

### 1. Environment Configuration

First, we created a `.env` file to securely store connection details:

```
# DeepSeek API settings
AZURE_DEEPSEEK_ENDPOINT=https://DeepSeek-R1-gADK.eastus.models.ai.azure.com
AZURE_DEEPSEEK_API_KEY=sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i
AZURE_DEEPSEEK_MODEL_NAME=DeepSeek-R1-gADK
```

### 2. Installing Dependencies

We need the Azure AI Inference SDK to communicate with the model:

```bash
pip install azure-ai-inference python-dotenv tiktoken
```

### 3. Building the Client

Our solution uses the official Azure AI SDK for inference with asyncio for non-blocking operation. The key components include:

- **Authentication**: Using AzureKeyCredential with the API key
- **Message Formatting**: Using SystemMessage and UserMessage models
- **Asyncio Integration**: Running synchronous SDK calls in a thread pool
- **Message Conversion**: Converting between our format and the SDK format

Here's the core structure of our client implementation:

```python
class AsyncAzureDeepSeekClient:
    def __init__(self, endpoint=None, api_key=None, model=None):
        self.endpoint = endpoint or os.environ.get("AZURE_DEEPSEEK_ENDPOINT")
        self.api_key = api_key or os.environ.get("AZURE_DEEPSEEK_API_KEY")
        self.model = model or os.environ.get("AZURE_DEEPSEEK_MODEL")
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )

    async def complete(self, messages, max_tokens=2048, temperature=0.7, 
                     tools=None, tool_choice=None, model=None, stream=False):
        # Convert message dictionaries to Azure SDK message objects
        azure_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                azure_messages.append(SystemMessage(content=content))
            elif role == "user":
                azure_messages.append(UserMessage(content=content))
            elif role == "assistant":
                azure_messages.append(AssistantMessage(content=content))
            elif role == "tool" or role == "function":
                # Convert tool messages to user messages for compatibility
                tool_message = f"Tool response: {content}"
                azure_messages.append(UserMessage(content=tool_message))
        
        # Run synchronous client in a thread pool for async operation
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.complete(
                messages=azure_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
                model=model or self.model
            )
        )
        
        return response
```

### 4. Key Challenges & Solutions

#### Asynchronous Operation

Since the Azure AI Inference SDK doesn't provide an async client, we used asyncio's `run_in_executor` to run the synchronous client in a thread pool, ensuring non-blocking operation:

```python
loop = asyncio.get_event_loop()
response = await loop.run_in_executor(
    None,
    lambda: self.client.complete(...)
)
```

#### Message Type Conversion

We needed to convert between our message format and the Azure SDK's message classes:

```python
if role == "system":
    azure_messages.append(SystemMessage(content=content))
elif role == "user":
    azure_messages.append(UserMessage(content=content))
```

#### Tool Messages Handling

Since the Azure AI Inference SDK might not fully support tool messages in the same way as OpenAI, we convert tool messages to user messages with a clear prefix:

```python
if role == "tool" or role == "function":
    tool_message = f"Tool response: {content}"
    azure_messages.append(UserMessage(content=tool_message))
```

## Integration with MCP Framework

Our implementation fully integrates with our existing MCP (Modular Communication Protocol) framework:

### 1. Tool Definition Protocol

We define tools using a structured JSON schema:

```python
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
    }
]
```

### 2. Tool Invocation Protocol

We use our custom XML-like syntax for tool invocation that's easily recognizable by the model and parsable with regex:

```
<mcp:tool>
name: calculator
parameters: {
  "expression": "sqrt(144)"
}
</mcp:tool>
```

### 3. Two-Phase Conversation Flow

Our implementation follows the two-phase conversation pattern:

1. **Request Phase**:
   - Send query to LLM with tool descriptions
   - LLM decides if it needs a tool and formats the request

2. **Execution Phase**:
   - Parse tool invocation using regex pattern matching
   - Execute the requested tool with parameters
   - Return results to LLM for final response

## Token Management Integration

We've integrated TokenManagedConversation to track token usage:

```python
conversation = TokenManagedConversation(
    max_tokens=100000,
    client=client,
    model_name=AZURE_DEEPSEEK_MODEL_NAME
)
```

This enables:
- Automatic token counting
- Warning when approaching limits
- Intelligent summarization of older messages

## Memory System Integration

Our implementation includes both temporary and permanent memory:

```python
# Initialize the memory bank for permanent storage
memory_bank = MemoryBank("permanent_memories")
```

This allows the agent to:
- Remember important information across sessions
- Recall prior conversations
- Store user preferences

## Running the Agent

The agent is run from the command line:

```bash
python -m agents.deepseek_agent
```

This provides:
- Natural language interaction with DeepSeek R1
- Tool-based capabilities (calculator, weather, filesystem, memory)
- Token management
- Permanent memory storage

## Conclusion

By integrating with the Azure AI Inference SDK, we've created a powerful DeepSeek-based agent with advanced capabilities like token management, permanent memory, and tool usage. The implementation is modular, maintainable, and follows best practices for asynchronous operation. 