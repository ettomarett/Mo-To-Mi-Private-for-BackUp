# Custom MCP (Modular Communication Protocol)

## 1. Introduction

The Modular Communication Protocol (MCP) is a standardized protocol for enabling AI models to invoke tools, process their outputs, and return coherent responses. Developed by ETTALBI OMAR in April 2025, this protocol offers a simple, regex-parsable syntax that maintains readability while enabling complex tool interactions.

Key advantages of MCP include:

- **Simplicity**: Easy to parse with regex patterns
- **Readability**: Human-readable format for easier debugging
- **Modularity**: Tools can be developed and tested independently
- **Flexibility**: Works with any LLM that can follow text-based instructions
- **Two-phase execution**: Clear separation between tool invocation and response formulation

## 2. Protocol Specification

### 2.1 Tool Invocation Format

MCP uses a standardized XML-like syntax for tool invocation:

```
<mcp:tool>
name: tool_name
parameters: {
  "param1": "value1",
  "param2": "value2"
}
</mcp:tool>
```

Key components:
- **Opening tag**: `<mcp:tool>`
- **Tool name**: Simple text identifier
- **Parameters**: Valid JSON object with tool parameters
- **Closing tag**: `</mcp:tool>`

### 2.2 Tool Definition Format

Tools are defined using JSON Schema:

```json
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
```

### 2.3 Pattern Matching

Tool invocations are extracted using a regex pattern:

```python
tool_pattern = r"<mcp:tool>\s*name:\s*([^\n]+)\s*parameters:\s*({[^<]+})\s*</mcp:tool>"
```

This pattern captures:
1. The tool name (first capture group)
2. The parameter JSON (second capture group)

## 3. Implementation

### 3.1 Key Components

The MCP implementation consists of three core components:

1. **Protocol Definition**: Tool schemas, extraction patterns
2. **Tool Executor**: Functions that implement tool logic
3. **MCP Processor**: Workflow management for handling tools

### 3.2 Workflow

The MCP workflow follows a two-phase execution model:

1. **Phase 1 - Tool Determination**:
   - Send user query and conversation history to the model
   - Model decides if a tool is needed
   - If needed, model formats a tool call using MCP syntax

2. **Phase 2 - Tool Execution and Response**:
   - Extract tool name and parameters 
   - Execute the requested tool
   - Send tool result back to the model
   - Model formulates a final response incorporating the tool output

### 3.3 Code Implementation

Core processing function:

```python
async def process_with_tools(user_input, conversation, client, memory_bank):
    # Phase 1: Model decides if tool is needed
    conversation.add_message("user", user_input)
    formatted_messages = conversation.get_messages()
    response = await client.complete(
        messages=formatted_messages,
        tools=TOOLS,
        temperature=0.7
    )
    
    content = response.choices[0].message.content or ""
    tool_calls = extract_tool_calls(content)
    
    # Phase 2: Execute tool and get final response
    if tool_calls:
        for tool_call in tool_calls:
            tool_result = execute_tool(
                tool_call["name"], 
                tool_call["parameters"],
                conversation,
                memory_bank
            )
            conversation.add_message(
                "system",
                f"Tool '{tool_call['name']}' returned: {tool_result}"
            )
        
        # Call model again with tool results
        formatted_messages = conversation.get_messages()
        final_response = await client.complete(
            messages=formatted_messages,
            tools=TOOLS,
            temperature=0.7
        )
        content = final_response.choices[0].message.content or ""
    
    conversation.add_message("assistant", content)
    return content
```

Tool extraction function:

```python
def extract_tool_calls(content):
    tool_calls = []
    matches = re.finditer(tool_pattern, content, re.DOTALL)
    
    for match in matches:
        try:
            tool_name = match.group(1).strip()
            parameters_str = match.group(2).strip()
            parameters = json.loads(parameters_str)
            tool_calls.append({
                "name": tool_name,
                "parameters": parameters
            })
        except json.JSONDecodeError:
            print(f"Failed to parse parameters: {parameters_str}")
    
    return tool_calls
```

## 4. Building Tools for MCP

### 4.1 Tool Structure

Each MCP tool consists of:

1. **Definition**: JSON Schema in protocol.py
2. **Implementation**: Execution function in tool_executor.py
3. **Registration**: Entry in the TOOLS list

### 4.2 Example: Calculator Tool

#### Definition:

```python
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
```

#### Implementation:

