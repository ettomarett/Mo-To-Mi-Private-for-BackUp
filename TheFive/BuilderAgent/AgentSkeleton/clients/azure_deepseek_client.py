import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ChatRole
from azure.core.credentials import AzureKeyCredential

default_endpoint = "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com"
default_api_key = "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i"
default_model = "DeepSeek-R1"

class AsyncAzureDeepSeekClient:
    def __init__(
        self,
        endpoint: str = None,
        api_key: str = None,
        model: str = None,
    ):
        self.endpoint = endpoint or os.environ.get("AZURE_DEEPSEEK_ENDPOINT", default_endpoint)
        self.api_key = api_key or os.environ.get("AZURE_DEEPSEEK_API_KEY", default_api_key)
        self.model = model or os.environ.get("AZURE_DEEPSEEK_MODEL", default_model)
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        model: str = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a chat completion request with the Azure DeepSeek model.
        
        Args:
            messages: List of message dictionaries with role and content
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature
            tools: List of tool definitions
            tool_choice: Tool choice configuration
            model: Model name override
            stream: Whether to stream the response
            
        Returns:
            Response from the model
        """
        # Use provided model or default
        model_to_use = model or self.model
        
        # Convert message dictionaries to Azure SDK message objects
        azure_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                azure_messages.append(SystemMessage(content=content))
            elif role == "user":
                azure_messages.append(UserMessage(content=content))
            elif role == "assistant":
                # Handle tool calls in assistant messages (simplified)
                azure_messages.append(AssistantMessage(content=content))
            elif role == "tool" or role == "function":
                # For the moment, convert tool/function messages to user messages
                # since the Azure SDK message classes might not support these directly
                tool_message = f"Tool response: {content}"
                azure_messages.append(UserMessage(content=tool_message))
        
        try:
            # We need to run the synchronous client in a thread pool since we don't have an async client
            loop = asyncio.get_event_loop()
            if stream:
                # Run the synchronous call in a thread pool
                response_stream = await loop.run_in_executor(
                    None,
                    lambda: self.client.complete(
                        messages=azure_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        tools=tools,
                        tool_choice=tool_choice,
                        model=model_to_use,
                        stream=True
                    )
                )
                
                # Return a generator that will iterate through the stream in a non-blocking way
                return response_stream
            else:
                # Run the synchronous call in a thread pool
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.complete(
                        messages=azure_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        tools=tools,
                        tool_choice=tool_choice,
                        model=model_to_use
                    )
                )
                
                # Return the response in a format compatible with the existing MCP framework
                return response
        except Exception as e:
            print(f"Error in chat completion: {str(e)}")
            raise

    async def close(self):
        """Close the client session."""
        # Close the client if it has a close method
        if hasattr(self.client, 'close'):
            self.client.close()


def initialize_client(deployment_name=None, api_key=None, endpoint=None):
    """
    Initialize the AsyncAzureDeepSeekClient with the given parameters or environment variables.
    
    Args:
        deployment_name: Optional model deployment name
        api_key: Optional API key
        endpoint: Optional endpoint URL
        
    Returns:
        An instance of AsyncAzureDeepSeekClient
    """
    return AsyncAzureDeepSeekClient(
        endpoint=endpoint,
        api_key=api_key,
        model=deployment_name
    ) 