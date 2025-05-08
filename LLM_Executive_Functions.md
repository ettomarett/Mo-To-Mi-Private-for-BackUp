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
    "description": "Store and retrieve permanent memories",  # Human-readable description
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {  # What action to perform
                "type": "string",
                "enum": ["store", "retrieve", "search", "delete", "list"]
            },
            "has_explicit_permission": {  # Critical for privacy
                "type": "boolean",
                "description": "REQUIRED for storing user preferences or personal information"
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

See Annex A for the complete tool definition.

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

Let's explore how this parsing mechanism works in practice:

#### Step 1: Regular Expression Pattern Recognition

The regex pattern captures two groups:
- The tool name after "name:"
- The parameters JSON object after "parameters:"

#### Step 2: Parsing Parameters

The system attempts to parse the parameters as JSON, with a fallback mechanism for when LLMs produce imperfect JSON (see Annex B for details).

#### Step 3: Integration with Agent Processing

The extracted tool calls are processed through these high-level steps:

```python
# Simplified flow of processing tool calls
# 1. Extract tool calls from LLM response
tool_calls = extract_tool_calls(response_text)

# 2. For each tool call:
for tool_call in tool_calls:
    # 3. Execute the tool and get result
    tool_result = execute_tool(tool_call["name"], tool_call["parameters"])
    
    # 4. Append result to original response
    updated_response = append_tool_result(response_text, tool_call, tool_result)

# 5. Send augmented response back to LLM for final processing
final_response = get_llm_response(updated_response)
```

The complete processing flow and implementation details are provided in Annex C.

### 4. Tool Executor

The `execute_tool()` function in `tool_executor.py` handles the actual execution:

```python
# Simplified memory tool execution
if tool_name == "memory" and memory_bank is not None:
    operation = params.get("operation")
    
    if operation == "store":
        # Extract key parameters
        content = params.get("content", "")
        has_explicit_permission = params.get("has_explicit_permission", False)
        
        # Call the actual storage method
        stored_key = memory_bank.store_memory(
            content, 
            params.get("key"), 
            params.get("tags", []), 
            has_explicit_permission
        )
        
        # Check for permission errors
        if stored_key.startswith("ERROR:"):
            return {"success": False, "error": stored_key}
        
        # Return success response
        return {"success": True, "key": stored_key}
```

## Permanent Memory: A Complete Example

Let's trace the entire process of storing permanent memory:

### 1. User Request

The user tells the assistant: "Please remember that I prefer Dark Mode"

### 2. LLM Message Processing

The LLM:
1. Recognizes this as a request to store a preference
2. Follows system instructions to ask for explicit permission
3. Generates: "Would you like me to remember your preference for Dark Mode?"

### 3. User Confirmation

The user responds: "Yes, please save that"

### 4. LLM Tool Call Generation

The LLM generates a tool call in the required format (see the structured output example above).

### 5. Tool Call Parsing

The system extracts and structures the tool call (see the parsing mechanism section).

### 6. Tool Execution

The system executes the memory storage operation using the extracted parameters.

### 7. Memory Bank Storage

The `MemoryBank.store_memory()` method:
1. Checks for explicit permission (required for preferences)
2. Generates a key (e.g., "user_prefers_dark")
3. Creates a file in the `permanent_memories/` directory
4. Updates the memory index with metadata
5. Returns the key

### 8. Response Back to LLM

The system sends the result back to the LLM:

```json
{
  "success": true,
  "key": "user_prefers_dark",
  "message": "Memory stored successfully with key: user_prefers_dark"
}
```

### 9. LLM Final Response

The LLM:
1. Processes the tool result
2. Generates a human-friendly response: "I've saved your preference for Dark Mode. I'll remember this for future conversations."

## Permission Enforcement Example

Our memory system has specific safeguards for personal information:

### Attempt Without Permission

If the LLM tries to store personal information without permission, the `store_memory()` function will detect preference keywords and return:

```
ERROR: Cannot store user preferences or personal information without explicit permission
```

The LLM then receives this error and can adjust its response accordingly.

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
    "description": "Store and retrieve permanent memories across conversations",
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
                "description": "REQUIRED for storing user preferences or personal information. Must ONLY be set to true if the user has EXPLICITLY granted permission to store this specific information."
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