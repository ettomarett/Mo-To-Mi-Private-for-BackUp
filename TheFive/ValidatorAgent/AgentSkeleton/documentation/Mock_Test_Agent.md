# Mock Test Agent

## Overview

The Mock Test Agent is a simulation environment for testing and developing the MCP (Modular Communication Protocol) framework without requiring actual LLM API credentials or internet connectivity. It provides a controlled, predictable way to verify functionality, develop new features, and demonstrate the system's capabilities.

## What is a "Mock" Agent?

In software development, a "mock" is a simulated object or system that mimics the behavior of a real system in a controlled way. Our Mock Test Agent:

1. **Simulates AI responses** with pre-programmed text instead of calling real LLM APIs
2. **Executes tools locally** rather than using actual external services
3. **Provides consistent, predictable output** for testing purposes
4. **Functions without API keys** or internet connectivity

## Benefits of Using a Mock Agent

1. **Development Without Credentials**
   - Team members can develop and test without needing actual API keys
   - No API costs incurred during development and testing

2. **Controlled Testing Environment**
   - Reproducible responses for testing code paths
   - No variability from real AI models that might change responses

3. **Demonstration Capabilities**
   - Showcase functionality without depending on external services
   - Presentations and demos work reliably offline

4. **Faster Development Cycle**
   - No network latency when testing functionality
   - Immediate response for quicker iteration

## Implementation Details

The Mock Test Agent consists of several key components:

1. **MockLLMClient**
   - Simulates an LLM service with pre-defined responses
   - Recognizes specific query patterns to provide appropriate responses
   - Creates responses in the same format as real LLM services

2. **Tool Simulation**
   - Implements local versions of tools (calculator, weather, memory)
   - Returns predictable results for given inputs
   - Follows the same interface as real tool implementations

3. **MCP Protocol Support**
   - Generates proper tool calls in MCP format
   - Parses and executes tool calls using the same protocol as real agents
   - Maintains full compatibility with the MCP framework

## Code Example: Mock LLM Client

```python
class MockLLMClient:
    """A mock LLM client for demonstration purposes"""
    
    def __init__(self):
        self.responses = {
            "greeting": "Hello! I'm a mock AI assistant...",
            "calculation": "The square root of 144 is 12.",
            # More pre-defined responses...
        }
        
    async def complete(self, messages, max_tokens=2048, model=None):
        """Simulate LLM completion"""
        last_message = messages[-1]["content"].lower()
        
        # Pattern matching to select appropriate response
        if "hello" in last_message:
            content = self.responses["greeting"]
        elif "calculate" in last_message:
            content = self.responses["calculation"]
        # More pattern matching...
        
        # For tool demonstration, generate MCP-compatible tool calls
        if "calculate" in last_message and "square root" in last_message:
            content = """I'll calculate that for you.
            
<mcp:tool>
name: calculator
parameters: {
  "expression": "sqrt(144)"
}
</mcp:tool>

Let me compute the square root of 144."""
        
        # Return in the same format as a real LLM response
        return MockResponse(content)
```

## Usage

### Running the Mock Agent

```bash
python -m agents.mock_mcp_agent
```

### Example Interactions

```
You: Hello
Assistant: Hello! I'm a mock AI assistant. I can pretend to help with calculations, 
weather, and other tasks.

You: Calculate the square root of 144
Assistant: I'll calculate that for you.

<mcp:tool>
name: calculator
parameters: {
  "expression": "sqrt(144)"
}
</mcp:tool>

Let me compute the square root of 144.

I executed the tools you requested:

Tool: calculator
Result: {
  "result": 12
}

The square root of 144 is 12.
```

## Integrating with Development Workflow

The Mock Test Agent can be integrated into your development workflow in several ways:

1. **Development Phase**: Use during initial development to build against a stable interface.

2. **Testing**: Incorporate into automated tests for predictable results.

3. **CI/CD Pipelines**: Run tests without requiring actual API credentials in your CI/CD environment.

4. **Demonstrations**: Use for offline demos or presentations.

5. **Documentation**: Help users understand system behavior with predictable examples.

## Extending the Mock Agent

You can extend the Mock Agent by:

1. **Adding New Canned Responses**: Expand the `responses` dictionary for more query types.

2. **Implementing Tool Simulations**: Add more mock tool implementations.

3. **Enhancing Pattern Recognition**: Improve the logic for selecting appropriate responses.

4. **Creating Scenario-Based Tests**: Develop specific scenarios with predetermined flows.

## When to Use Real vs. Mock Agent

| Use Mock Agent When... | Use Real Agent When... |
|------------------------|------------------------|
| You don't have API credentials | You need genuine AI responses |
| You're testing basic functionality | You're evaluating response quality |
| You need predictable responses | You need real-world variability |
| You're working offline | Online connectivity is available |
| You're in the early development stages | You're finalizing features |

## Conclusion

The Mock Test Agent provides a valuable development tool that lets you build, test, and demonstrate your MCP-based application without depending on external services or API credentials. By providing a controlled environment with predictable responses, it accelerates development and allows for more robust testing. 