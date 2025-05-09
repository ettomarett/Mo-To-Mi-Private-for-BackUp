# How LLMs Execute Actions: Understanding the MCP Framework and Permanent Memory

## The Fundamental Challenge

Language Models (LLMs) like GPT-4 and Deepseek have a fundamental limitation: they can only generate text. Unlike traditional software with direct system access, LLMs cannot directly:

- Write to a database
- Create or modify files
- Make API calls
- Execute code

Yet in our Mo-To-Mi framework, LLMs appear to perform these actions. When a user says "remember this preference," the system actually stores data in permanent memory. This document explains how this seemingly impossible capability works.

## The Bridge Between Text and Action

Every executive action in our system follows this flow:

1. **Text Generation**: The LLM generates text in a specific format
2. **Parsing**: The system parses this text to identify tool calls
3. **Execution**: A separate executor component performs the actual operation
4. **Response**: The results are fed back to the LLM as text

This approach creates the illusion that the LLM is performing actions, when it's actually just requesting them through a structured protocol.

## The MCP Framework

Our Modular Communication Protocol (MCP) framework standardizes this process through these components:

### 1. Tool Definitions

In `protocol.py`, we define the tools available to the LLM and their parameters:

```python
# Example of memory tool definition (simplified with comments)
{
    "name": "memory",  # Tool identifier
    "description": "Store and retrieve permanent memories. IMPORTANT: Always ask for explicit user confirmation BEFORE storing ANY information.",  # Human-readable description
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {  # What action to perform
                "type": "string",
                "enum": ["store", "retrieve", "search", "delete", "list"]
            },
            "has_explicit_permission": {  # Critical for privacy
                "type": "boolean",
                "description": "REQUIRED for storing user preferences or personal information. Always ask first, and only set this to true after user confirmation."
            }
            # Other parameters omitted for brevity...
        },
        "required": ["operation"]
    }
}
```

These definitions serve two purposes:
- They inform the LLM about available tools through the system prompt
- They provide a schema for validating tool calls

The tool description is critical - it gives the LLM clear instructions about when and how to use the tool. Notice how we explicitly tell the LLM to "Always ask for explicit user confirmation BEFORE storing ANY information" directly in the tool description.

### 2. Structured Output Format

The LLM is instructed to output tool calls in a specific format:

```
<mcp:tool>
name: memory
parameters: {
  "operation": "store",
  "content": "User prefers Dark Mode",
  "has_explicit_permission": true
}
</mcp:tool>
```

### 3. Parsing Mechanism

The parsing process extracts structured data from the LLM's text output:

```python
# Key parts of the tool call parsing process
def extract_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    # This regex pattern captures the tool name and parameters JSON
    tool_pattern = r"<mcp:tool>\s*name:\s*([^\n]+)\s*parameters:\s*({[^<]+})\s*</mcp:tool>"
    matches = re.findall(tool_pattern, response_text, re.DOTALL)
    
    tool_calls = []
    for match in matches:
        tool_name = match[0].strip()  # Extract tool name
        
        # Try to parse parameters as JSON
        try:
            parameters = json.loads(match[1].strip())
            # Add successfully parsed tool call to list
            tool_calls.append({"name": tool_name, "parameters": parameters})
        except json.JSONDecodeError:
            # Fallback for imperfect JSON (handling omitted for brevity)
            # ...
    
    return tool_calls  # Return list of structured tool calls
```

## Permission System for Memory Storage

One of the most important aspects of our framework is the permission system for storing user information. This ensures user privacy and data protection.

### How the Permission System Works

1. **Tool Description**: The LLM learns about the permission requirements directly from the tool description.

2. **System Prompt Reinforcement**: A concise reminder is included in the system prompt:
   ```
   MEMORY PROTOCOL: Always ask for explicit confirmation BEFORE storing any information permanently. 
   Only after receiving clear confirmation should you use the memory tool with has_explicit_permission=true.
   If you store without permission or with permission=false, the request will be rejected.
   ```