```python
def execute_calculator(params, conversation=None, memory_bank=None):
    expression = params.get("expression", "")
    try:
        # Use safer eval with limited namespace
        result = simple_eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
```

#### Registration:

```python
def execute_tool(tool_name, params, conversation=None, memory_bank=None):
    if tool_name == "calculator":
        return execute_calculator(params, conversation, memory_bank)
    # Other tools...
    return {"error": f"Unknown tool: {tool_name}"}
```

## 5. Detailed Examples

### 5.1 Basic Calculator

**User Input:**
```
Calculate 25 * 48 + 120 / 4
```

**Phase 1 - Model Response:**
```
I'll calculate that for you.
<mcp:tool>
name: calculator
parameters: {"expression": "25 * 48 + 120 / 4"}
</mcp:tool>
```

**Tool Execution:**
```
Tool 'calculator' returned: {"result": 1230.0}
```

**Phase 2 - Final Response:**
```
The result of 25 * 48 + 120 / 4 is 1,230.

First I calculated:
25 * 48 = 1,200
120 / 4 = 30
1,200 + 30 = 1,230
```

### 5.2 Weather Tool

**User Input:**
```
Do I need an umbrella today in Seattle?
```

**Phase 1 - Model Response:**
```
Let me check the weather for you.
<mcp:tool>
name: weather
parameters: {"location": "Seattle", "units": "imperial"}
</mcp:tool>
```

**Tool Execution:**
```
Tool 'weather' returned: {"temperature": 52, "condition": "rainy", "precipitation_chance": 80}
```

**Phase 2 - Final Response:**
```
Yes, you should definitely bring an umbrella today in Seattle. The current weather is rainy with a temperature of 52°F and an 80% chance of precipitation.
```

### 5.3 Memory Storage and Retrieval

**User Input:**
```
Remember that my daughter's birthday is June 15th
```

**Phase 1 - Model Response:**
```
I'll store that information for you.
<mcp:tool>
name: memory
parameters: {"operation": "store", "content": "User's daughter's birthday is June 15th", "tags": ["important_dates", "family"]}
</mcp:tool>
```

**Tool Execution:**
```
Tool 'memory' returned: {"status": "success", "memory_id": "mem_1234567890"}
```

**Phase 2 - Final Response:**
```
I've saved that your daughter's birthday is June 15th. I'll remember this for future conversations.
```

**Later Conversation - User Input:**
```
When is my daughter's birthday?
```

**Phase 1 - Model Response:**
```
Let me check my memory.
<mcp:tool>
name: memory
parameters: {"operation": "search", "query": "daughter birthday"}
</mcp:tool>
```

**Tool Execution:**
```
Tool 'memory' returned: {"results": [{"content": "User's daughter's birthday is June 15th", "score": 0.95}]}
```

**Phase 2 - Final Response:**
```
Your daughter's birthday is June 15th.
```

## 6. Advanced MCP Features

### 6.1 Chained Tool Calls

MCP supports sequential tool calls in a single response:

```
I need to gather some information.
<mcp:tool>
name: weather
parameters: {"location": "Chicago", "units": "imperial"}
</mcp:tool>

Now I'll check the time there.
<mcp:tool>
name: time
parameters: {"timezone": "America/Chicago"}
</mcp:tool>
```

### 6.2 Conditional Tool Calls

Models can make decisions about whether to call tools:

```python
if weather_data["temperature"] < 32:
    # Call another tool for cold weather recommendations
    execute_tool("recommendations", {"weather": "cold"})
```

### 6.3 Tool Error Handling

MCP includes error handling for tool failures:

```python
try:
    result = execute_tool(tool_name, parameters)
    if "error" in result:
        # Handle error case
        error_message = f"Tool execution failed: {result['error']}"
        conversation.add_message("system", error_message)
except Exception as e:
    # Handle unexpected exceptions
    error_message = f"Unexpected error executing tool: {str(e)}"
    conversation.add_message("system", error_message)
```

## 7. System Prompt Design

Effective MCP use requires proper system prompt design:

```
You are an AI assistant that can use tools to help answer questions.

When you need to use a tool, format your response like this:
<mcp:tool>
name: tool_name
parameters: {
  "param1": "value1",
  "param2": "value2"
}
</mcp:tool>

Always make sure the parameters match what the tool expects and are in valid JSON format.

Available tools:
- calculator: Performs mathematical calculations.
  Parameters: {"expression": "math expression to evaluate"}
- weather: Gets weather information for a location.
  Parameters: {"location": "city name", "units": "metric or imperial"}
- memory: Stores and retrieves information.
  Parameters: {"operation": "store, retrieve, or search", "content": "content to store", "query": "search query"}
```

