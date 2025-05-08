# Agent Craft: Comprehensive Guide to the DeepSeek MCP Framework

## 1. System Overview

The DeepSeek MCP Framework is a modular, extensible architecture for building AI assistants with advanced capabilities:

- **Azure DeepSeek Integration**: Direct integration with DeepSeek R1 on Azure
- **Tool Usage**: Standardized function calling through our MCP (Modular Communication Protocol)
- **Memory Management**: Both session-based and permanent storage systems
- **Token Awareness**: Intelligent handling of context limits with summarization
- **Asynchronous Architecture**: Non-blocking design for responsive interactions

![System Architecture](../assets/system_architecture.png)

### Key Components

Our system consists of five core components working together:

1. **Client Layer**: Azure DeepSeek integration with asyncio support
2. **Core Systems**: Token management, memory systems, and utilities
3. **MCP Framework**: Protocol definition, tool registration, and execution
4. **Tools**: Calculator, weather, filesystem, memory, and more
5. **Agent Implementation**: Complete agents integrating all components

## 2. Setup and Installation

### Prerequisites

- Python 3.8+ environment
- Azure AI Foundry account with DeepSeek R1 deployment
- API key for authentication

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/basic-agent.git
cd basic-agent

# Create a virtual environment
python -m venv deepseek_env

# Activate the environment (Windows)
.\deepseek_env\Scripts\Activate.ps1
# OR (Mac/Linux)
source deepseek_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with your Azure DeepSeek credentials:

```
# DeepSeek API settings
AZURE_DEEPSEEK_ENDPOINT=https://your-deployment.eastus.models.ai.azure.com
AZURE_DEEPSEEK_API_KEY=your_api_key_here
AZURE_DEEPSEEK_MODEL_NAME=DeepSeek-R1-gADK

# Paths and settings
PERMANENT_MEMORY_DIR=permanent_memories
```

### Running the Agent

```bash
# From the project root
python -m agents.deepseek_agent
```

## 3. Core Components

### 3.1 Azure DeepSeek Client

Our client implementation uses the Azure AI Inference SDK with asyncio for non-blocking operation:

```python
class AsyncAzureDeepSeekClient:
    def __init__(self, endpoint=None, api_key=None, model=None):
        # Initialize client with credentials
        
    async def complete(self, messages, max_tokens=2048, temperature=0.7, 
                     tools=None, tool_choice=None, model=None, stream=False):
        # Convert message formats
        # Run synchronous client in a thread pool
        # Return response
```

Key features:
- Thread pool execution for non-blocking operation
- Message format conversion between our system and Azure SDK
- Proper handling of tool messages
- Configurable parameters like temperature and max_tokens

### 3.2 Token Management

Our token management system prevents context window overflows:

```python
class TokenManager:
    def __init__(self, max_tokens=100000, warning_threshold=0.8, summarize_threshold=0.9):
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.warning_threshold = warning_threshold
        self.summarize_threshold = summarize_threshold
        self.warning_issued = False
```

Key concepts:
- **Context Length**: DeepSeek R1 has a 128K token context window
- **Token Counting**: Using tiktoken for accurate counts
- **Thresholds**: Warning (80%) and summarization (90%) triggers
- **Safety Buffer**: 100K default limit (vs. 128K maximum)

### 3.3 Memory Systems

Our agent implements a dual-layer memory architecture:

#### 3.3.1 Session Memory (TokenManagedConversation)

```python
class TokenManagedConversation:
    def __init__(self, max_tokens=100000, summarize_threshold=0.9, 
                warning_threshold=0.8, client=None, model_name=None):
        # Initialize conversation with token management
```

Features:
- Message history tracking with token counting
- System prompt management
- Automatic summarization of older messages
- Support for conversation status queries

#### 3.3.2 Permanent Memory (MemoryBank)

```python
class MemoryBank:
    def __init__(self, storage_dir="permanent_memories"):
        # Initialize memory bank with filesystem storage
```

Features:
- File-based persistence across sessions
- JSON indexing with metadata
- Tagging system for categorization
- Content-based search capabilities

