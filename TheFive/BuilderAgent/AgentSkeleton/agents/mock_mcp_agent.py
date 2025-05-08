import os
import asyncio
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our core components
from core.memory_bank import MemoryBank
from core.token_management import TokenManagedConversation

# Load environment variables
load_dotenv()

# Mock client for testing without API keys
class MockLLMClient:
    """A mock LLM client for demonstration purposes"""
    
    def __init__(self):
        self.responses = {
            "greeting": "Hello! I'm a mock AI assistant. I can pretend to help with calculations, weather, and other tasks.",
            "calculation": "The square root of 144 is 12.",
            "weather": "The weather in [location] is simulated to be sunny and 72°F.",
            "memory_store": "I've stored that in my memory.",
            "memory_retrieve": "I remember you told me that your favorite color is blue.",
            "default": "I'm a mock assistant, so I can't actually process that request. But in a real implementation, I would use the appropriate tools to help you."
        }
        
    async def complete(self, messages, max_tokens=2048, model=None):
        """Simulate LLM completion"""
        last_message = messages[-1]["content"].lower() if messages and "content" in messages[-1] else ""
        
        # Determine which canned response to use
        if "hello" in last_message or "hi " in last_message:
            content = self.responses["greeting"]
        elif "square root" in last_message or "calculate" in last_message:
            content = self.responses["calculation"]
        elif "weather" in last_message:
            location = "the location you mentioned" 
            if "in " in last_message:
                parts = last_message.split("in ")
                if len(parts) > 1:
                    location = parts[1].split("?")[0].strip()
            content = self.responses["weather"].replace("[location]", location)
        elif "remember" in last_message and "that" in last_message:
            content = self.responses["memory_store"]
        elif "favorite color" in last_message:
            content = self.responses["memory_retrieve"]
        else:
            content = self.responses["default"]
            
        # Add a tool call for demonstration
        if "calculate" in last_message and "square root" in last_message:
            content = """I'll calculate that for you.

<mcp:tool>
name: calculator
parameters: {
  "expression": "sqrt(144)"
}
</mcp:tool>

Let me compute the square root of 144."""
        
        # Create a mock response object with the structure expected by our processor
        class MockResponse:
            def __init__(self, content):
                self.choices = [
                    type('Choice', (), {
                        'message': type('Message', (), {
                            'content': content
                        })
                    })
                ]
                
        return MockResponse(content)
        
    def close(self):
        """Mock closing the connection"""
        pass

def initialize_mock_client():
    """Initialize a mock client for testing"""
    return MockLLMClient()

class MockMCPAgent:
    """A mock agent for demonstration without real API credentials"""
    
    def __init__(self, name: str = "Mock MCP Agent"):
        """Initialize the agent"""
        self.name = name
        
        # Initialize mock client
        self.client = initialize_mock_client()
        self.model_name = "mock-model"
        
        # Initialize conversation with token management
        self.conversation = TokenManagedConversation(
            max_tokens=100000,
            client=self.client,
            model_name=self.model_name
        )
        
        # Initialize memory bank
        self.memory_bank = MemoryBank("permanent_memories")
        
        # Set up simple tool handling
        self.tools = {
            "calculator": self.mock_calculator,
            "weather": self.mock_weather,
            "memory": self.mock_memory,
        }
    
    def mock_calculator(self, params):
        """Mock calculator implementation"""
        expression = params.get("expression", "")
        if "sqrt" in expression and "144" in expression:
            return {"result": 12}
        return {"result": "Calculated result would appear here"}
    
    def mock_weather(self, params):
        """Mock weather implementation"""
        location = params.get("location", "unknown location")
        return {
            "location": location,
            "temperature": "72°F",
            "conditions": "Sunny",
            "humidity": "50%",
            "note": "This is simulated weather data"
        }
    
    def mock_memory(self, params):
        """Mock memory operations"""
        operation = params.get("operation", "")
        if operation == "store":
            return {"success": True, "message": "Memory stored successfully"}
        elif operation == "retrieve":
            return {"content": "This would be retrieved memory content"}
        return {"message": "Memory operation simulated"}
        
    def extract_tool_calls(self, text):
        """Extract tool calls from response text"""
        import re
        tool_pattern = r"<mcp:tool>\s*name:\s*([^\n]+)\s*parameters:\s*({[^<]+})\s*</mcp:tool>"
        matches = re.findall(tool_pattern, text, re.DOTALL)
        
        tool_calls = []
        for match in matches:
            tool_name = match[0].strip()
            try:
                parameters = json.loads(match[1].strip())
                tool_calls.append({"name": tool_name, "parameters": parameters})
            except json.JSONDecodeError:
                # Simplified parameter parsing
                parameters = {"error": "Could not parse parameters"}
                tool_calls.append({"name": tool_name, "parameters": parameters})
                
        return tool_calls
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        if message.lower() == 'clear':
            self.conversation.clear()
            return "Conversation history cleared."
            
        if message.lower() == 'status':
            # Status command
            status = self.conversation.get_token_status()
            status_text = "\nToken Usage Statistics (simulated):\n"
            status_text += f"Current tokens: {status['current_tokens']:,}\n"
            status_text += f"Maximum tokens: {status['max_tokens']:,}\n"
            status_text += f"Usage: {status['usage_percent']:.1f}%\n"
            return status_text
        
        # Add user message to conversation
        self.conversation.add_message(content=message, role="user")
        
        # Get LLM response
        response = await self.client.complete(
            messages=self.conversation.get_messages(),
            max_tokens=2048,
            model=self.model_name
        )
        
        response_text = response.choices[0].message.content
        
        # Check for tool calls
        tool_calls = self.extract_tool_calls(response_text)
        if tool_calls:
            # Handle tool calls
            results = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                params = tool_call["parameters"]
                
                if tool_name in self.tools:
                    result = self.tools[tool_name](params)
                    results.append(f"Tool: {tool_name}\nResult: {json.dumps(result, indent=2)}")
                else:
                    results.append(f"Tool: {tool_name}\nError: Tool not found")
            
            # Generate follow-up response with tool results
            followup = f"I executed the tools you requested:\n\n" + "\n\n".join(results)
            self.conversation.add_message(content=response_text, role="assistant")
            self.conversation.add_message(content=followup, role="user")
            
            final_response = await self.client.complete(
                messages=self.conversation.get_messages(),
                max_tokens=2048,
                model=self.model_name
            )
            
            final_text = final_response.choices[0].message.content
            self.conversation.add_message(content=final_text, role="assistant")
            
            return f"{response_text}\n\n{followup}\n\n{final_text}"
        
        # No tool calls, just return the response
        self.conversation.add_message(content=response_text, role="assistant")
        return response_text
    
    def close(self):
        """Clean up resources"""
        self.client.close()

async def main():
    """Run the mock agent in interactive mode"""
    print("Mock MCP Agent - Demonstration Mode")
    print("-----------------------------------------------------")
    print("Type 'exit' to quit")
    print("Type 'clear' to clear conversation history")
    print("Type 'status' to see token usage statistics")
    print()
    print("This is a MOCK agent that simulates responses without using real APIs.")
    print("Try these sample queries:")
    print("- Calculate the square root of 144")
    print("- What's the weather like in Boston?") 
    print("- Remember that my favorite color is blue")
    print("- What's my favorite color?")
    print("-----------------------------------------------------")
    
    # Initialize agent
    agent = MockMCPAgent()
    
    try:
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            print("Assistant: ", end="", flush=True)
            response = await agent.process_message(user_input)
            print(response)
    finally:
        agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 