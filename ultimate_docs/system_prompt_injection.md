# System Prompt Architecture in Mo-To-Mi Framework

## The Issue: System Prompt Override

We encountered an issue where custom system prompts set for the Observer agent in TheFiveinterFace wouldn't persist during agent interactions. The system prompt would start correctly but would get replaced during processing.

### Where System Prompts Are Set

System prompts are set in multiple places across the codebase:

1. **TheFiveinterFace/config/constants.py**: Contains default system prompts for all agents
   ```python
   OBSERVER_SYSTEM_PROMPT = """You are the Observer Agent (The Analyzer) in the Mo-To-Mi framework.
   Your role is to analyze Spring Boot monolithic applications and identify potential microservice boundaries.
   ...
   ```

2. **TheFiveinterFace/agents/chat.py**: Initializes conversations with the appropriate system prompt
   ```python
   def create_conversation_for_agent(agent_type, client):
       conversation = TokenManagedConversation(
           max_tokens=100000,
           client=client,
           model_name=constants.AZURE_DEEPSEEK_MODEL_NAME
       )
       
       # Set the system prompt based on agent type
       if agent_type == "architect":
           conversation.set_system_prompt(constants.ARCHITECT_SYSTEM_PROMPT)
       elif agent_type == "observer":
           # Use the system prompt from Observer's protocol if available
           if observer_system_prompt:
               conversation.set_system_prompt(observer_system_prompt())
           else:
               conversation.set_system_prompt(constants.OBSERVER_SYSTEM_PROMPT)
       # ... other agents ...
   ```

3. **TheFive/ObserverAgent/AgentSkeleton/mcp_framework/protocol.py**: Defines the default system prompt for the Observer agent
   ```python
   def create_default_system_prompt() -> str:
       """Create the default system prompt with tool descriptions"""
       # Return the default system prompt for the Observer agent
       return """You are the Observer Agent..."""
   ```

4. **TheFive/ObserverAgent/AgentSkeleton/mcp_framework/processor.py**: Processes messages and handles system prompts during interactions

## The TokenManagedConversation Class

The TokenManagedConversation class is the core component that manages conversation state and system prompts in the Mo-To-Mi framework. It's defined in `AgentSkeleton.core.token_management` and imported by all agent modules.

### Key Features and Functionality

1. **System Prompt Management**: 
   ```python
   # In TokenManagedConversation class
   def set_system_prompt(self, prompt: str):
       self.system_prompt = prompt
       # Update token count for the new prompt
   ```

   This method stores the system prompt in the conversation object, making it available for future LLM interactions.

2. **Token Management**:
   ```python
   def get_token_status(self):
       return {
           "total_tokens": self.total_tokens,
           "max_tokens": self.max_tokens,
           "usage_percent": (self.total_tokens / self.max_tokens) * 100,
           "warning_issued": self.warning_issued
       }
   ```

   The class tracks token usage to prevent exceeding LLM context limits, which is especially important when system prompts are large.

3. **Conversation History**:
   ```python
   def add_message(self, content: str, role: str = "user"):
       # Add message to the conversation history
       self.messages.append({"role": role, "content": content})
       # Update token count
   ```

   Manages message history with automatic token counting.

4. **Message Formatting**:
   ```python
   def get_messages(self):
       # Format conversation including system prompt for API submission
       if self.system_prompt:
           formatted_messages = [{"role": "system", "content": self.system_prompt}]
       else:
           formatted_messages = []
       
       # Add the rest of the messages
       formatted_messages.extend(self.messages)
       return formatted_messages
   ```

   This method returns conversation messages with the system prompt as the first message, formatted for the LLM API.

5. **Automatic Summarization**:
   ```python
   async def maybe_summarize(self):
       # Check if token count is approaching limit
       # If so, summarize older messages to save space
   ```

   Automatically summarizes older messages when approaching token limits, preserving recent context while reducing token usage.

### Relationship to System Prompt Override Issue

The system prompt override issue occurred because:

1. `TheFiveinterFace/agents/chat.py` correctly set the system prompt in the `TokenManagedConversation` instance
2. Later, `processor.py` created a new system prompt with `create_default_system_prompt()` and called `conversation.set_system_prompt(system_prompt)`, replacing the original prompt

