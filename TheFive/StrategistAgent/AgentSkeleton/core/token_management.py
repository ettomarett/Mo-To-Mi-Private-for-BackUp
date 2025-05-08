import re
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
import tiktoken
import json

# Approximate token count based on GPT tokenization patterns
def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Utility function to estimate tokens for a text string
    
    Args:
        text: Text to estimate tokens for
        model: Model name for token counting
        
    Returns:
        Estimated token count
    """
    counter = TokenCounter(model)
    return counter.count_text_tokens(text)

def estimate_message_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    """
    Utility function to estimate tokens for a list of messages
    
    Args:
        messages: Messages to estimate tokens for
        model: Model name for token counting
        
    Returns:
        Estimated token count
    """
    counter = TokenCounter(model)
    return counter.count_messages_tokens(messages)

class TokenCounter:
    """
    Utility for counting tokens in text and messages using tiktoken
    """
    
    # Default models and their token limits
    MODEL_LIMITS = {
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "o3-mini": 16384,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
    }
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the token counter
        
        Args:
            model_name: The name of the model to use for token counting
        """
        self.model_name = model_name
        self.encoding = self._get_encoding()
        self.token_limit = self._get_token_limit()
    
    def _get_encoding(self):
        """Get the appropriate encoding for the model"""
        try:
            if "gpt-4" in self.model_name or "gpt-3.5" in self.model_name or "o3" in self.model_name:
                return tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base for other models
                return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            # Fallback to cl100k_base if model-specific encoding is not available
            print(f"Warning: Using fallback encoding. Error: {str(e)}")
            return tiktoken.get_encoding("cl100k_base")
    
    def _get_token_limit(self) -> int:
        """Get the token limit for the current model"""
        return self.MODEL_LIMITS.get(self.model_name, 4096)
    
    def count_text_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        tokens = self.encoding.encode(text)
        return len(tokens)
    
    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """
        Count the number of tokens in a message
        
        Args:
            message: Message dict with role and content
            
        Returns:
            Number of tokens
        """
        # Baseline tokens for message format
        num_tokens = 4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n

        for key, value in message.items():
            if key in ["role", "content", "name"] and value:
                num_tokens += self.count_text_tokens(value)
                if key == "name":  # If there's a name, the role is omitted
                    num_tokens -= 1  # Role is always required for the count, but adjusted here
        
        return num_tokens
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count the number of tokens in a list of messages
        
        Args:
            messages: List of message dicts
            
        Returns:
            Total number of tokens
        """
        total_tokens = 0
        
        # Add tokens for each message
        for message in messages:
            total_tokens += self.count_message_tokens(message)
        
        # Add tokens for the model response format, varies by model
        # Using a standard value as approximation for chat models
        total_tokens += 3  # <im_start>assistant\n
        
        return total_tokens

class TokenManager:
    """
    Manages token usage and truncation for conversations
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", max_tokens: Optional[int] = None,
                response_token_buffer: int = 1000, system_prompt_tokens: int = 0,
                warning_threshold: float = 0.8, summarize_threshold: float = 0.9):
        """
        Initialize the token manager
        
        Args:
            model_name: Name of the model
            max_tokens: Maximum tokens allowed (overrides model default)
            response_token_buffer: Buffer for model response
            system_prompt_tokens: Tokens to reserve for system prompt
            warning_threshold: Threshold percentage (0.0-1.0) to issue warning
            summarize_threshold: Threshold percentage (0.0-1.0) to trigger summarization
        """
        self.token_counter = TokenCounter(model_name)
        self.max_tokens = max_tokens or self.token_counter.token_limit
        self.response_token_buffer = response_token_buffer
        self.system_prompt_tokens = system_prompt_tokens
        self.warning_threshold = warning_threshold
        self.summarize_threshold = summarize_threshold
        self.warning_issued = False
        self.summarization_performed = False
        self.current_tokens = 0
        
        # Calculate usable token limit
        self.usable_token_limit = self.max_tokens - self.response_token_buffer
    
    def fit_messages_to_context(self, messages: List[Dict[str, str]],
                                preserve_system_messages: bool = True,
                                preserve_recent_messages: int = 4) -> List[Dict[str, str]]:
        """
        Fit messages to the context window, trimming as needed
        
        Args:
            messages: List of messages to fit to context
            preserve_system_messages: Whether to always include system messages
            preserve_recent_messages: Minimum number of recent messages to keep
            
        Returns:
            Trimmed list of messages that fits within token limits
        """
        if not messages:
            return []
        
        # Count tokens for all messages
        all_tokens = self.token_counter.count_messages_tokens(messages)
        
        # If we're under the limit, return all messages
        if all_tokens <= self.usable_token_limit:
            return messages
        
        # Split messages by type
        system_messages = []
        regular_messages = []
        
        for msg in messages:
            if msg["role"] == "system" and preserve_system_messages:
                system_messages.append(msg)
            else:
                regular_messages.append(msg)
        
        # Keep recent messages
        recent_messages = regular_messages[-preserve_recent_messages:] if preserve_recent_messages > 0 else []
        older_messages = regular_messages[:-preserve_recent_messages] if preserve_recent_messages > 0 else regular_messages
        
        # Calculate tokens for system and recent messages
        fixed_messages = system_messages + recent_messages
        fixed_tokens = self.token_counter.count_messages_tokens(fixed_messages)
        
        # If fixed messages exceed limit, we need to truncate even these
        if fixed_tokens >= self.usable_token_limit:
            # Prioritize system messages and very recent messages
            # This is a last resort and tries to keep as much context as possible
            result = system_messages + recent_messages[-2:] if recent_messages else system_messages
            
            # Truncate content of messages if still needed
            truncated = self._truncate_message_contents(result, self.usable_token_limit)
            
            return truncated
        
        # Space available for older messages
        available_tokens = self.usable_token_limit - fixed_tokens
        
        # Add as many older messages as possible, starting from most recent
        included_older_messages = []
        
        for msg in reversed(older_messages):
            msg_tokens = self.token_counter.count_message_tokens(msg)
            
            if msg_tokens <= available_tokens:
                included_older_messages.insert(0, msg)
                available_tokens -= msg_tokens
            else:
                # Message is too large, try truncating its content
                if available_tokens > 100:  # Only if reasonable space available
                    truncated_msg = self._truncate_message_content(msg, available_tokens)
                    included_older_messages.insert(0, truncated_msg)
                break
        
        # Combine system messages, included older messages, and recent messages
        result = system_messages + included_older_messages + recent_messages
        
        return result
    
    def _truncate_message_contents(self, messages: List[Dict[str, str]], 
                                 max_tokens: int) -> List[Dict[str, str]]:
        """
        Truncate content of messages to fit within token limit
        
        Args:
            messages: List of messages to truncate
            max_tokens: Maximum number of tokens allowed
            
        Returns:
            Truncated list of messages
        """
        if not messages:
            return []
            
        result = []
        remaining_tokens = max_tokens
        
        # Prioritize more recent messages
        for msg in reversed(messages):
            msg_tokens = self.token_counter.count_message_tokens(msg)
            
            if msg_tokens <= remaining_tokens:
                # Can include whole message
                result.insert(0, msg)
                remaining_tokens -= msg_tokens
            else:
                # Need to truncate this message
                truncated_msg = self._truncate_message_content(msg, remaining_tokens)
                result.insert(0, truncated_msg)
                break  # Stop including more messages once truncation happens
                
        return result
    
    def _truncate_message_content(self, message: Dict[str, str], 
                                max_tokens: int) -> Dict[str, str]:
        """
        Truncate a single message's content to fit within max_tokens
        
        Args:
            message: Message to truncate
            max_tokens: Maximum tokens for the entire message
            
        Returns:
            Truncated message
        """
        result = message.copy()
        content = result.get("content", "")
        
        # Calculate non-content tokens (role, format)
        msg_without_content = result.copy()
        msg_without_content["content"] = ""
        non_content_tokens = self.token_counter.count_message_tokens(msg_without_content)
        
        # Calculate available tokens for content
        content_token_limit = max_tokens - non_content_tokens
        
        if content_token_limit <= 0:
            # Cannot fit content, set to minimum
            result["content"] = "[Content truncated due to length]"
            return result
        
        # Count current content tokens
        content_tokens = self.token_counter.count_text_tokens(content)
        
        if content_tokens <= content_token_limit:
            # Already fits, return as is
            return result
        
        # Needs truncation
        encoded = self.token_counter.encoding.encode(content)
        truncated_encoded = encoded[:content_token_limit-10]  # Leave room for truncation notice
        
        # Decode back to text
        truncated_content = self.token_counter.encoding.decode(truncated_encoded)
        
        # Add truncation notice
        truncated_content += " [... truncated]"
        
        result["content"] = truncated_content
        return result

    # Add methods needed by TokenManagedConversation
    def add_tokens(self, count: int) -> None:
        """Add tokens to the current count"""
        self.current_tokens += count
        
        # Check if we should issue a warning
        if not self.warning_issued and self.get_usage_percent() >= self.warning_threshold:
            self.warning_issued = True
    
    def reset(self) -> None:
        """Reset token count and flags"""
        self.current_tokens = 0
        self.warning_issued = False
        self.summarization_performed = False
    
    def reset_warning(self) -> None:
        """Reset the warning flag"""
        self.warning_issued = False
    
    def get_usage_percent(self) -> float:
        """Get current token usage as a percentage"""
        return self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0
    
    def should_summarize(self) -> bool:
        """Check if summarization should be performed"""
        return (not self.summarization_performed and 
                self.get_usage_percent() >= self.summarize_threshold)
    
    def get_status(self) -> Dict[str, Any]:
        """Get token usage status"""
        usage_percent = self.get_usage_percent() * 100
        return {
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "warning_threshold": self.warning_threshold * 100,
            "summarize_threshold": self.summarize_threshold * 100,
            "warning_issued": self.warning_issued,
            "summarization_performed": self.summarization_performed
        }

