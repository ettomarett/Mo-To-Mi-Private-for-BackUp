# TheFiveinterFace - Memory Architecture

This document provides a detailed explanation of the memory management system in TheFiveinterFace, which is designed to handle different types of memory for the agents in the monolith-to-microservices migration tool.

## Memory Management Overview

TheFiveinterFace implements three interconnected types of memory:

1. **Token Management System** - Tracks conversation token usage and performs auto-summarization
2. **Conversation Memory** - Saves and loads entire chat sessions with persistence
3. **Permanent Memory** - Stores important information that persists across all conversations

![Memory Architecture](https://mermaid.ink/img/pako:eNp1kU1PwzAMhv9KlBMgbYeduOxQtEnAwA9AHKJim9aisaM4YdOm_nfSdmyTEL7YfvzGr-QjKmMpEoldYyudwx2xK5AHk_Xv1LJzDZyxdJI8PK1fXsN8Op_fwevdA0wXd-F6D4tWqacDOoI8JMbkNHYkzSl_qY0x8EWZL7wBB3tX-wj8mjLr1y4QUVNjV2i9-9Bz9LWU1iL1aS4oUEZlYdDWoVSptipk43_JvmLjCZRZu5L1vaNKB0eArrC9vP-_naMIpXLM89FoNIg4SU4n5Jt5RcRZFqEd8IQ_qL6sQxzKVEKb_WCtP57cLMajK5TZmVJqp2sdgZq3dYKSsNLZE5qKY-A0YmPjUJu296_bvyNJDV5lGCQR3qftAMc47a7fAYbCmBg?type=png)

## 1. Token Management System

### Purpose
The token management system prevents hitting token limits during conversations by tracking usage and summarizing older messages when approaching limits.

### Implementation
Located in `agents/chat.py` as part of the `TokenManagedConversation` class.

Key components:
- **Token Counting**: Tracks tokens used in the conversation
- **Auto-Summarization**: Summarizes older messages when approaching token limits
- **Token Status Reporting**: Provides a dashboard of current token usage

```python
# Example of token tracking logic
def get_token_status(self):
    return {
        "current_tokens": self.current_tokens,
        "max_tokens": self.max_tokens,
        "num_summarized": len(self.summarized_groups),
        "percentage": (self.current_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
    }
```

### Auto-Summarization Process
1. Continuously monitors token usage during conversations
2. When usage exceeds threshold (typically ~80%), oldest messages are grouped
3. AI generates a summary of the grouped messages
4. Original messages are replaced with the summary
5. Process repeats as needed to maintain token usage below limits

## 2. Conversation Memory

### Purpose
Enables saving and loading entire conversations, allowing users to revisit past interactions or continue previous sessions.

### Implementation
Primarily managed through:
- `utils/conversation_manager.py`: Core storage/retrieval functions
- `utils/session.py`: Session state management for conversations

Key functions:
- `save_current_conversation(agent_type, name)`: Saves the current conversation
- `load_conversation_for_agent(agent_type, name)`: Loads a saved conversation
- `start_new_conversation(agent_type)`: Initializes a new conversation

### Storage Format
Conversations are stored as JSON files in `saved_chats/<agent_type>/` with this structure:

```json
{
  "name": "conversation_name",
  "agent_type": "architect",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "timestamp": "2025-05-08T02:50:03.673067"
}
```

### Naming Strategy
- Default naming is timestamp-based: `{agent_type}_{YYYYMMDD_HHMMSS}`
- Users can provide custom names via the UI
- The system ensures unique names by appending numbers when needed
- **Display vs. Storage**: The system now preserves the exact user-provided display name in the conversation metadata, while using a sanitized version only for the underlying file storage
- User-provided names are displayed exactly as entered throughout the interface
- The UI clearly indicates that names will be preserved as entered, improving user experience

### Implementation Details
The conversation saving process now follows these steps:
1. User enters a desired name in the UI
2. The exact name is stored as the `display_name` in the conversation JSON metadata
3. A sanitized version of the name (alphanumeric and certain symbols only) is used for the filename
4. When loading or displaying conversations, the original display name from the metadata is used
5. This approach maintains a clean filesystem while preserving the user's intended naming scheme

### Key Files and Functions
The conversation naming strategy is implemented across several files:

- **`utils/conversation_manager.py`**:
  - `save_conversation()`: Handles preserving the display name in JSON metadata while using a sanitized filename
  - `load_conversation()`: Loads conversations by their sanitized filenames
  - `list_conversations()`: Returns the display names from metadata rather than filename stems
  - `get_unique_name()`: Ensures unique display names by appending numerical suffixes

- **`utils/session.py`**:
  - `save_current_conversation()`: Passes the user-provided name to the conversation manager
  - `load_conversation_for_agent()`: Updates the UI state with the loaded conversation's display name
  - `start_new_conversation()`: Resets the conversation name to default

- **`ui/migration_workflow.py`**:
  - Contains the text input field for naming conversations
  - Handles the UI presentation and feedback for conversation naming
  - Passes the user-provided name to the session management functions

## 3. Permanent Memory

### Purpose
Stores key information that persists across all conversations and sessions, creating a long-term memory for agents.

### Implementation
Built on `AgentSkeleton.core.memory_bank.MemoryBank` with UI integrations.

Key operations:
- **Storage**: Save named memories with optional tags
- **Retrieval**: Load memories by name or search
- **Searching**: Find memories by content or tags

### Storage Format
Permanent memories are stored as individual text files in `permanent_memories/` with metadata tracking.

## UI Integration

The memory management system is exposed to users through a tabbed interface in the agent sidebar:

1. **Conversations Tab**: Save, load, and manage conversations
2. **Permanent Memory Tab**: Create, view, and search permanent memories
3. **Token Status Tab**: View token usage with visualization

### Key UI Components
Located in `ui/migration_workflow.py`:

- **Conversation Management UI**: 
  - Save/load conversation dialogs
  - Conversation naming interface
  - New conversation management

- **Permanent Memory UI**:
  - Memory creation form
  - Memory browsing and search
  - Memory viewing and deletion

- **Token Status UI**:
  - Visual gauge of token usage
  - Statistics on token consumption
  - Manual summarization trigger

## Integration with TheFive

The memory system in TheFiveinterFace works in conjunction with TheFive's AgentSkeleton framework. This integration requires careful management of import paths and module access.

### Key Integration Points

1. **Memory Bank Integration**:
   - TheFiveinterFace uses `AgentSkeleton.core.memory_bank.MemoryBank` from TheFive
   - Import path resolution is handled in `config/paths.py`

2. **Agent Access to Memory**:
   - Agents loaded from TheFive access the memory bank through parameter passing
   - Memory bank instances are created in TheFiveinterFace and passed to TheFive agents

### Import Path Considerations

When working with memory functionality, be aware of potential import conflicts:

```python
# The paths.setup_paths() function adds TheFive directories to sys.path
# This can cause imports to resolve to TheFive modules instead of TheFiveinterFace

# PROBLEMATIC:
from agents import chat  # May resolve to TheFive's agents module

# RECOMMENDED:
# Use direct module loading for critical components
agent_chat_path = current_dir / "agents" / "chat.py"
spec = importlib.util.spec_from_file_location("chat", agent_chat_path)
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)
```

### Memory Permission System

A critical addition to the memory system is the explicit permission requirement for storing user preferences. This is implemented at two levels:

1. **System Prompts**:
   - All agent system prompts in `config/constants.py` include strict rules about requiring explicit permission
   - Examples of permitted and non-permitted storage are provided to guide agent behavior

2. **Code-Level Restrictions**:
   - The `has_explicit_permission` flag should be checked in memory storage functions
   - Only information with explicit user consent should be stored with permanent persistence

## Best Practices for Development

When extending the memory management system:

1. **Token Management**: 
   - Keep the token counting logic in sync with the AI model's actual token counting
   - Test summarization with large conversations to ensure stability

2. **Conversation Memory**:
   - Maintain backward compatibility for saved conversation files
   - Consider implementing conversation export/import features

3. **Permanent Memory**:
   - Add robust search capabilities as the memory grows
   - Consider implementing memory relationships and hierarchies

4. **UI Considerations**:
   - Keep memory tools visible only when relevant agent is selected
   - Provide clear feedback for memory operations
   - Consider adding batch operations for conversation management

5. **Import Path Management**:
   - Always be mindful of import path resolution when dealing with memory systems
   - Consider using explicit imports or direct module loading for critical components
   - Test memory integrations thoroughly when modifying path configuration 