import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
import sys
from pathlib import Path

# Add the TheFive directory to the Python path for importing the system prompt logger
parent_dir = Path(__file__).parent.parent.parent.parent  # Get to TheFive directory
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from system_prompt_logger import log_system_prompt_from_messages
from .protocol import extract_tool_calls, create_system_prompt_with_tools
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
        # Only set default system prompt for new conversations if none exists
        if not conversation.system_prompt:
            conversation.set_system_prompt(create_system_prompt_with_tools())
            print(f"DEBUG: New conversation created with default system prompt")
    else:
        print(f"DEBUG: Using existing conversation with system prompt: {conversation.system_prompt[:50]}...")
    
    try:
        # Add user question
        conversation.add_message(content=question, role="user")
        
        # Check if we need to summarize older context to save tokens
        summarization_occurred = await conversation.maybe_summarize()
        
        # Check if we should warn about token usage
        token_status = conversation.get_token_status()
        should_warn = token_status.get("warning_issued", False)
        
        # IMPORTANT: Keep the original system prompt instead of creating a new one
        current_system_prompt = conversation.system_prompt
        print(f"DEBUG: Original system prompt before augmentation: {current_system_prompt[:50]}...")
        
        # Only augment the system prompt with extra information, don't replace it
        augmentations = []
        
        # Add memory bank information if available - formatted to preserve agent identity
        if memory_bank:
            memories = memory_bank.format_for_context(max_memories=3)
            if memories:
                # Format memory as contextual information, not identity information
                memory_context = f"\n\n=== CONTEXTUAL MEMORY ===\nThe following is stored memory from previous conversations (this does not change your identity or role):\n{memories}\n=== END CONTEXTUAL MEMORY ==="
                augmentations.append(memory_context)
                print(f"DEBUG: Added contextual memory (preserving agent identity)")
        
        # Add notices if needed
        if summarization_occurred:
            augmentations.append("NOTE: Some earlier conversation has been summarized to save space.")
        
        if should_warn:
            augmentations.append(f"WARNING: Conversation is approaching the token limit ({token_status['usage_percent']:.1f}% used). Consider summarizing, saving important information to memory, or starting a new conversation soon.")
        
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
            print(f"DEBUG: Augmented system prompt: {augmented_prompt[:50]}...")
        
        # Initial request to the model with full conversation history
        messages = conversation.get_messages()
        
        # 🎯 LOG THE FINAL SYSTEM PROMPT BEING SENT TO LLM
        log_system_prompt_from_messages("OBSERVER", messages)
        
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