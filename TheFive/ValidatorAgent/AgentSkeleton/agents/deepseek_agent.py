import os
import asyncio
import json
from dotenv import load_dotenv
from core.token_management import TokenManagedConversation
from core.memory_bank import MemoryBank
from clients.azure_deepseek_client import initialize_client, AsyncAzureDeepSeekClient

# Load environment variables
load_dotenv()

# Define the Azure DeepSeek settings
AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com")
AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i")
AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1-gADK")

async def process_with_tools(client, model_name, question, conversation, memory_bank=None):
    """
    Process a user question with the MCP agent and execute any tools.
    
    Args:
        client: The LLM client to use for chat completion
        model_name: The model name/deployment to use
        question: The user's question to process
        conversation: The token-managed conversation object
        memory_bank: Optional memory bank for permanent storage
        
    Returns:
        Tuple of (final_response, updated_conversation)
    """
    from mcp_framework import process_with_tools as mcp_process
    
    # Use the MCP framework to process the message with tools
    return await mcp_process(
        client=client,
        model_name=model_name,
        question=question,
        conversation=conversation,
        memory_bank=memory_bank
    )

async def main():
    """
    Main entry point for the DeepSeek MCP agent.
    """
    print("\nDeepSeek MCP Agent with Token Management and Tool Support")
    print("=" * 60)
    print("Type 'exit' to quit. Type 'token status' to see token information.\n")
    
    # Initialize the Azure DeepSeek client
    client = initialize_client(
        deployment_name=AZURE_DEEPSEEK_MODEL_NAME,
        api_key=AZURE_DEEPSEEK_API_KEY,
        endpoint=AZURE_DEEPSEEK_ENDPOINT
    )
    
    # Initialize the token-managed conversation
    conversation = TokenManagedConversation(
        max_tokens=100000,  # Adjust based on model's context window
        client=client,
        model_name=AZURE_DEEPSEEK_MODEL_NAME
    )
    
    # Initialize the memory bank for permanent storage
    memory_bank = MemoryBank("permanent_memories")
    
    # Set the system prompt for the conversation
    conversation.set_system_prompt(
        "You are a helpful AI assistant with an Azure DeepSeek backend. "
        "You have access to tools and can use them when needed. "
        "You maintain a conversation history and can access permanent memory storage."
    )
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Handle exit command
        if user_input.lower() in ("exit", "quit", "bye"):
            print("\nGoodbye! Thank you for using the DeepSeek MCP Agent.")
            break
        
        # Handle token status command
        if user_input.lower() == "token status":
            token_info = conversation.get_token_status()
            print("\nToken Status:")
            print(f"Current usage: {token_info['current_tokens']} tokens")
            print(f"Maximum allowed: {token_info['max_tokens']} tokens")
            print(f"Percentage used: {token_info['percent_used']:.1f}%")
            print(f"Summarized messages: {token_info['num_summarized']}")
            continue
        
        # Process the user's question with the MCP framework
        try:
            response, conversation = await process_with_tools(
                client=client,
                model_name=AZURE_DEEPSEEK_MODEL_NAME,
                question=user_input,
                conversation=conversation,
                memory_bank=memory_bank
            )
            
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("An error occurred while processing your request. Please try again.\n")
    
    # Clean up resources
    await client.close()

if __name__ == "__main__":
    asyncio.run(main()) 