Our fix ensures that the `TokenManagedConversation`'s system prompt is preserved throughout the process flow, only being augmented when necessary rather than replaced.

### Token Management Impact on System Prompts

System prompts contribute to token usage, so the `TokenManagedConversation` class:

1. Counts tokens used by the system prompt
2. Factors this into the overall token usage calculations
3. May trigger summarization if the combined tokens (system prompt + conversation) approach limits

This token management functionality is why augmenting existing prompts (rather than replacing them) is the optimal approach - it preserves the custom instructions while allowing for contextual additions when needed.

## The Bug: System Prompt Override

The issue occurred in the processor.py file of each agent. There were two points where system prompts were being overridden:

1. **Initial Override**: When creating a new conversation with no existing system prompt
   ```python
   # Initialize conversation if not provided
   if conversation is None:
       conversation = TokenManagedConversation(...)
       # Set default system prompt for new conversations
       conversation.set_system_prompt(create_default_system_prompt())
   ```

2. **Processing Override**: More critically, during every message processing, the system prompt was completely replaced
   ```python
   # Build system prompt with memories if applicable
   system_prompt = create_default_system_prompt()  # <-- This always overwrote the custom prompt!
   if memory_bank:
       # Add recent memories to the system prompt
       memories = memory_bank.format_for_context(max_memories=3)
       system_prompt += f"\n\n{memories}"
   
   # Update the conversation with the system prompt
   conversation.set_system_prompt(system_prompt)
   ```

This second override was the primary issue. Every time a message was processed, the system would discard whatever custom system prompt was set and replace it with the default one from protocol.py.

## The Solution: Preserving System Prompts

We implemented two fixes:

1. **Conditional Initial Setting**: Only set the default system prompt for new conversations if one doesn't already exist
   ```python
   if conversation is None:
       conversation = TokenManagedConversation(...)
       # Only set default system prompt for new conversations if none exists
       if not conversation.system_prompt:
           conversation.set_system_prompt(create_default_system_prompt())
   ```

2. **Augmenting Instead of Replacing**: Preserve the original system prompt and only augment it
   ```python
   # IMPORTANT: Keep the original system prompt instead of creating a new one
   current_system_prompt = conversation.system_prompt
   
   # Only augment the system prompt with extra information, don't replace it
   augmentations = []
   
   # Add memory bank information if available
   if memory_bank:
       memories = memory_bank.format_for_context(max_memories=3)
       if memories:
           augmentations.append(memories)
   
   # Add notices if needed
   if summarization_occurred:
       augmentations.append("NOTE: Some earlier conversation has been summarized to save space.")
   
   # Only update system prompt if we have augmentations to add
   if augmentations:
       augmented_prompt = current_system_prompt
       
       # Add each augmentation with proper spacing
       for aug in augmentations:
           if not augmented_prompt.endswith("\n\n"):
               augmented_prompt += "\n\n"
           augmented_prompt += aug
       
       # Update the conversation with the augmented system prompt
       conversation.set_system_prompt(augmented_prompt)
   ```

These changes were applied to all agent processor.py files:
- TheFive/ObserverAgent/AgentSkeleton/mcp_framework/processor.py
- TheFive/ArchitectAgent/AgentSkeleton/mcp_framework/processor.py
- TheFive/StrategistAgent/AgentSkeleton/mcp_framework/processor.py
- TheFive/BuilderAgent/AgentSkeleton/mcp_framework/processor.py
- TheFive/ValidatorAgent/AgentSkeleton/mcp_framework/processor.py

## System Prompt Flow in Mo-To-Mi

Here's how the system prompt flows through the application now:

1. **Initial Setting**: In TheFiveinterFace/agents/chat.py, the appropriate system prompt is set based on agent type.
   - For Observer agent, it tries to load the prompt from protocol.py using the observer_system_prompt function
   - If that fails, it falls back to constants.OBSERVER_SYSTEM_PROMPT

2. **Conversation Creation**: When a conversation is created, the system prompt is set in TokenManagedConversation