3. **Parameter Requirement**: The memory tool has a special `has_explicit_permission` parameter that must be set to `true` for storing personal information.

4. **Back-end Validation**: The `memory_bank.py` file checks content for personal information keywords and rejects storage attempts without permission.

### Complete Permission Flow Example

Let's walk through a complete example:

#### Step 1: User Asks to Store Information
User: "Please remember that I like chocolate ice cream."

#### Step 2: LLM Asks for Permission
LLM: "Would you like me to remember your preference for chocolate ice cream for future conversations?"

#### Step 3: User Confirms
User: "Yes, please remember that."

#### Step 4: LLM Makes Tool Call with Permission Flag
```
<mcp:tool>
name: memory
parameters: {
  "operation": "store",
  "key": "food_preference_ice_cream",
  "content": "User likes chocolate ice cream",
  "has_explicit_permission": true
}
</mcp:tool>
```

#### Step 5: Tool Executor Processes Request
The `execute_tool` function calls `memory_bank.store_memory()` with the parameters, including the permission flag.

#### Step 6: Memory Bank Stores Information
```python
# Inside memory_bank.py
def store_memory(self, content, key, tags=None, has_explicit_permission=False):
    # Check for personal information markers
    if not has_explicit_permission and (
        "prefer" in content.lower() or 
        "like" in content.lower() or 
        "my " in content.lower() or
        # other personal indicators...
    ):
        return "ERROR: Cannot store user preferences or personal information without explicit permission"
        
    # If permission is granted or not needed, proceed with storage
    # ... storage code ...
    return stored_key
```

#### Step 7: Success Response Returned
```json
{
  "success": true,
  "key": "food_preference_ice_cream",
  "message": "Memory stored successfully with key: food_preference_ice_cream"
}
```

#### Step 8: LLM Acknowledges Storage
LLM: "I've saved your preference for chocolate ice cream. I'll remember this for future conversations."

### What Happens When Permission Is Missing

If the LLM tries to store personal information without setting `has_explicit_permission: true`:

```
<mcp:tool>
name: memory
parameters: {
  "operation": "store",
  "key": "likes_boots",
  "content": "User mentioned they like boots"
  // has_explicit_permission is missing
}
</mcp:tool>
```

The memory bank will detect personal information keywords ("like") and return:

```json
{
  "success": false,
  "error": "ERROR: Cannot store user preferences or personal information without explicit permission",
  "status": "error"
}
```

The LLM will then see this error and respond appropriately by asking for permission first.

### Debugging Permission Issues

Our comprehensive logging system helps debug permission issues by capturing:

1. **Tool Parsing Logs**: Shows exactly how the LLM's text was parsed into tool calls
2. **Tool Execution Logs**: Records all tool operations including parameters and results

If a memory storage fails, the logs will show:
- Whether permission was requested
- If the permission parameter was properly set
- The exact error message from the memory bank

## Best Practices for Memory Permission

To ensure reliable permission handling:

1. **Clear Tool Descriptions**: Always include permission requirements directly in the tool definition
2. **Concise System Prompt**: Include a short reminder about the memory protocol
3. **Defensive Coding**: Always check for permission in the back-end
4. **Comprehensive Logging**: Log both parsing and execution for debugging

By embedding permission instructions at multiple levels (tool description, system prompt, and back-end validation), we ensure robust protection of user information.

## The Illusion of Agency

This multi-step process creates the illusion that the LLM is performing actions, when in reality:

1. The LLM is still just generating text
2. The structured format signals intent to the system
3. Separate code components perform the actual execution
4. Results are fed back as text

This architecture creates a powerful abstraction layer where:
- The LLM focuses on understanding user intent and generating appropriate tool calls
- The MCP framework handles the parsing and execution
- The execution components (like MemoryBank) implement the actual functionality

## Extending the Pattern

This same pattern can be extended to any executive function:
- File operations
- Database queries
- API calls
- Code execution

