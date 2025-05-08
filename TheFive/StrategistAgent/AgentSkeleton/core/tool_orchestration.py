import inspect
import json
import asyncio
from typing import Dict, List, Any, Callable, Optional, Union, Tuple
import traceback
import sys
from abc import ABC, abstractmethod

class MCPTool(ABC):
    """Base class for MCP tools"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        Initialize an MCP tool
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for tool parameters
        """
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters
        
        Args:
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass

class ToolDefinition:
    """Definition of a tool that can be used by the LLM"""
    
    def __init__(self, name: str, description: str, function: Callable, 
                 required_params: List[str] = None, param_descriptions: Dict[str, str] = None):
        """
        Initialize a tool definition
        
        Args:
            name: Tool name
            description: Tool description
            function: Function to call when the tool is invoked
            required_params: List of required parameter names
            param_descriptions: Descriptions for parameters
        """
        self.name = name
        self.description = description
        self.function = function
        self.required_params = required_params or []
        self.param_descriptions = param_descriptions or {}
        
        # Extract parameter info from function signature if not provided
        if not self.required_params or not self.param_descriptions:
            self._extract_params_from_function()
    
    def _extract_params_from_function(self):
        """Extract parameter information from the function signature"""
        sig = inspect.signature(self.function)
        
        # Get required parameters (those without defaults)
        if not self.required_params:
            self.required_params = [
                name for name, param in sig.parameters.items()
                if param.default is inspect.Parameter.empty
                and name != 'self'  # Skip self for class methods
            ]
        
        # Get parameter descriptions from docstring if available
        if not self.param_descriptions and self.function.__doc__:
            # This is a simple parser, a more robust solution might be needed
            docstring = self.function.__doc__
            param_sections = docstring.split('Args:')
            if len(param_sections) > 1:
                param_text = param_sections[1].split('Returns:')[0]
                param_lines = param_text.strip().split('\n')
                
                for line in param_lines:
                    line = line.strip()
                    if ':' in line:
                        param_name, desc = line.split(':', 1)
                        param_name = param_name.strip()
                        self.param_descriptions[param_name] = desc.strip()
    
    def to_mcp_schema(self) -> Dict[str, Any]:
        """
        Convert tool definition to MCP tool schema format
        
        Returns:
            Dictionary with tool schema
        """
        parameters = {}
        required = []
        
        # Add parameters from signature
        sig = inspect.signature(self.function)
        for name, param in sig.parameters.items():
            if name == 'self':  # Skip self for class methods
                continue
                
            parameters[name] = {
                "type": "string"  # Default type
            }
            
            # Add description if available
            if name in self.param_descriptions:
                parameters[name]["description"] = self.param_descriptions[name]
                
            # Add to required list if needed
            if name in self.required_params:
                required.append(name)
        
        # Create the schema
        schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }
        
        return schema
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate if the provided parameters are valid for this tool
        
        Args:
            params: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required parameters
        for param in self.required_params:
            if param not in params:
                return False, f"Missing required parameter: {param}"
        
        # Check parameter types (simple validation)
        sig = inspect.signature(self.function)
        for name, value in params.items():
            if name in sig.parameters:
                param = sig.parameters[name]
                # Simple type checking could be implemented here
                pass
        
        return True, None


class ToolOrchestrator:
    """Orchestrate tool registration, validation, and execution"""
    
    def __init__(self):
        """Initialize tool orchestrator"""
        self.tools: Dict[str, ToolDefinition] = {}
        self.mcp_tools: Dict[str, MCPTool] = {}
    
    def register_tool(self, tool: Union[ToolDefinition, MCPTool]) -> None:
        """
        Register a tool with the orchestrator
        
        Args:
            tool: Tool definition or MCP tool to register
        """
        if isinstance(tool, MCPTool):
            self.mcp_tools[tool.name] = tool
        else:
            self.tools[tool.name] = tool
    
    def register_function_as_tool(self, function: Callable, 
                                 name: Optional[str] = None,
                                 description: Optional[str] = None,
                                 required_params: Optional[List[str]] = None,
                                 param_descriptions: Optional[Dict[str, str]] = None) -> None:
        """
        Register a function as a tool
        
        Args:
            function: Function to register
            name: Tool name (defaults to function name)
            description: Tool description (defaults to function docstring)
            required_params: List of required parameters
            param_descriptions: Descriptions of parameters
        """
        # Use function name if not provided
        tool_name = name or function.__name__
        
        # Use function docstring if description not provided
        tool_description = description
        if not tool_description and function.__doc__:
            tool_description = function.__doc__.split('\n')[0].strip()
        elif not tool_description:
            tool_description = f"Executes the {tool_name} function"
        
        # Create and register the tool
        tool = ToolDefinition(
            name=tool_name,
            description=tool_description,
            function=function,
            required_params=required_params,
            param_descriptions=param_descriptions
        )
        
        self.register_tool(tool)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all registered tools
        
        Returns:
            List of tool schemas in MCP format
        """
        return [tool.to_mcp_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a tool with the given parameters
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool
            
        Returns:
            Result of tool execution
            
        Raises:
            ValueError: If tool not found or parameters invalid
            Exception: If tool execution fails
        """
        # Check if it's an MCP tool
        if tool_name in self.mcp_tools:
            return self.mcp_tools[tool_name].execute(params)
            
        # Check if tool exists in regular tools
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Get the tool
        tool = self.tools[tool_name]
        
        # Validate parameters
        is_valid, error = tool.validate_params(params)
        if not is_valid:
            raise ValueError(f"Invalid parameters for tool {tool_name}: {error}")
        
        # Execute the tool
        try:
            function = tool.function
            
            # Check if it's an async function
            if inspect.iscoroutinefunction(function):
                return await function(**params)
            else:
                # Run synchronous functions in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: function(**params))
        except Exception as e:
            # Get detailed exception info
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            error_details = ''.join(tb_lines)
            
            # Raise a more informative error
            raise Exception(f"Error executing tool {tool_name}: {str(e)}\n{error_details}")
    
    def parse_tool_calls(self, model_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse tool calls from a model response
        
        Args:
            model_response: The raw response from the LLM
            
        Returns:
            List of parsed tool calls with name and arguments
        """
        tool_calls = []
        
        # Extract tool calls based on the response format
        # OpenAI format
        if 'choices' in model_response and model_response['choices']:
            choice = model_response['choices'][0]
            if 'message' in choice and 'tool_calls' in choice['message']:
                for tool_call in choice['message']['tool_calls']:
                    if 'function' in tool_call:
                        function_call = tool_call['function']
                        tool_name = function_call.get('name', '')
                        
                        # Parse arguments
                        arguments = {}
                        args_str = function_call.get('arguments', '{}')
                        try:
                            arguments = json.loads(args_str)
                        except json.JSONDecodeError:
                            print(f"Error parsing arguments: {args_str}")
                        
                        tool_calls.append({
                            'name': tool_name,
                            'arguments': arguments
                        })
        
        # Azure OpenAI format (similar to OpenAI)
        # Or AzureChatCompletion format
        elif 'choices' in model_response and model_response['choices']:
            choice = model_response['choices'][0]
            if 'message' in choice and 'function_call' in choice['message']:
                function_call = choice['message']['function_call']
                tool_name = function_call.get('name', '')
                
                # Parse arguments
                arguments = {}
                args_str = function_call.get('arguments', '{}')
                try:
                    arguments = json.loads(args_str)
                except json.JSONDecodeError:
                    print(f"Error parsing arguments: {args_str}")
                
                tool_calls.append({
                    'name': tool_name,
                    'arguments': arguments
                })
        
        return tool_calls 