3. **Message Processing**: When the user interacts with an agent:
   - TheFiveinterFace/ui/migration_workflow.py calls session.update_conversation(agent_type, updated_conversation)
   - TheFiveinterFace/agents/chat.py calls chat_with_agent() which uses the agent's processor.py
   - processor.py preserves the existing system prompt while adding any necessary augmentations

## The Role of Augmented Prompts

The "augmented system prompt" is a feature that adds contextual information to the base system prompt without replacing it. Augmentations include:

1. **Memory Bank Information**: If the agent needs to reference items from its memory
   ```python
   if memory_bank:
       memories = memory_bank.format_for_context(max_memories=3)
       if memories:
           augmentations.append(memories)
   ```

2. **Summarization Notice**: If conversation history was summarized to save tokens
   ```python
   if summarization_occurred:
       augmentations.append("NOTE: Some earlier conversation has been summarized to save space.")
   ```

3. **Token Limit Warning**: If approaching the maximum token limit
   ```python
   if should_warn:
       augmentations.append(f"WARNING: Conversation is approaching the token limit ({token_status['usage_percent']:.1f}% used)...")
   ```

These augmentations are added only when needed and are appended to the existing system prompt rather than replacing it. This ensures that the core instruction set remains intact while providing contextual information for the current interaction.

## System Prompt in TheFiveinterFace vs StreamlitInterface

The bug manifested differently in different interfaces:

1. **StreamlitInterface/app.py**: Worked correctly because it only used the agent's processor.py once without reloading conversations

2. **TheFiveinterFace**: Had issues because it manages persistent conversations that get processed multiple times:
   - TheFiveinterFace/utils/session.py stores conversations
   - TheFiveinterFace/agents/agent_loader.py loads agent modules
   - Sessions get saved/loaded via TheFiveinterFace/utils/conversation_manager.py

The fix ensures consistency across both interfaces.

## Debugging the System

To identify and fix this issue, we added strategic debug prints in processor.py:

```python
# Debug existing conversation
print(f"DEBUG: Using existing conversation with system prompt: {conversation.system_prompt[:50]}...")

# Debug before augmentation
print(f"DEBUG: Original system prompt before augmentation: {current_system_prompt[:50]}...")

# Debug after augmentation
print(f"DEBUG: Augmented system prompt: {augmented_prompt[:50]}...")
```

These prints provide visibility into the system prompt lifecycle and can be left in the code for future debugging or wrapped in conditional logic for production environments.

## Conclusion

The system prompt architecture now properly preserves custom prompts throughout the agent lifecycle. Custom prompts set in TheFiveinterFace will persist through processing in each agent's processor.py, with augmentations added only when necessary to provide additional context.

The debugging system implemented alongside this fix provides visibility into the system prompt flow, making similar issues easier to detect and resolve in the future.

## How to Modify System Prompts

There are several ways to modify the system prompts for each agent, depending on your specific requirements:

### 1. Modifying Default System Prompts

To change the default system prompts that are used when no custom prompt is available:

1. **In TheFiveinterFace/config/constants.py**:
   - Edit the corresponding system prompt constant for the target agent
   ```python
   # For example, to modify the Observer agent's default prompt:
   OBSERVER_SYSTEM_PROMPT = """
   Your new system prompt here...
   """
   ```

2. **In each agent's protocol.py file**:
   - Modify the `create_default_system_prompt()` function 
   - Located at `TheFive/{AgentName}Agent/AgentSkeleton/mcp_framework/protocol.py`
   ```python
   def create_default_system_prompt() -> str:
       return """
       Your new system prompt here...
       """
   ```
   - This is particularly useful when you want to modify tool descriptions and capabilities

### 2. Setting Custom Prompts Programmatically

To set a custom system prompt programmatically:

1. **When creating a new conversation**:
   ```python
   conversation = TokenManagedConversation(...)
   conversation.set_system_prompt("Your custom system prompt")
   ```

2. **In TheFiveinterFace/agents/chat.py**:
   - Modify the `create_conversation_for_agent` function to use your custom prompt
   ```python
   if agent_type == "observer":
       conversation.set_system_prompt("Your custom Observer prompt")
   ```

### 3. Using the Interface Settings (Future Enhancement)

