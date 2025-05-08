# Memory Management in the DeepSeek MCP Agent

This document explains the memory management architecture in our DeepSeek MCP Agent implementation, which features a dual-layer memory system: temporary session memory and permanent persistent memory.

## Overview

Our agent implements two complementary memory systems:

1. **Temporary Session Memory**: Maintains conversation context within a single session
2. **Permanent Memory Storage**: Persists important information across multiple sessions

This dual-layer approach provides both conversational coherence in the short term and long-term knowledge retention, similar to human short-term and long-term memory.

## Temporary Session Memory

### Implementation: `TokenManagedConversation` Class

The temporary session memory is implemented through the `TokenManagedConversation` class, which acts as a message buffer for the current conversation while also managing token usage.

```python
class TokenManagedConversation:
    def __init__(self, max_tokens=100000, summarize_threshold=0.9, warning_threshold=0.8, client=None, model_name=None):
        self.messages = []
        self.system_prompt = None
        self.token_manager = TokenManager(
            max_tokens=max_tokens,
            summarize_threshold=summarize_threshold,
            warning_threshold=warning_threshold
        )
        self.client = client
        self.model_name = model_name
        self.num_summarized = 0
```

### Key Features

- **Message Storage**: Maintains an ordered list of messages (user and assistant)
- **System Prompt Management**: Stores the system prompt separately from conversation turns
- **Token Tracking**: Counts tokens for all messages to prevent context window overflow
- **Automatic Summarization**: Condenses older messages when approaching token limits
- **Azure Client Integration**: Works with the Azure DeepSeek client for completions and summarization

### How It Works

1. Each user and assistant message is added to the history with token counting
2. When querying the DeepSeek model, all messages are included in the request
3. When approaching token limits, older messages are automatically summarized
4. The system can warn when nearing context limits and trigger actions

### Example Usage

```python
# Initialize with the Azure DeepSeek client
conversation = TokenManagedConversation(
    max_tokens=100000,
    client=azure_deepseek_client,
    model_name="DeepSeek-R1-gADK"
)

# Set system prompt
conversation.set_system_prompt("You are a helpful AI assistant.")

# Add messages with automatic token tracking
conversation.add_message("Hello, how are you?", role="user")
conversation.add_message("I'm doing well! How can I help you today?", role="assistant")

# Get formatted messages for the DeepSeek model
messages = conversation.get_messages()

# Check token status
token_info = conversation.get_token_status()
print(f"Using {token_info['current_tokens']} out of {token_info['max_tokens']} tokens")

# Maybe summarize if needed
await conversation.maybe_summarize()
```

## Permanent Memory Storage

### Implementation: `MemoryBank` Class

The permanent memory system is implemented through the `MemoryBank` class, which provides persistent storage of important information across sessions.

```python
class MemoryBank:
    def __init__(self, storage_dir="memories"):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        self.memory_index = self._load_index()
    
    def store_memory(self, content, key=None, tags=None):
        # Generate or use provided key
        # Store content to file
        # Update index
        return key
    
    def retrieve_memory(self, key):
        # Find and load content from storage
        return content
```

### Key Features

- **File-Based Storage**: Each memory is stored in a separate text file
- **Indexing System**: Maintains a JSON index of all memories with metadata
- **Content Addressing**: Each memory has a unique key for retrieval
- **Tagging System**: Memories can be tagged for categorization
- **Search Capabilities**: Content and tag-based search functionality

### Folder Structure

```
permanent_memories/
├── index.json         # Metadata for all memories
├── memory_20240520123456.txt  # Individual memory file
└── ...
```

### Memory Tool Operations

The DeepSeek model interacts with the memory system through a dedicated MCP tool:

```python
{
    "name": "memory",
    "description": "Store and retrieve permanent memories across conversations",
    "parameters": {
        "operation": {
            "enum": ["store", "retrieve", "search", "delete", "list"]
        },
        ...
    }
}
```

Operations include:
- **store**: Save new information
- **retrieve**: Get specific memory by key
- **search**: Find memories by content or tags
- **delete**: Remove a memory
- **list**: Show all available memories

## Integration of Both Systems

### System Prompt Enhancement

When processing a query, the agent enhances the system prompt with relevant memories:

```python
system_prompt = create_default_system_prompt()
if memory_bank:
    memories = memory_bank.format_for_context(max_memories=3)
    system_prompt += f"\n\n{memories}"
```

### Natural Language Interface

The DeepSeek model is instructed to use the memory tool when appropriate:

```
You have access to permanent memory storage. When the user mentions something 
important they want to remember, or when they ask about something they've told 
you before, use the memory tool to store or retrieve information.
```

### MCP Protocol Integration

When the DeepSeek model decides to use the memory tool:

1. It formats a tool call using the MCP syntax:
   ```
   <mcp:tool>
   name: memory
   parameters: {
     "operation": "store",
     "content": "User's name is Omar",
     "tags": ["personal", "identity"]
   }
   </mcp:tool>
   ```

2. The agent executes the memory operation and returns results
3. DeepSeek incorporates the memory information in its response

## Usage Examples

### Natural Memory Storage

Users can store memories through natural language:

```
User: Remember that my name is Omar
Assistant: [Uses memory tool to store] Great, I've stored your name as "Omar" in my permanent memory!
```

### Memory Retrieval

When asked about previously stored information:

```
User: What's my name?
Assistant: [Uses memory tool to retrieve] Your name is Omar!
```

### Search and List Operations

The agent can search for relevant memories:

```
User: What do you know about my preferences?
Assistant: [Uses memory tool to search tags="preferences"] I know that your favorite fruit is mango and you prefer coffee over tea.
```

## Advanced Features

### Conversation Summarization for Memory

The agent can save important conversation segments to memory:

```python
def get_conversation_for_memory(self, num_exchanges=3):
    recent_messages = self.messages[-num_exchanges*2:]
    formatted = "Recent conversation:\n\n"
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n\n"
    return formatted
```

### Smart Memory Suggestions

When the token manager triggers summarization, important information is automatically saved to permanent memory:

```python
async def maybe_summarize(self):
    if self.token_manager.should_summarize():
        # Identify key information in messages to be summarized
        important_info = self._extract_important_info(messages_to_summarize)
        
        # Save to memory bank
        if important_info and self.memory_bank:
            self.memory_bank.store_memory(
                content=important_info,
                tags=["auto_saved", "summarized"]
            )
```

## Conclusion

This dual-layer memory system provides DeepSeek R1 with both short-term conversational context and long-term knowledge persistence. The natural language interface to memory operations creates an intuitive user experience where the agent automatically manages what information to remember without explicit commands from the user. 