class Message:
    """Class to represent a message with token counting"""
    
    def __init__(self, content: str, role: str, token_count: Optional[int] = None):
        """
        Initialize a message
        
        Args:
            content: Message text
            role: Message role (user, assistant, system)
            token_count: Pre-calculated token count (if None, will be estimated)
        """
        self.content = content
        self.role = role
        self.token_count = token_count if token_count is not None else estimate_tokens(content)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dict format for API calls"""
        return {
            "role": self.role,
            "content": self.content
        }

class TokenManagedConversation:
    """Conversation manager with token tracking and summarization"""
    
    def __init__(self, max_tokens=100000, warning_threshold=0.8, 
                 summarize_threshold=0.9, client=None, model_name=None):
        """
        Initialize a token-managed conversation
        
        Args:
            max_tokens: Maximum token capacity
            warning_threshold: Percentage at which to issue warnings
            summarize_threshold: Percentage at which to trigger summarization
            client: LLM client for generating summaries
            model_name: Model name for the client
        """
        self.token_manager = TokenManager(
            max_tokens=max_tokens,
            warning_threshold=warning_threshold,
            summarize_threshold=summarize_threshold
        )
        self.messages = []
        self.system_prompt = None
        self.client = client
        self.model_name = model_name
    
    def add_message(self, content: str, role: str) -> None:
        """Add a message to the conversation"""
        message = Message(content, role)
        self.messages.append(message)
        self.token_manager.add_tokens(message.token_count)
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set or update the system prompt"""
        old_token_count = 0
        if self.system_prompt:
            old_token_count = estimate_tokens(self.system_prompt)
        
        self.system_prompt = prompt
        new_token_count = estimate_tokens(prompt)
        
        # Adjust token count - only add the difference
        self.token_manager.add_tokens(new_token_count - old_token_count)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages including system prompt if set"""
        result = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        
        for message in self.messages:
            result.append(message.to_dict())
        
        return result
    
    def clear(self) -> None:
        """Clear conversation history but keep system prompt"""
        system_tokens = 0
        if self.system_prompt:
            system_tokens = estimate_tokens(self.system_prompt)
        
        self.messages = []
        self.token_manager.reset()
        
        # Re-add system prompt tokens
        if self.system_prompt:
            self.token_manager.add_tokens(system_tokens)
    
    def get_token_status(self) -> Dict[str, Any]:
        """Get token usage status"""
        return self.token_manager.get_status()
    
    async def maybe_summarize(self) -> bool:
        """
        Check if summarization is needed and perform it if so
        
        Returns:
            True if summarization was performed, False otherwise
        """
        if not self.token_manager.should_summarize():
            return False
        
        if not self.client or len(self.messages) < 6:
            return False
        
        # Only summarize if we have at least 3 exchanges
        # and keep the most recent exchange intact
        num_to_summarize = len(self.messages) - 4  # Keep last 2 messages (1 exchange)
        if num_to_summarize <= 0:
            return False
        
        # Get the messages to summarize
        to_summarize = self.messages[:num_to_summarize]
        recent_messages = self.messages[num_to_summarize:]
        
        # Format messages for summarization
        summarize_content = ""
        for msg in to_summarize:
            role = "User" if msg.role == "user" else "Assistant"
            summarize_content += f"{role}: {msg.content}\n\n"
        
        # Request to summarize the conversation
        summary_request = [
            {"role": "system", "content": "Summarize the following conversation segment concisely while preserving key information. Use third person, objective language."},
            {"role": "user", "content": summarize_content}
        ]
        
        try:
            # Generate summary
            summary_response = await self.client.complete(
                messages=summary_request,
                max_tokens=1024,
                model=self.model_name
            )
            
            summary_text = summary_response.choices[0].message.content
            
            # Calculate tokens
            old_tokens = sum(msg.token_count for msg in to_summarize)
            summary_tokens = estimate_tokens(summary_text)
            
            # Only use summary if it's actually shorter
            if summary_tokens < old_tokens:
                # Create a new summary message
                summary_message = Message(
                    f"[SUMMARY OF PREVIOUS CONVERSATION: {summary_text}]",
                    "system",
                    summary_tokens
                )
                
                # Replace summarized messages with the summary
                self.messages = [summary_message] + recent_messages
                
                # Adjust token count
                token_adjustment = summary_tokens - old_tokens
                self.token_manager.current_tokens += token_adjustment
                
                # Mark summarization as performed
                self.token_manager.summarization_performed = True
                return True
        except Exception as e:
            print(f"Error during summarization: {str(e)}")
        
        return False
    
    def get_recent_conversation_text(self, num_exchanges: int = 3) -> str:
        """
        Get the recent conversation formatted as text
        
        Args:
            num_exchanges: Number of recent exchanges to include
            
        Returns:
            Formatted conversation text
        """
        # Get recent messages, limited to num_exchanges user-assistant pairs
        message_limit = num_exchanges * 2
        recent_messages = self.messages[-message_limit:] if len(self.messages) >= message_limit else self.messages
        
        # Format the conversation
        conversation_text = "Recent conversation:\n\n"
        for msg in recent_messages:
            role = "User" if msg.role == "user" else "Assistant"
            conversation_text += f"{role}: {msg.content}\n\n"
        
        return conversation_text

class ContextSummarizer:
    """Summarize conversation context to reduce token usage"""
    
    @staticmethod
    async def summarize_conversation_block(messages: List[Dict[str, Any]], 
                                     client, 
                                     model_name: str) -> Dict[str, Any]:
        """Summarize a block of conversation messages using the LLM"""
        # Format the conversation for summarization
        conversation_text = "\n\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # Create summarization prompt
        prompt = f"""Below is a segment of conversation. 