## 8. Designing New Tools

When designing new tools for the MCP system, follow these principles:

1. **Clear Purpose**: Each tool should have a single, well-defined purpose
2. **Appropriate Parameters**: Include only necessary parameters
3. **Robust Error Handling**: Anticipate and handle potential issues
4. **Comprehensive Documentation**: Document parameters and return values
5. **Minimal Side Effects**: Avoid changing system state unless necessary

### Example: Creating a Translation Tool

#### 1. Define the tool schema:

```python
{
    "name": "translate",
    "description": "Translates text from one language to another",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to translate"
            },
            "source_language": {
                "type": "string",
                "description": "The source language (optional, will auto-detect if not provided)"
            },
            "target_language": {
                "type": "string",
                "description": "The target language to translate into"
            }
        },
        "required": ["text", "target_language"]
    }
}
```

#### 2. Implement the tool function:

```python
def execute_translate(params, conversation=None, memory_bank=None):
    text = params.get("text", "")
    source_language = params.get("source_language", "auto")
    target_language = params.get("target_language", "")
    
    if not text or not target_language:
        return {"error": "Missing required parameters"}
    
    try:
        # Implementation with your preferred translation service
        translated_text = translation_service.translate(
            text=text,
            source=source_language,
            target=target_language
        )
        
        return {
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language
        }
    except Exception as e:
        return {"error": f"Translation failed: {str(e)}"}
```

#### 3. Add to the tool execution switch:

```python
def execute_tool(tool_name, params, conversation=None, memory_bank=None):
    if tool_name == "translate":
        return execute_translate(params, conversation, memory_bank)
    # Other tools...
```

## 9. MCP vs. Other Tool Protocols

### 9.1 Advantages of MCP

Compared to other function calling methods like OpenAI's JSON-mode or Anthropic's tool use:

1. **Simplicity**: Simple regex parsing without complex JSON schema validation
2. **Model Compatibility**: Works with any LLM that can follow text-based instructions
3. **Readability**: Easier to debug and understand tool calls
4. **Lightweight**: Minimal dependencies compared to full frameworks
5. **Extensibility**: Easy to modify for specific requirements

### 9.2 When to Use MCP

MCP is particularly well-suited for:

- Applications requiring custom tool implementations
- Working with models that don't natively support function calling
- Educational contexts where protocol clarity is important
- Systems where both humans and AI might need to interpret tool calls
- Environments where minimal dependencies are preferred

## 10. Best Practices

### 10.1 Tool Design

- Keep tools simple and focused on a single capability
- Use clear, descriptive parameter names
- Document expected input and output formats
- Include examples in documentation
- Handle edge cases and errors gracefully

### 10.2 Prompt Engineering

- Include clear instructions on MCP syntax
- Provide examples of correct tool usage
- Be explicit about available tools and parameters
- Include error handling instructions

### 10.3 Implementation

- Keep tool execution code isolated and testable
- Implement comprehensive error handling
- Log tool calls and results for debugging
- Implement timeouts for long-running tools
- Add unit tests for each tool

## 11. Troubleshooting

### 11.1 Common Issues

#### Invalid JSON in tool parameters

**Problem**: Model outputs malformed JSON in parameters section

**Solution**:
- Improve prompt examples
- Add JSON validation with helpful error messages
- Consider simplifying complex parameter structures

#### Model ignores tool format

**Problem**: Model doesn't use the correct MCP syntax

**Solution**:
- Add more examples to system prompt
- Emphasize format requirements 
- Try few-shot examples with correct usage

#### Tool execution errors

**Problem**: Tool functions raise exceptions

**Solution**:
- Wrap execution in try/except blocks
- Return informative error messages
- Log detailed error information for debugging

## 12. Conclusion

The Modular Communication Protocol (MCP) offers a lightweight, flexible, and readable approach to enabling tool use in AI assistant applications. By standardizing the interaction between models and tools, MCP creates a more modular and maintainable architecture that can easily adapt to new requirements and capabilities.

Whether you're building a simple calculator or complex multi-tool agent, MCP provides the infrastructure needed to create robust, capable AI assistants that can safely and effectively use tools to enhance their capabilities. 

---

*Created by ETTALBI OMAR in April 2025* 