While not currently implemented, a common enhancement would be to:
- Add a settings screen in TheFiveinterFace
- Allow users to edit and save custom system prompts through the UI
- Store these in a configuration file or database
- Load custom prompts from these settings when initializing conversations

### 4. Override Priority

When multiple system prompt definitions exist, they are prioritized in this order:

1. Custom prompt set directly on the TokenManagedConversation instance
2. Agent-specific prompt from protocol.py's `create_default_system_prompt()`
3. Default prompt from TheFiveinterFace/config/constants.py
4. Generic fallback prompt ("You are a helpful AI assistant.")

## System Prompt Augmentation Details

### When and How Augmentations Happen

System prompt augmentations occur in the `process_with_tools` function in each agent's processor.py file:

```python
# In TheFive/{AgentName}Agent/AgentSkeleton/mcp_framework/processor.py
async def process_with_tools(client, model_name: str, question: str, conversation=None, 
                            memory_bank=None):
    # ...
    
    # IMPORTANT: Keep the original system prompt instead of creating a new one
    current_system_prompt = conversation.system_prompt
    
    # Only augment the system prompt with extra information, don't replace it
    augmentations = []
    
    # Add augmentations based on conditions...
    
    # Only update system prompt if we have augmentations to add
    if augmentations:
        augmented_prompt = current_system_prompt
        
        # Add each augmentation with proper spacing
        for aug in augmentations:
            if not augmented_prompt.endswith("\n\n"):
                augmented_prompt += "\n\n"
            augmented_prompt += aug
        
        # Update the conversation with the augmented system prompt
        conversation.set_system_prompt(augmented_prompt)
```

### Augmentation Types and Triggers

1. **Memory Bank Augmentation**:
   - **Trigger**: When the agent has access to a memory bank with retrievable memories
   - **Purpose**: Provides the agent with context from previous interactions
   - **Code**:
     ```python
     if memory_bank:
         memories = memory_bank.format_for_context(max_memories=3)
         if memories:
             augmentations.append(memories)
     ```
   - **Format**: Typically includes a "From Memory:" section with retrieved relevant memories

2. **Summarization Notice**:
   - **Trigger**: When older messages have been automatically summarized to save tokens
   - **Purpose**: Informs the agent that some context has been condensed
   - **Code**:
     ```python
     if summarization_occurred:
         augmentations.append("NOTE: Some earlier conversation has been summarized to save space.")
     ```

3. **Token Limit Warning**:
   - **Trigger**: When approaching the token limit (typically 70-80% usage)
   - **Purpose**: Encourages the agent to be concise or save information to memory
   - **Code**:
     ```python
     if should_warn:
         augmentations.append(f"WARNING: Conversation is approaching the token limit ({token_status['usage_percent']:.1f}% used). Consider summarizing, saving important information to memory, or starting a new conversation soon.")
     ```

### Customizing Augmentation Behavior

To modify how system prompt augmentations work:

1. **Adding New Augmentation Types**:
   ```python
   # Add to the augmentations list in processor.py
   if some_condition:
       augmentations.append("Your new augmentation text here")
   ```

2. **Modifying Existing Augmentations**:
   - Change the text or conditions for existing augmentations
   - For example, to change the token warning threshold:
   ```python
   # In processor.py
   should_warn = token_status.get("usage_percent", 0) > 85  # Change from default 70% to 85%
   ```

3. **Disabling Specific Augmentations**:
   - Comment out or remove specific augmentation blocks
   - Or add conditional flags:
   ```python
   # Example: Disable memory augmentation
   ENABLE_MEMORY_AUGMENTATION = False
   
   if memory_bank and ENABLE_MEMORY_AUGMENTATION:
       # Memory augmentation code...
   ```

### Preserving Augmentations

It's important to note that augmentations are temporary and are recalculated with each message processing. If you want to permanently modify the system prompt with information that looks like an augmentation, you should modify the base system prompt instead of relying on the augmentation mechanism.

## Resolving the System Prompt Override Issue

This centralized approach helps avoid the system prompt override issue by:

1. Eliminating duplicate prompt definitions across the codebase
2. Providing a clear ownership model for system prompts
3. Making it easier to track and debug prompt modifications

The same augmentation mechanism is preserved, but now it builds upon a centralized base prompt rather than potentially conflicting prompts from different sources.