Please summarize the key points in a concise way that preserves all important information.
Focus on facts, preferences, and context that would be important for continuing the conversation.

CONVERSATION:
{conversation_text}

SUMMARY:"""
        
        # Call the LLM for summarization
        try:
            response = await client.complete(
                messages=[{"role": "system", "content": "You are a summarization assistant."},
                         {"role": "user", "content": prompt}],
                max_tokens=1024,
                model=model_name
            )
            summary = response.choices[0].message.content
            
            # Create a special summary message
            return {
                "role": "system",
                "content": f"CONVERSATION SUMMARY: {summary}",
                "is_summary": True
            }
        except Exception as e:
            # Fallback if summarization fails
            return {
                "role": "system",
                "content": f"Previous conversation omitted to save space. Contains {len(messages)} messages.",
                "is_summary": True
            }
    
    @staticmethod
    def create_fallback_summary(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a simple summary without using the LLM (for fallback)"""
        # Count message types
        user_messages = sum(1 for m in messages if m.get("role") == "user")
        assistant_messages = sum(1 for m in messages if m.get("role") == "assistant")
        
        # Extract key topics (simple keyword extraction)
        all_text = " ".join([m.get("content", "") for m in messages])
        words = re.findall(r'\b\w{4,}\b', all_text.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top 5 words as topics
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        topics = [word for word, _ in top_words]
        
        # Create summary content
        content = f"SUMMARIZED CONTEXT: {user_messages} user messages and {assistant_messages} assistant messages about {', '.join(topics)}"
        
        return {
            "role": "system",
            "content": content,
            "is_summary": True
        } 