### 3.4 MCP Framework

Our Modular Communication Protocol (MCP) enables LLM-tool interaction:

```python
# Tool definition
TOOLS = [
    {
        "name": "calculator",
        "description": "Performs mathematical calculations",
        "parameters": {
            # Parameter schema
        }
    },
    # More tools...
]

# Tool extraction pattern
tool_pattern = r"<mcp:tool>\s*name:\s*([^\n]+)\s*parameters:\s*({[^<]+})\s*</mcp:tool>"
```

Key components:
- Tool definitions with JSON Schema
- Pattern matching for tool extraction
- Tool execution engine
- Two-phase conversation flow

## 4. Tool Development

### 4.1 Tool Structure

Each tool follows a consistent structure:

1. **Tool Definition**: JSON Schema in `protocol.py`
2. **Tool Implementation**: Function in `tool_executor.py`
3. **Tool Registration**: Added to the `TOOLS` list

### 4.2 Creating a New Tool

To create a new tool:

```python
# 1. Define the tool in protocol.py
{
    "name": "my_new_tool",
    "description": "Description of what the tool does",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Description of parameter 1"
            }
        },
        "required": ["param1"]
    }
}

# 2. Implement in tool_executor.py
def execute_my_new_tool(params, conversation=None, memory_bank=None):
    param1 = params.get("param1")
    # Tool logic here
    return {"result": "processed result"}
    
# 3. Add to tool execution switch
def execute_tool(tool_name, params, conversation=None, memory_bank=None):
    if tool_name == "my_new_tool":
        return execute_my_new_tool(params, conversation, memory_bank)
    # Other tools...
```

## 5. Workflow Examples

### 5.1 Basic Conversation

```
You: Hello, I'm new here.
Agent: Welcome! I'm the DeepSeek assistant. I can help with various tasks. Would you like to see what I can do?
You: Can you calculate 1234 * 5678?
Agent: I'll calculate that for you.
<mcp:tool>
name: calculator
parameters: {"expression": "1234 * 5678"}
</mcp:tool>
The answer is 7,006,652.

You: Can you remember that my favorite color is blue?
Agent: I'll remember that for you.
<mcp:tool>
name: memory
parameters: {"operation": "store", "content": "User's favorite color is blue", "tags": ["preferences", "colors"]}
</mcp:tool>
I've stored that your favorite color is blue in my permanent memory.

You: What's my favorite color?
Agent: Let me check my memory.
<mcp:tool>
name: memory
parameters: {"operation": "search", "query": "favorite color"}
</mcp:tool>
According to my memory, your favorite color is blue.
```

### 5.2 Using Multiple Tools

```
You: I need to know if I should take an umbrella today in New York.
Agent: Let me check the weather for you.
<mcp:tool>
name: weather
parameters: {"location": "New York", "units": "imperial"}
</mcp:tool>
I checked the weather in New York. It's currently 68°F with a 70% chance of rain. I would recommend taking an umbrella with you today.

You: How many days until Christmas?
Agent: Let me calculate that for you.
<mcp:tool>
name: date
parameters: {"operation": "days_until", "target_date": "2023-12-25"}
</mcp:tool>
There are 45 days until Christmas.
```

### 5.3 Token Management in Action

```
You: Can you tell me a very long story?
Agent: I'd be happy to tell you a story about...
[Long story content]

You: Tell me another long story.
Agent: I notice our conversation is getting quite long (currently at 82% of our token limit). I'll tell you another story, but I may need to summarize our earlier conversation if we approach the limit.
[Second long story]

You: Tell me one more long story.
Agent: Our conversation is now at 92% of the token limit. I'll summarize our earlier conversation to make room.
<mcp:tool>
name: token
parameters: {"operation": "summarize"}
</mcp:tool>
I've summarized our previous conversation to save space. Now I can tell you a third story...
```

## 6. Agent Implementation

### 6.1 Agent Structure

The main DeepSeek agent file integrates all components:

```python
async def main():
    # 1. Load environment variables
    load_dotenv()
    
    # 2. Initialize the client
    client = initialize_client()
    
    # 3. Initialize memory systems
    conversation = TokenManagedConversation(
        max_tokens=100000,
        client=client,
        model_name="DeepSeek-R1-gADK"
    )
    memory_bank = MemoryBank()
    
    # 4. Set the system prompt
    conversation.set_system_prompt(SYSTEM_PROMPT)
    
    # 5. Main conversation loop
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Process with the model
        response = await process_with_tools(
            user_input, 
            conversation, 
            client, 
            memory_bank
        )
        
        print(f"Agent: {response}")
```

### 6.2 Core Processing Logic

```python
async def process_with_tools(user_input, conversation, client, memory_bank):
    # 1. Add user message to conversation
    conversation.add_message("user", user_input)
    
    # 2. Get the formatted conversation for the model
    formatted_messages = conversation.get_messages()
    
    # 3. Call the model
    response = await client.complete(
        messages=formatted_messages,
        tools=TOOLS,
        temperature=0.7
    )
    
    # 4. Extract content and tool calls
    content = response.choices[0].message.content or ""
    tool_calls = extract_tool_calls(content)
    
    # 5. Process any tool calls
    if tool_calls:
        for tool_call in tool_calls:
            # Execute the tool
            tool_result = execute_tool(
                tool_call["name"], 
                tool_call["parameters"],
                conversation,
                memory_bank
            )
            
            # Add tool result to conversation
            conversation.add_message(
                "system",
                f"Tool '{tool_call['name']}' returned: {tool_result}"
            )
        
        # Call the model again with tool results
        formatted_messages = conversation.get_messages()
        final_response = await client.complete(
            messages=formatted_messages,
            tools=TOOLS,
            temperature=0.7
        )
        content = final_response.choices[0].message.content or ""
    
    # 6. Add assistant response to conversation
    conversation.add_message("assistant", content)
    
    return content
```

## 7. API Reference

### 7.1 AsyncAzureDeepSeekClient

```python
class AsyncAzureDeepSeekClient:
    """Client for interacting with Azure-hosted DeepSeek models."""
    
    def __init__(self, endpoint=None, api_key=None, model=None):
        """
        Initialize the client.
        
        Args:
            endpoint (str): Azure endpoint URL
            api_key (str): Azure API key
            model (str): Model deployment name
        """
        
    async def complete(self, messages, max_tokens=2048, temperature=0.7, 
                     tools=None, tool_choice=None, model=None, stream=False):
        """
        Generate a completion from the model.
        
        Args:
            messages (list): List of message dicts with role and content
            max_tokens (int): Maximum tokens to generate
            temperature (float): Sampling temperature
            tools (list): Tool definitions in OpenAI format
            tool_choice (str/dict): Tool choice specification
            model (str): Override model name
            stream (bool): Whether to stream the response
            
        Returns:
            CompletionResponse: Response object with choices
        """
```

### 7.2 TokenManagedConversation

```python
class TokenManagedConversation:
    """Manages conversation history with token awareness."""
    
    def __init__(self, max_tokens=100000, summarize_threshold=0.9, 
                warning_threshold=0.8, client=None, model_name=None):
        """
        Initialize the conversation manager.
        
        Args:
            max_tokens (int): Maximum tokens allowed
            summarize_threshold (float): Threshold to trigger summarization
            warning_threshold (float): Threshold to trigger warnings
            client (AsyncAzureDeepSeekClient): Client for summarization
            model_name (str): Model name for token counting
        """
    
    def add_message(self, role, content):
        """
        Add a message to the conversation.
        
        Args:
            role (str): Message role (user, assistant, system)
            content (str): Message content
            
        Returns:
            bool: Whether token threshold was exceeded
        """
    
    def set_system_prompt(self, prompt):
        """
        Set or update the system prompt.
        
        Args:
            prompt (str): System prompt text
        """
    
    def get_messages(self):
        """
        Get all messages in the conversation.
        
        Returns:
            list: List of message dictionaries
        """
    
    def maybe_summarize(self):
        """
        Summarize older messages if token threshold is exceeded.
        
        Returns:
            bool: Whether summarization was performed
        """
    
    def get_token_status(self):
        """
        Get the current token usage status.
        
        Returns:
            dict: Token usage statistics
        """
```