## MCP Tools Integration Fix

### The MCP Tools Issue

We discovered an issue where the MCP tools weren't being properly included in agent system prompts:

1. **Root Cause**: In TheFiveinterFace/agents/chat.py, we were only loading the basic agent prompt from the centralized file, without the MCP tool descriptions.

2. **Problem Impact**: Agents in TheFiveinterFace were responding without knowledge of their available tools, limiting their functionality.

### The Solution: Protocol-Based System Prompts

We fixed this by changing how system prompts are loaded in TheFiveinterFace:

```python
# New approach in TheFiveinterFace/agents/chat.py
protocol_module = load_agent_protocol(agent_type)
    
if protocol_module and hasattr(protocol_module, "create_system_prompt_with_tools"):
    # Use the agent's protocol.py create_system_prompt_with_tools which includes tools
    system_prompt = protocol_module.create_system_prompt_with_tools()
else:
    # Fallback to centralized system prompt without tools
    from Agents_System_Prompts import get_system_prompt
    system_prompt = get_system_prompt(agent_type)
```

This ensures that:

1. We try to load the complete system prompt (base prompt + MCP tools) from each agent's protocol.py file
2. Only if that fails do we fall back to the basic system prompt without tools
3. Agents have consistent access to their tools in both TheFiveinterFace and individual StreamlitInterface apps

### Improved Function Naming

To make the code more self-documenting, we renamed the function that creates the system prompt with tools:

1. **Old Name**: `create_default_system_prompt()`
2. **New Name**: `create_system_prompt_with_tools()`

The new name clearly indicates that this function:
- Takes the base system prompt from the centralized file
- Combines it with the agent-specific tool descriptions
- Returns a complete system prompt with both components

For backward compatibility, we added an alias:

```python
# Add an alias for backward compatibility
create_default_system_prompt = create_system_prompt_with_tools
```

This ensures that any existing code referencing the old function name will continue to work.

## Complete System Prompt Flow

The updated system prompt flow now works as follows:

1. **Definition**: Core agent identities and responsibilities are defined in `Agents_System_Prompts.py`

2. **Enrichment**: Each agent's protocol.py enhances its base prompt with MCP tools using `create_system_prompt_with_tools()`

3. **Loading**: TheFiveinterFace loads the complete system prompt directly from each agent's protocol module

4. **Augmentation**: During conversations, processor.py may add temporary augmentations (memory context, etc.)

This clean separation ensures that:
- Agent identities are centrally managed
- Tool definitions remain with their respective agents
- The complete system prompt (identity + tools) is consistently used everywhere

## Documentation: Centralized System Prompts

> For complete documentation, see `TheFive/SYSTEM_PROMPTS.md`

### Summary of Centralized System Prompt Architecture

The Mo-To-Mi framework now implements a centralized system prompt architecture with the following key features:

1. **Single Source of Truth**: All agent system prompts are defined in `TheFive/Agents_System_Prompts.py`

2. **Key Benefits**:
   - Easier maintenance and updates
   - Consistent prompt format across agents
   - Simplified debugging of system prompt issues
   - Elimination of duplicated prompt definitions

3. **Architecture Components**:
   - **Definition**: System prompts defined as constants in the centralized file
   - **Distribution**: Other parts of the codebase import prompts from this file
   - **Backward Compatibility**: Constants file still exposes the prompts for existing code

4. **Simple Prompt Modification**:
   - Edit the corresponding prompt in `Agents_System_Prompts.py`
   - Changes automatically propagate throughout the system

5. **Import Patterns**:
   - From TheFiveinterFace/agents/chat.py: `from Agents_System_Prompts import get_system_prompt`
   - From agent protocol files: `from Agents_System_Prompts import OBSERVER_SYSTEM_PROMPT`
   - For backward compatibility: Import constants into TheFiveinterFace/config/constants.py

6. **Augmentation Preservation**:
   - Centralized prompts work with the existing augmentation system
   - Base prompts aren't replaced, only augmented when needed
   - Augmentations remain temporary and recalculated with each message

This centralized approach, combined with the proper handling of tool appendices and augmentations described earlier, creates a robust system for managing system prompts throughout the Mo-To-Mi framework. 