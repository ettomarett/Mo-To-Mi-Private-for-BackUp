# Token Management System

## Overview

The token management system is designed to monitor and control token usage in long-running conversations with large language models (LLMs). This system helps prevent context window overflows and provides tools for managing conversation length intelligently.

## Understanding Context Length

### What is Context Length?

The "128K context length" of DeepSeek R1 refers to the maximum number of tokens that the model can process in a single interaction:

1. **Token Capacity**: The model can handle up to 128,000 tokens combined between input (prompts, questions, history) and output (responses).

2. **Practical Translation**: This is approximately:
   - 85,000-100,000 words of text
   - 200-300 pages of a typical document
   - Hours of conversation history

3. **Working Memory**: It represents how much information the model can "remember" and reference at once.

### Context Length vs. Permanent Memory

It's important to understand that context length only affects memory within the current conversation session:

1. **Session Memory Limitation**: The 128K context limit only determines how much of your current conversation history can be retained in a single session.

2. **Permanent Memory Independence**: Our permanent memory system (MemoryBank) operates independently of this limit:
   - Memories are stored in files on disk
   - Persist across different conversation sessions
   - Can be retrieved even after restarting the agent
   - Are not bounded by the context window

3. **Memory Integration**: When needed, relevant permanent memories are selectively added to the system prompt to provide context without consuming the entire token budget.

4. **Default Limit**: While the model supports 128K tokens, our system uses a 100K default limit to provide a safety buffer and ensure reliable performance.

## Core Components

### 1. Token Estimation

The system uses tiktoken for accurate token counting with OpenAI-compatible models like DeepSeek:

```python
import tiktoken

def count_tokens(text: str, model_name="gpt-3.5-turbo") -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    For DeepSeek models, we use the OpenAI compatible tokenizers.
    
    Args:
        text: The text to count tokens for
        model_name: The model name to use for tokenization
        
    Returns:
        The number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception:
        # Fall back to a simpler estimate if tiktoken doesn't support the model
        return estimate_tokens(text)
```

With a fallback to heuristic estimation when needed:

```python
def estimate_tokens(text: str) -> int:
    # Simple estimation: spaces + punctuation + words
    words = len(re.findall(r'\w+', text))
    punctuation = len(re.findall(r'[.,!?;:]', text))
    spaces = len(re.findall(r'\s', text))
    
    # Average factor for English text based on tokenization patterns
    return int(1.3 * words + 0.5 * punctuation + 0.3 * spaces)
```

### 2. TokenManager Class

This class tracks token usage and provides thresholds for warnings and summarization:

- `max_tokens`: Maximum number of tokens allowed (default: 100,000)
- `warning_threshold`: Percentage at which to warn about token usage (default: 80%)
- `summarize_threshold`: Percentage at which to trigger summarization (default: 90%)

Key methods:
- `add_message_tokens()`: Tracks tokens for new messages
- `should_warn()`: Determines if a warning should be issued
- `should_summarize()`: Checks if older messages should be summarized
- `get_status()`: Returns current token usage statistics

### 3. TokenManagedConversation Class

This class maintains conversation history with intelligent token management:

- Tracks messages and their token counts
- Manages the system prompt
- Provides methods for summarizing older parts of the conversation
- Exposes token usage statistics

## MCP Tool Implementation

We've implemented token management as an MCP (Modular Communication Protocol) tool, allowing the agent to access and control token management directly through tool calls.

### Tool Definition

```json
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
```

### Supported Operations

1. **status**: Get current token usage statistics
   - Shows current tokens used
   - Maximum token limit
   - Usage percentage
   - Warning and summarization thresholds
   - Whether summarization has been performed

2. **reset**: Reset token count and clear conversation history
   - Clears the conversation
   - Resets token counters

3. **summarize**: Force a summarization of the conversation
   - Attempts to summarize older parts of the conversation
   - Returns success/failure status

4. **Parameter Updates**: Adjust token management settings
   - `max_tokens`: Change the maximum token limit
   - `warning_threshold`: Adjust when warnings appear (0.1-0.95)
   - `summarize_threshold`: Control when summarization occurs (0.2-0.98)

## Using the Token Manager Tool

The agent can use the token manager tool via the MCP tool calling syntax:

```
<mcp:tool>
name: token_manager
parameters: {
  "operation": "status"
}
</mcp:tool>
```

Example operations:

1. **Check token status**:
   ```
   <mcp:tool>
   name: token_manager
   parameters: {
     "operation": "status"
   }
   </mcp:tool>
   ```

2. **Reset the conversation**:
   ```
   <mcp:tool>
   name: token_manager
   parameters: {
     "operation": "reset"
   }
   </mcp:tool>
   ```

3. **Force summarization**:
   ```
   <mcp:tool>
   name: token_manager
   parameters: {
     "operation": "summarize"
   }
   </mcp:tool>
   ```

4. **Update token settings**:
   ```
   <mcp:tool>
   name: token_manager
   parameters: {
     "operation": "status",
     "max_tokens": 120000,
     "warning_threshold": 0.75
   }
   </mcp:tool>
   ```

## Benefits of the MCP Tool Approach

1. **Agent-Controlled Management**: The agent can proactively manage token usage without user intervention
2. **Natural Conversation Flow**: Users can ask about token usage in natural language
3. **Transparency**: Makes token usage visible to users who are curious about it
4. **Flexibility**: Allows runtime adjustments to token management parameters
5. **Integration**: Token management becomes part of the agent's capabilities rather than a separate system
6. **Extensibility**: Easy to add new token management features in the future

## Command-Line Support

For convenience, the command-line interface supports the direct `token status` command, providing a quick way to check token usage:

```
You: token status

Token Status:
Current usage: 1543 tokens
Maximum allowed: 100000 tokens
Percentage used: 1.5%
Summarized messages: 0
```

## Automatic Safeguards

Even without explicit tool calls, the system includes automatic safeguards:

1. **Warning Threshold**: When token usage crosses the warning threshold, a notice appears in the system prompt
2. **Automatic Summarization**: When token usage crosses the summarization threshold, older messages are automatically summarized
3. **Token Tracking**: All messages are automatically tracked for token usage

## Implementation Notes

- Token counting uses tiktoken for OpenAI-compatible models with fallback estimation
- Summarization uses the same LLM to create condensed versions of older conversation parts
- The token manager is fully integrated with the conversation memory system
- Token management is critical for the DeepSeek R1 model which has a finite context window 