By standardizing the protocol and adding appropriate executors, we can give the illusion that the LLM is performing a wide range of actions, while maintaining a clear separation between understanding (LLM) and execution (system code).

## Security Considerations

This architecture introduces important security boundaries:

1. The LLM can only call tools explicitly defined in the protocol
2. Each tool has a specific parameter schema that constrains what can be requested
3. The executor can implement additional safeguards (like our permission system)
4. All actions are mediated by code, never directly executed by the LLM

These boundaries ensure that while the LLM appears to have agency, it's operating within a carefully controlled sandbox.

---

## Annexes

### Annex A: Complete Tool Definition

```python
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
}
```

### Annex B: Complete Parameter Parsing Logic

```python
# If parameters aren't valid JSON, try to extract them as key-value pairs
params_text = match[1].strip()
parameters = {}
for line in params_text.split("\n"):
    if ":" in line:
        key, value = line.split(":", 1)
        parameters[key.strip()] = value.strip()
tool_calls.append({"name": tool_name, "parameters": parameters})
```

This fallback handles cases where the LLM generates imperfect JSON, such as:

```
<mcp:tool>
name: memory
parameters: {
  operation: store
  content: User prefers Dark Mode
  has_explicit_permission: true
}
</mcp:tool>
```

### Annex C: Complete Agent Processing Flow

```python
async def process_with_tools(client, model_name, question, conversation, memory_bank):
    """Process a message with tool capabilities"""
    # Add user question to conversation
    conversation.add_user_message(question)
    
    # Get the full conversation
    messages = conversation.get_messages()
    
    # Get response from model
    response = await client.chat_completion(
        model=model_name,
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )
    
    # Extract the response content
    response_text = response.choices[0].message.content
    
    # Check for tool calls in the response
    tool_calls = extract_tool_calls(response_text)
    
    # If there are tool calls, process them and get a new response
    if tool_calls:
        updated_response = response_text
        
        # Process each tool call
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            parameters = tool_call["parameters"]
            
            # Execute the tool
            tool_result = execute_tool(tool_name, parameters, conversation, memory_bank)
            
            # Format the tool call and result for replacement
            tool_call_text = f"""<mcp:tool>
name: {tool_name}
parameters: {json.dumps(parameters, indent=2)}
</mcp:tool>"""
            
            tool_result_text = f"""<mcp:tool_result>
{json.dumps(tool_result, indent=2)}
</mcp:tool_result>"""
            
            # Replace the tool call with the tool call + result
            updated_response = updated_response.replace(
                tool_call_text, 
                tool_call_text + "\n\n" + tool_result_text
            )
        
        # Add the updated response to conversation
        conversation.add_assistant_message(updated_response)
        
        # Get another response from the model with the tool results
        messages = conversation.get_messages()
        final_response = await client.chat_completion(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        # Extract the final response content
        final_response_text = final_response.choices[0].message.content
        
        # Update conversation with final response
        conversation.replace_last_assistant_message(final_response_text)
        
        return final_response_text, conversation
    
    # If no tool calls, just add response to conversation and return
    conversation.add_assistant_message(response_text)
    return response_text, conversation
```

### Annex D: Multiple Tool Call Example

```python
# Multiple tool calls in a response
response_text = """
Let me check your memory and calculate something.

<mcp:tool>
name: memory
parameters: {
  "operation": "list"
}
</mcp:tool>

Now I'll calculate the result:

<mcp:tool>
name: calculator
parameters: {
  "expression": "2 * 3.14 * 5"
}
</mcp:tool>

Here are your results.
"""

# This will extract both tool calls
tool_calls = extract_tool_calls(response_text)
# Results in:
# [
#   {"name": "memory", "parameters": {"operation": "list"}},
#   {"name": "calculator", "parameters": {"expression": "2 * 3.14 * 5"}}
# ]
```

The system processes these tool calls sequentially, replacing each with its result before sending the augmented response back to the LLM for final processing. 