### 7.3 MemoryBank

```python
class MemoryBank:
    """Manages permanent memories with search and retrieval."""
    
    def __init__(self, storage_dir="permanent_memories"):
        """
        Initialize the memory bank.
        
        Args:
            storage_dir (str): Directory for storage
        """
    
    def store(self, content, tags=None, metadata=None):
        """
        Store a new memory.
        
        Args:
            content (str): Memory content
            tags (list): List of tags
            metadata (dict): Additional metadata
            
        Returns:
            str: Memory ID
        """
    
    def retrieve(self, memory_id):
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id (str): Memory identifier
            
        Returns:
            dict: Memory data
        """
    
    def search(self, query, limit=5):
        """
        Search memories by content similarity.
        
        Args:
            query (str): Search query
            limit (int): Maximum results
            
        Returns:
            list: Matching memories
        """
    
    def list_memories(self, tag=None, limit=10):
        """
        List available memories.
        
        Args:
            tag (str): Optional tag filter
            limit (int): Maximum results
            
        Returns:
            list: Memory summaries
        """
```

## 8. Troubleshooting and Best Practices

### 8.1 Common Issues

#### 8.1.1 Authentication Issues
```
Error: AuthenticationError: Authentication failed. Please check your credentials.
```

**Solution:**
- Verify API key is correctly set in .env file
- Check endpoint URL format
- Ensure Azure subscription is active

#### 8.1.2 Tool Parsing Failures
```
Error: Failed to parse tool call: Invalid JSON in parameters
```

**Solution:**
- Check tool definitions for schema conformance
- Ensure model is generating valid JSON
- Add more examples to the system prompt

#### 8.1.3 Token Limit Exceeded
```
Error: Token limit exceeded. Maximum tokens: 100000, Attempted: 102500
```

**Solution:**
- Lower the token warning threshold
- Implement more aggressive summarization
- Clear conversation history periodically

### 8.2 Best Practices

#### 8.2.1 System Prompt Design
- Keep instructions clear and concise
- Include examples of tool usage
- Define conversation boundaries

#### 8.2.2 Memory Management
- Store only important information in permanent memory
- Use tags effectively for retrieval
- Clear temporary session memory when appropriate

#### 8.2.3 Error Handling
- Implement graceful fallbacks for tool failures
- Provide meaningful error messages to users
- Log errors for debugging

#### 8.2.4 Performance Optimization
- Use appropriate temperature settings
- Implement caching for frequent operations
- Consider batching requests when possible

## 9. Extending the Framework

### 9.1 Adding New Models

To add support for a new model:

1. Create a new client implementation in `clients/`
2. Implement the same interface as `AsyncAzureDeepSeekClient`
3. Add token counting support if needed
4. Update the client factory in `initialize_client()`

### 9.2 Custom Tool Integration

To integrate with external services:

1. Define the tool interface in `protocol.py`
2. Implement API calls in `tool_executor.py`
3. Add authentication if required
4. Register the tool in the `TOOLS` list

### 9.3 UI Integration

The agent can be integrated with various UI frameworks:

- Command-line interface (current implementation)
- Web interface with Flask/FastAPI
- Desktop application with PyQt/Tkinter
- Mobile apps through REST API

## 10. Conclusion

The DeepSeek MCP Framework provides a robust foundation for building advanced AI assistants with:

- Powerful language model capabilities through Azure DeepSeek
- Extensible tool usage with our MCP protocol
- Sophisticated memory management for long-running conversations
- Token-aware conversation handling for reliability
- Modular design for easy customization and extension

By understanding the components and workflows detailed in this guide, you can leverage the full power of this framework to create intelligent, responsive, and capable AI assistants for a wide range of applications.