import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple

from .protocol import extract_tool_calls, create_default_system_prompt
from .tool_executor import execute_tool
from core.token_management import TokenManagedConversation

async def process_with_tools(client, model_name: str, question: str, conversation=None, 
                            memory_bank=None) -> Tuple[str, TokenManagedConversation]:
    """
    Process a question with access to tools, maintaining conversation history with token management
    
    Args:
        client: The LLM client to use for requests
        model_name: The model name to use
        question: The user's question or input
        conversation: Optional existing conversation to use
        memory_bank: Optional memory bank for persistent storage
        
    Returns:
        Tuple of (response_text, updated_conversation)
    """
    # Initialize conversation if not provided
    if conversation is None:
        conversation = TokenManagedConversation(
            max_tokens=100000,  # 100K token safe limit
            client=client,
            model_name=model_name
        )
        conversation.set_system_prompt(create_default_system_prompt())
    
    try:
        # Add user question
        conversation.add_message(content=question, role="user")
        
        # Check if we need to summarize older context to save tokens
        summarization_occurred = await conversation.maybe_summarize()
        
        # Check if we should warn about token usage
        token_status = conversation.get_token_status()
        should_warn = token_status.get("warning_issued", False)
        
        # Get the current system prompt from the conversation instead of creating a new one
        current_system_prompt = conversation.system_prompt
        
        # Only create a default system prompt if the current one is empty
        if not current_system_prompt:
            current_system_prompt = create_default_system_prompt()
            
        # Build system prompt with memories if applicable
        system_prompt = current_system_prompt
        if memory_bank:
            # Add recent memories to the system prompt
            memories = memory_bank.format_for_context(max_memories=3)
            system_prompt += f"\n\n{memories}"
        
        # If summarization occurred or close to token limit, add notice to system prompt
        if summarization_occurred:
            system_prompt += "\n\nNOTE: Some earlier conversation has been summarized to save space."
        
        if should_warn:
            system_prompt += f"\n\nWARNING: Conversation is approaching the token limit ({token_status['usage_percent']:.1f}% used). Consider summarizing, saving important information to memory, or starting a new conversation soon."
            
        # Update the conversation with the augmented system prompt
        conversation.set_system_prompt(system_prompt)
        
        # Initial request to the model with full conversation history
        messages = conversation.get_messages()
        response = await client.complete(
            messages=messages,
            max_tokens=2048,
            model=model_name
        )
        
        # Handle Azure AI Inference SDK response format
        response_text = response.choices[0].message.content
        tool_calls = extract_tool_calls(response_text)
        
        # If there are tool calls, execute them and send results back
        if tool_calls:
            # Process each tool call and collect results
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                params = tool_call["parameters"]
                
                result = execute_tool(tool_name, params, conversation, memory_bank)
                tool_results.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result
                })
            
            # Format tool results for the follow-up prompt
            tool_results_text = "\n".join([
                f"Tool: {r['tool']}\nParameters: {json.dumps(r['params'])}\nResult: {json.dumps(r['result'])}"
                for r in tool_results
            ])
            
            # Send follow-up request with tool results
            follow_up_prompt = f"""You previously requested to use the following tools:

{tool_results_text}

Please provide your final response based on these tool results."""

            # Add interim assistant message with tool requests
            conversation.add_message(content=response_text, role="assistant")
            
            # Add follow-up prompt as user message
            conversation.add_message(content=follow_up_prompt, role="user")
            
            # Get updated messages with the tool results
            updated_messages = conversation.get_messages()
            
            final_response = await client.complete(
                messages=updated_messages,
                max_tokens=2048,
                model=model_name
            )
            
            final_response_text = final_response.choices[0].message.content
            
            # Add final assistant response to history
            conversation.add_message(content=final_response_text, role="assistant")
            
            return final_response_text, conversation
        
        # If no tool calls, just return the original response
        conversation.add_message(content=response_text, role="assistant")
        return response_text, conversation
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Error during API call: {str(e)}")
        return error_msg, conversation 